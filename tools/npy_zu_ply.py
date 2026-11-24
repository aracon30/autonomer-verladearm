"""Aufnahmen (.npy, Punkte x y z in m) als .ply speichern, z. B. für CloudCompare oder MeshLab.

    .venv\\Scripts\\python tools\\npy_zu_ply.py data\\aufnahmen\\*.npy

Legt neben jeder Datei eine .ply an (binär, mit Farbe nach Abstand: blau nah … rot fern).
"""

import glob
import sys
from pathlib import Path

import numpy as np


def farbe(t):
    k = np.array([[40, 60, 200], [40, 170, 220], [60, 190, 90], [240, 210, 40], [220, 60, 40]],
                 float)
    x = np.clip(t, 0, 1) * (len(k) - 1)
    i = np.minimum(x.astype(int), len(k) - 2)
    f = (x - i)[:, None]
    return (k[i] * (1 - f) + k[i + 1] * f).astype(np.uint8)


def schreibe_ply(punkte: np.ndarray, ziel: Path) -> None:
    p = punkte[np.isfinite(punkte).all(axis=1)].astype(np.float32)
    d = np.linalg.norm(p, axis=1)
    rgb = farbe(d / max(np.percentile(d, 98), 1e-6))
    rec = np.empty(len(p), dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"),
                                  ("r", "u1"), ("g", "u1"), ("b", "u1")])
    rec["x"], rec["y"], rec["z"] = p[:, 0], p[:, 1], p[:, 2]
    rec["r"], rec["g"], rec["b"] = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    kopf = ("ply\nformat binary_little_endian 1.0\n"
            f"element vertex {len(p)}\n"
            "property float x\nproperty float y\nproperty float z\n"
            "property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n")
    with open(ziel, "wb") as f:
        f.write(kopf.encode("ascii"))
        f.write(rec.tobytes())


if __name__ == "__main__":
    dateien = [g for a in sys.argv[1:] for g in (glob.glob(a) or [a])]
    if not dateien:
        sys.exit(__doc__)
    for name in dateien:
        quelle = Path(name)
        ziel = quelle.with_suffix(".ply")
        schreibe_ply(np.load(quelle, allow_pickle=False)[:, :3], ziel)
        print(f"{ziel}")
