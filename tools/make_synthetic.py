"""Erzeugt synthetische Punktwolken eines Tankdachs mit Domöffnung.

    python tools/make_synthetic.py --out data/samples --count 5
"""

import argparse
from pathlib import Path

import numpy as np

from verladearm_vision.synthetic import make_tank_roof

parser = argparse.ArgumentParser()
parser.add_argument("--out", default="data/samples")
parser.add_argument("--count", type=int, default=5)
args = parser.parse_args()

out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)
for i in range(args.count):
    cx, cy = rng.uniform(-0.4, 0.4, 2)
    pts = make_tank_roof(center_xy=(cx, cy), height=rng.uniform(3.0, 4.0), seed=i)
    path = out / f"synthetic_{i:02d}.npy"
    np.save(path, pts.astype(np.float32))
    print(f"{path}: Öffnung bei x={cx:+.3f} m, y={cy:+.3f} m")
