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


DOME_TYPES = ("offen", "armatur")


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
    lid_azimuth_deg=None,
    lid_open_deg=105.0,
    dome="offen",
    walkways=False,
    seed=0,
    return_info=False,
):
    """Runder Tank (Lkw oder Kesselwagen), Achse entlang Sensor-y, Dom mit Kragen oben.

    `center_xy` ist die Lage des ersten Doms, `height` der Abstand Sensor -> Oberkante Domkragen.
    Durch die offene Öffnung sieht der Sensor Produkt bzw. Tankinneres in `fill_depth` Tiefe.
    `lid_azimuth_deg`: offener Deckel, am Rand der Öffnung in dieser Richtung angeschlagen
    (Sensor-xy, 0° = +x) und um `lid_open_deg` aufgeklappt (90° = senkrecht).

    `dome`:
    - "offen": das ganze Mannloch ist offen, der Deckel am Kragenrand aufgeklappt.
    - "armatur": wie an realen Fahrzeugen – Domring mit vertieftem, geschlossenem Domdeckel; darin
      eine kleinere, seitlich versetzte Füllöffnung mit aufgeklappter Füllklappe sowie Armaturen
      (Be-/Entlüftung, Hebel). Maße zufällig in üblichen Grenzen.
    `walkways`: Laufstege (Gitterroste) links und rechts neben dem Dom, etwas über dem Dach.
    `return_info`: zusätzlich Sollwerte (Mitte und Durchmesser der Füllöffnung, Sensor-Koordinaten).
    """
    v = VEHICLES[kind]
    rng = np.random.default_rng(seed)
    r_tank = v["radius"]
    apex = height + v["collar_height"]  # Tankscheitel, weiter vom Sensor entfernt als der Kragen
    cx, cy = center_xy
    domes = [(cx, cy - i * v["dome_pitch"]) for i in range(openings)]
    if dome == "armatur":
        r_in = rng.uniform(0.25, 0.32)  # Domring innen
    else:
        r_in = v["opening_diameter"] / 2
    r_out = r_in + 0.04 if dome == "armatur" else r_in + 0.05  # Kragenwand

    def roof(xx):
        return apex + r_tank - np.sqrt(np.maximum(r_tank**2 - (xx - cx) ** 2, 0.0))

    ax = np.arange(-size / 2, size / 2, spacing)
    x, y = np.meshgrid(ax, ax)
    x, y = x.ravel(), y.ravel()
    on_tank = np.abs(x - cx) < r_tank * 0.97
    x, y = x[on_tank], y[on_tank]
    z = roof(x)
    keep = np.ones(len(x), dtype=bool)
    for ox, oy in domes:
        keep &= np.hypot(x - ox, y - oy) > r_out
    parts = [np.column_stack([x[keep], y[keep], z[keep]])]

    def disc(c, r0, r1, depth, n):
        a = rng.uniform(0, 2 * np.pi, n)
        rr = np.sqrt(rng.uniform(r0**2, r1**2, n))
        return np.column_stack([c[0] + rr * np.cos(a), c[1] + rr * np.sin(a), np.full(n, depth)])

    def wall(c, r, z0, z1, n):
        a = rng.uniform(0, 2 * np.pi, n)
        return np.column_stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a), rng.uniform(z0, z1, n)])

    info = {"dome": dome}
    for i, (ox, oy) in enumerate(domes):
        parts.append(disc((ox, oy), r_in + 0.005, r_out, height, 2500))  # Oberkante Kragen
        parts.append(wall((ox, oy), r_out, height, apex, 1500))  # Außenwand
        if dome != "armatur":
            depth = height - 0.02 if lid_closed else apex + fill_depth
            inner = disc((ox, oy), 0, r_in * 0.85, depth, 1500)
            parts.append(inner)
            if i == 0:
                info.update(center=np.array([ox, oy, height]), diameter=2 * r_in)
            continue
        # vertiefter Domdeckel mit versetzter Füllöffnung, Klappe und Armaturen
        plate = height + rng.uniform(0.04, 0.12)
        parts.append(wall((ox, oy), r_in, height, plate, 800))  # Innenwand Ring
        r_f = rng.uniform(0.11, 0.16)
        ecc, az = rng.uniform(0.0, r_in - r_f - 0.07), rng.uniform(0, 2 * np.pi)
        f = np.array([ox + ecc * np.cos(az), oy + ecc * np.sin(az)])
        rim_top = plate - 0.02  # Füllöffnung mit 2 cm hohem Rand
        fittings = []
        for _ in range(int(rng.integers(1, 4))):
            for _try in range(30):
                rc = rng.uniform(0.04, 0.07)
                a, d = rng.uniform(0, 2 * np.pi), rng.uniform(0, r_in - rc - 0.01)
                c = np.array([ox + d * np.cos(a), oy + d * np.sin(a)])
                if (np.linalg.norm(c - f) > r_f + rc + 0.05
                        and all(np.linalg.norm(c - c2) > rc + r2 + 0.02 for c2, r2, _ in fittings)):
                    fittings.append((c, rc, plate - rng.uniform(0.05, 0.18)))
                    break
        pl = disc((ox, oy), 0, r_in, plate, 6000)
        free = np.hypot(pl[:, 0] - f[0], pl[:, 1] - f[1]) > r_f + 0.02
        for c, rc, _ in fittings:
            free &= np.hypot(pl[:, 0] - c[0], pl[:, 1] - c[1]) > rc
        parts.append(pl[free])
        parts.append(disc(f, r_f, r_f + 0.02, rim_top, 600))
        parts.append(wall(f, r_f + 0.02, rim_top, plate, 300))
        parts.append(disc(f, 0, r_f * 0.85, apex + fill_depth, 800))  # Blick ins Tankinnere
        for c, rc, top in fittings:
            parts.append(disc(c, 0, rc, top, 400))
            parts.append(wall(c, rc, top, plate, 300))
        if i == 0:
            info.update(center=np.array([f[0], f[1], rim_top]), diameter=2 * r_f,
                        ring_center=np.array([ox, oy, height]), ring_diameter=2 * r_in,
                        fittings=len(fittings))
            if lid_azimuth_deg is not None:  # Füllklappe am Rand der Füllöffnung
                parts.append(_open_lid(f, r_f + 0.02, rim_top, lid_azimuth_deg, lid_open_deg, rng,
                                       n=1200))

    if lid_azimuth_deg is not None and not lid_closed and dome != "armatur":
        parts.append(_open_lid(domes[0], r_out, height, lid_azimuth_deg, lid_open_deg, rng))
    if walkways:  # Gitterroste neben dem Dom, entlang der Tankachse, mit Lücken
        for side in (-1, 1):
            w = rng.uniform(0.35, 0.5)
            x0 = cx + side * (r_out + rng.uniform(0.1, 0.25))
            gx = np.arange(0, w, spacing)
            gx = x0 + side * gx
            gy = np.arange(-size / 2, size / 2, spacing)
            mx, my = np.meshgrid(gx, gy)
            mx, my = mx.ravel(), my.ravel()
            ok = (np.abs(mx - cx) < r_tank * 0.9) & (rng.uniform(0, 1, mx.size) > 0.45)
            mz = roof(mx[ok]) - rng.uniform(0.05, 0.12)
            parts.append(np.column_stack([mx[ok], my[ok], mz]))
    pts = np.vstack(parts)
    pts += rng.normal(0, noise, pts.shape)
    clutter = rng.uniform([-1.5, -1.5, 1.0], [1.5, 1.5, height - 0.8], (300, 3))
    pts = np.vstack([pts, clutter])
    return (pts, info) if return_info else pts


def _open_lid(dome_xy, r_out, rim_depth, azimuth_deg, open_deg, rng, n=2500):
    """Punkte eines aufgeklappten Domdeckels (Sensorkoordinaten, z = Tiefe, oben = -z)."""
    phi, alpha = np.radians(azimuth_deg), np.radians(open_deg)
    radius = r_out + 0.02
    e_r = np.array([np.cos(phi), np.sin(phi), 0.0])  # nach außen
    t = np.array([-np.sin(phi), np.cos(phi), 0.0])  # Scharnierachse
    up = np.array([0.0, 0.0, -1.0])
    hinge = np.array([dome_xy[0], dome_xy[1], rim_depth]) + r_out * e_r
    v = -np.cos(alpha) * e_r + np.sin(alpha) * up  # vom Scharnier zur Deckelmitte
    center = hinge + radius * v
    a = rng.uniform(0, 2 * np.pi, n)
    rr = radius * np.sqrt(rng.uniform(0, 1, n))
    return center + np.outer(rr * np.cos(a), t) + np.outer(rr * np.sin(a), v)
