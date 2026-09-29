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


VEHICLES = {
    # Tankradius, Domöffnung, Kragenhöhe über Tankscheitel, Abstand mehrerer Dome [m]
    "lkw": dict(radius=1.1, opening_diameter=0.5, collar_height=0.12, dome_pitch=1.6),
    "kesselwagen": dict(radius=1.5, opening_diameter=0.5, collar_height=0.25, dome_pitch=2.0),
}


def make_tank_vehicle(
    kind="lkw",
    center_xy=(0.0, 0.0),
    height=3.5,
    size=4.0,
    spacing=0.012,
    noise=0.003,
    openings=1,
    lid_closed=False,
    fill_depth=1.2,
    seed=0,
) -> np.ndarray:
    """Runder Tank (Lkw oder Kesselwagen), Achse entlang Sensor-y, Dom mit Kragen oben.

    `center_xy` ist die Lage des ersten Doms, `height` der Abstand Sensor -> Oberkante Domkragen.
    Durch die offene Öffnung sieht der Sensor Produkt bzw. Tankinneres in `fill_depth` Tiefe.
    """
    v = VEHICLES[kind]
    rng = np.random.default_rng(seed)
    r_tank, r_in = v["radius"], v["opening_diameter"] / 2
    r_out = r_in + 0.05  # Kragenwand
    apex = height + v["collar_height"]  # Tankscheitel, weiter vom Sensor entfernt als der Kragen
    cx, cy = center_xy
    domes = [(cx, cy - i * v["dome_pitch"]) for i in range(openings)]

    ax = np.arange(-size / 2, size / 2, spacing)
    x, y = np.meshgrid(ax, ax)
    x, y = x.ravel(), y.ravel()
    dx = x - cx
    on_tank = np.abs(dx) < r_tank * 0.97
    x, y, dx = x[on_tank], y[on_tank], dx[on_tank]
    z = apex + r_tank - np.sqrt(r_tank**2 - dx**2)
    keep = np.ones(len(x), dtype=bool)
    for ox, oy in domes:
        keep &= np.hypot(x - ox, y - oy) > r_out
    parts = [np.column_stack([x[keep], y[keep], z[keep]])]

    for ox, oy in domes:
        # Oberkante Kragen (Ring) und etwas Außenwand
        ring = rng.uniform(0, 2 * np.pi, 2500)
        rr = np.sqrt(rng.uniform((r_in + 0.005) ** 2, r_out**2, 2500))
        parts.append(np.column_stack([ox + rr * np.cos(ring), oy + rr * np.sin(ring),
                                      np.full(2500, height)]))
        wall = rng.uniform(0, 2 * np.pi, 1500)
        parts.append(np.column_stack([ox + r_out * np.cos(wall), oy + r_out * np.sin(wall),
                                      rng.uniform(height, apex, 1500)]))
        n_in = 1500
        a = rng.uniform(0, 2 * np.pi, n_in)
        rr = np.sqrt(rng.uniform(0, (r_in * 0.85) ** 2, n_in))
        disc = np.column_stack([ox + rr * np.cos(a), oy + rr * np.sin(a)])
        if lid_closed:  # Deckel liegt auf dem Kragen
            parts.append(np.column_stack([disc, np.full(n_in, height - 0.02)]))
        else:  # Blick ins Tankinnere
            parts.append(np.column_stack([disc, np.full(n_in, apex + fill_depth)]))

    pts = np.vstack(parts)
    pts += rng.normal(0, noise, pts.shape)
    clutter = rng.uniform([-1.5, -1.5, 1.0], [1.5, 1.5, height - 0.8], (300, 3))
    return np.vstack([pts, clutter])
