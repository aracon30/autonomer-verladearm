"""Auslass über der Domöffnung finden (Job 2: Nachmessen vor dem Eintauchen).

Der Sensor sieht Dom und Auslass im selben Bild. Die gemessene Lage des Auslassendes relativ
zum Dom ist unabhängig von Getriebespiel, Durchbiegung des Auslegers und Kalibrierfehlern.

Markierungsscheibe: Eine waagerechte Ringscheibe am Auslass (größer als der Rohrbogen darüber)
ist von oben immer sichtbar, auch wenn der Sensor genau längs in das senkrechte Rohr blickt und
dessen Wand gar nicht sieht. Ihr Außenrand liefert die Rohrmitte ohne Verzerrung. Ein
vorhandener Flansch am Auslassrohr kann die Scheibe ersetzen (`marker_radius` = halber
Flanschdurchmesser, `marker_offset` = Flanschoberkante bis Auslassende). Das Auslassende liegt
`marker_offset` unter der Markierung entlang der Rohrachse (`axis`, aus dem Armmodell), nicht
senkrecht darunter – bei großem Abstand zählt schon eine leichte Schräglage.

Vorgehen (Armbasis-Koordinaten, z oben):
1. Punkte in einem senkrechten Zylinder über dem Dom (knapp über Domoberkante bis `max_above`)
2. Mit Scheibe: dichteste waagerechte Schicht = Scheibenoberseite; äußerster Punkt je
   Winkelsektor = Scheibenrand; Kreisfit -> Mittelpunkt
   Ohne Scheibe: unterstes Band der Rohrwand, Kreisfit mit bekanntem Rohrradius
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

from .opening import DetectionError

ERR_OUTLET_NOT_FOUND = 33


@dataclass
class OutletConfig:
    search_radius: float = 0.4  # m um die Dommitte
    min_above: float = 0.08  # m über der Domoberkante
    max_above: float | None = None  # m; None = aus marker_offset (Anfahrhöhe + Reserve)
    marker_radius: float | None = 0.125  # m, Außenradius Markierungsscheibe; None = ohne
    marker_offset: float = 0.15  # m, Scheibe über dem Auslassende
    tip_band: float = 0.1  # m, ohne Scheibe: ausgewertetes unterstes Band der Rohrwand
    pipe_radius: float = 0.06  # m, Außenradius Auslassrohr
    min_points: int = 15


def _fit_circle(xy: np.ndarray, radius: float | None, centroid: np.ndarray) -> np.ndarray:
    """Kreismittelpunkt; mehrere Startwerte gegen gespiegelte lokale Minima bei Teilbögen."""
    r0 = radius if radius else np.hypot(*(xy - centroid).T).mean()

    def residual(m):
        rr = m[2] if radius is None else radius
        return np.hypot(*(xy - m[:2]).T) - rr

    best = None
    for ang in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        start = centroid + r0 * 0.7 * np.array([np.cos(ang), np.sin(ang)])
        if radius is None:
            start = np.append(start, r0)
        fit = least_squares(residual, start)
        if best is None or fit.cost < best.cost:
            best = fit
    return best.x[:2]


def _marker_center(sel: np.ndarray, cfg: OutletConfig):
    """Mittelpunkt und Höhe der Markierungsscheibe oder None, wenn keine gefunden."""
    bins = np.arange(sel[:, 2].min(), sel[:, 2].max() + 0.02, 0.01)
    if len(bins) < 2:
        return None
    hist, edges = np.histogram(sel[:, 2], bins=bins)
    k = int(np.argmax(hist))
    z0 = 0.5 * (edges[k] + edges[k + 1])
    layer = sel[np.abs(sel[:, 2] - z0) < 0.015]
    if len(layer) < cfg.min_points:
        return None
    xy = layer[:, :2]
    # nur die Scheibe: um den Median sammeln (Domdeckel o. ä. in derselben Höhe fallen heraus)
    c = np.median(xy, axis=0)
    for _ in range(3):
        xy_near = xy[np.hypot(*(xy - c).T) < 1.5 * cfg.marker_radius]
        if len(xy_near) < cfg.min_points:
            return None
        c = xy_near.mean(axis=0)
    xy = xy_near
    r = np.hypot(*(xy - c).T)
    # Scheibe erkennbar an ihrer Ausdehnung (größer als jedes Rohr darüber)
    if np.percentile(r, 95) < 0.6 * cfg.marker_radius:
        return None
    ang = np.arctan2(xy[:, 1] - c[1], xy[:, 0] - c[0])
    sector = ((ang + np.pi) / (2 * np.pi) * 36).astype(int) % 36
    rim = np.array([xy[sector == s][np.argmax(r[sector == s])] for s in np.unique(sector)])
    if len(rim) < 8:
        return None
    return _fit_circle(rim, cfg.marker_radius, c), z0


def _window(cfg: OutletConfig) -> float:
    if cfg.max_above is not None:
        return cfg.max_above
    return max(1.0, (cfg.marker_offset if cfg.marker_radius else 0.0) + 0.6)


def _select(points_arm, dome_center, cfg: OutletConfig) -> np.ndarray:
    c = np.asarray(dome_center, dtype=float)
    p = np.asarray(points_arm, dtype=float)
    r = np.hypot(p[:, 0] - c[0], p[:, 1] - c[1])
    above = p[:, 2] - c[2]
    sel = p[(r < cfg.search_radius) & (above > cfg.min_above) & (above < _window(cfg))]
    if len(sel) < cfg.min_points:
        raise DetectionError(ERR_OUTLET_NOT_FOUND, "Auslass über dem Dom nicht gefunden")
    return sel


def detect_marker(points_arm: np.ndarray, dome_center,
                  cfg: OutletConfig | None = None) -> np.ndarray:
    """Mitte der Markierung (Oberseite Scheibe/Flansch) (3,) in Armbasis-Koordinaten [m]."""
    cfg = cfg or OutletConfig()
    found = _marker_center(_select(points_arm, dome_center, cfg), cfg)
    if found is None:
        raise DetectionError(ERR_OUTLET_NOT_FOUND, "Markierungsscheibe nicht gefunden")
    xy, z = found
    return np.array([xy[0], xy[1], z])


def detect_outlet(points_arm: np.ndarray, dome_center, sensor_pos=None,
                  cfg: OutletConfig | None = None, axis=None) -> np.ndarray:
    """Lage des Auslassendes (3,) in Armbasis-Koordinaten [m].

    `axis`: Richtung des Auslassrohrs nach oben (aus dem Armmodell), Standard senkrecht."""
    cfg = cfg or OutletConfig()
    if cfg.marker_radius:
        a = np.array([0.0, 0.0, 1.0]) if axis is None else np.asarray(axis, float)
        a = a / np.linalg.norm(a)
        return detect_marker(points_arm, dome_center, cfg) - cfg.marker_offset * a
    sel = _select(points_arm, dome_center, cfg)

    bottom = np.sort(sel[:, 2])[min(4, len(sel) - 1)]  # 5. tiefster Punkt, robust gegen Ausreißer
    band = sel[sel[:, 2] < bottom + cfg.tip_band]
    if len(band) < cfg.min_points:
        raise DetectionError(ERR_OUTLET_NOT_FOUND, "Zu wenige Punkte am Auslassende")
    xy = _fit_circle(band[:, :2], cfg.pipe_radius, band[:, :2].mean(axis=0))
    return np.array([xy[0], xy[1], bottom])
