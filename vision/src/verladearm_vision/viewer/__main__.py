"""Live-Ansicht im Browser: Punktwolke, Erkennung und schematische Armbewegung.

Zwei Betriebsarten:
    python -m verladearm_vision.viewer            eigene Messungen aus der konfigurierten Quelle
    python -m verladearm_vision.viewer --opcua    liest DB_Vision per OPC UA mit (nur lesend) und
                                                  zeigt, was der Vision-Dienst an die SPS liefert
-> http://127.0.0.1:8000 im Browser öffnen
"""

import argparse
import asyncio
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path

import numpy as np
from asyncua import Client

from verladearm_vision.calibration import SensorToArm
from verladearm_vision.config import load_config
from verladearm_vision.detection import DetectionError, DetectorConfig, detect_opening
from verladearm_vision.kinematics import (
    ArmGeometry,
    forward,
    plan_motion,
    product_insertion_depth,
)
from verladearm_vision.plc import VARIABLES
from verladearm_vision.service.main import build_source

log = logging.getLogger("verladearm.viewer")

# Handshake-Signale aus DB_Vision, die die Seite live anzeigt
SIGNALS = ("Ready", "Trigger", "Busy", "Done", "Error", "ErrorCode", "ResultId", "ProductId",
           "HeartbeatPLC", "HeartbeatPC", "InterfaceVersion")


class FrameProducer:
    """Nimmt eine Punktwolke auf, erkennt die Öffnung und bereitet alles für den Browser auf."""

    def __init__(self, cfg: dict, max_points: int = 20000):
        self.source = build_source(cfg["source"])
        self.det_cfg = DetectorConfig(**cfg.get("detection", {}))
        self.transform = SensorToArm(cfg["calibration"]["matrix"])
        self.geom = ArmGeometry(**cfg.get("arm", {}))
        self.products = cfg.get("products")
        self.max_points = max_points
        self.rng = np.random.default_rng()
        self.frame_id = 0
        self.lock = threading.Lock()  # Quelle und Zähler nicht parallel benutzen

    def next_frame(self) -> dict:
        with self.lock:
            points = self.source.grab()
            self.frame_id += 1
            frame_id = self.frame_id

        t0 = time.perf_counter()
        try:
            op = detect_opening(points, self.det_cfg)
            result = {
                "ok": True,
                "error_code": 0,
                "target_mm": [round(float(x), 1) for x in self.transform.point(op.center) * 1000],
                "normal": [round(float(x), 4) for x in self.transform.direction(op.normal)],
                "diameter_mm": round(op.diameter * 1000, 1),
                "confidence": round(op.confidence, 3),
            }
        except DetectionError as e:
            result = {"ok": False, "error_code": e.code, "message": str(e)}
        detect_ms = (time.perf_counter() - t0) * 1000

        frame = points_for_view(points, self.transform, self.max_points, self.rng)
        frame.update(id=frame_id, detect_ms=round(detect_ms, 1), result=result,
                     arm=arm_for_view(self.geom, result, 0, self.products))
        return frame

    def state(self) -> dict:
        return {"mode": "standalone"}


def points_for_view(points, transform: SensorToArm, max_points: int, rng) -> dict:
    """Für die Anzeige ausdünnen und in Armbasis-Koordinaten umrechnen."""
    shown = points
    if len(shown) > max_points:
        shown = shown[rng.choice(len(shown), max_points, replace=False)]
    shown = shown @ transform.T[:3, :3].T + transform.T[:3, 3]
    return {
        "n_points": len(points),
        "sensor_mm": [round(float(x), 1) for x in transform.point(np.zeros(3)) * 1000],
        "points": np.round(shown, 3).ravel().tolist(),
    }


def arm_for_view(geom: ArmGeometry, result: dict, product_id: int = 0,
                 products: dict | None = None) -> dict:
    """Geplante Armbewegung zum Ergebnis; ohne gültiges Ziel nur die Parkstellung."""
    if result.get("ok"):
        depth = product_insertion_depth(products, product_id, geom.insertion_depth)
        arm = plan_motion(geom, result["target_mm"], result["normal"], insertion_depth=depth)
    else:
        arm = {"ok": False, "park": forward(geom, geom.park).round(4).tolist()}
    arm["ground_z"] = -geom.base_height
    arm["product_id"] = product_id
    arm["obstacles"] = [{"name": o.name, "min": o.min, "max": o.max} for o in geom.obstacles]
    return arm


class PlcMonitor:
    """Liest DB_Vision zyklisch per OPC UA mit. Schreibt nie, beeinflusst den Ablauf also nicht.

    Die Ergebniswerte kommen aus dem Datenbaustein, die Punktwolke aus dem Snapshot, den der
    Vision-Dienst vor dem Setzen von Done ablegt (Konfiguration snapshot.path).
    """

    def __init__(self, cfg: dict, max_points: int = 20000, poll_s: float = 0.1):
        plc = cfg["plc"]
        self.url = plc["url"]
        self.namespace_uri = plc["namespace_uri"]
        self.node_template = plc["node_template"]
        self.poll_s = poll_s
        snapshot = (cfg.get("snapshot") or {}).get("path")
        self.snapshot = Path(snapshot) if snapshot else None
        self.transform = SensorToArm(cfg["calibration"]["matrix"])
        self.geom = ArmGeometry(**cfg.get("arm", {}))
        self.products = cfg.get("products")
        self.max_points = max_points
        self.rng = np.random.default_rng()
        self.lock = threading.Lock()
        self.values: dict = {}
        self.connected = False
        self.error = ""
        self.updated = 0.0

    def start(self):
        threading.Thread(target=lambda: asyncio.run(self._run()), daemon=True).start()

    async def _run(self):
        while True:
            try:
                async with Client(url=self.url) as client:
                    ns = await client.get_namespace_index(self.namespace_uri)
                    names = list(VARIABLES)
                    nodes = [
                        client.get_node(self.node_template.format(ns=ns, name=n)) for n in names
                    ]
                    log.info("OPC UA verbunden mit %s", self.url)
                    while True:
                        values = await client.read_values(nodes)
                        with self.lock:
                            self.values = dict(zip(names, values, strict=True))
                            self.connected, self.error = True, ""
                            self.updated = time.time()
                        await asyncio.sleep(self.poll_s)
            except Exception as e:  # Verbindung verloren: anzeigen und neu verbinden
                with self.lock:
                    self.connected, self.error = False, f"{type(e).__name__}: {e}"
                log.warning("OPC UA: %s, neuer Versuch in 2 s", self.error)
                await asyncio.sleep(2.0)

    def state(self) -> dict:
        with self.lock:
            v = dict(self.values)
            connected, error = self.connected, self.error
        return {
            "mode": "opcua",
            "url": self.url,
            "connected": connected,
            "error": error,
            "signals": {k: v.get(k) for k in SIGNALS},
        }

    def next_frame(self) -> dict:
        with self.lock:
            v = dict(self.values)
        if not v:
            raise RuntimeError("Noch keine Daten von der SPS")
        ok = not v["Error"]
        result = {"ok": ok, "error_code": int(v["ErrorCode"])}
        if ok:
            result.update(
                target_mm=[round(float(v[k]), 1) for k in ("TargetX", "TargetY", "TargetZ")],
                normal=[round(float(v[k]), 4) for k in ("NormalX", "NormalY", "NormalZ")],
                diameter_mm=round(float(v["DiameterMm"]), 1),
                confidence=round(float(v["Confidence"]), 3),
            )
        frame = {"id": int(v["ResultId"]), "detect_ms": None, "result": result,
                 "arm": arm_for_view(self.geom, result, int(v["ProductId"]), self.products)}
        if self.snapshot and self.snapshot.exists():
            frame.update(points_for_view(np.load(self.snapshot), self.transform,
                                         self.max_points, self.rng))
        else:
            frame.update(points=[], n_points=0, note="Keine Punktwolke: snapshot.path im "
                         "Vision-Dienst setzen und denselben Pfad hier konfigurieren.")
        return frame


def make_handler(producer):
    page = resources.files("verladearm_vision.viewer").joinpath("index.html").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body: bytes, content_type: str, status: int = 200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(page, "text/html; charset=utf-8")
            elif self.path == "/api/state":
                self._send(json.dumps(producer.state()).encode(), "application/json")
            elif self.path == "/api/frame":
                try:
                    frame = producer.next_frame()
                except Exception as e:  # Anzeige soll den Fehler zeigen statt abzubrechen
                    log.exception("Messung fehlgeschlagen")
                    frame = {"result": {"ok": False, "error_code": 90, "message": str(e)}}
                self._send(json.dumps(frame).encode(), "application/json")
            else:
                self._send(b"Nicht gefunden", "text/plain; charset=utf-8", 404)

        def log_message(self, fmt, *args):
            log.debug(fmt, *args)

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Live-Ansicht Verladearm")
    parser.add_argument("--config", default="vision/config/default.yaml")
    parser.add_argument("--host", default="127.0.0.1", help="0.0.0.0 = im Netzwerk erreichbar")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-points", type=int, default=20000, help="Punkte je Bild im Browser")
    parser.add_argument(
        "--opcua", action="store_true", help="DB_Vision per OPC UA mitlesen statt selbst zu messen"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    cfg = load_config(args.config)
    if args.opcua:
        producer = PlcMonitor(cfg, args.max_points)
        producer.start()
    else:
        producer = FrameProducer(cfg, args.max_points)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(producer))
    log.info("Live-Ansicht: http://%s:%d", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Beendet")


if __name__ == "__main__":
    main()
