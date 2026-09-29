"""Spielt aufgenommene Punktwolken aus einem Ordner ab (Entwicklung ohne Sensor).

Auch Aufzeichnungen des Vision-Dienstes: path = Aufzeichnungsordner, pattern = "**/punkte.npz".
"""

from itertools import cycle
from pathlib import Path

import numpy as np


def load_points(path: Path) -> np.ndarray:
    if path.suffix == ".npy":
        return np.load(path).astype(float)
    if path.suffix == ".npz":
        with np.load(path) as data:
            return data["points"].astype(float)
    if path.suffix == ".ply":
        import open3d as o3d  # optional: pip install -e ".[viz]"

        return np.asarray(o3d.io.read_point_cloud(str(path)).points, dtype=float)
    raise ValueError(f"Nicht unterstütztes Format: {path.suffix}")


class FileSource:
    def __init__(self, folder: str | Path, pattern: str = "*"):
        suffixes = (".npy", ".npz", ".ply")
        files = sorted(p for p in Path(folder).glob(pattern) if p.suffix in suffixes)
        if not files:
            raise FileNotFoundError(
                f"Keine Punktwolken in {folder}. Tipp: python tools/make_synthetic.py"
            )
        self._files = cycle(files)

    def grab(self) -> np.ndarray:
        return load_points(next(self._files))
