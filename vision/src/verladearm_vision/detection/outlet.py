"""Auslass über der Domöffnung finden (Job 2: Nachmessen vor dem Eintauchen).

Der Sensor sieht Dom und Auslass im selben Bild. Die gemessene Lage des Auslassendes relativ
zum Dom ist unabhängig von Getriebespiel, Durchbiegung des Auslegers und Kalibrierfehlern.

Markierungsscheibe: Eine waagerechte Ringscheibe am Auslass (größer als der Rohrbogen darüber)
ist von oben immer sichtbar, auch wenn der Sensor genau längs in das senkrechte Rohr blickt und
dessen Wand gar nicht sieht. Ihr Außenrand liefert die Rohrmitte ohne Verzerrung.

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
    max_above: float = 1.0
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
    c = xy.mean(axis=0)
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


def detect_outlet(points_arm: np.ndarray, dome_center, sensor_pos=None,
                  cfg: OutletConfig | None = None) -> np.ndarray:
    """Lage des Auslassendes (3,) in Armbasis-Koordinaten [m]."""
    cfg = cfg or OutletConfig()
    c = np.asarray(dome_center, dtype=float)
    p = np.asarray(points_arm, dtype=float)
    r = np.hypot(p[:, 0] - c[0], p[:, 1] - c[1])
    above = p[:, 2] - c[2]
    sel = p[(r < cfg.search_radius) & (above > cfg.min_above) & (above < cfg.max_above)]
    if len(sel) < cfg.min_points:
        raise DetectionError(ERR_OUTLET_NOT_FOUND, "Auslass über dem Dom nicht gefunden")

    if cfg.marker_radius:
        found = _marker_center(sel, cfg)
        if found is None:
            raise DetectionError(ERR_OUTLET_NOT_FOUND, "Markierungsscheibe nicht gefunden")
        xy, z = found
        return np.array([xy[0], xy[1], z - cfg.marker_offset])

    bottom = np.sort(sel[:, 2])[min(4, len(sel) - 1)]  # 5. tiefster Punkt, robust gegen Ausreißer
    band = sel[sel[:, 2] < bottom + cfg.tip_band]
    if len(band) < cfg.min_points:
        raise DetectionError(ERR_OUTLET_NOT_FOUND, "Zu wenige Punkte am Auslassende")
    xy = _fit_circle(band[:, :2], cfg.pipe_radius, band[:, :2].mean(axis=0))
    return np.array([xy[0], xy[1], bottom])
