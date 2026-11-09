"""Punktwolken mit der echten Kamera aufnehmen und speichern (Kameratest, Daten von Tankwagen).

    python tools/aufnahme.py --config vision/config/anlagen/kameratest.yaml
    python tools/aufnahme.py --config ... --anzahl 5 --notiz "Lkw 3 Kammern, Dom offen"

Jede Aufnahme landet als `data/aufnahmen/<Datum>_<Zeit>_<Notiz>.npy` (Sensorkoordinaten, m).
Ohne `--anzahl` wird bei jedem Enter eine Aufnahme gemacht, `q` + Enter beendet. Abspielen:
source: {type: file, path: data/aufnahmen}.
"""

import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from verladearm_vision.config import load_config
from verladearm_vision.konsole import quickedit_aus
from verladearm_vision.service.main import build_source


def speichern(points: np.ndarray, ordner: Path, notiz: str) -> Path:
    ordner.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if notiz:
        name += "_" + re.sub(r"[^\w\-]+", "_", notiz)[:40]
    path = ordner / f"{name}.npy"
    np.save(path, points.astype(np.float32))
    return path


def main():
    quickedit_aus()
    p = argparse.ArgumentParser(description="Punktwolken mit der Kamera aufnehmen")
    p.add_argument("--config", required=True, help="Anlagendatei mit source: sick")
    p.add_argument("--ordner", default="data/aufnahmen")
    p.add_argument("--anzahl", type=int, default=0, help="so viele Aufnahmen, dann Ende")
    p.add_argument("--notiz", default="", help="kurz: Fahrzeug, Dom, Wetter …")
    args = p.parse_args()
    cfg = load_config(args.config)
    source = build_source(cfg["source"], cfg)
    print("Warte auf die Kamera …")
    for _ in range(60):
        if getattr(source, "ready", True):
            break
        time.sleep(1)
    else:
        sys.exit("Kamera nicht erreichbar: IP, Netzwerkeinstellung und 24 V prüfen.")
    print("Kamera bereit.")
    n = 0
    while True:
        if args.anzahl:
            if n >= args.anzahl:
                break
        else:
            eingabe = input("Enter = Aufnahme, q = Ende: ").strip().lower()
            if eingabe == "q":
                break
        t0 = time.perf_counter()
        points = source.grab()
        path = speichern(points, Path(args.ordner), args.notiz)
        n += 1
        print(f"  {path}  ({len(points):,} Punkte, {time.perf_counter() - t0:.1f} s)")
    if hasattr(source, "close"):
        source.close()


if __name__ == "__main__":
    main()
