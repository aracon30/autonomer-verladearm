"""Hauptprogramm: Sensor -> Erkennung -> Kalibrierung -> SPS.

Beispiele:
    python -m verladearm_vision.service.main --config vision/config/default.yaml --once
    python -m verladearm_vision.service.main --config vision/config/default.yaml
"""

import argparse
import asyncio
import inspect
import logging
import os
import time
from pathlib import Path

import numpy as np

from verladearm_vision.acquisition import FileSource, SickVisionarySource
from verladearm_vision.acquisition.simulation import SimulatedScene
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
    JOINTS,
    ArmGeometry,
    pick,
    plan_correction,
    plan_motion,
    plan_retract,
    product_insertion_depth,
)
from verladearm_vision.plc import (
    JOB_CORRECT,
    JOB_MEASURE_PLAN,
    JOB_RETRACT,
    MAX_WAYPOINTS,
    MeasureResult,
    PlcInterface,
    Request,
)
from verladearm_vision.recording import Recorder
from verladearm_vision.scene import SceneConfig, build_obstacles

log = logging.getLogger("verladearm")

ERR_NOT_HOMED = 32
ERR_NO_TARGET = 34  # Job 2 ohne vorheriges Ergebnis aus Job 1
ERR_UNKNOWN_JOB = 91


def _params_for(cls, cfg: dict) -> dict:
    """Nur die Einträge, die die Quelle kennt (Anlagendateien erben z. B. `path` von default)."""
    accepted = inspect.signature(cls.__init__).parameters
    return {k: v for k, v in cfg.items() if k in accepted}


def build_source(cfg: dict, full_cfg: dict | None = None):
    kind = cfg["type"]
    if kind == "file":
        return FileSource(cfg["path"], cfg.get("pattern", "*"))
    if kind == "sick":
        return SickVisionarySource(**_params_for(SickVisionarySource, cfg))
    if kind == "sim":
        full_cfg = full_cfg or {}
        return SimulatedScene(ArmGeometry(**full_cfg.get("arm", {})),
                              SensorToArm(full_cfg["calibration"]["matrix"]),
                              **_params_for(SimulatedScene, cfg))
    raise ValueError(f"Unbekannte Quelle: {kind}")


def save_snapshot(path: Path, points: np.ndarray):
    """Letzte Punktwolke für die Live-Ansicht ablegen (atomar, nie halbe Dateien)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "wb") as f:
            np.save(f, points.astype(np.float32))
        os.replace(tmp, path)
    except OSError as e:
        log.warning("Snapshot nicht gespeichert: %s", e)


def _r(v, digits=1):
    return tuple(round(float(x), digits) for x in v)


class VisionService:
    """Bearbeitet die Aufträge der SPS (docs/schnittstelle.md, InterfaceVersion 2).

    Job 0: nur messen · Job 1: Dom messen und Bahn planen · Job 2: Auslass nachmessen und Bahn
    korrigieren · Job 3: Rückfahrt planen. Die SPS prüft jede Vorgabe und fährt mit ihren
    Technologieobjekten (Rampen, Ruckbegrenzung).
    """

    def __init__(self, cfg: dict):
        self.transform = SensorToArm(cfg["calibration"]["matrix"])
        self.geom = ArmGeometry(**cfg.get("arm", {}))
        self.source = build_source(cfg["source"], cfg)
        self.det_cfg = DetectorConfig(**cfg.get("detection", {}))
        self.outlet_cfg = OutletConfig(**cfg.get("outlet", {}))
        self.scene_cfg = SceneConfig(**cfg.get("scene", {}))
        self.products = cfg.get("products")
        planning = cfg.get("planning", {})
        self.move_waypoints = int(planning.get("move_waypoints", 3))
        self.insert_waypoints = int(planning.get("insert_waypoints", 5))
        self.plan_time_limit = float(planning.get("time_limit_s", 3.5))
        snapshot = (cfg.get("snapshot") or {}).get("path")
        self.snapshot = Path(snapshot) if snapshot else None
        self.last = None  # Ziel aus Job 1: target_mm, normal, depth, diameter, confidence
        rec = cfg.get("recording") or {}
        self.recorder = Recorder(rec.get("dir", "data/aufzeichnung"), rec.get("keep_days", 60),
                                 rec.get("enabled", True), cfg.get("station", ""))
        self._points = None
        self._info = {}

    # --- Hilfen ---------------------------------------------------------------------------
    def _grab(self, req: Request) -> np.ndarray:
        if hasattr(self.source, "prepare"):  # Simulation: Stellung des Arms mitgeben
            self.source.prepare(req.job, req.actual_deg if req.axes_homed else None)
        t0 = time.perf_counter()
        points = self.source.grab()
        self._points = points
        self._info["aufnahme_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        if self.snapshot:
            save_snapshot(self.snapshot, points)
        return points

    def _q_actual(self, req: Request):
        q = np.array([self.geom.joints[k].to_model(v)
                      for k, v in zip(JOINTS, req.actual_deg, strict=True)])
        lo, hi = self.geom.bounds
        tol = np.radians(1.0)
        if np.any(q < lo - tol) or np.any(q > hi + tol):
            return None
        return q

    def _waypoints(self, *segments):
        wps, approach = [], 0
        for seq, n, is_approach in segments:
            part = pick(seq, n)
            wps += [self.geom.to_servo(q) for q in part]
            if is_approach:
                approach = len(wps)
        if len(wps) > MAX_WAYPOINTS:
            raise ValueError(f"{len(wps)} Stützpunkte, maximal {MAX_WAYPOINTS}")
        return [tuple(w) for w in wps], approach

    def _move_segment(self, plan, q_start, n):
        """Anfahrt: Zwischenziele eines Umwegs oder gleichmäßig verteilte Punkte der Direktfahrt."""
        vias = plan.get("move_vias") or []
        if len(vias) > 1:
            return [q_start] + vias, len(vias)
        return plan["q_move"], n

    def _scene_geom(self):
        """Armgeometrie mit den Hindernissen des aktuellen Tankwagens (aus Job 1)."""
        return self.geom.with_obstacles((self.last or {}).get("obstacles"))

    def _fail(self, code, message, **kw):
        log.warning("%s (Code %d)", message, code)
        return MeasureResult(ok=False, error_code=code, message=message, **kw)

    # --- Aufträge -------------------------------------------------------------------------
    def __call__(self, req: Request) -> MeasureResult:
        self._points, self._info = None, {}
        t0 = time.perf_counter()
        result = self._dispatch(req)
        self._info["gesamt_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        self.recorder.save(req, result, self._points, self._info)
        return result

    def _dispatch(self, req: Request) -> MeasureResult:
        if req.job == 0:
            return self._measure(req)[0]
        if req.job not in (JOB_MEASURE_PLAN, JOB_CORRECT, JOB_RETRACT):
            return self._fail(ERR_UNKNOWN_JOB, f"Unbekannter Auftrag {req.job}")
        q_act = self._q_actual(req) if req.axes_homed else None
        if q_act is None:
            return self._fail(ERR_NOT_HOMED, "Achsen nicht referenziert oder Istwinkel unplausibel")
        if req.job == JOB_MEASURE_PLAN:
            return self._job_measure_plan(req, q_act)
        if req.job == JOB_CORRECT:
            return self._job_correct(req, q_act)
        return self._job_retract(q_act)

    def _measure(self, req: Request):
        try:
            op = detect_opening(self._grab(req), self.det_cfg)
        except DetectionError as e:
            return self._fail(e.code, str(e)), None
        res = MeasureResult(
            ok=True,
            target_mm=_r(self.transform.point(op.center) * 1000.0),
            normal=_r(self.transform.direction(op.normal), 4),
            diameter_mm=round(op.diameter * 1000.0, 1),
            confidence=round(op.confidence, 3),
        )
        return res, op

    def _job_measure_plan(self, req: Request, q_act) -> MeasureResult:
        res, op = self._measure(req)
        if not res.ok:
            self.last = None
            return res
        depth = product_insertion_depth(self.products, req.product_id, self.geom.insertion_depth)
        # Tankkörper, Domkragen und offener Deckel als Hindernisse für alle folgenden Bahnen
        obstacles, scene_info = build_obstacles(op, self.transform, self._points,
                                                self.outlet_cfg, self.scene_cfg)
        self.last = dict(target_mm=res.target_mm, normal=res.normal, depth=depth,
                         diameter_mm=res.diameter_mm, confidence=res.confidence,
                         obstacles=obstacles)
        plan = plan_motion(self._scene_geom(), res.target_mm, res.normal, insertion_depth=depth,
                           q_start=q_act, time_limit=self.plan_time_limit)
        self._info.update(eintauchtiefe_m=depth, szene=scene_info,
                          umweg=len(plan.get("move_vias") or []) > 1)
        if plan["ok"]:  # geprüfter Anfahrweg bis zum Vorpunkt, rückwärts Notweg für Job 3
            self.last["approach"] = [q_act.tolist()] + plan["move_vias"][:-1]
        if not plan["ok"]:
            return self._fail(plan["code"], plan["reason"], target_mm=res.target_mm,
                              normal=res.normal, diameter_mm=res.diameter_mm,
                              confidence=res.confidence)
        move, n_move = self._move_segment(plan, q_act, self.move_waypoints)
        res.waypoints, res.approach_index = self._waypoints(
            (move, n_move, True),
            (plan["q_insert"], self.insert_waypoints, False),
        )
        return res

    def _job_correct(self, req: Request, q_act) -> MeasureResult:
        if self.last is None:
            return self._fail(ERR_NO_TARGET, "Kein Dom aus Job 1 vorhanden")
        last = self.last
        keep = dict(target_mm=last["target_mm"], normal=last["normal"],
                    diameter_mm=last["diameter_mm"], confidence=last["confidence"])
        points = self._grab(req)
        arm_pts = points @ self.transform.T[:3, :3].T + self.transform.T[:3, 3]
        try:
            tip = detect_outlet(arm_pts, np.asarray(last["target_mm"]) / 1000.0,
                                self.transform.point(np.zeros(3)), self.outlet_cfg)
        except DetectionError as e:
            return self._fail(e.code, str(e), **keep)
        plan = plan_correction(self._scene_geom(), q_act, tip, last["target_mm"],
                               last["normal"], last["depth"])
        self._info.update(auslass_gemessen_mm=(tip * 1000).round(1),
                          modellabweichung_mm=plan["model_offset_mm"])
        corr = tuple(plan["correction_mm"][:2])
        if not plan["ok"]:
            return self._fail(plan["code"], plan["reason"], correction_mm=corr, **keep)
        q_ins = plan["q_insert"]
        wps, _ = self._waypoints(([q_act, q_ins[0]], 1, False), (q_ins, self.insert_waypoints,
                                                                   False))
        log.info("Korrektur %s mm, Modellabweichung %s mm", corr, plan["model_offset_mm"])
        return MeasureResult(ok=True, waypoints=wps, approach_index=1, correction_mm=corr, **keep)

    def _job_retract(self, q_act) -> MeasureResult:
        if self.last is not None:
            lift = self.geom.approach_height + self.geom.approach_lift + self.last["depth"]
        else:  # z. B. nach Neustart: größte hinterlegte Eintauchtiefe annehmen
            depths = [product_insertion_depth(self.products, k, self.geom.insertion_depth)
                      for k in (self.products or {})] or [self.geom.insertion_depth]
            lift = self.geom.approach_height + self.geom.approach_lift + max(depths)
        plan = plan_retract(self._scene_geom(), q_act, lift,
                            fallback=(self.last or {}).get("approach"))
        self._info["rueckfahrt_rueckwaerts"] = bool(plan.get("reversed"))
        if not plan["ok"]:
            return self._fail(plan["code"], plan["reason"])
        move, n_move = self._move_segment(plan, plan["q_lift"][-1], 3)
        wps, _ = self._waypoints((plan["q_lift"], 2, False), (move, n_move, False))
        self.last = None
        return MeasureResult(ok=True, waypoints=wps, approach_index=0)


def main():
    parser = argparse.ArgumentParser(description="Verladearm Vision-Dienst")
    parser.add_argument("--config", default="vision/config/default.yaml")
    parser.add_argument("--once", action="store_true",
                        help="einen Auftrag ohne SPS ausführen (Arm in Parkstellung)")
    parser.add_argument("--job", type=int, default=0, help="Auftrag für --once (0 = nur messen)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    cfg = load_config(args.config)
    service = VisionService(cfg)

    if args.once:
        park = tuple(service.geom.joints[k].park for k in JOINTS)
        print(service(Request(job=args.job, actual_deg=park, axes_homed=True)))
        return

    plc = PlcInterface(**cfg["plc"])
    try:
        asyncio.run(plc.run(service))
    except KeyboardInterrupt:
        log.info("Beendet")


if __name__ == "__main__":
    main()
