"""SICK Visionary-T Mini CX (3D-Time-of-Flight, Gigabit Ethernet).

Nutzt die offizielle SICK-Bibliothek `visionary-python-base` (Import `python_base`):
    pip install -e ".[sick]"

Ablauf je Messung (Snapshot-Betrieb, damit nie ein veraltetes Bild aus dem Puffer kommt):
    Kamera steht im FrontendMode "Stopped" -> singleStep() -> Bild über den Blob-Stream (TCP 2114)
Mehrere Bilder werden pixelweise per Median gemittelt, das senkt das ToF-Rauschen (Tankwagen steht).

Koordinaten: Kamerasystem der Visionary-Bibliothek ohne die in SOPAS eingestellte Montage.
z entlang der optischen Achse (vom Sensor weg), Meter. Die Lage zur Armbasis bestimmt allein die
Hand-Auge-Kalibrierung (calibration.matrix).
"""

import logging
import threading
import time
import warnings
from dataclasses import dataclass

import numpy as np

log = logging.getLogger(__name__)


@dataclass
class CameraParams:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    k1: float = 0.0
    k2: float = 0.0
    f2rc: float = 0.0  # Abstand Brennpunkt -> Strahlenkreuzung [mm]

    @classmethod
    def from_sick(cls, p):
        return cls(int(p.width), int(p.height), float(p.fx), float(p.fy), float(p.cx),
                   float(p.cy), float(p.k1), float(p.k2), float(p.f2rc or 0.0))


def depth_to_points(distance_mm: np.ndarray, cam: CameraParams) -> np.ndarray:
    """Radiale ToF-Distanzen (H, W) in mm -> Punkte (N, 3) in Metern; NaN-Pixel entfallen.

    Formel wie in SICK PointCloud.convertToPointCloudOptimized (Mono/ToF), vektorisiert.
    """
    d = np.asarray(distance_mm, dtype=float).reshape(cam.height, cam.width)
    xp = (cam.cx - np.arange(cam.width)) / cam.fx
    yp = (cam.cy - np.arange(cam.height)) / cam.fy
    xp, yp = np.meshgrid(xp, yp)  # (H, W)
    r2 = xp * xp + yp * yp
    k = 1 + cam.k1 * r2 + cam.k2 * r2 * r2
    xd, yd = xp * k, yp * k
    s0 = np.sqrt(xd * xd + yd * yd + 1)
    pts = np.stack([xd * d / s0, yd * d / s0, d / s0 - cam.f2rc], axis=-1).reshape(-1, 3)
    return pts[np.isfinite(pts).all(axis=1)] / 1000.0


class SickVisionarySource:
    """Punktquelle für den Visionary-T Mini CX (siehe PointSource).

    Die Kamera braucht nach dem Einschalten ca. 20 s (bei Frost länger). Der Dienst startet
    trotzdem: Ein Hintergrund-Thread verbindet sich alle `retry_s` Sekunden neu, bis die Kamera
    antwortet. `ready` meldet, ob sie verbunden ist (die SPS sieht dann `Ready`).
    """

    def __init__(
        self,
        ip: str = "192.168.1.10",
        control_port: int = 2122,
        streaming_port: int = 2114,
        frames: int = 3,
        password: str = "CUST_SERV",
        min_valid_fraction: float = 0.2,
        retry_s: float = 5.0,
        connect: bool = True,
    ):
        self.ip = ip
        self.control_port = control_port
        self.streaming_port = streaming_port
        self.frames = max(1, int(frames))
        self.password = password
        self.min_valid_fraction = min_valid_fraction
        self.retry_s = retry_s
        self._auto = connect  # False: ohne Gerät (Tests), kein Verbindungsaufbau
        self._control = None
        self._stream = None
        self._lock = threading.RLock()
        self._stop = threading.Event()
        if connect:
            threading.Thread(target=self._keep_connected, name="sick-verbinden",
                             daemon=True).start()

    @property
    def ready(self) -> bool:
        """Kamera verbunden und bereit (ohne Gerät, z. B. in Tests: immer bereit)."""
        return self._control is not None or not self._auto

    # --- Geräteanbindung (SICK-Bibliothek) -------------------------------------------------
    def _keep_connected(self):
        failed = 0
        while not self._stop.is_set():
            if self._control is None and self._lock.acquire(blocking=False):
                try:  # Lock nur, wenn gerade keine Messung läuft (die verbindet selbst neu)
                    if self._control is None:
                        self._connect()
                    failed = 0
                except Exception as e:  # Kamera startet noch, Netz weg, falsche IP
                    failed += 1
                    log.log(logging.WARNING if failed in (1, 12) else logging.DEBUG,
                            "Visionary-T Mini %s nicht erreichbar (%s), neuer Versuch alle %.0f s",
                            self.ip, e, self.retry_s)
                finally:
                    self._lock.release()
            self._stop.wait(self.retry_s)

    def _connect(self):
        try:
            from python_base.Control import Control
            from python_base.Stream import Streaming
            from python_base.Usertypes import FrontendMode
        except ImportError as e:
            raise ImportError(
                "SICK-Bibliothek fehlt. Installation: pip install -e \".[sick]\""
            ) from e
        log.info("Verbinde mit Visionary-T Mini %s", self.ip)
        control = Control(self.ip, "Cola2", self.control_port)
        control.open()
        control.login(Control.USERLEVEL_SERVICE, self.password)
        control.setFrontendMode(FrontendMode.Stopped)  # Snapshot-Betrieb
        control.logout()
        stream = Streaming(self.ip, self.streaming_port)
        stream.openStream()
        self._control, self._stream = control, stream
        # Nach dem Stoppen braucht das Frontend ein Aufwärmbild (Hinweis in den SICK-Beispielen)
        try:
            self._snapshot()
        except Exception:
            self._drop()
            raise
        log.info("Visionary-T Mini bereit")

    def _snapshot(self):
        """Ein Bild: (Distanz [mm] als (H, W) mit NaN für ungültige Pixel, CameraParams)."""
        from python_base.Streaming import Data

        self._control.singleStep()
        self._stream.getFrame()
        data = Data.Data()
        data.read(self._stream.frame, convertToMM=True)
        if not data.hasDepthMap:
            raise RuntimeError("Bild ohne Tiefendaten empfangen")
        cam = CameraParams.from_sick(data.cameraParams)
        dist = np.asarray(data.depthmap.distance, dtype=float).reshape(cam.height, cam.width)
        conf = np.asarray(data.depthmap.confidence).reshape(cam.height, cam.width)
        dist[(conf != 0) | (dist <= 0)] = np.nan  # SICK: Zustandswert 0 = gültig
        return dist, cam

    def _drop(self):
        """Verbindung verwerfen (nach Fehler), der Hintergrund-Thread verbindet neu."""
        for closer in (lambda: self._stream.closeStream(), lambda: self._control.close()):
            try:
                closer()
            except Exception:
                pass
        self._control = self._stream = None

    def close(self):
        self._stop.set()
        with self._lock:
            if self._control is None:
                return
            try:
                from python_base.Control import Control
                from python_base.Usertypes import FrontendMode

                self._stream.closeStream()
                self._control.login(Control.USERLEVEL_SERVICE, self.password)
                self._control.setFrontendMode(FrontendMode.Continuous)
                self._control.logout()
                self._control.close()
            except Exception as e:  # beim Beenden nur protokollieren
                log.warning("Visionary-T Mini sauber trennen fehlgeschlagen: %s", e)
            self._control = self._stream = None

    # --- PointSource ---------------------------------------------------------------------
    def grab(self) -> np.ndarray:
        if not self.ready:  # sofort melden, nicht auf einen laufenden Verbindungsversuch warten
            raise RuntimeError(f"Visionary-T Mini {self.ip} nicht verbunden")
        with self._lock:
            try:
                return self._grab()
            except (OSError, RuntimeError) as e:  # Verbindung weg: einmal neu verbinden
                if not self._auto:
                    raise
                log.warning("Visionary-T Mini: %s, verbinde neu", e)
                self._drop()
                time.sleep(1.0)
                self._connect()
                return self._grab()

    def _grab(self) -> np.ndarray:
        shots = [self._snapshot() for _ in range(self.frames)]
        cam = shots[0][1]
        stack = np.stack([s[0] for s in shots])
        with warnings.catch_warnings():  # Pixel ohne gültigen Wert sind hier erwartet
            warnings.simplefilter("ignore", category=RuntimeWarning)
            dist = np.nanmedian(stack, axis=0)
        valid = np.isfinite(dist).mean()
        if valid < self.min_valid_fraction:
            log.warning("Nur %.0f %% gültige Pixel (Verschmutzung, Blendung?)", valid * 100)
        return depth_to_points(dist, cam)

