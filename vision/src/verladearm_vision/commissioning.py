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
    axes = [np.arange(a, b + step / 2, step) for a, b in zip(lo, hi, strict=True)]
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
            w(f"- {o.name}: {o.min} … {o.max} m\n")
    else:
        w("- ⚠️ keine Hindernisse hinterlegt – Schwenkbereich vor Ort prüfen\n")
    if hit := collision(geom, park):
        w(f"- ❌ Parkstellung kollidiert mit {hit}\n")
    w("\n")

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
    return not failures and not collision(geom, park)


def main():
    parser = argparse.ArgumentParser(description="Inbetriebnahmeprüfung Verladearm")
    parser.add_argument("--config", default="vision/config/default.yaml")
    args = parser.parse_args()
    ok = check(load_config(args.config), args.config)
    print("**Ergebnis: " + ("in Ordnung" if ok else "Mängel, siehe oben") + "**")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
