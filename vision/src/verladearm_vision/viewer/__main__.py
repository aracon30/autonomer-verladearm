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
from verladearm_vision.detection import (
    DetectionError,
    DetectorConfig,
    OutletConfig,
    detect_opening,
    detect_outlet,
)
from verladearm_vision.kinematics import (
    FEED_NAME,
    JOINTS,
    ArmGeometry,
    CylinderObstacle,
    OrientedBoxObstacle,
    fixed_parts,
    forward,
    marker_point,
    outlet_axis,
    plan_correction,
    plan_motion,
    product_insertion_depth,
)
from verladearm_vision.plc import VARIABLES
from verladearm_vision.scene import SceneConfig, build_obstacles
from verladearm_vision.service.main import build_source

log = logging.getLogger("verladearm.viewer")

# Handshake-Signale aus DB_Vision, die die Seite live anzeigt
SIGNALS = ("Ready", "Trigger", "Busy", "Done", "Error", "ErrorCode", "ResultId", "ProductId",
           "HeartbeatPLC", "HeartbeatPC", "InterfaceVersion", "Job", "AxesHomed", "ArmState",
           "ActualJ1", "ActualJ2", "ActualJ3", "WaypointCount", "ApproachIndex", "CorrectionX",
           "CorrectionY")


class FrameProducer:
    """Nimmt eine Punktwolke auf, erkennt die Öffnung und bereitet alles für den Browser auf."""

    def __init__(self, cfg: dict, max_points: int = 20000):
        self.source = build_source(cfg["source"], cfg)
        self.det_cfg = DetectorConfig(**cfg.get("detection", {}))
        self.transform = SensorToArm(cfg["calibration"]["matrix"])
        self.geom = ArmGeometry(**cfg.get("arm", {}))
        self.outlet_cfg = OutletConfig(**cfg.get("outlet", {}))
        self.scene_cfg = SceneConfig(**cfg.get("scene", {}))
        self.products = cfg.get("products")
        self.max_points = max_points
        self.rng = np.random.default_rng()
        self.frame_id = 0
        self.lock = threading.Lock()  # Quelle und Zähler nicht parallel benutzen

    def next_frame(self) -> dict:
        sim = hasattr(self.source, "prepare")  # simulierter Sensor: Arm steht in Parkstellung
        with self.lock:
            if sim:
                self.source.prepare(1, [self.geom.joints[k].park for k in JOINTS])
            points = self.source.grab()
            self.frame_id += 1
            frame_id = self.frame_id

        t0 = time.perf_counter()
        op = None
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

        # Tankkörper, Domkragen und offener Deckel als Hindernisse wie im Vision-Dienst
        geom, scene = scene_geom(self.geom, op, self.transform, points, self.outlet_cfg,
                                 self.scene_cfg)
        q_park = self.geom.park
        frame = points_for_view(points, self.transform, self.max_points, self.rng,
                                self.geom, q_park)
        arm = arm_for_view(geom, result, 0, self.products, self.outlet_cfg)
        frame.update(id=frame_id, detect_ms=round(detect_ms, 1), result=result, scene=scene,
                     arm=arm, vehicle=vehicle_for_view(op, self.transform),
                     relief=dome_relief(points, self.transform, op, self.geom, q_park),
                     passage=passage_for_view(op, self.transform, scene, arm))
        if sim and frame["arm"].get("ok"):
            with self.lock:
                self._simulate_correction(frame, geom)
        for key in ("q_move", "q_insert"):
            frame["arm"].pop(key, None)
        return frame

    def _simulate_correction(self, frame: dict, geom: ArmGeometry):
        """Job 2 mit simuliertem Getriebespiel: Arm steht daneben, Scheibe nachmessen, korrigieren.

        Gezeichnet wird die tatsächliche Stellung (Modell + Getriebespiel) wie im Sensorbild.
        """
        arm, res = frame["arm"], frame["result"]
        q_above = np.array(arm["q_insert"][0])
        self.source.prepare(2, self.geom.to_servo(q_above))
        err = getattr(self.source, "offset", np.zeros(3))  # inkl. Getriebespiel
        points = self.source.grab()
        arm_pts = points @ self.transform.T[:3, :3].T + self.transform.T[:3, 3]
        try:
            tip = detect_outlet(arm_pts, np.asarray(res["target_mm"]) / 1000.0,
                                cfg=self.outlet_cfg, axis=outlet_axis(self.geom, q_above),
                                expected=marker_point(self.geom, q_above,
                                                      self.outlet_cfg.marker_offset))
        except DetectionError as e:
            arm["correction_note"] = str(e)
            return
        corr = plan_correction(geom, q_above, tip, res["target_mm"], res["normal"],
                               arm["insertion_depth"])
        if not corr["ok"]:
            arm["correction_note"] = corr["reason"]
            return

        def true(q):
            return forward(self.geom, np.asarray(q) + err).round(4).tolist()

        q_c = np.array(corr["q_insert"][0])
        arm["move"] = [true(q) for q in arm["q_move"]]
        arm["adjust"] = [true(q_above + (q_c - q_above) * u) for u in np.linspace(0, 1, 12)]
        arm["insert"] = [true(q) for q in corr["q_insert"]]
        arm["correction_mm"] = corr["correction_mm"]
        arm["servo_inside_deg"] = corr.get("servo_inside_deg", arm.get("servo_inside_deg"))
        view2 = points_for_view(points, self.transform, self.max_points, self.rng, self.geom,
                                q_above + err)
        frame["points2"], frame["arm_points2"] = view2["points"], view2["arm_points"]

    def state(self) -> dict:
        return {"mode": "standalone"}


def arm_mask(arm_pts: np.ndarray, geom: ArmGeometry, q, radius: float = 0.22) -> np.ndarray:
    """Punkte, die zum Arm selbst gehören (Rohrführung in Stellung q, Fallleitung bzw. Säule)."""
    near = np.zeros(len(arm_pts), bool)
    if q is None or len(arm_pts) == 0:
        return near
    pts = forward(geom, np.asarray(q, float))
    segs = list(zip(pts[:-1], pts[1:], strict=True))
    segs += [(a, b) for a, b, r, _ in fixed_parts(geom)]
    for a, b in segs:
        ab = b - a
        t = np.clip((arm_pts - a) @ ab / max(ab @ ab, 1e-12), 0, 1)
        near |= np.linalg.norm(arm_pts - (a + t[:, None] * ab), axis=1) < radius
    return near


def points_for_view(points, transform: SensorToArm, max_points: int, rng,
                    geom: ArmGeometry | None = None, q=None) -> dict:
    """Für die Anzeige ausdünnen und in Armbasis-Koordinaten umrechnen. Mit Armstellung `q`
    kommen die Punkte am Arm getrennt (`arm_points`), damit man sie ausblenden kann."""
    arm_pts = np.asarray(points) @ transform.T[:3, :3].T + transform.T[:3, 3]
    near = arm_mask(arm_pts, geom, q) if geom is not None else np.zeros(len(arm_pts), bool)
    shown, at_arm = arm_pts[~near], arm_pts[near]
    if len(shown) > max_points:
        shown = shown[rng.choice(len(shown), max_points, replace=False)]
    if len(at_arm) > max_points // 4:
        at_arm = at_arm[rng.choice(len(at_arm), max_points // 4, replace=False)]
    return {
        "n_points": len(points),
        "sensor_mm": [round(float(x), 1) for x in transform.point(np.zeros(3)) * 1000],
        "points": np.round(shown, 3).ravel().tolist(),
        "arm_points": np.round(at_arm, 3).ravel().tolist(),
    }


def dome_relief(points, transform: SensorToArm, op, geom: ArmGeometry, q=None,
                radius: float = 1.0, cell: float = 0.03) -> dict | None:
    """Höhenrelief um die Öffnung aus den Messpunkten: je 3-cm-Zelle unterste und oberste Höhe.

    Zeigt jede Dombauart so, wie sie gemessen wurde (Domring, vertiefter Domdeckel, Füllöffnung
    als Lücke, Klappe, Armaturen, Laufstege). Blick ins Tankinnere und der Arm selbst entfallen."""
    if op is None or points is None:
        return None
    c = transform.point(op.center)
    p = np.asarray(points) @ transform.T[:3, :3].T + transform.T[:3, 3]
    p = p[~arm_mask(p, geom, q)]
    p = p[(np.hypot(p[:, 0] - c[0], p[:, 1] - c[1]) < radius)
          & (p[:, 2] > c[2] - 0.6) & (p[:, 2] < c[2] + 1.2)]
    if len(p) == 0:
        return None
    idx = np.floor((p[:, :2] - c[:2]) / cell).astype(int)
    cells, inv, counts = np.unique(idx, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    order = np.argsort(inv, kind="stable")
    out = []
    for (ix, iy), z in zip(cells, np.split(p[order, 2], np.cumsum(counts)[:-1]), strict=True):
        if len(z) < 2:
            continue
        z = np.sort(z)
        x, y = c[0] + (ix + 0.5) * cell, c[1] + (iy + 0.5) * cell
        out.append([round(float(x), 3), round(float(y), 3), round(float(z[0]), 3),
                    round(float(z[-2]), 3)])
    return {"cell": cell, "rim_z": round(float(c[2]), 3), "cells": out}


def passage_for_view(op, transform: SensorToArm, scene: dict | None, arm: dict) -> dict | None:
    """Senkrechter Durchgang über der Öffnung, in dem der Auslass eintaucht."""
    if op is None or not scene or "durchgang_radius_m" not in scene:
        return None
    c = transform.point(op.center)
    return {"center": c.round(4).tolist(), "radius": scene["durchgang_radius_m"],
            "depth": arm.get("insertion_depth", 0.4)}


def vehicle_for_view(op, transform: SensorToArm) -> dict | None:
    """Tankform für die Anzeige (Armbasis, m). Fahrzeugart grob aus dem Tankradius geschätzt."""
    if op is None:
        return None
    apex = transform.point(op.tank_apex)
    rim = transform.point(op.center)
    v = {"apex": apex.round(4).tolist(), "rim": rim.round(4).tolist(),
         "diameter": round(op.diameter, 3)}
    if op.tank_radius is None:
        v["kind"] = "eben"
    else:
        v.update(kind="kesselwagen" if op.tank_radius >= 1.3 else "lkw",
                 radius=round(op.tank_radius, 3),
                 axis=transform.direction(op.tank_axis).round(4).tolist())
    return v


def scene_geom(geom: ArmGeometry, op, transform: SensorToArm, points, outlet: OutletConfig,
               cfg: SceneConfig):
    """Armgeometrie mit den gemessenen Hindernissen und Szeneninfo (Deckel) für die Anzeige."""
    if op is None:
        return geom, None
    obstacles, info = build_obstacles(op, transform, points, outlet, cfg)
    return geom.with_obstacles(obstacles), info


def obstacle_for_view(o) -> dict:
    """Hindernis für die Anzeige: Quader, gedrehter Quader oder Zylinder (Armbasis, m)."""
    if isinstance(o, OrientedBoxObstacle):
        return {"name": o.name, "type": "obox", "center": list(o.center),
                "axes": [list(a) for a in o.axes], "half": list(o.half)}
    if isinstance(o, CylinderObstacle):
        return {"name": o.name, "type": "cyl", "p0": list(o.p0), "axis": list(o.axis),
                "radius": o.radius, "half_length": o.half_length}
    return {"name": o.name, "type": "box", "min": list(o.min), "max": list(o.max)}


def structure_for_view(geom: ArmGeometry) -> dict:
    """Bauform am Haltepunkt für die 3D-Ansicht: Fallleitung von oben samt Flansch oder Säule,
    dazu der Rohrdurchmesser der Ausleger."""
    return {"support": geom.support, "pipe_r": geom.pipe_diameter / 2,
            "flange_z": geom.flange_offset if geom.support == "oben" else None,
            "parts": [{"a": a.round(4).tolist(), "b": b.round(4).tolist(), "r": r, "kind": k}
                      for a, b, r, k in fixed_parts(geom)]}


def obstacles_for_view(geom: ArmGeometry) -> list:
    """Hindernisse ohne die Fallleitung (die zeigt die Bauform selbst)."""
    return [obstacle_for_view(o) for o in geom.obstacles if o.name != FEED_NAME]


def arm_for_view(geom: ArmGeometry, result: dict, product_id: int = 0,
                 products: dict | None = None, outlet: OutletConfig | None = None) -> dict:
    """Geplante Armbewegung zum Ergebnis; ohne gültiges Ziel nur die Parkstellung."""
    if result.get("ok"):
        depth = product_insertion_depth(products, product_id, geom.insertion_depth)
        arm = plan_motion(geom, result["target_mm"], result["normal"], insertion_depth=depth)
    else:
        arm = {"ok": False, "park": forward(geom, geom.park).round(4).tolist()}
    arm["ground_z"] = -geom.base_height
    arm["product_id"] = product_id
    arm["obstacles"] = obstacles_for_view(geom)
    arm["structure"] = structure_for_view(geom)
    if outlet and outlet.marker_radius:
        arm["marker"] = {"radius": outlet.marker_radius, "offset": outlet.marker_offset}
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
        self.det_cfg = DetectorConfig(**cfg.get("detection", {}))
        self.outlet_cfg = OutletConfig(**cfg.get("outlet", {}))
        self.scene_cfg = SceneConfig(**cfg.get("scene", {}))
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
                    # nur der SPS-Simulator hat einen Bedienstatus (Betriebsart, Verriegelungen)
                    status = client.get_node(f'ns={ns};s="Simulator"."Bedienstatus"')
                    try:
                        await status.read_value()
                    except Exception:
                        status = None
                    while True:
                        values = await client.read_values(nodes)
                        sim_status = await status.read_value() if status else None
                        with self.lock:
                            self.values = dict(zip(names, values, strict=True))
                            self.values["Bedienstatus"] = sim_status
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
        state = {
            "mode": "opcua",
            "url": self.url,
            "connected": connected,
            "error": error,
            "signals": {k: v.get(k) for k in SIGNALS},
            "operation": v.get("Bedienstatus"),
            "ground_z": -self.geom.base_height,
            "obstacles": obstacles_for_view(self.geom),
            "structure": structure_for_view(self.geom),
        }
        if self.outlet_cfg.marker_radius:
            state["marker"] = {"radius": self.outlet_cfg.marker_radius,
                               "offset": self.outlet_cfg.marker_offset}
        if connected and v.get("AxesHomed"):
            # Arm live aus den Istwinkeln der SPS, geplante Stützpunkte als Auslasspositionen
            state["arm_pts"] = forward(self.geom, self._model(
                [v["ActualJ1"], v["ActualJ2"], v["ActualJ3"]])).round(4).tolist()
            n = int(v.get("WaypointCount") or 0)
            if n and not v.get("Error"):
                wps = zip(v["WaypointsJ1"][:n], v["WaypointsJ2"][:n], v["WaypointsJ3"][:n],
                          strict=True)
                state["path"] = [forward(self.geom, self._model(w))[-1].round(4).tolist()
                                 for w in wps]
        return state

    def _model(self, servo_deg):
        return np.array([self.geom.joints[k].to_model(float(d))
                         for k, d in zip(JOINTS, servo_deg, strict=True)])

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
        job = int(v.get("Job") or 0)
        points = np.load(self.snapshot) if self.snapshot and self.snapshot.exists() else None
        op = None
        if points is not None and ok and job != 3:  # Tankform und Hindernisse für die Anzeige
            try:
                op = detect_opening(points, self.det_cfg)
            except DetectionError:
                pass
        geom, scene = scene_geom(self.geom, op, self.transform, points, self.outlet_cfg,
                                 self.scene_cfg)
        frame = {"id": int(v["ResultId"]), "detect_ms": None, "result": result, "job": job,
                 "scene": scene,
                 "correction_mm": [round(float(v["CorrectionX"]), 1),
                                   round(float(v["CorrectionY"]), 1)],
                 "arm": arm_for_view(geom, result, int(v["ProductId"]), self.products,
                                     self.outlet_cfg)}
        n = int(v.get("WaypointCount") or 0)
        if ok and n:
            frame["servo_target"] = [round(float(v[k][n - 1]), 2)
                                     for k in ("WaypointsJ1", "WaypointsJ2", "WaypointsJ3")]
        if points is not None:
            q_act = self._model([v["ActualJ1"], v["ActualJ2"], v["ActualJ3"]])
            frame.update(points_for_view(points, self.transform, self.max_points, self.rng,
                                         self.geom, q_act))
            if op is not None:
                frame["vehicle"] = vehicle_for_view(op, self.transform)
                frame["relief"] = dome_relief(points, self.transform, op, self.geom, q_act)
                frame["passage"] = passage_for_view(op, self.transform, scene, frame["arm"])
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
    try:
        server = ThreadingHTTPServer((args.host, args.port), make_handler(producer))
    except OSError as e:
        raise SystemExit(f"Port {args.port} ist nicht verfügbar ({e.strerror}). "
                         f"Anderen Port wählen, z. B. --port 8080") from None
    shown = args.host if args.host != "0.0.0.0" else "<IP dieses Rechners>"
    log.info("Live-Ansicht: http://%s:%d", shown, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Beendet")


if __name__ == "__main__":
    main()
