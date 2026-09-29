"""Live-Ansicht im Browser: Punktwolke, Erkennung und schematische Armbewegung.

Beispiel:
    python -m verladearm_vision.viewer --config vision/config/default.yaml
    -> http://127.0.0.1:8000 im Browser öffnen
"""

import argparse
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources

import numpy as np

from verladearm_vision.calibration import SensorToArm
from verladearm_vision.config import load_config
from verladearm_vision.detection import DetectionError, DetectorConfig, detect_opening
from verladearm_vision.service.main import build_source

log = logging.getLogger("verladearm.viewer")


class FrameProducer:
    """Nimmt eine Punktwolke auf, erkennt die Öffnung und bereitet alles für den Browser auf."""

    def __init__(self, cfg: dict, max_points: int = 20000):
        self.source = build_source(cfg["source"])
        self.det_cfg = DetectorConfig(**cfg.get("detection", {}))
        self.transform = SensorToArm(cfg["calibration"]["matrix"])
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

        # Für die Anzeige ausdünnen und in Armbasis-Koordinaten umrechnen
        shown = points
        if len(shown) > self.max_points:
            shown = shown[self.rng.choice(len(shown), self.max_points, replace=False)]
        shown = shown @ self.transform.T[:3, :3].T + self.transform.T[:3, 3]
        return {
            "id": frame_id,
            "n_points": len(points),
            "detect_ms": round(detect_ms, 1),
            "sensor_mm": [round(float(x), 1) for x in self.transform.point(np.zeros(3)) * 1000],
            "points": np.round(shown, 3).ravel().tolist(),
            "result": result,
        }


def make_handler(producer: FrameProducer):
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
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
    producer = FrameProducer(load_config(args.config), args.max_points)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(producer))
    log.info("Live-Ansicht: http://%s:%d", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Beendet")


if __name__ == "__main__":
    main()
