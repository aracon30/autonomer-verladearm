"""Hindernisse aus der Messung: Tankkörper, Domkragen und offener Domdeckel.

Die Bahnplanung prüft jede Stellung des Arms gegen diese Hindernisse (zusätzlich zu den festen
Sperrbereichen der Anlage). Durch die Domöffnung bleibt ein senkrechter Durchgang frei, der
schmal genug ist, dass Auslass und Markierungsscheibe den Kragen nicht berühren.

Alle Angaben in Armbasis-Koordinaten (m, z oben).
"""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from verladearm_vision.kinematics import CylinderObstacle, Obstacle, OrientedBoxObstacle


@dataclass
class SceneConfig:
    tank_length: float = 14.0  # angenommene Länge des Tankkörpers (Messung sieht nur einen Teil)
    tank_clearance: float = 0.1  # Mindestabstand Rohrachse zum Tank
    flat_extent: float = 1.5  # ebenes Dach: angenommene halbe Breite/Länge um den Dom
    collar_wall: float = 0.05  # Wandstärke Domkragen
    passage_margin: float = 0.03  # Sicherheitsabstand im Durchgang durch die Öffnung
    lid_search: float = 0.9  # Deckel bis so weit außerhalb der Öffnung suchen
    lid_max_above: float = 1.2  # m über der Domoberkante
    lid_min_points: int = 80
    lid_margin: float = 0.05
    lid_clearance: float = 0.08


def detect_lid(arm_pts: np.ndarray, center, open_radius: float, cfg: SceneConfig | None = None):
    """Offenen Domdeckel neben der Öffnung finden; None, wenn keiner zu sehen ist.

    Kandidaten liegen seitlich der Öffnung und über der Domoberkante. Größte zusammenhängende
    Gruppe dicht belegter Rasterzellen (4 cm, mind. 3 Punkte) = Deckel. Vereinzelte Störpunkte
    (Geländer, Rauschen) verbinden sich so nicht mit dem Deckel; die Ausdehnung kommt aus
    Perzentilen, damit ein einzelner Ausreißer den Sperrbereich nicht aufbläht.
    """
    cfg = cfg or SceneConfig()
    c = np.asarray(center, float)
    p = np.asarray(arm_pts, float)
    d = np.hypot(p[:, 0] - c[0], p[:, 1] - c[1])
    h = p[:, 2] - c[2]
    cand = p[(d > open_radius * 0.8) & (d < open_radius + cfg.lid_search)
             & (h > 0.04) & (h < cfg.lid_max_above)]
    if len(cand) < cfg.lid_min_points:
        return None
    g = 0.04
    origin = cand[:, :2].min(axis=0)
    idx = np.floor((cand[:, :2] - origin) / g).astype(int)
    grid = np.zeros(idx.max(axis=0) + 1, dtype=int)
    np.add.at(grid, (idx[:, 0], idx[:, 1]), 1)
    labels, n = ndimage.label(grid >= 3, structure=np.ones((3, 3)))
    if n == 0:
        return None
    point_label = labels[idx[:, 0], idx[:, 1]]
    counts = np.bincount(point_label, minlength=n + 1)
    counts[0] = 0
    best = int(np.argmax(counts))
    if counts[best] < cfg.lid_min_points:
        return None
    lid = cand[point_label == best]
    mid = np.median(lid, axis=0)
    # am Deckel ausgerichteter Quader: radial (vom Dom weg), tangential (Scharnier), senkrecht
    e_r = np.array([mid[0] - c[0], mid[1] - c[1], 0.0])
    e_r /= np.linalg.norm(e_r)
    axes = np.array([e_r, [-e_r[1], e_r[0], 0.0], [0.0, 0.0, 1.0]])
    local = (lid - mid) @ axes.T
    lo, hi = np.percentile(local, 1, axis=0), np.percentile(local, 99, axis=0)
    return {
        "center": (mid + ((lo + hi) / 2) @ axes).round(3).tolist(),
        "axes": axes.round(4).tolist(),
        "half": ((hi - lo) / 2 + cfg.lid_margin).round(3).tolist(),
        "azimuth_deg": round(float(np.degrees(np.arctan2(e_r[1], e_r[0]))), 1),
        "height_m": round(float(lid[:, 2].max() - c[2]) if len(lid) < 20
                          else float(np.percentile(lid[:, 2], 99) - c[2]), 3),
        "points": int(len(lid)),
    }


def build_obstacles(op, transform, points_sensor, outlet_cfg, cfg: SceneConfig | None = None):
    """Hindernisse zum erkannten Dom (Opening aus detect_opening) und Zusatzinfos."""
    cfg = cfg or SceneConfig()
    center = transform.point(op.center)  # Oberkante Domkragen, Mitte
    apex = transform.point(op.tank_apex)  # Tankoberfläche unter der Mitte
    r_open = op.diameter / 2
    inner = max(outlet_cfg.pipe_radius, outlet_cfg.marker_radius or 0.0)
    passage = (float(center[0]), float(center[1]),
               max(0.02, r_open - inner - cfg.passage_margin))
    obstacles, info = [], {"durchgang_radius_m": round(passage[2], 3)}

    if op.tank_radius:  # runder Tank: Zylinder entlang der Tankachse
        axis = transform.direction(op.tank_axis)
        axis[2] = 0.0
        axis /= np.linalg.norm(axis)
        obstacles.append(CylinderObstacle(
            "Tankkörper", (apex - [0, 0, op.tank_radius]).tolist(), axis.tolist(),
            op.tank_radius, cfg.tank_length / 2, passage, cfg.tank_clearance))
    else:  # ebenes Dach: Quader unter der Dachfläche
        e = cfg.flat_extent
        obstacles.append(Obstacle(
            "Tankkörper", [apex[0] - e, apex[1] - e, apex[2] - 3.0],
            [apex[0] + e, apex[1] + e, apex[2]], passage, cfg.tank_clearance))
    if center[2] - apex[2] > 0.02:  # Domkragen
        mid = (center + apex) / 2
        obstacles.append(CylinderObstacle(
            "Domkragen", mid.tolist(), [0, 0, 1], r_open + cfg.collar_wall,
            float(center[2] - apex[2]) / 2, passage, cfg.tank_clearance))

    arm_pts = np.asarray(points_sensor) @ transform.T[:3, :3].T + transform.T[:3, 3]
    lid = detect_lid(arm_pts, center, r_open, cfg)
    if lid:
        obstacles.append(OrientedBoxObstacle("Domdeckel", lid["center"], lid["axes"],
                                             lid["half"], clearance=cfg.lid_clearance))
        info["deckel"] = lid
    return obstacles, info
