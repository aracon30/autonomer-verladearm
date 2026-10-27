"""Prüfung der Anlagenparameter bei der Inbetriebnahme.

    python -m verladearm_vision.commissioning --config vision/config/anlagen/<anlage>.yaml

Prüft Parameter, Achsen und Parkstellung und ob jede mögliche Lage der Domöffnung im Arbeitsraum
kollisionsfrei angefahren und mit der größten Eintauchtiefe erreicht werden kann. Die Ausgabe ist
Markdown und kann als Inbetriebnahmeprotokoll abgelegt werden (`> protokoll.md`).
Rückgabewert 0 = alles in Ordnung, 1 = Mängel.
"""

import argparse
import sys
from collections import Counter
from datetime import date

import numpy as np

from verladearm_vision.config import load_config
from verladearm_vision.drives import Drives
from verladearm_vision.kinematics import (
    JOINTS,
    ArmGeometry,
    collision,
    forward,
    plan_motion,
    validate,
)


def workspace_grid(cfg: dict) -> np.ndarray:
    c = cfg.get("commissioning", {})
    lo, hi = np.asarray(c["workspace_min"], float), np.asarray(c["workspace_max"], float)
    step = float(c.get("step", 0.2))
    # Ränder genau treffen, nie darüber hinaus (np.arange würde je nach Schrittweite überschießen)
    axes = [np.linspace(a, b, int(np.ceil((b - a) / step - 1e-9)) + 1) if b > a else np.array([a])
            for a, b in zip(lo, hi, strict=True)]
    return np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)


def max_insertion_depth(cfg: dict, geom: ArmGeometry) -> tuple[float, str]:
    depth, name = geom.insertion_depth, "Standard"
    for key, entry in (cfg.get("products") or {}).items():
        d = float((entry or {}).get("insertion_depth", geom.insertion_depth))
        if d > depth:
            depth, name = d, f"ProductId {key} {entry.get('name', '')}".strip()
    return depth, name


def check(cfg: dict, config_name: str, out=sys.stdout) -> bool:
    geom = ArmGeometry(**cfg.get("arm", {}))
    w = out.write
    w(f"# Inbetriebnahmeprüfung Verladearm\n\nKonfiguration: `{config_name}`  \n")
    w(f"Datum: {date.today():%d.%m.%Y}\n\n")

    problems = validate(geom)
    w("## 1. Parameter\n\n")
    if problems:
        w("".join(f"- ❌ {p}\n" for p in problems) + "\n")
        w("Weitere Prüfungen übersprungen, bitte Parameter korrigieren.\n")
        return False
    w("- ✅ Maße, Achsbereiche und Parkstellung plausibel\n\n")

    w("## 2. Achsen (Servo-Grad)\n\n| Achse | min | max | Park | Null | Richtung |\n")
    w("|---|---|---|---|---|---|\n")
    for k, label in zip(JOINTS, ("J1 Drehen", "J2 Drehen", "J3 Heben/Senken"), strict=True):
        j = geom.joints[k]
        w(f"| {label} | {j.min:g} | {j.max:g} | {j.park:g} | {j.zero:g} | {j.direction:+d} |\n")
    park = forward(geom, geom.park)
    w(f"\nAuslassende in Parkstellung: x {park[-1][0]:.2f} m, y {park[-1][1]:.2f} m, "
      f"z {park[-1][2]:.2f} m (Armbasis)\n\n")

    w("## 3. Hindernisse\n\n")
    if geom.obstacles:
        w(f"Mindestabstand Rohrachse: {geom.clearance * 1000:.0f} mm\n\n")
        for o in geom.obstacles:
            if hasattr(o, "min"):
                w(f"- {o.name}: Quader {o.min} … {o.max} m\n")
            elif hasattr(o, "radius"):
                w(f"- {o.name}: Zylinder Achse durch {o.p0}, Radius {o.radius} m\n")
            else:
                w(f"- {o.name}: gedrehter Quader um {o.center} m\n")
    else:
        w("- ⚠️ keine Hindernisse hinterlegt – Schwenkbereich vor Ort prüfen\n")
    if hit := collision(geom, park):
        w(f"- ❌ Parkstellung kollidiert mit {hit}\n")
    w("\n")
    station_report(cfg, w)

    depth, depth_from = max_insertion_depth(cfg, geom)
    points = workspace_grid(cfg)
    w("## 4. Reichweite im Arbeitsraum\n\n")
    w(f"{len(points)} mögliche Lagen der Domöffnung, Eintauchtiefe {depth * 1000:.0f} mm "
      f"({depth_from}), Anfahrhöhe {geom.approach_height * 1000:.0f} mm\n\n")
    failures = []
    for p in points:
        plan = plan_motion(geom, p * 1000, [0, 0, 1], insertion_depth=depth, insert_steps=8)
        if not plan["ok"]:
            failures.append((p, plan["reason"]))
    ok = len(points) - len(failures)
    w(f"- {'✅' if not failures else '❌'} erreichbar: {ok} von {len(points)} "
      f"({ok / len(points) * 100:.0f} %)\n")
    if failures:
        for reason, n in Counter(r for _, r in failures).most_common():
            w(f"  - {n}× {reason}\n")
        w("\nNicht erreichbare Lagen (Auszug, m):\n\n| x | y | z | Grund |\n|---|---|---|---|\n")
        for p, reason in failures[:15]:
            w(f"| {p[0]:.2f} | {p[1]:.2f} | {p[2]:.2f} | {reason} |\n")
    w("\n")
    drive_report(cfg, geom, depth, w)
    return not failures and not collision(geom, park)


VEHICLE_WIDTH = 2.55  # m, Tankwagen (Lkw/Kesselwagen) ohne Spiegel


def station_report(cfg: dict, w):
    """Verladestelle: Fahrtrichtung (Zählung der Dome von vorn) und eigene Spur (Domsuche)."""
    v = cfg.get("vehicle") or {}
    w("## 3a. Verladestelle\n\n")
    if "front" in v:
        f = np.asarray(v["front"], float)
        names = {(0, 1): "nach links (+y)", (0, -1): "nach rechts (−y)", (1, 0): "nach vorne (+x)",
                 (-1, 0): "nach hinten (−x)"}
        side = names.get(tuple(np.round(f[:2]).astype(int)), str(f.tolist()))
        w(f"- Fahrzeugfront zeigt {side}: Dom 1 ist der vorderste – vor Ort an der Spur prüfen\n")
    else:
        w("- ⚠️ Fahrtrichtung nicht festgelegt (Annahme +y) – bei Mehrkammer-Fahrzeugen falsche "
          "Kammer möglich\n")
    if v.get("lane_center") is None or not v.get("lane_width"):
        w("- ⚠️ eigene Spur nicht festgelegt: Domsuche im ganzen Bild, Nachbarspur kann stören\n\n")
        return
    width = float(v["lane_width"])
    w(f"- Domsuche nur in der eigenen Spur: Mitte {_xy(v['lane_center'])} m, Breite "
      f"{width:.2f} m\n")
    if width < VEHICLE_WIDTH + 0.3:
        w(f"- ⚠️ Spur schmaler als Tankwagen ({VEHICLE_WIDTH} m) plus Haltetoleranz\n")
    c = cfg.get("commissioning") or {}
    if c.get("workspace_min") and c.get("workspace_max"):
        f = np.asarray(v.get("front", (0.0, 1.0)), float)[:2]
        cross = np.array([-f[1], f[0]]) / np.linalg.norm(f)
        lo, hi = np.asarray(c["workspace_min"], float), np.asarray(c["workspace_max"], float)
        corners = [np.array([x, y]) for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]
        off = max(abs((p - np.asarray(v["lane_center"], float)[:2]) @ cross) for p in corners)
        if off > width / 2:
            w("- ⚠️ Arbeitsraum (mögliche Domlagen) reicht über die Spur hinaus – Spurbreite "
              "oder Haltetoleranz prüfen\n")
    w("\n")


def _xy(p) -> str:
    return f"x {float(p[0]):.2f} / y {float(p[1]):.2f}"


def drive_report(cfg: dict, geom: ArmGeometry, depth: float, w):
    """Antriebe und geschätzte Fahrzeiten einer Verladung (Mitte des Arbeitsraums)."""
    drives = Drives.from_config(cfg.get("drives"))
    w("## 5. Antriebe\n\n")
    if not drives.configured:
        w("- ⚠️ keine Antriebsdaten (`drives`) – Fahrzeiten nicht berechnet\n\n")
        return
    w("| Achse | Motor | Getriebe | i | max. °/s | Rampe s | Spiel ° | Moment Nm | Bremse |\n")
    w("|---|---|---|---|---|---|---|---|---|\n")
    for k, label in zip(JOINTS, ("J1", "J2", "J3"), strict=True):
        d = drives.axes[k]
        torque = f"{d.torque:g} / {d.torque_peak:g}" if d.torque and d.torque_peak else "–"
        w(f"| {label} | {d.motor or '–'} | {d.gear or '–'} | {d.ratio:g} | {d.speed_max:.1f} "
          f"| {d.accel_time:g} | {d.backlash:g} | {torque} | {'ja' if d.brake else '**nein**'} |\n")
    inverters = {k: d.inverter for k, d in drives.axes.items() if d.inverter}
    if inverters:
        w("\n" + "".join(f"- Umrichter {k.replace('q', 'J')}: {v}\n" for k, v in inverters.items()))
    jerk = {d.jerk_time for d in drives.axes.values()}
    if len(jerk) > 1:
        w(f"- ⚠️ Ruckzeit nicht auf allen Achsen gleich ({sorted(jerk)} s) – synchrone Fahrt "
          "weicht von der geprüften Bahn ab\n")
    c = cfg.get("commissioning", {})
    center = (np.asarray(c["workspace_min"], float) + np.asarray(c["workspace_max"], float)) / 2
    plan = plan_motion(geom, center * 1000, [0, 0, 1], insertion_depth=depth)
    if not plan["ok"]:
        w(f"\nFahrzeit nicht berechnet: {plan['reason']}\n\n")
        return
    servo = [geom.to_servo(q) for q in [geom.park] + [np.array(v) for v in plan["move_vias"]]]
    approach = sum(drives.sync_time(a, b) for a, b in zip(servo[:-1], servo[1:], strict=True))
    q_in = [geom.to_servo(np.array(q)) for q in plan["q_insert"]]
    insert = drives.sync_time(q_in[0], q_in[-1], 0.3)
    w(f"\nFahrzeiten zur Mitte des Arbeitsraums (x {center[0]:.1f}, y {center[1]:.1f}, "
      f"z {center[2]:.1f} m), synchron, langsamste Achse bestimmt:\n\n")
    w(f"- Anfahrt Park → über Dom: {approach:.0f} s\n")
    w(f"- Eintauchen ({depth * 1000:.0f} mm, 30 % Geschwindigkeit): {insert:.0f} s\n")
    total = 2 * (approach + insert)
    w(f"- Verladung gesamt ohne Befüllung (hin und zurück): ca. {total:.0f} s\n\n")


def main():
    parser = argparse.ArgumentParser(description="Inbetriebnahmeprüfung Verladearm")
    parser.add_argument("--config", default="vision/config/default.yaml")
    args = parser.parse_args()
    ok = check(load_config(args.config), args.config)
    print("**Ergebnis: " + ("in Ordnung" if ok else "Mängel, siehe oben") + "**")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
