"""Hauptprogramm: Sensor -> Erkennung -> Kalibrierung -> SPS.

Beispiele:
    python -m verladearm_vision.service.main --config vision/config/default.yaml --once
    python -m verladearm_vision.service.main --config vision/config/default.yaml
"""

import argparse
import asyncio
import logging

from verladearm_vision.acquisition import FileSource
from verladearm_vision.calibration import SensorToArm
from verladearm_vision.config import load_config
from verladearm_vision.detection import DetectionError, DetectorConfig, detect_opening
from verladearm_vision.plc import MeasureResult, PlcInterface

log = logging.getLogger("verladearm")


def build_source(cfg: dict):
    kind = cfg["type"]
    if kind == "file":
        return FileSource(cfg["path"])
    raise ValueError(f"Unbekannte Quelle: {kind}")  # hier später echte Sensortreiber ergänzen


def build_measure(cfg: dict):
    source = build_source(cfg["source"])
    det_cfg = DetectorConfig(**cfg.get("detection", {}))
    transform = SensorToArm(cfg["calibration"]["matrix"])

    def measure(product_id: int) -> MeasureResult:
        try:
            opening = detect_opening(source.grab(), det_cfg)
        except DetectionError as e:
            log.warning("Erkennung: %s (Code %d)", e, e.code)
            return MeasureResult(ok=False, error_code=e.code, message=str(e))
        target = transform.point(opening.center) * 1000.0
        normal = transform.direction(opening.normal)
        return MeasureResult(
            ok=True,
            target_mm=tuple(round(float(x), 1) for x in target),
            normal=tuple(round(float(x), 4) for x in normal),
            diameter_mm=round(opening.diameter * 1000.0, 1),
            confidence=round(opening.confidence, 3),
        )

    return measure


def main():
    parser = argparse.ArgumentParser(description="Verladearm Vision-Dienst")
    parser.add_argument("--config", default="vision/config/default.yaml")
    parser.add_argument("--once", action="store_true", help="eine Messung ohne SPS ausführen")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    cfg = load_config(args.config)
    measure = build_measure(cfg)

    if args.once:
        print(measure(0))
        return

    plc = PlcInterface(**cfg["plc"])
    try:
        asyncio.run(plc.run(measure))
    except KeyboardInterrupt:
        log.info("Beendet")


if __name__ == "__main__":
    main()
