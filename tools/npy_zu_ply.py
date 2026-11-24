"""Aufnahmen (.npy, Punkte x y z in m) als .ply speichern, z. B. für CloudCompare oder MeshLab.

    .venv\\Scripts\\python tools\\npy_zu_ply.py data\\aufnahmen\\*.npy
    .venv\\Scripts\\python tools\\npy_zu_ply.py --pts data\\aufnahmen\\*.npy   # für ReCap/Inventor

Legt neben jeder Datei eine .ply an (binär, mit Farbe nach Abstand: blau nah … rot fern).
Mit --pts zusätzlich eine .pts (Text, Millimeter, x y z Intensität r g b), die Autodesk ReCap
einliest; ReCap speichert daraus ein .rcp, das Inventor als Punktwolke anhängt.
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


def schreibe_pts(daten: np.ndarray, ziel: Path) -> None:
    """Leica-PTS (Text): Anzahl, dann je Zeile x y z [mm] Intensität r g b (Grau aus Infrarot)."""
    p = daten[np.isfinite(daten[:, :3]).all(axis=1)]
    xyz = p[:, :3] * 1000.0
    if p.shape[1] >= 4:  # Infrarot als Intensität und Grauwert
        ir = p[:, 3].astype(float)
        lo, hi = np.percentile(ir, [1, 99])
        g = (np.clip((ir - lo) / max(hi - lo, 1e-9), 0, 1) * 255).astype(int)
        rgb = np.column_stack([g, g, g])
        inten = (g * 8 - 1024).clip(-2047, 2047)
    else:
        rgb = farbe(np.linalg.norm(p[:, :3], axis=1) / 6.0).astype(int)
        inten = np.zeros(len(p), int)
    with open(ziel, "w", encoding="ascii") as f:
        f.write(f"{len(p)}\n")
        np.savetxt(f, np.column_stack([xyz, inten, rgb]), fmt="%.1f %.1f %.1f %d %d %d %d")


if __name__ == "__main__":
    pts = "--pts" in sys.argv
    dateien = [g for a in sys.argv[1:] if a != "--pts" for g in (glob.glob(a) or [a])]
    if not dateien:
        sys.exit(__doc__)
    for name in dateien:
        quelle = Path(name)
        daten = np.load(quelle, allow_pickle=False)
        ziel = quelle.with_suffix(".ply")
        schreibe_ply(daten[:, :3], ziel)
        print(f"{ziel}")
        if pts:
            schreibe_pts(daten, quelle.with_suffix(".pts"))
            print(f"{quelle.with_suffix('.pts')}")
