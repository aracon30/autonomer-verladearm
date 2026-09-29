"""Erzeugt synthetische Punktwolken eines Tankdachs mit Domöffnung.

    python tools/make_synthetic.py --out data/samples --count 5
    python tools/make_synthetic.py --vehicle kesselwagen
"""

import argparse
from pathlib import Path

import numpy as np

from verladearm_vision.synthetic import make_tank_roof, make_tank_vehicle

parser = argparse.ArgumentParser()
parser.add_argument("--out", default="data/samples")
parser.add_argument("--count", type=int, default=5)
parser.add_argument(
    "--vehicle", choices=["eben", "lkw", "kesselwagen", "gemischt"], default="gemischt",
    help="Tankform; gemischt = abwechselnd Lkw und Kesselwagen",
)
args = parser.parse_args()

out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)
for i in range(args.count):
    cx, cy = rng.uniform(-0.4, 0.4, 2)
    kind = args.vehicle if args.vehicle != "gemischt" else ("lkw", "kesselwagen")[i % 2]
    if kind == "eben":
        pts = make_tank_roof(center_xy=(cx, cy), height=rng.uniform(3.0, 4.0), seed=i)
    else:  # Abstand Sensor -> Domkragen passend zur Platzhalter-Kalibrierung
        h = rng.uniform(3.5, 3.8) if kind == "lkw" else rng.uniform(2.6, 2.8)
        pts = make_tank_vehicle(kind, center_xy=(cx, cy), height=h, seed=i)
    path = out / f"synthetic_{i:02d}_{kind}.npy"
    np.save(path, pts.astype(np.float32))
    print(f"{path}: Öffnung bei x={cx:+.3f} m, y={cy:+.3f} m")
