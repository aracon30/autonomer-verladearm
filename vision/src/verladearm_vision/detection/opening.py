"""Erkennung der Domöffnung in einer Punktwolke.

Ablauf:
1. Punktwolke auf den Arbeitsraum zuschneiden
2. Tankoberfläche per RANSAC als Ebene fitten (lokal über dem Dom ausreichend)
3. Oberfläche in ein 2D-Raster projizieren, leere Bereiche suchen
4. Geschlossene Lücke passender Größe = Domöffnung -> Mittelpunkt, Durchmesser, Normale

TODO: gewölbte Tankdächer (Zylinderfit), Domkragen, Mehrkammer-Tankwagen.
"""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

# Fehlercodes (identisch zu docs/schnittstelle.md)
ERR_TOO_FEW_POINTS = 11
ERR_NO_SURFACE = 12
ERR_NO_OPENING = 20
ERR_MULTIPLE_OPENINGS = 21


class DetectionError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class DetectorConfig:
    roi_min: tuple = (-2.0, -2.0, 0.5)
    roi_max: tuple = (2.0, 2.0, 8.0)
    plane_threshold: float = 0.015  # m
    ransac_iterations: int = 300
    ransac_sample: int = 5000  # Punkte zur Bewertung der Hypothesen
    min_surface_fraction: float = 0.3
    grid_size: float = 0.02  # m
    min_diameter: float = 0.35  # m
    max_diameter: float = 0.65  # m
    min_points: int = 2000
    seed: int = 0


@dataclass
class Opening:
    center: np.ndarray  # (3,) Meter, Sensorkoordinaten
    normal: np.ndarray  # (3,) Einheitsvektor, zeigt zum Sensor
    diameter: float  # Meter
    confidence: float  # 0..1


def crop(points: np.ndarray, lo, hi) -> np.ndarray:
    mask = np.all((points >= np.asarray(lo)) & (points <= np.asarray(hi)), axis=1)
    return points[mask]


def fit_plane_ransac(points, threshold, iterations, rng, sample_size=5000):
    """Ebene per RANSAC. Hypothesen werden vektorisiert auf einer Stichprobe bewertet."""
    n = len(points)
    sample = points[rng.choice(n, sample_size, replace=False)] if n > sample_size else points
    m = len(sample)

    # Alle Hypothesen auf einmal: je 3 Punkte -> Normale
    tri = sample[rng.integers(0, m, (iterations, 3))]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    valid = lengths > 1e-9
    if not valid.any():
        raise DetectionError(ERR_NO_SURFACE, "Keine Ebene gefunden")
    normals = normals[valid] / lengths[valid, None]
    offsets = np.einsum("ij,ij->i", normals, tri[valid, 0])

    # Inlier zählen, blockweise um den Speicher zu begrenzen
    counts = np.empty(len(normals), dtype=np.int64)
    for i in range(0, len(normals), 64):
        dist = np.abs(sample @ normals[i : i + 64].T - offsets[i : i + 64])
        counts[i : i + 64] = (dist < threshold).sum(axis=0)
    best = int(np.argmax(counts))
    if counts[best] < 3:
        raise DetectionError(ERR_NO_SURFACE, "Keine Ebene gefunden")

    # Verfeinerung über alle Inlier der vollen Punktwolke (Kovarianz statt SVD über N Punkte)
    inliers = np.abs(points @ normals[best] - offsets[best]) < threshold
    p = points[inliers]
    centroid = p.mean(axis=0)
    d = p - centroid
    _, vecs = np.linalg.eigh(d.T @ d)
    normal = vecs[:, 0]
    inliers = np.abs((points - centroid) @ normal) < threshold
    return centroid, normal, inliers


def _plane_basis(normal):
    helper = np.array([1.0, 0, 0]) if abs(normal[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(normal, helper)
    u /= np.linalg.norm(u)
    return u, np.cross(normal, u)


def detect_opening(points: np.ndarray, cfg: DetectorConfig | None = None) -> Opening:
    cfg = cfg or DetectorConfig()
    rng = np.random.default_rng(cfg.seed)

    pts = crop(points, cfg.roi_min, cfg.roi_max)
    if len(pts) < cfg.min_points:
        raise DetectionError(ERR_TOO_FEW_POINTS, f"Zu wenige Punkte im Arbeitsraum: {len(pts)}")

    centroid, normal, inliers = fit_plane_ransac(
        pts, cfg.plane_threshold, cfg.ransac_iterations, rng, cfg.ransac_sample
    )
    if inliers.mean() < cfg.min_surface_fraction:
        raise DetectionError(ERR_NO_SURFACE, "Tankoberfläche nicht eindeutig erkannt")

    # In Ebenenkoordinaten projizieren und rastern
    u, v = _plane_basis(normal)
    q = (pts[inliers] - centroid) @ np.stack([u, v]).T
    g = cfg.grid_size
    origin = q.min(axis=0)
    idx = np.floor((q - origin) / g).astype(int)
    occupied = np.zeros(idx.max(axis=0) + 1, dtype=bool)
    occupied[idx[:, 0], idx[:, 1]] = True
    occupied = ndimage.binary_closing(occupied, structure=np.ones((3, 3)))

    # Leere, vollständig umschlossene Bereiche suchen
    labels, count = ndimage.label(~occupied)
    border = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    sizes = np.bincount(labels.ravel(), minlength=count + 1)
    diameters = 2 * np.sqrt(sizes * g * g / np.pi)
    in_range = (diameters >= cfg.min_diameter) & (diameters <= cfg.max_diameter)
    in_range[0] = False
    in_range[border] = False

    candidates = []
    slices = ndimage.find_objects(labels)
    for label in np.flatnonzero(in_range):
        sl = slices[label - 1]
        cells = np.argwhere(labels[sl] == label) + [sl[0].start, sl[1].start]
        centers = (cells + 0.5) * g + origin
        c2d = centers.mean(axis=0)
        r_max = np.linalg.norm(centers - c2d, axis=1).max() + g / 2
        confidence = float(np.clip((diameters[label] / 2) ** 2 / r_max**2, 0, 1))
        candidates.append((c2d, float(diameters[label]), confidence))

    if not candidates:
        raise DetectionError(ERR_NO_OPENING, "Keine Domöffnung gefunden")
    if len(candidates) > 1:
        raise DetectionError(ERR_MULTIPLE_OPENINGS, f"{len(candidates)} Öffnungen gefunden")

    c2d, diameter, confidence = candidates[0]
    center = centroid + c2d[0] * u + c2d[1] * v
    if normal @ (-center) < 0:  # Normale zum Sensor ausrichten
        normal = -normal
    return Opening(center=center, normal=normal, diameter=float(diameter), confidence=confidence)
