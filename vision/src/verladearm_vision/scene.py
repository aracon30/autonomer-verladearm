"""Hindernisse aus der Messung: Tankkörper, Domkragen und offener Domdeckel.

Die Bahnplanung prüft jede Stellung des Arms gegen diese Hindernisse (zusätzlich zu den festen
Sperrbereichen der Anlage). Durch die Domöffnung bleibt ein senkrechter Durchgang frei, der
schmal genug ist, dass Auslass und Markierungsscheibe den Kragen nicht berühren.

Alle Angaben in Armbasis-Koordinaten (m, z oben).
"""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from verladearm_vision.kinematics import (
    CylinderObstacle,
    Obstacle,
    OrientedBoxObstacle,
    fixed_parts,
    forward,
    tip,
)


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
    # Aufbauten am Dom (Domring, Füllklappe, Armaturen, Laufstege): alles im Umkreis, was über den
    # Rand der Öffnung ragt, wird Hindernis; über der Öffnung bleibt der Durchgang frei
    dome_scan: float = 1.0  # Umkreis um die Öffnung [m]
    dome_min_height: float = 0.03  # ab dieser Höhe über dem Öffnungsrand [m]
    dome_cell: float = 0.06  # Rasterweite [m]
    flange_margin: float = 0.03  # Referenzflansch mindestens so weit über dem Öffnungsrand [m]
    # Rückfahrt ohne gültige Messung aus Job 1 (z. B. nach Handbetrieb): Höhenkarte, neu aufgenommen
    context_max_age_s: float = 4 * 3600  # Messung aus Job 1 gilt so lange für die Rückfahrt
    context_max_offset: float = 0.5  # Auslass so weit neben dem gemessenen Dom: neu messen [m]
    map_cell: float = 0.3  # Rasterweite der Höhenkarte [m]
    map_min_points: int = 5  # Punkte je Zelle, damit sie als belegt gilt
    map_voxel_points: int = 4  # Mindestpunkte je 10-cm-Würfel (Ausreißer verwerfen)
    map_step: float = 0.05  # Höhen auf diese Stufen aufrunden (fasst Zellen zusammen) [m]
    map_clearance: float = 0.08  # Mindestabstand Rohrachse zur Höhenkarte (wie Deckel) [m]
    arm_exclude: float = 0.35  # Punkte so nah am eigenen Arm gehören zum Arm [m]


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
    inner = outlet_cfg.pipe_radius  # durch die Öffnung taucht nur das Auslassrohr
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
                                             lid["half"], passage, cfg.lid_clearance))
        info["deckel"] = lid
    built, info["aufbauten"] = dome_structures(arm_pts, center, passage, cfg, lid)
    obstacles += built
    return obstacles, info


def dome_structures(arm_pts: np.ndarray, center, passage, cfg: SceneConfig | None = None,
                    lid: dict | None = None):
    """Aufbauten rund um die Öffnung als Höhenkarte: Domring, Füllklappe, Armaturen, Laufstege.

    Jede Rasterzelle mit Punkten höher als `dome_min_height` über dem Öffnungsrand wird ein Quader
    bis zu ihrer Höhe; der senkrechte Durchgang über der Öffnung bleibt frei. Ragt etwas in den
    Durchgang (z. B. Klappe nicht ganz geöffnet), entsteht dort ein Hindernis ohne Durchgang – das
    Eintauchen wird dann abgelehnt (Fehler 31).
    """
    cfg = cfg or SceneConfig()
    c = np.asarray(center, float)
    p = np.asarray(arm_pts, float)
    d = np.hypot(p[:, 0] - c[0], p[:, 1] - c[1])
    h = p[:, 2] - c[2]
    p = p[(d < cfg.dome_scan) & (h > cfg.dome_min_height) & (h < cfg.lid_max_above)]
    if lid:  # der Deckel ist schon als eng anliegender Quader erfasst
        local = (p - np.asarray(lid["center"])) @ np.asarray(lid["axes"]).T
        p = p[np.any(np.abs(local) > np.asarray(lid["half"]), axis=1)]
    info = {"punkte": int(len(p)), "quader": 0, "durchgang_frei": True}
    if len(p) == 0:
        return [], info
    vox = np.floor(p / 0.05).astype(int)  # vereinzelte Punkte verwerfen
    _, vinv, vcount = np.unique(vox, axis=0, return_inverse=True, return_counts=True)
    p = p[vcount[vinv.ravel()] >= 3]
    obstacles = []
    inside = np.hypot(p[:, 0] - passage[0], p[:, 1] - passage[1]) < passage[2]
    if inside.sum() >= 15:  # etwas hängt über der Öffnung
        q = p[inside]
        obstacles.append(Obstacle("Öffnung verdeckt", (q.min(axis=0) - 0.02).tolist(),
                                  (q.max(axis=0) + 0.02).tolist(), None, cfg.lid_clearance))
        info["durchgang_frei"] = False
    p = p[~inside]
    if len(p) == 0:
        return obstacles, info
    g = cfg.dome_cell
    idx = np.floor(p[:, :2] / g).astype(int)
    cells, inv, counts = np.unique(idx, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    order = np.argsort(inv, kind="stable")
    tops = np.array([np.sort(z)[-3] if len(z) >= 3 else -np.inf
                     for z in np.split(p[order, 2], np.cumsum(counts)[:-1])])
    ok = counts >= 3
    cells, tops = cells[ok], np.ceil(tops[ok] / 0.02) * 0.02
    bottom = float(c[2] - 0.3)
    for iy in np.unique(cells[:, 1]):  # Zellen einer Zeile mit gleicher Höhe zusammenfassen
        row = np.where(cells[:, 1] == iy)[0]
        row = row[np.argsort(cells[row, 0])]
        start = row[0]
        for prev, cur in zip(list(row), list(row[1:]) + [None], strict=True):
            if (cur is not None and cells[cur, 0] == cells[prev, 0] + 1
                    and np.isclose(tops[cur], tops[start])):
                continue
            obstacles.append(Obstacle(
                "Aufbauten am Dom", [cells[start, 0] * g, iy * g, bottom],
                [(cells[prev, 0] + 1) * g, (iy + 1) * g, float(tops[start])], passage,
                cfg.lid_clearance))
            start = cur
    info["quader"] = len(obstacles)
    return obstacles, info


def _segment_distance(p, a, b):
    ab = b - a
    t = np.clip((p - a) @ ab / max(ab @ ab, 1e-12), 0.0, 1.0)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def obstacles_from_points(arm_pts: np.ndarray, geom, q, cfg: SceneConfig | None = None,
                          passage=None, known=(), exclude=None, interior=None,
                          name: str = "Fahrzeug/Aufbau (Höhenkarte)"):
    """Hindernisse aus einer Aufnahme ohne Domerkennung: Höhenkarte von allem, was nicht Arm ist.

    Für die Rückfahrt, wenn keine passende Messung aus Job 1 vorliegt (Arm von Hand in einen Dom
    gefahren, Dienst neu gestartet). Jede belegte Rasterzelle wird ein Quader vom Boden bis zur
    höchsten Stelle, die mindestens `map_min_points` Punkte erreichen – Tankwagen, offener Deckel,
    Treppe, Geländer. Punkte nahe der Rohrführung in Stellung `q` gehören zum Arm und entfallen.
    Senkrecht über dem Auslass bleibt ein Durchgang frei, damit der Arm herausfahren kann.

    Auch für den **Scan bei jeder Fahrt** (Fremdkörper): `known` sind schon erfasste Hindernisse
    (Tank, Domkragen, Deckel, feste Sperrbereiche) – ihre Punkte entfallen, übrig bleibt, was neu
    im Weg steht (Leiter, Fass, Führerhaus, Geländer am Fahrzeug). `exclude` (x, y, Radius): Bereich
    um den Dom, den `dome_structures` schon abdeckt. `passage` (x, y, Radius): freier Durchgang,
    Standard über dem Auslassende.
    """
    cfg = cfg or SceneConfig()
    p = np.asarray(arm_pts, float)
    ground = -geom.base_height
    pts = forward(geom, q)
    keep = p[:, 2] > ground + 0.2
    for a, b in zip(pts[:-1], pts[1:], strict=True):
        keep &= _segment_distance(p, a, b) > cfg.arm_exclude
    for a, b, r, _ in fixed_parts(geom):  # Fallleitung bzw. Säule am Haltepunkt
        keep &= _segment_distance(p, a, b) > r + 0.2
    if exclude is not None:
        keep &= np.hypot(p[:, 0] - exclude[0], p[:, 1] - exclude[1]) > exclude[2]
    if interior is not None:  # Blick durch die Öffnung ins Tankinnere (x, y, Radius, Randhöhe)
        x, y, r, z = interior
        keep &= ~((np.hypot(p[:, 0] - x, p[:, 1] - y) < r) & (p[:, 2] < z + 0.03))
    for o in known:  # schon als Hindernis erfasst (samt Sicherheitsabstand)
        if keep.any():
            c = o.clearance if o.clearance is not None else geom.clearance
            keep[keep] &= ~o.contains(p[keep], c)
    p = p[keep]
    # vereinzelte Punkte (fliegende Pixel an Kanten, Regen, Insekten) verwerfen: Würfel mit 10 cm
    # Kantenlänge brauchen mehrere Punkte; echte Flächen liefern dort Dutzende
    if len(p):
        vox = np.floor(p / 0.1).astype(int)
        _, vinv, vcount = np.unique(vox, axis=0, return_inverse=True, return_counts=True)
        p = p[vcount[vinv.ravel()] >= cfg.map_voxel_points]
    if passage is None:
        t = tip(geom, q)
        passage = (float(t[0]), float(t[1]), 0.05)
    info = {"punkte": int(len(p)), "zellen": 0, "quader": 0}
    if len(p) == 0:
        return [], info
    g = cfg.map_cell
    idx = np.floor(p[:, :2] / g).astype(int)
    cells, inv, counts = np.unique(idx, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    order = np.argsort(inv, kind="stable")
    splits = np.cumsum(counts)[:-1]
    k = cfg.map_min_points  # Höhe, die mindestens k Punkte erreichen: einzelne Ausreißer
    ok = counts >= k        # (fliegende Pixel, Regen) blähen die Zelle so nicht auf
    heights = np.array([np.sort(z)[-k] if len(z) >= k else -np.inf
                        for z in np.split(p[order, 2], splits)])
    cells, heights = cells[ok], heights[ok]
    info["zellen"] = int(len(cells))
    levels = np.ceil((heights - ground) / cfg.map_step) * cfg.map_step + ground
    # benachbarte Zellen einer Zeile mit gleicher Höhenstufe zu einem Quader zusammenfassen
    obstacles = []
    for iy in np.unique(cells[:, 1]):
        row = np.where(cells[:, 1] == iy)[0]
        row = row[np.argsort(cells[row, 0])]
        start = row[0]
        for prev, cur in zip(list(row), list(row[1:]) + [None], strict=True):
            if (cur is not None and cells[cur, 0] == cells[prev, 0] + 1
                    and np.isclose(levels[cur], levels[start])):
                continue
            x0, x1 = cells[start, 0] * g, (cells[prev, 0] + 1) * g
            obstacles.append(Obstacle(
                name, [x0, iy * g, ground],
                [x1, (iy + 1) * g, float(levels[start])], passage, cfg.map_clearance))
            start = cur
    info["quader"] = len(obstacles)
    info["hoechster_punkt_m"] = round(float(heights.max()), 3) if len(heights) else None
    return obstacles, info


FOREIGN_NAME = "Fremdkörper (Scan)"


def foreign_obstacles(arm_pts: np.ndarray, geom, q, known, passage, dome_center=None,
                      cfg: SceneConfig | None = None, opening=None):
    """Scan bei jeder automatischen Fahrt: alles im Blickfeld, was weder Fahrbahn noch Arm noch
    schon erfasstes Hindernis ist, wird Hindernis (Höhenkarte bis zum Boden). `opening`
    (x, y, Radius, Randhöhe): Innenraum der Öffnung, der Blick hinein ist kein Hindernis."""
    cfg = cfg or SceneConfig()
    exclude = None
    if dome_center is not None:
        exclude = (float(dome_center[0]), float(dome_center[1]), cfg.dome_scan)
    return obstacles_from_points(arm_pts, geom, q, cfg, passage=passage,
                                 known=list(known) + list(geom.obstacles), exclude=exclude,
                                 interior=opening, name=FOREIGN_NAME)
