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

Verdeckung: Die Rohrleitung über der Markierung (Bogen, Drehgelenk J4, Ausleger) verdeckt aus
Sicht des Sensors oft einen großen Teil des Randes. Der Mittelpunkt wird deshalb mit bekanntem
Radius nahe der vom Armmodell erwarteten Lage gesucht (Punkte auf dem Rand, keine außerhalb,
keine im Rohrquerschnitt). Ist weniger als ca. 90° Rand sichtbar, liefert die Wand des
Auslassrohrs über der Markierung (bekannter `pipe_radius`, konzentrisch) die Mitte.

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
    marker_offset: float = 0.8  # m, Scheibe über dem Auslassende (über größter Eintauchtiefe)
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


def _circle_search(xy: np.ndarray, radius: float, seed: np.ndarray, window: float,
                   hole: float = 0.0, pull: float = 0.0, step: float = 0.004):
    """Mittelpunkt eines Kreises mit bekanntem Radius, dessen Rand teilweise verdeckt ist.

    Gesucht wird im Fenster um `seed` der Mittelpunkt, bei dem möglichst viele Punkte genau auf
    dem Rand liegen und (fast) keiner außerhalb. Schattenkanten verdeckender Rohre sind gerade
    und passen nicht zum Kreis; die gespiegelte Lösung eines Teilbogens hätte Punkte außerhalb.
    `hole`: Innerhalb dieses Radius (Auslassrohr) kann in Höhe der Markierung nichts liegen –
    ein falscher Mittelpunkt, dessen Kreis den Rohrquerschnitt statt des Randes trifft, hätte
    dort Markierungspunkte. `pull` [Punkte/m]: leichte Bevorzugung von Lösungen nahe `seed`.
    """
    g = np.arange(-window, window + step / 2, step)
    cx, cy = np.meshgrid(seed[0] + g, seed[1] + g)
    cand = np.column_stack([cx.ravel(), cy.ravel()])
    cand = cand[np.hypot(*(cand - seed).T) <= window]
    best, best_support = None, 0
    for chunk in np.array_split(cand, max(1, len(cand) // 500)):
        d = np.hypot(xy[None, :, 0] - chunk[:, None, 0], xy[None, :, 1] - chunk[:, None, 1])
        outside = np.mean(d > radius + 0.008, axis=1)
        support = np.sum((d > radius - 0.008) & (d <= radius + 0.008), axis=1)
        support[outside > 0.02] = 0
        if hole > 0:
            support = support - 3 * np.sum(d < hole, axis=1)
        if pull > 0:
            support = support - pull * np.hypot(*(chunk - seed).T)
        k = int(np.argmax(support))
        if support[k] > best_support:
            best, best_support = chunk[k], support[k]
    return best if best_support >= 10 else None


def _pipe_center(sel: np.ndarray, cfg: OutletConfig, z0: float, seed, window: float, axis):
    """Mitte des Auslassrohrs über der Markierung (senkrechte Rohrwand, bekannter Radius).

    Das Rohr sitzt konzentrisch auf der Markierung und ist oft dort sichtbar, wo der Rand der
    Markierung von der Rohrleitung darüber verdeckt wird. Liefert (Mitte in Höhe z0, Anzahl
    Randpunkte) oder None."""
    band = sel[(sel[:, 2] > z0 + 0.03) & (sel[:, 2] < z0 + 0.35)]
    if len(band) < 30:
        return None
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    xy = band[:, :2] - np.outer(band[:, 2] - z0, a[:2] / a[2])  # auf Höhe z0 zurückprojiziert
    xy = xy[np.hypot(*(xy - seed).T) < cfg.pipe_radius + window + 0.03]
    if len(xy) < 30:
        return None
    c = _circle_search(xy, cfg.pipe_radius, np.asarray(seed, float), window,
                       hole=cfg.pipe_radius - 0.012, pull=150.0, step=0.003)
    if c is None:
        return None
    rim = xy[np.abs(np.hypot(*(xy - c).T) - cfg.pipe_radius) < 0.008]
    if len(rim) < 30:
        return None
    c = least_squares(lambda m: np.hypot(*(rim - m).T) - cfg.pipe_radius, c).x
    return c, len(rim)


def _marker_center(sel: np.ndarray, cfg: OutletConfig, expected=None, prior: float = 0.07,
                   axis=(0.0, 0.0, 1.0)):
    """Mittelpunkt und Höhe der Markierung oder None, wenn keine gefunden.

    Der Rand kann teilweise verdeckt sein (Rohrleitung darüber). `expected`: erwartete Mitte
    aus dem Armmodell; dann wird nur in dieser Höhe und bis `prior` daneben gesucht.
    """
    R = cfg.marker_radius
    if expected is not None:
        e = np.asarray(expected, float)
        sel = sel[(np.abs(sel[:, 2] - e[2]) < 0.2)
                  & (np.hypot(sel[:, 0] - e[0], sel[:, 1] - e[1]) < R + prior + 0.05)]
        if len(sel) < cfg.min_points:
            return None
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
    if expected is not None:
        c = e[:2]
        xy = xy[np.hypot(*(xy - c).T) < R + prior]
    else:  # nur die Scheibe: um den Median sammeln (Deckel o. ä. in derselben Höhe fallen heraus)
        c = np.median(xy, axis=0)
        for _ in range(3):
            near = xy[np.hypot(*(xy - c).T) < 1.5 * R]
            if len(near) < cfg.min_points:
                return None
            c = near.mean(axis=0)
        xy = near
    if len(xy) < cfg.min_points:
        return None
    if expected is not None and len(xy) < 40:  # Markierung fast ganz verdeckt: nur das Rohr
        pipe = _pipe_center(sel, cfg, z0, c, prior, axis)
        return (pipe[0], z0) if pipe is not None else None
    r = np.hypot(*(xy - c).T)
    # Markierung erkennbar an ihrer Ausdehnung (größer als jedes Rohr darüber)
    if np.percentile(r, 95) < 0.5 * R:
        return None
    center = _circle_search(xy, R, c, prior if expected is not None else R,
                            hole=max(0.0, cfg.pipe_radius - 0.015),
                            pull=150.0 if expected is not None and prior <= 0.1 else 0.0)
    if center is None:
        if expected is None:
            return None
        pipe = _pipe_center(sel, cfg, z0, c, prior, axis)
        return (pipe[0], z0) if pipe is not None else None
    # Feinanpassung an den Rand: äußerster Punkt je 5°-Sektor (die Kante, nicht das Band
    # innerhalb, sonst wandert die Mitte vom sichtbaren Bogen weg); Sektoren, die an einer
    # Schattenkante enden, liegen deutlich innerhalb und fallen heraus
    for _ in range(3):
        d = np.hypot(*(xy - center).T)
        ang = np.arctan2(xy[:, 1] - center[1], xy[:, 0] - center[0])
        sector = ((ang + np.pi) / (2 * np.pi) * 72).astype(int) % 72
        rim = []
        for k in np.unique(sector):
            m = sector == k
            i = np.argmax(d[m])
            if d[m][i] > R - 0.012:
                rim.append(xy[m][i])
        if len(rim) < 10:  # weniger als ca. 50° sichtbarer Rand: nur das Rohr darüber
            pipe = _pipe_center(sel, cfg, z0, c, prior, axis) if expected is not None else None
            return (pipe[0], z0) if pipe is not None else None
        rim = np.array(rim)
        center = least_squares(lambda m, p=rim: np.hypot(*(p - m).T) - R, center).x
    if expected is not None and len(rim) < 18:  # Rand über weniger als ca. 90° sichtbar
        pipe = _pipe_center(sel, cfg, z0, c, prior, axis)
        if pipe is not None:  # Rohrachse darüber ist dann das verlässlichere Merkmal
            return pipe[0], z0
    return center, z0


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


def detect_marker(points_arm: np.ndarray, dome_center, cfg: OutletConfig | None = None,
                  expected=None, prior: float = 0.07, axis=(0.0, 0.0, 1.0)) -> np.ndarray:
    """Mitte der Markierung (Oberseite Scheibe/Flansch) (3,) in Armbasis-Koordinaten [m].

    `expected`: erwartete Mitte aus dem Armmodell (Suche bis `prior` daneben)."""
    cfg = cfg or OutletConfig()
    found = _marker_center(_select(points_arm, dome_center, cfg), cfg, expected, prior, axis)
    if found is None:
        raise DetectionError(ERR_OUTLET_NOT_FOUND, "Markierungsscheibe nicht gefunden")
    xy, z = found
    return np.array([xy[0], xy[1], z])


def detect_outlet(points_arm: np.ndarray, dome_center, sensor_pos=None,
                  cfg: OutletConfig | None = None, axis=None, expected=None) -> np.ndarray:
    """Lage des Auslassendes (3,) in Armbasis-Koordinaten [m].

    `axis`: Richtung des Auslassrohrs nach oben (aus dem Armmodell), Standard senkrecht.
    `expected`: erwartete Mitte der Markierung laut Armmodell (engere, robustere Suche)."""
    cfg = cfg or OutletConfig()
    if cfg.marker_radius:
        a = np.array([0.0, 0.0, 1.0]) if axis is None else np.asarray(axis, float)
        a = a / np.linalg.norm(a)
        return detect_marker(points_arm, dome_center, cfg, expected, axis=a) - cfg.marker_offset * a
    sel = _select(points_arm, dome_center, cfg)

    bottom = np.sort(sel[:, 2])[min(4, len(sel) - 1)]  # 5. tiefster Punkt, robust gegen Ausreißer
    band = sel[sel[:, 2] < bottom + cfg.tip_band]
    if len(band) < cfg.min_points:
        raise DetectionError(ERR_OUTLET_NOT_FOUND, "Zu wenige Punkte am Auslassende")
    xy = _fit_circle(band[:, :2], cfg.pipe_radius, band[:, :2].mean(axis=0))
    return np.array([xy[0], xy[1], bottom])
