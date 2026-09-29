"""Synthetische Punktwolken eines Tankdachs mit Domöffnung (für Tests und Entwicklung)."""

import numpy as np


def make_tank_roof(
    center_xy=(0.0, 0.0),
    opening_diameter=0.5,
    height=3.5,
    size=2.0,
    spacing=0.01,
    noise=0.003,
    openings=1,
    tilt_deg=0.0,
    seed=0,
) -> np.ndarray:
    """Ebene Fläche in Abstand `height` vom Sensor, mit `openings` kreisrunden Öffnungen."""
    rng = np.random.default_rng(seed)
    ax = np.arange(-size / 2, size / 2, spacing)
    x, y = np.meshgrid(ax, ax)
    pts = np.column_stack([x.ravel(), y.ravel(), np.full(x.size, height)])
    r = opening_diameter / 2
    for i in range(openings):
        cx, cy = center_xy[0] - i * 0.8, center_xy[1]
        pts = pts[np.hypot(pts[:, 0] - cx, pts[:, 1] - cy) > r]
    if tilt_deg:
        a = np.radians(tilt_deg)
        pts[:, 2] += pts[:, 0] * np.tan(a)
    pts += rng.normal(0, noise, pts.shape)
    # Störpunkte oberhalb der Fläche (z. B. Arm, Geländer)
    clutter = rng.uniform([-1, -1, 1.0], [1, 1, 3.0], (300, 3))
    return np.vstack([pts, clutter])
