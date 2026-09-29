"""Hand-Auge-Kalibrierung bei der Inbetriebnahme (Ablauf: docs/kalibrierung.md).

Station leer (kein Tankwagen), Markierungsscheibe am Auslass. Der Arm wird im Handbetrieb der
SPS nacheinander in die vorgeschlagenen Stellungen gefahren; je Stellung Enter drücken.

    python -m verladearm_vision.calibrate --config vision/config/anlagen/<anlage>.yaml --from-plc
    python -m verladearm_vision.calibrate --config ... --sim     # Probelauf mit Simulation

Istwinkel kommen mit --from-plc aus dem DB_Vision (OPC UA, nur lesend), sonst per Eingabe.
Ergebnis: neue calibration.matrix zum Eintragen in die Anlagendatei und ein Protokoll (Markdown).
"""

import argparse
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np

from verladearm_vision.calibration.handeye import HandEyeCalibration, suggest_poses
from verladearm_vision.config import load_config
from verladearm_vision.detection import OutletConfig
from verladearm_vision.kinematics import ArmGeometry


def read_plc_angles(plc_cfg: dict):
    from asyncua.sync import Client

    with Client(plc_cfg["url"]) as client:
        ns = client.get_namespace_index(plc_cfg["namespace_uri"])
        node = lambda n: client.get_node(plc_cfg["node_template"].format(ns=ns, name=n))  # noqa: E731
        if not node("AxesHomed").read_value():
            raise RuntimeError("Achsen nicht referenziert")
        return tuple(float(node(f"ActualJ{i}").read_value()) for i in (1, 2, 3))


def ask_angles(suggested):
    text = input(f"  Istwinkel J1 J2 J3 [Enter = {' '.join(f'{v:.1f}' for v in suggested)}]: ")
    if not text.strip():
        return suggested
    return tuple(float(v.replace(",", ".")) for v in text.split())


def protocol(result: dict, cal: HandEyeCalibration, config: str) -> str:
    t = result["matrix"]
    lines = ["# Kalibrierprotokoll Sensor → Armbasis", "",
             f"Konfiguration: `{config}`  ", f"Datum: {date.today():%d.%m.%Y}", "",
             f"Gültige Stellungen: {result['used']} von {result['total']}", "",
             "| Nr. | J1 | J2 | J3 | Soll x/y/z [mm] | Restfehler [mm] |",
             "|---|---|---|---|---|---|"]
    res = iter(result["residuals_m"])
    for i, s in enumerate(cal.samples, 1):
        err = f"{next(res) * 1000:.1f}" if s.sensor is not None else f"– ({s.error})"
        lines.append(f"| {i} | {s.servo_deg[0]:.1f} | {s.servo_deg[1]:.1f} | {s.servo_deg[2]:.1f} "
                     f"| {' / '.join(f'{v * 1000:.0f}' for v in s.arm)} | {err} |")
    r = result["residuals_m"] * 1000
    lines += ["", f"Restfehler: Mittel {r.mean():.1f} mm, max. {r.max():.1f} mm", ""]
    lines += [f"- ⚠️ {w}" for w in result["warnings"]] or ["- ✅ keine Auffälligkeiten"]
    lines += ["", "Eintrag für die Anlagendatei:", "", "```yaml", yaml_block(t), "```", ""]
    return "\n".join(lines)


def yaml_block(t: np.ndarray) -> str:
    rows = "\n".join(f"    - [{', '.join(f'{v:.6f}' for v in row)}]" for row in t)
    return f"calibration:\n  matrix:\n{rows}"


def main():
    p = argparse.ArgumentParser(description="Hand-Auge-Kalibrierung Verladearm")
    p.add_argument("--config", default="vision/config/default.yaml")
    p.add_argument("--from-plc", action="store_true", help="Istwinkel per OPC UA lesen")
    p.add_argument("--sim", action="store_true", help="Probelauf mit simuliertem Sensor")
    p.add_argument("--out", help="Protokolldatei (Markdown)")
    args = p.parse_args()

    cfg = load_config(args.config)
    geom = ArmGeometry(**cfg.get("arm", {}))
    guess = np.asarray(cfg["calibration"]["matrix"], dtype=float)
    ws = cfg.get("commissioning", {})
    poses = suggest_poses(geom, ws["workspace_min"], ws["workspace_max"])
    outlet = OutletConfig(**cfg.get("outlet", {}))
    cal = HandEyeCalibration(geom, guess, outlet)

    if args.sim:
        from verladearm_vision.acquisition.simulation import SimulatedScene
        from verladearm_vision.calibration import SensorToArm

        # tatsächliche Montage weicht von der Schätzung ab: 4 cm versetzt, 1,5° verdreht
        a = np.radians(1.5)
        true_t = guess.copy()
        true_t[:3, :3] = guess[:3, :3] @ np.array([[np.cos(a), -np.sin(a), 0],
                                                    [np.sin(a), np.cos(a), 0], [0, 0, 1]])
        true_t[:3, 3] += [0.04, -0.03, 0.02]
        source = SimulatedScene(geom, SensorToArm(guess), empty=True, sensor_matrix=true_t,
                                seed=1)
    else:
        from verladearm_vision.service.main import build_source

        source = build_source(cfg["source"], cfg)

    print(f"{len(poses)} Stellungen vorgeschlagen. Station leer, Markierungsscheibe am Auslass.")
    for i, pose in enumerate(poses, 1):
        print(f"\n[{i}/{len(poses)}] Arm fahren auf J1 {pose[0]:.1f}°  J2 {pose[1]:.1f}°  "
              f"J3 {pose[2]:.1f}°, Auslass auspendeln lassen")
        if args.sim:
            angles = pose
            source.prepare(2, angles)
        else:
            cmd = input("  Enter = messen, s = überspringen, f = fertig: ").strip().lower()
            if cmd == "f":
                break
            if cmd == "s":
                continue
            angles = read_plc_angles(cfg["plc"]) if args.from_plc else ask_angles(pose)
            time.sleep(0.5)
        s = cal.add(source.grab(), angles)
        print("  " + ("Scheibe gefunden" if s.sensor is not None else f"nicht gefunden: {s.error}"))

    try:
        result = cal.solve()
    except ValueError as e:
        print(f"\nKalibrierung nicht möglich: {e}")
        sys.exit(1)
    text = protocol(result, cal, args.config)
    print("\n" + text)
    if args.sim:
        err = np.abs(result["matrix"] - true_t)
        print(f"Probelauf: Abweichung zur tatsächlichen Montage: Drehung {err[:3, :3].max():.5f}, "
              f"Versatz {err[:3, 3].max() * 1000:.1f} mm")
    out = Path(args.out or f"kalibrierung_{date.today():%Y-%m-%d}.md")
    out.write_text(text, encoding="utf-8")
    print(f"Protokoll: {out}")


if __name__ == "__main__":
    main()
