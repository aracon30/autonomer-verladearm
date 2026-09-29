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
    """Punktquelle für den Visionary-T Mini CX (siehe PointSource)."""

    def __init__(
        self,
        ip: str = "192.168.1.10",
        control_port: int = 2122,
        streaming_port: int = 2114,
        frames: int = 3,
        password: str = "CUST_SERV",
        min_valid_fraction: float = 0.2,
        connect: bool = True,
    ):
        self.ip = ip
        self.control_port = control_port
        self.streaming_port = streaming_port
        self.frames = max(1, int(frames))
        self.password = password
        self.min_valid_fraction = min_valid_fraction
        self._control = None
        self._stream = None
        if connect:
            self._connect()

    # --- Geräteanbindung (SICK-Bibliothek) -------------------------------------------------
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
        self._snapshot()
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

    def close(self):
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
        try:
            return self._grab()
        except (OSError, RuntimeError) as e:  # Verbindung weg: einmal neu verbinden
            log.warning("Visionary-T Mini: %s, verbinde neu", e)
            self.close()
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

