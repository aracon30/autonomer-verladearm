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


def fit_plane_ransac(points, threshold, iterations, rng):
    n = len(points)
    best_inliers, best_count = None, 0
    for _ in range(iterations):
        s = points[rng.choice(n, 3, replace=False)]
        normal = np.cross(s[1] - s[0], s[2] - s[0])
        length = np.linalg.norm(normal)
        if length < 1e-9:
            continue
        normal /= length
        inliers = np.abs((points - s[0]) @ normal) < threshold
        count = int(inliers.sum())
        if count > best_count:
            best_inliers, best_count = inliers, count
    if best_inliers is None:
        raise DetectionError(ERR_NO_SURFACE, "Keine Ebene gefunden")
    # Verfeinerung per SVD über alle Inlier
    p = points[best_inliers]
    centroid = p.mean(axis=0)
    _, _, vt = np.linalg.svd(p - centroid, full_matrices=False)
    return centroid, vt[2], best_inliers


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
        pts, cfg.plane_threshold, cfg.ransac_iterations, rng
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
    border = set(np.unique(np.concatenate(
        [labels[0], labels[-1], labels[:, 0], labels[:, -1]]
    )))
    candidates = []
    for label in range(1, count + 1):
        if label in border:
            continue
        cells = np.argwhere(labels == label)
        diameter = 2 * np.sqrt(len(cells) * g * g / np.pi)
        if not cfg.min_diameter <= diameter <= cfg.max_diameter:
            continue
        centers = (cells + 0.5) * g + origin
        c2d = centers.mean(axis=0)
        r_max = np.linalg.norm(centers - c2d, axis=1).max() + g / 2
        confidence = float(np.clip((diameter / 2) ** 2 / r_max**2, 0, 1))
        candidates.append((c2d, diameter, confidence))

    if not candidates:
        raise DetectionError(ERR_NO_OPENING, "Keine Domöffnung gefunden")
    if len(candidates) > 1:
        raise DetectionError(ERR_MULTIPLE_OPENINGS, f"{len(candidates)} Öffnungen gefunden")

    c2d, diameter, confidence = candidates[0]
    center = centroid + c2d[0] * u + c2d[1] * v
    if normal @ (-center) < 0:  # Normale zum Sensor ausrichten
        normal = -normal
    return Opening(center=center, normal=normal, diameter=float(diameter), confidence=confidence)
