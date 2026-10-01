"""Erkennung der Domöffnung in einer Punktwolke.

Ablauf:
1. Punktwolke auf den Arbeitsraum zuschneiden
2. Tankoberfläche per RANSAC als quadratische Höhenfläche z = f(x, y) fitten. Das deckt ebene,
   geneigte und runde Tankdächer (Lkw, Kesselwagen) im Bereich um den Scheitel ab.
3. Raster in Blickrichtung des Sensors: belegt sind Zellen mit Punkten nahe der Oberfläche –
   darüber (Domkragen, Armaturen, Deckel, Laufstege) oder wenig darunter (vertiefter Domdeckel
   im Domring). Nur Punkte deutlich tiefer (`deep_min`, Blick ins Tankinnere) und Störpunkte
   weit oberhalb (Geländer, Arm) zählen nicht.
4. Geschlossene Lücke passender Größe = Öffnung, durch die der Auslass eintaucht. Bei Domen mit
   Armaturen ist das die kleine, oft seitlich versetzte Füllöffnung im Domdeckel, bei offenem
   Mannloch das ganze Mannloch.
5. Mittelpunkt und Durchmesser per Kreis-Fit auf dem innersten Rand der Öffnung (je 5°-Sektor),
   Höhe und Normale aus diesem Rand.

Der Sensor muss ungefähr senkrecht nach unten blicken. Der Arbeitsraum (roi) muss die Fahrbahn
ausschließen, sonst kann statt des Tanks der Boden als Oberfläche gefunden werden.
TODO: Mehrkammer-Tankwagen (Auswahl der Kammer), Laufstege direkt am Dom.
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
    plane_threshold: float = 0.015  # m, Abstand zur Oberfläche
    raised_max: float = 0.5  # m, bis zu dieser Höhe über der Oberfläche zählt ein Punkt als Kragen
    ransac_iterations: int = 400
    ransac_sample: int = 5000  # Punkte zur Bewertung der Hypothesen
    min_surface_fraction: float = 0.3
    grid_size: float = 0.02  # m
    min_diameter: float = 0.18  # m (kleine Füllöffnung im Domdeckel)
    max_diameter: float = 0.70  # m (offenes Mannloch)
    deep_min: float = 0.25  # m unter der Oberfläche: ab hier Blick ins Tankinnere
    min_points: int = 2000
    seed: int = 0


@dataclass
class Opening:
    center: np.ndarray  # (3,) Meter, Sensorkoordinaten
    normal: np.ndarray  # (3,) Einheitsvektor, zeigt zum Sensor
    diameter: float  # Meter
    confidence: float  # 0..1
    tank_radius: float | None = None  # Krümmungsradius des Tanks am Dom, None = eben
    tank_axis: np.ndarray | None = None  # (3,) Richtung der Tankachse, Sensorkoordinaten
    tank_apex: np.ndarray | None = None  # (3,) Tankoberfläche unter dem Dommittelpunkt


def crop(points: np.ndarray, lo, hi) -> np.ndarray:
    mask = np.all((points >= np.asarray(lo)) & (points <= np.asarray(hi)), axis=1)
    return points[mask]


class Surface:
    """Quadratische Höhenfläche z = f(x, y) in normierten Koordinaten (numerisch stabil)."""

    def __init__(self, coeffs, center, scale):
        self.c, self.center, self.scale = coeffs, center, scale

    def design(self, xy):
        u = (np.asarray(xy)[..., :2] - self.center) / self.scale
        x, y = u[..., 0], u[..., 1]
        return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], axis=-1)

    def height(self, xy):
        return self.design(xy) @ self.c

    def gradient(self, xy):
        u = (np.asarray(xy, dtype=float) - self.center) / self.scale
        c = self.c
        return np.array([c[1] + 2 * c[3] * u[0] + c[4] * u[1],
                         c[2] + c[4] * u[0] + 2 * c[5] * u[1]]) / self.scale

    def hessian(self):
        c = self.c
        return np.array([[2 * c[3], c[4]], [c[4], 2 * c[5]]]) / self.scale**2


def fit_surface_ransac(points, threshold, iterations, rng, sample_size=5000):
    """Tankoberfläche als quadratische Höhenfläche; Hypothesen vektorisiert auf einer Stichprobe."""
    n = len(points)
    sample = points[rng.choice(n, sample_size, replace=False)] if n > sample_size else points
    m = len(sample)
    center = sample[:, :2].mean(axis=0)
    scale = float(max(sample[:, :2].std(), 1e-6))
    probe = Surface(None, center, scale)
    a = probe.design(sample)

    # Alle Hypothesen auf einmal: je 6 Punkte -> Koeffizienten
    idx = rng.integers(0, m, (iterations, 6))
    coeffs = np.einsum("nij,nj->ni", np.linalg.pinv(a[idx]), sample[idx, 2])

    counts = np.empty(iterations, dtype=np.int64)
    for i in range(0, iterations, 64):
        resid = np.abs(a @ coeffs[i : i + 64].T - sample[:, 2:3])
        counts[i : i + 64] = (resid < threshold).sum(axis=0)
    best = int(np.argmax(counts))
    if counts[best] < 6:
        raise DetectionError(ERR_NO_SURFACE, "Keine Tankoberfläche gefunden")

    # Verfeinerung über alle Inlier der vollen Punktwolke
    a_full = probe.design(points)
    c = coeffs[best]
    for _ in range(3):
        inliers = np.abs(a_full @ c - points[:, 2]) < threshold
        if inliers.sum() < 6:
            raise DetectionError(ERR_NO_SURFACE, "Keine Tankoberfläche gefunden")
        c = np.linalg.lstsq(a_full[inliers], points[inliers, 2], rcond=None)[0]
    inliers = np.abs(a_full @ c - points[:, 2]) < threshold
    return Surface(c, center, scale), inliers


def _edge(solid_pts: np.ndarray, c2d, radius: float, g: float) -> np.ndarray:
    """Innerster Randpunkt der Öffnung je 5°-Sektor (aus den belegten Punkten um die Lücke)."""
    d = solid_pts[:, :2] - c2d
    r = np.hypot(d[:, 0], d[:, 1])
    near = (r > 0.5 * radius) & (r < radius + 4 * g)
    p, r = solid_pts[near], r[near]
    sector = ((np.arctan2(d[near, 1], d[near, 0]) + np.pi) / np.radians(5)).astype(int)
    order = np.lexsort((r, sector))
    first = np.ones(len(order), bool)
    first[1:] = sector[order][1:] != sector[order][:-1]
    return p[order[first]]


def _fit_circle(xy: np.ndarray, rounds: int = 3, tol: float = 0.012):
    """Kreis durch Randpunkte (algebraisch, Ausreißer werden schrittweise verworfen)."""
    pts = np.asarray(xy, float)
    for _ in range(rounds):
        if len(pts) < 8:
            return None
        a = np.column_stack([pts, np.ones(len(pts))])
        b = (pts**2).sum(axis=1)
        (cx2, cy2, c), *_ = np.linalg.lstsq(a, b, rcond=None)
        center = np.array([cx2 / 2, cy2 / 2])
        r2 = c + center @ center
        if r2 <= 0:
            return None
        radius = float(np.sqrt(r2))
        resid = np.abs(np.linalg.norm(pts - center, axis=1) - radius)
        keep = resid < max(tol, 2.5 * np.median(resid))
        if keep.all():
            break
        pts = pts[keep]
    return center, radius


def detect_opening(points: np.ndarray, cfg: DetectorConfig | None = None) -> Opening:
    cfg = cfg or DetectorConfig()
    rng = np.random.default_rng(cfg.seed)

    pts = crop(points, cfg.roi_min, cfg.roi_max)
    if len(pts) < cfg.min_points:
        raise DetectionError(ERR_TOO_FEW_POINTS, f"Zu wenige Punkte im Arbeitsraum: {len(pts)}")

    surface, inliers = fit_surface_ransac(
        pts, cfg.plane_threshold, cfg.ransac_iterations, rng, cfg.ransac_sample
    )
    if inliers.mean() < cfg.min_surface_fraction:
        raise DetectionError(ERR_NO_SURFACE, "Tankoberfläche nicht eindeutig erkannt")

    # Höhe über der Oberfläche (Sensor-z zeigt nach unten, also f - z)
    above = surface.height(pts) - pts[:, 2]
    solid = inliers | ((above > -cfg.deep_min) & (above <= cfg.raised_max))

    # Raster in Blickrichtung
    g = cfg.grid_size
    q = pts[solid, :2]
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

    # Rand der Öffnung: innerster Punkt je Sektor, darauf Kreis-Fit (genauer als Rasterzellen)
    rim = _edge(pts[solid], c2d, diameter / 2, g)
    fit = _fit_circle(rim[:, :2]) if len(rim) >= 20 else None
    if fit is not None and abs(2 * fit[1] - diameter) < 0.3 * diameter:
        c2d, diameter = fit[0], 2 * fit[1]
    if len(rim) >= 20:
        # vorherrschende Randhöhe: Klappe, Armaturen oder Kragenwand am Rand sind Ausreißer
        top = rim[np.abs(rim[:, 2] - np.median(rim[:, 2])) < 0.015]
        if len(top) < 10:
            top = rim
        centroid = top.mean(axis=0)
        normal = np.linalg.eigh(np.cov((top - centroid).T))[1][:, 0]
        center = np.array([c2d[0], c2d[1], centroid[2]])
        # Ebene durch den Rand, am Mittelpunkt ausgewertet
        if abs(normal[2]) > 1e-6:
            center[2] = centroid[2] - (normal[:2] @ (c2d - centroid[:2])) / normal[2]
    else:
        center = np.array([c2d[0], c2d[1], float(surface.height(c2d))])
        gx, gy = surface.gradient(c2d)
        normal = np.array([-gx, -gy, 1.0])
        normal /= np.linalg.norm(normal)
    if normal @ (-center) < 0:  # Normale zum Sensor ausrichten
        normal = -normal

    # Tankform am Dom: stärkste Krümmung quer zur Tankachse
    evals, evecs = np.linalg.eigh(surface.hessian())
    tank_radius, tank_axis = None, None
    if evals[1] > 0.2:  # Radius < 5 m -> runder Tank
        tank_axis = np.array([evecs[0, 0], evecs[1, 0], 0.0])
        # Kreis im Querschnitt durch die Oberflächenpunkte (genauer als die Parabelkrümmung)
        on = pts[inliers]
        s_ = (on[:, :2] - c2d) @ evecs[:, 1]
        z_ = on[:, 2]
        a_mat = np.column_stack([s_, z_, np.ones_like(s_)])
        d, e, f = np.linalg.lstsq(a_mat, -(s_**2 + z_**2), rcond=None)[0]
        radius_sq = (d * d + e * e) / 4 - f
        tank_radius = float(np.sqrt(radius_sq)) if radius_sq > 0 else float(1.0 / evals[1])

    apex = np.array([c2d[0], c2d[1], float(surface.height(c2d))])
    return Opening(center=center, normal=normal, diameter=float(diameter), confidence=confidence,
                   tank_radius=tank_radius, tank_axis=tank_axis, tank_apex=apex)
