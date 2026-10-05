"""Kinematik des Verladearms (Vorwärts- und Rückwärtsrechnung).

Aufbau vom Haltepunkt zum Auslass:
    J1  Servo, dreht um die senkrechte Achse am Haltepunkt (links/rechts)
        innerer Ausleger, fest `incline_deg` fallend, Länge `inner_length`
        Winkel nach unten, Fallrohr `drop` senkrecht (bzw. `drop_tilt_deg` geneigt)
    J2  Servo, dreht um die Achse des Fallrohrs (links/rechts)
        90°-Winkel nach rechts, Rohr `offset_right`
    J3  Servo, dreht um die Achse dieses Rohrs (Ausleger heben/senken)
        90°-Winkel nach vorne, äußerer Ausleger `outer_length` (bei J3 = 0 waagerecht)
        90°-Winkel nach links, Rohr `offset_left`
    J4  freies Drehgelenk ohne Motor
        90°-Winkel nach unten, Auslass `outlet_length`; hängt durch die Schwerkraft

Koordinatensystem Armbasis: Ursprung auf der Achse J1 am Haltepunkt, x nach vorne (Richtung des
inneren Auslegers bei J1 = 0), y nach links, z nach oben. Einheit Meter, Winkel im Bogenmaß.

Die Achsregelung liegt in der SPS. Dieses Modul dient der Planung und Plausibilisierung,
der Live-Ansicht und als Referenz für die SPS-Programmierung.

Alle anlagenspezifischen Werte (Maße, Servo-Nullstellungen, Grenzen, Parkstellung, Hindernisse)
kommen aus der Anlagenkonfiguration und werden bei der Inbetriebnahme eingestellt
(docs/inbetriebnahme.md). Servowerte werden so angegeben, wie sie am Antrieb abgelesen werden.
"""

import dataclasses
import time
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import least_squares


def _rx(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _ry(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rz(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


_HALF_PI = np.pi / 2


JOINTS = ("q1", "q2", "q3")


@dataclass
class Joint:
    """Servoachse. Alle Werte in Servo-Grad, wie am Antrieb angezeigt."""

    min: float
    max: float
    park: float
    zero: float = 0.0  # Servowert in Nullstellung des Modells (Ausleger gestreckt nach vorne)
    direction: int = 1  # +1: Servo positiv = links drehen (J1, J2) bzw. heben (J3); sonst -1

    def to_model(self, servo_deg):
        return np.radians(self.direction * (np.asarray(servo_deg, dtype=float) - self.zero))

    def to_servo(self, q):
        return self.zero + self.direction * np.degrees(q)


def _outside_passage(samples, passage):
    """Punkte außerhalb eines senkrechten Durchgangs (x, y, Radius) durch das Hindernis."""
    if not passage:
        return np.ones(len(samples), dtype=bool)
    x, y, r = passage
    return np.hypot(samples[:, 0] - x, samples[:, 1] - y) >= r


@dataclass
class Obstacle:
    """Sperrbereich als Quader in Armbasis-Koordinaten [m].

    `passage` (x, y, Radius) lässt einen senkrechten Durchgang frei, z. B. durch die Domöffnung.
    `clearance` überschreibt den allgemeinen Mindestabstand.
    """

    name: str
    min: list
    max: list
    passage: tuple | None = None
    clearance: float | None = None

    def __post_init__(self):
        # Ecken in beliebiger Reihenfolge erlaubt (z. B. z-Werte unter J1 negativ und leicht
        # vertauscht): sonst wäre der Quader für die Kollisionsprüfung leer, aber sichtbar
        a, b = np.asarray(self.min, float), np.asarray(self.max, float)
        self.min, self.max = np.minimum(a, b).tolist(), np.maximum(a, b).tolist()

    def contains(self, samples: np.ndarray, clearance: float) -> np.ndarray:
        c = clearance if self.clearance is None else self.clearance
        lo, hi = np.asarray(self.min) - c, np.asarray(self.max) + c
        inside = np.all((samples >= lo) & (samples <= hi), axis=1)
        return inside & _outside_passage(samples, self.passage)


@dataclass
class OrientedBoxObstacle:
    """Gedrehter Quader: Mittelpunkt, drei Achsrichtungen (Zeilen) und halbe Kantenlängen."""

    name: str
    center: list
    axes: list
    half: list
    passage: tuple | None = None
    clearance: float | None = None

    def __post_init__(self):
        self.half = np.abs(np.asarray(self.half, float)).tolist()

    def contains(self, samples: np.ndarray, clearance: float) -> np.ndarray:
        c = clearance if self.clearance is None else self.clearance
        local = (samples - np.asarray(self.center, float)) @ np.asarray(self.axes, float).T
        inside = np.all(np.abs(local) <= np.asarray(self.half, float) + c, axis=1)
        return inside & _outside_passage(samples, self.passage)


@dataclass
class CylinderObstacle:
    """Zylinder (Tankkörper, Domkragen) um die Achse durch `p0` mit Richtung `axis`."""

    name: str
    p0: list
    axis: list
    radius: float
    half_length: float
    passage: tuple | None = None
    clearance: float | None = None

    def __post_init__(self):
        self.radius, self.half_length = abs(float(self.radius)), abs(float(self.half_length))

    def contains(self, samples: np.ndarray, clearance: float) -> np.ndarray:
        c = clearance if self.clearance is None else self.clearance
        a = np.asarray(self.axis, float)
        a = a / np.linalg.norm(a)
        d = samples - np.asarray(self.p0, float)
        along = d @ a
        radial = np.linalg.norm(d - along[:, None] * a, axis=1)
        inside = (np.abs(along) <= self.half_length + c) & (radial <= self.radius + c)
        return inside & _outside_passage(samples, self.passage)


def _default_joints():
    return {
        "q1": {"min": -120, "max": 120, "park": 70},
        "q2": {"min": -170, "max": 170, "park": -150},
        "q3": {"min": -35, "max": 50, "park": 10},
    }


def obstacle_from_dict(o: dict):
    """Sperrbereich aus der Anlagendatei. `form`: quader (Standard, achsparallel),
    quader_gedreht (center, axes, half) oder zylinder (p0, axis, radius, half_length)."""
    o = dict(o)
    form = o.pop("form", "quader")
    cls = {"quader": Obstacle, "quader_gedreht": OrientedBoxObstacle,
           "zylinder": CylinderObstacle}.get(form)
    if cls is None:
        raise ValueError(f"Hindernis {o.get('name')}: unbekannte Form {form!r}")
    return cls(**o)


@dataclass
class ArmGeometry:
    base_height: float = 5.0  # Rohrmitte innerer Ausleger auf Achse J1 über Fahrbahn [m]
    # Höhenbezug vor Ort: Oberkante Schnittstellenflansch am Eintritt J1 (Fallleitung von oben).
    # Ist flange_height gesetzt, gilt base_height = flange_height − flange_offset.
    flange_height: float | None = None  # Oberkante Schnittstellenflansch über Fahrbahn [m]
    flange_offset: float = 0.0  # Oberkante Flansch bis Rohrmitte innerer Ausleger auf J1 [m]
    # Bauform am Haltepunkt: "oben" = Zulauf als Fallleitung von oben durch J1 (HETA),
    # "unten" = Arm auf einer Säule. Bestimmt Darstellung, Simulation und festes Hindernis.
    support: str = "unten"
    feed_length: float = 1.5  # sichtbare Fallleitung über dem Schnittstellenflansch [m]
    pipe_diameter: float = 0.15  # Außendurchmesser Rohr der Ausleger [m] (Darstellung, Simulation)
    incline_deg: float = 3.0  # festes Gefälle des inneren Auslegers [°]
    drop_tilt_deg: float = 0.0  # Neigung des Fallrohrs (J2-Achse) gegen die Senkrechte [°]
    inner_length: float = 2.2
    drop: float = 0.5
    offset_right: float = 0.35
    outer_length: float = 2.4
    offset_left: float = 0.35
    outlet_length: float = 1.2
    joints: dict = field(default_factory=_default_joints)
    obstacles: list = field(default_factory=list)
    clearance: float = 0.15  # Mindestabstand Rohrachse zu Hindernissen [m]
    # Mindestspalt zwischen den Rohren des eigenen Arms (äußerer gegen inneren Ausleger, Säule/
    # Anschluss an J1) – deckt auch Antriebsgehäuse grob ab [m]
    self_clearance: float = 0.10
    approach_height: float = 0.3  # Anfahrpunkt über der Domöffnung [m]
    approach_lift: float = 0.5  # Vorpunkt so viel höher: von dort senkrecht absenken [m]
    insertion_depth: float = 0.4  # Eintauchtiefe, wenn für das Produkt nichts hinterlegt ist [m]

    def __post_init__(self):
        if self.flange_height is not None:
            self.base_height = float(self.flange_height) - float(self.flange_offset)
        self.joints = {
            k: j if isinstance(j, Joint) else Joint(**j) for k, j in self.joints.items()
        }
        self.obstacles = [obstacle_from_dict(o) if isinstance(o, dict) else o
                          for o in self.obstacles if getattr(o, "name", None) != FEED_NAME]
        for a, b, r, kind in fixed_parts(self):  # Fallleitung über J1: nicht dagegen schwenken
            if kind == "zulauf":
                # Eigener Abstand (Rohrradius + 5 cm) statt `clearance`: Lage und Maß sind genau
                # bekannt, und der Bereich darf nicht unter den Flansch bis an J1 heranreichen.
                c = self.pipe_diameter / 2 + 0.05
                lo, hi = float(min(a[2], b[2])), float(max(a[2], b[2])) + c
                self.obstacles.append(CylinderObstacle(
                    FEED_NAME, [0.0, 0.0, (lo + hi) / 2], [0.0, 0.0, 1.0], r,
                    max(0.0, (hi - lo) / 2 - c), clearance=c))

    def with_obstacles(self, extra) -> "ArmGeometry":
        """Kopie mit zusätzlichen Hindernissen (z. B. erkannter Tankwagen und Domdeckel)."""
        return dataclasses.replace(self, obstacles=list(self.obstacles) + list(extra or []))

    @property
    def bounds(self):
        a = np.array([self.joints[k].to_model([self.joints[k].min, self.joints[k].max])
                      for k in JOINTS])
        return a.min(axis=1), a.max(axis=1)

    @property
    def park(self) -> np.ndarray:
        return np.array([self.joints[k].to_model(self.joints[k].park) for k in JOINTS])

    def to_servo(self, q) -> list:
        return [round(float(self.joints[k].to_servo(v)), 2) for k, v in zip(JOINTS, q, strict=True)]


FEED_NAME = "Fallleitung Zulauf J1"


def shift_obstacle(o, d):
    """Hindernis um d [m] verschoben (gemessene Lage -> Modellraum bei bekanntem Modellfehler)."""
    d = np.asarray(d, float)
    p = o.passage and (o.passage[0] + d[0], o.passage[1] + d[1], o.passage[2])
    if isinstance(o, Obstacle):
        return dataclasses.replace(o, min=(np.asarray(o.min) + d).tolist(),
                                   max=(np.asarray(o.max) + d).tolist(), passage=p)
    if isinstance(o, OrientedBoxObstacle):
        return dataclasses.replace(o, center=(np.asarray(o.center) + d).tolist(), passage=p)
    return dataclasses.replace(o, p0=(np.asarray(o.p0) + d).tolist(), passage=p)


def fixed_parts(geom: "ArmGeometry") -> list:
    """Feste bzw. nur um die eigene Achse drehende Teile am Haltepunkt als Rohrstücke
    (Anfang, Ende, Radius, Art) in Armbasis-Koordinaten: Zulauf von oben samt Stück bis zum
    3°-Rohr, oder die Säule von unten. Für Darstellung, Simulation und Höhenkarte."""
    r = geom.pipe_diameter / 2
    if geom.support == "oben":
        top = geom.flange_offset + geom.feed_length
        return [(np.array([0.0, 0.0, geom.flange_offset]), np.array([0.0, 0.0, top]), r,
                 "zulauf"),
                (np.zeros(3), np.array([0.0, 0.0, geom.flange_offset]), r, "anschluss")]
    return [(np.array([0.0, 0.0, -geom.base_height]), np.array([0.0, 0.0, -0.25]), 0.18,
             "saeule")]


def product_insertion_depth(products: dict | None, product_id: int, fallback: float) -> float:
    """Eintauchtiefe für ProductId aus der Produkttabelle (Eintrag `default` als Rückfall)."""
    products = products or {}
    entry = products.get(product_id) or products.get(str(product_id)) or products.get("default")
    return float((entry or {}).get("insertion_depth", fallback))


SELF_NAME = "eigenem inneren Ausleger"
_OUTER = (3, 4, 5)  # Strecken ab J3: äußerer Ausleger, Winkel links, Auslass


def _seg_distance(p, a, b):
    """Abstand der Punkte p (N, M, 3) zur Strecke a–b (N, 3) bzw. (3,)."""
    a, b = np.broadcast_to(a, (len(p), 3)), np.broadcast_to(b, (len(p), 3))
    ab = (b - a)[:, None]
    t = np.clip(((p - a[:, None]) * ab).sum(-1) / np.maximum((ab * ab).sum(-1), 1e-12), 0, 1)
    return np.linalg.norm(p - (a[:, None] + t[..., None] * ab), axis=-1)


def self_collision(geom: ArmGeometry, pts_list, step: float = 0.05):
    """Je Stellung (N, 7, 3): Name des eigenen Armteils, das der äußere Teil berührt, sonst None.

    Geprüft wird alles ab J3 (äußerer Ausleger, Auslass) gegen den inneren Ausleger und die
    festen Teile an J1 (Anschluss/Säule; die Fallleitung ist ein normales Hindernis)."""
    pts = np.asarray(pts_list, float)
    if pts.ndim != 3 or pts.shape[1] != 7:  # keine vollständige Armstellung (z. B. eine Linie)
        return np.full(len(pts), None, dtype=object)
    seg = []
    for i in _OUTER:
        n = max(2, int(np.ceil(np.linalg.norm(pts[0, i + 1] - pts[0, i]) / step)) + 1)
        t = np.linspace(0, 1, n)[None, :, None]
        seg.append(pts[:, i][:, None] + t * (pts[:, i + 1] - pts[:, i])[:, None])
    outer = np.concatenate(seg, axis=1)
    names = np.full(len(pts), None, dtype=object)
    gap = geom.self_clearance
    hit = _seg_distance(outer, pts[:, 0], pts[:, 1]).min(axis=1) < geom.pipe_diameter + gap
    names[hit] = SELF_NAME
    for a, b, r, kind in fixed_parts(geom):
        if kind == "zulauf":
            continue
        h = _seg_distance(outer, a, b).min(axis=1) < r + geom.pipe_diameter / 2 + gap
        names[h & (names == None)] = "eigener Säule" if kind == "saeule" else "Anschluss J1"  # noqa: E711
    return names


def collision(geom: ArmGeometry, pts, step: float = 0.05) -> str | None:
    """Name des ersten Hindernisses, dem die Rohrführung näher als `clearance` kommt."""
    pts = np.asarray(pts)
    if (own := self_collision(geom, pts[None], step)[0]) is not None:
        return own
    if not geom.obstacles:
        return None
    samples = [pts[:1]]
    for a, b in zip(pts[:-1], pts[1:], strict=True):
        n = max(2, int(np.ceil(np.linalg.norm(b - a) / step)) + 1)
        samples.append(a + np.linspace(0, 1, n)[:, None] * (b - a))
    samples = np.vstack(samples)
    for o in geom.obstacles:
        if np.any(o.contains(samples, geom.clearance)):
            return o.name
    return None


def first_collision(geom: ArmGeometry, pts_list, step: float = 0.05):
    """Wie `collision`, aber für viele Stellungen auf einmal (N, 7, 3).

    Liefert (Index der ersten kollidierenden Stellung, Hindernis) oder (None, None)."""
    pts = np.asarray(pts_list, float)
    if len(pts) == 0:
        return None, None
    own = self_collision(geom, pts, step)
    if not geom.obstacles:
        hit = own != None  # noqa: E711
        return (int(np.argmax(hit)), own[int(np.argmax(hit))]) if hit.any() else (None, None)
    seg = []
    for i in range(pts.shape[1] - 1):
        a, b = pts[:, i], pts[:, i + 1]
        n = max(2, int(np.ceil(np.linalg.norm(b[0] - a[0]) / step)) + 1)  # Längen fest
        t = np.linspace(0, 1, n)[None, :, None]
        seg.append(a[:, None] + t * (b - a)[:, None])
    samples = np.concatenate(seg, axis=1)  # (N, M, 3)
    flat = samples.reshape(-1, 3)
    names = own.copy()
    hit_any = names != None  # noqa: E711
    for o in geom.obstacles:
        h = o.contains(flat, geom.clearance).reshape(samples.shape[:2]).any(axis=1)
        names[h & ~hit_any] = o.name
        hit_any |= h
    if not hit_any.any():
        return None, None
    i = int(np.argmax(hit_any))
    return i, names[i]


def validate(geom: ArmGeometry) -> list[str]:
    """Plausibilitätsprüfung der Parameter; leere Liste = in Ordnung."""
    problems = []
    for name in ("inner_length", "drop", "offset_right", "outer_length", "offset_left",
                 "outlet_length", "base_height"):
        if getattr(geom, name) <= 0:
            problems.append(f"{name} muss größer 0 sein")
    if geom.support not in ("oben", "unten"):
        problems.append("support: oben (Fallleitung von oben) oder unten (Säule)")
    if not 0.0 <= geom.flange_offset <= 3.0:
        problems.append("flange_offset (Flansch bis Rohrmitte innerer Ausleger) 0 … 3 m")
    for k in JOINTS:
        j = geom.joints.get(k)
        if j is None:
            problems.append(f"Achse {k} fehlt")
            continue
        if j.min >= j.max:
            problems.append(f"{k}: min muss kleiner max sein")
        if not j.min <= j.park <= j.max:
            problems.append(f"{k}: Parkstellung {j.park}° außerhalb {j.min}…{j.max}°")
        if j.direction not in (1, -1):
            problems.append(f"{k}: direction muss 1 oder -1 sein")
    for o in geom.obstacles:
        if isinstance(o, Obstacle) and np.any(np.asarray(o.min) >= np.asarray(o.max)):
            problems.append(f"Hindernis {o.name}: min muss in allen Achsen kleiner max sein")
    if not problems and (hit := collision(geom, forward(geom, geom.park))):
        problems.append(f"Parkstellung kollidiert mit {hit}")
    return problems


def forward(geom: ArmGeometry, q) -> np.ndarray:
    """Eckpunkte der Rohrführung (7, 3) für die Gelenkwinkel q = (q1, q2, q3).

    Reihenfolge: J1, Winkel unten, Winkel rechts, J3, Winkel links, J4, Auslassende.
    """
    q1, q2, q3 = q
    pts = [np.zeros(3)]
    r = _rz(q1) @ _ry(np.radians(geom.incline_deg))
    p = r[:, 0] * geom.inner_length
    pts.append(p)
    r = _rz(q1) @ _ry(np.radians(geom.drop_tilt_deg) + _HALF_PI)  # Winkel nach unten
    p = p + r[:, 0] * geom.drop
    pts.append(p)
    r = r @ _rx(q2) @ _rz(-_HALF_PI)  # J2, Winkel nach rechts
    p = p + r[:, 0] * geom.offset_right
    pts.append(p)
    r = r @ _rx(q3) @ _ry(-_HALF_PI)  # J3, Winkel nach vorne
    p = p + r[:, 0] * geom.outer_length
    pts.append(p)
    r = r @ _ry(-_HALF_PI)  # Winkel nach links
    p = p + r[:, 0] * geom.offset_left
    pts.append(p)
    # J4 ist frei drehbar: der Auslass steht senkrecht zur Gelenkachse und pendelt so weit
    # nach unten, wie es die Achse zulässt (Projektion der Schwerkraft auf die Drehebene).
    axis = r[:, 0]
    down = np.array([0.0, 0.0, -1.0])
    d = down - (down @ axis) * axis
    d /= np.linalg.norm(d)
    pts.append(p + d * geom.outlet_length)
    return np.array(pts)


def _rot_many(axis: int, t) -> np.ndarray:
    c, s = np.cos(t), np.sin(t)
    r = np.zeros((len(t), 3, 3))
    i, j = [(1, 2), (2, 0), (0, 1)][axis]
    r[:, axis, axis] = 1.0
    r[:, i, i], r[:, j, j], r[:, i, j], r[:, j, i] = c, c, -s, s
    return r


def forward_many(geom: ArmGeometry, qs) -> np.ndarray:
    """`forward` für viele Stellungen auf einmal: (N, 3) -> (N, 7, 3)."""
    qs = np.atleast_2d(np.asarray(qs, float))
    n = len(qs)
    pts = np.zeros((n, 7, 3))
    rz1 = _rot_many(2, qs[:, 0])
    r = rz1 @ _ry(np.radians(geom.incline_deg))
    p = r[:, :, 0] * geom.inner_length
    pts[:, 1] = p
    r = rz1 @ _ry(np.radians(geom.drop_tilt_deg) + _HALF_PI)
    p = p + r[:, :, 0] * geom.drop
    pts[:, 2] = p
    r = r @ _rot_many(0, qs[:, 1]) @ _rz(-_HALF_PI)
    p = p + r[:, :, 0] * geom.offset_right
    pts[:, 3] = p
    r = r @ _rot_many(0, qs[:, 2]) @ _ry(-_HALF_PI)
    p = p + r[:, :, 0] * geom.outer_length
    pts[:, 4] = p
    r = r @ _ry(-_HALF_PI)
    p = p + r[:, :, 0] * geom.offset_left
    pts[:, 5] = p
    axis = r[:, :, 0]
    d = np.array([0.0, 0.0, -1.0]) + axis[:, 2:3] * axis  # wie forward: down - (down·a) a
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    pts[:, 6] = p + d * geom.outlet_length
    return pts


def outlet_axis(geom: ArmGeometry, q) -> np.ndarray:
    """Richtung des Auslassrohrs vom Auslassende nach oben (Einheitsvektor, fast senkrecht)."""
    p = forward(geom, q)
    a = p[5] - p[6]
    return a / np.linalg.norm(a)


def marker_point(geom: ArmGeometry, q, offset: float) -> np.ndarray:
    """Mitte der Markierung (Scheibe/Flansch) `offset` über dem Auslassende auf der Rohrachse."""
    return forward(geom, q)[6] + offset * outlet_axis(geom, q)


def tip(geom: ArmGeometry, q) -> np.ndarray:
    return forward(geom, q)[-1]


@dataclass
class IkResult:
    ok: bool
    q: np.ndarray
    error: float  # Restabstand zum Ziel [m]


def _newton(geom: ArmGeometry, target, q, lo, hi, iters: int = 30):
    """Gedämpftes Gauß-Newton-Verfahren mit Achsgrenzen, für Startwerte nahe der Lösung
    (Bahnen: der vorige Stützpunkt ist der Startwert). Etwa 10-mal schneller als least_squares."""
    h = 1e-6
    probe = np.vstack([np.zeros(3), h * np.eye(3)])
    for _ in range(iters):
        t = forward_many(geom, q + probe)[:, -1]
        r = t[0] - target
        if np.linalg.norm(r) < 1e-5:
            break
        jac = (t[1:] - t[0]).T / h
        dq = np.linalg.solve(jac.T @ jac + 1e-6 * np.eye(3), -jac.T @ r)
        q = np.clip(q + dq, lo, hi)
    return q, float(np.linalg.norm(tip(geom, q) - target))


def inverse(geom: ArmGeometry, target, q0=None, tol: float = 0.002,
            fast: bool = False) -> IkResult:
    """Gelenkwinkel, mit denen das Auslassende auf `target` steht (innerhalb der Achsgrenzen).

    Numerisch; mit `q0` wird die nächstgelegene Lösung bevorzugt (stetige Bahnen).
    Ohne `q0` werden mehrere Startwerte probiert und die Lösung nahe der Parkstellung gewählt.
    `fast=True`: allgemeiner Löser mit begrenzter Rechenzeit (Suche nach Umwegen, viele Versuche).
    """
    target = np.asarray(target, dtype=float)
    lo, hi = geom.bounds

    def residual(q):
        return tip(geom, q) - target

    starts = [q0] if q0 is not None else []
    if q0 is None:
        heading = np.arctan2(target[1], target[0])
        for q2 in (-2.0, -1.0, 0.0, 1.0, 2.0):
            starts.append([heading - q2 / 2, q2, 0.0])
        starts.append(geom.park)

    best = None
    for s in starts:
        s = np.clip(np.asarray(s, dtype=float), lo + 1e-6, hi - 1e-6)
        x, err = _newton(geom, target, s, lo, hi) if q0 is not None else (None, np.inf)
        if err >= tol:  # schneller Weg nicht konvergiert (z. B. an einer Achsgrenze)
            sol = least_squares(residual, s, bounds=(lo, hi), xtol=1e-10, ftol=1e-10,
                                max_nfev=40 if fast else None)
            x, err = sol.x, float(np.linalg.norm(sol.fun))
        cost = err + (0.0 if q0 is not None else 1e-3 * np.linalg.norm(x - geom.park))
        if best is None or cost < best[0]:
            best = (cost, x, err)
        if q0 is not None:
            break
    _, q, err = best
    return IkResult(ok=err < tol, q=q, error=err)


def _line(geom: ArmGeometry, q0, p_from, p_to, steps: int, what: str, offset=None):
    """Gerade Bahn des Auslassendes von p_from nach p_to per Rückwärtsrechnung.

    `offset` ist ein gemessener Modellfehler (Istlage - Modell); die Modellziele werden um ihn
    verschoben, damit das reale Auslassende auf der Bahn liegt.
    Liefert (Gelenkwinkel je Stützpunkt, Eckpunkte je Stützpunkt, Fehlertext oder None).
    """
    offset = np.zeros(3) if offset is None else np.asarray(offset, dtype=float)
    q, qs, pts = np.asarray(q0, dtype=float), [], []
    for u in np.linspace(0, 1, steps):
        res = inverse(geom, p_from + (p_to - p_from) * u - offset, q0=q)
        if not res.ok:
            return qs, pts, f"{what} nicht erreichbar ({u * 100:.0f} % der Bahn)"
        q = res.q
        qs.append(q)
        pts.append(forward(geom, q))
        if hit := collision(geom, pts[-1]):
            return qs, pts, f"Kollision mit {hit} ({what})"
    return qs, pts, None


def _arm_length(geom: ArmGeometry) -> float:
    return (geom.inner_length + geom.drop + geom.offset_right + geom.outer_length
            + geom.offset_left + geom.outlet_length)


def _joint_move(geom: ArmGeometry, q_from, q_to, steps: int, what: str,
                max_step: float = 0.03):
    """Synchrone Gelenkbewegung (alle Achsen starten und enden gemeinsam) mit Kollisionsprüfung.

    Geprüft wird so fein, dass sich kein Punkt der Rohrführung zwischen zwei Prüfstellungen mehr
    als `max_step` bewegt (sonst könnte ein weiter Schwenk durch einen dünnen Deckel „springen“).
    Zurück kommen `steps` Stellungen für Stützpunkte und Anzeige.
    """
    q_from, q_to = np.asarray(q_from, float), np.asarray(q_to, float)
    fine = int(np.ceil(np.abs(q_to - q_from).max() * _arm_length(geom) / max_step)) + 1
    if geom.obstacles:
        us = np.linspace(0, 1, max(fine, 2))
        i, hit = first_collision(geom, forward_many(geom, q_from + np.outer(us, q_to - q_from)))
        if hit:
            qs = [q_from + (q_to - q_from) * v for v in np.linspace(0, us[i], max(2, steps))]
            return qs, [forward(geom, q) for q in qs], f"Kollision mit {hit} ({what})"
    qs = [q_from + (q_to - q_from) * u for u in np.linspace(0, 1, steps)]
    return qs, [forward(geom, q) for q in qs], None


def _safe_joint_move(geom: ArmGeometry, q_from, q_to, steps: int, what: str):
    """Synchrone Gelenkbewegung; kollidiert sie, Umweg: J3 heben, schwenken, J3 senken.

    Liefert (Zwischenziele, Gelenkwinkel, Eckpunkte, Fehlertext oder None). Jedes Zwischenziel ist
    ein Stützpunkt für die SPS; dazwischen fährt sie synchron, also genau die geprüfte Bahn.
    """
    q_from, q_to = np.asarray(q_from, float), np.asarray(q_to, float)
    qs, pts, err = _joint_move(geom, q_from, q_to, steps, what)
    if not err:
        return [q_to], qs, pts, None
    top = geom.bounds[1][2]
    base = max(q_from[2], q_to[2])
    for q3 in np.unique(np.append(np.arange(base + np.radians(5), top, np.radians(5)), top)):
        a = np.array([q_from[0], q_from[1], q3])
        b = np.array([q_to[0], q_to[1], q3])
        all_q, all_p, ok = [], [], True
        for s, e, n in ((q_from, a, steps // 3), (a, b, steps), (b, q_to, steps // 3)):
            sq, sp, serr = _joint_move(geom, s, e, max(n, 4), what)
            if serr:
                ok = False
                break
            all_q += sq
            all_p += sp
        if ok:
            return [a, b, q_to], all_q, all_p, None
    return None, qs, pts, err


def _result(geom, plan, q_move, move, q_insert, insert):
    plan.update(
        ok=True,
        q_move=[q.tolist() for q in q_move],
        q_insert=[q.tolist() for q in q_insert],
        move=[m.round(4).tolist() for m in move],
        insert=[m.round(4).tolist() for m in insert],
    )
    if q_insert:
        plan.update(
            q_above_deg=np.degrees(q_insert[0]).round(2).tolist(),
            q_inside_deg=np.degrees(q_insert[-1]).round(2).tolist(),
            servo_above_deg=geom.to_servo(q_insert[0]),
            servo_inside_deg=geom.to_servo(q_insert[-1]),
        )
    return plan


def inverse_candidates(geom: ArmGeometry, target, tol: float = 0.002) -> list:
    """Alle deutlich verschiedenen Lösungen (z. B. Ellenbogen links/rechts), Park-nächste zuerst."""
    target = np.asarray(target, dtype=float)
    lo, hi = geom.bounds
    heading = np.arctan2(target[1], target[0])
    starts = [geom.park] + [[heading - q2 / 2, q2, 0.0] for q2 in (-2.4, -1.6, -0.8, 0.8, 1.6, 2.4)]
    sols = []
    for st in starts:
        st = np.clip(np.asarray(st, float), lo + 1e-6, hi - 1e-6)
        fit = least_squares(lambda q: tip(geom, q) - target, st, bounds=(lo, hi),
                            xtol=1e-10, ftol=1e-10)
        if np.linalg.norm(fit.fun) < tol and all(
                np.abs(fit.x - q).max() > np.radians(5) for q in sols):
            sols.append(fit.x)
    return sorted(sols, key=lambda q: np.linalg.norm(q - geom.park))


def _keyframes(geom: ArmGeometry, q0, keypoints, spacing: float = 0.35):
    """Gelenkwinkel für Stützpunkte entlang gerader Strecken (Rückwärtsrechnung, stetig)."""
    q, out = np.asarray(q0, float), []
    p = tip(geom, q)
    for k in keypoints:
        k = np.asarray(k, float)
        n = max(1, int(np.ceil(np.linalg.norm(k - p) / spacing)))
        for u in np.linspace(0, 1, n + 1)[1:]:
            res = inverse(geom, p + (k - p) * u, q0=q, fast=True)
            if not res.ok:
                return None
            q = res.q
            out.append(q)
        p = k
    return out


def _check_frames(geom: ArmGeometry, q0, frames, what: str, steps_per_rad: float = 40):
    """Gelenklineare Fahrt zwischen den Stützpunkten prüfen (so fährt die SPS)."""
    all_q, all_p, prev = [], [], np.asarray(q0, float)
    for q in frames:
        n = max(4, int(np.abs(q - prev).max() * steps_per_rad) + 2)
        sq, sp, err = _joint_move(geom, prev, q, n, what)
        if err:
            return None, None, err
        all_q += sq
        all_p += sp
        prev = q
    return all_q, all_p, None


def _transit(geom: ArmGeometry, q0, q_goal, goal_point, safe_z: float, move_steps: int,
             what: str, max_frames: int = 8, around=None, routes: bool = True,
             search: bool = True, deadline: float = float("inf")):
    """Kollisionsfreie Fahrt von q0 nach q_goal. Reihenfolge der Versuche:
    1. synchrone Gelenkbewegung (ggf. mit angehobenem Ausleger)
    2. senkrecht auf sichere Höhe, waagerecht zum Ziel
    3. wie 2, aber seitlich am Dom vorbei (`around`, 8 Richtungen, 1 m Abstand), z. B. wenn
       der offene Deckel höher ist, als der Arm den Auslass heben kann
    Liefert (Stützpunkte, Gelenkwinkel, Eckpunkte, Fehlertext)."""
    vias, qs, pts, err = _safe_joint_move(geom, q0, q_goal, move_steps, what)
    if not err or not routes:
        return vias, qs, pts, err
    first_err = err
    start = tip(geom, q0)
    goal = np.asarray(goal_point, float)
    z = max(safe_z, start[2])
    up = [start[0], start[1], z]
    c = np.asarray(goal if around is None else around, float)
    paths = [[up, [goal[0], goal[1], z]]]
    for ang in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        v = [c[0] + np.cos(ang), c[1] + np.sin(ang), z]
        paths += [[up, v, [goal[0], goal[1], z]], [up, v]]
    for keys in paths:
        # möglichst wenige Stützpunkte; jede gelenklineare Teilstrecke wird geprüft
        for spacing in (2.0, 1.2, 0.8, 0.5):
            if time.monotonic() > deadline:
                return None, None, None, f"{first_err}; Suche nach Umweg abgebrochen (Zeitlimit)"
            frames = _keyframes(geom, q0, keys + [goal], spacing)
            if frames is None or len(frames) > max_frames:
                continue
            if np.abs(frames[-1] - q_goal).max() > np.radians(2):
                # anderer Ast der Rückwärtsrechnung: in sicherer Höhe umorientieren
                if len(frames) >= max_frames:
                    continue
                frames.append(np.asarray(q_goal, float))
            else:
                frames[-1] = np.asarray(q_goal, float)
            qs, pts, err = _check_frames(geom, q0, frames, what)
            if not err:
                return frames, qs, pts, None
    # 4. Suche im Gelenkraum (RRT-Connect)
    if search:
        found = _search(geom, q0, [q_goal], deadline, what, max_frames)
        if found:
            return (*found[1:], None)
    if time.monotonic() > deadline:
        return None, None, None, f"{first_err}; Suche nach Umweg abgebrochen (Zeitlimit)"
    return None, None, None, first_err


def _search(geom: ArmGeometry, q0, goals, deadline: float, what: str, max_frames: int = 8):
    """Weg im Gelenkraum zu einem der Ziele, geglättet und fein geprüft.
    Liefert (Zielindex, Stützpunkte, Gelenkwinkel, Eckpunkte) oder None."""
    found = _rrt_connect(geom, q0, goals, deadline - 0.3)  # Reserve für Glätten und Prüfen
    if found is None:
        return None
    k, path = found
    frames = _shortcut(geom, q0, path)
    frames[-1] = np.asarray(goals[k], float)
    if len(frames) > max_frames:
        return None
    qs, pts, err = _check_frames(geom, q0, frames, what)
    return None if err else (k, frames, qs, pts)


def _edge_free(geom: ArmGeometry, a, b, max_step: float) -> bool:
    n = int(np.ceil(np.abs(b - a).max() * _arm_length(geom) / max_step)) + 1
    us = np.linspace(0, 1, max(n, 2))
    return first_collision(geom, forward_many(geom, a + np.outer(us, b - a)))[1] is None


def _rrt_connect(geom: ArmGeometry, qa, goals, deadline: float, step: float = 0.3,
                 max_step: float = 0.08, iters: int = 4000, seed: int = 0):
    """Kollisionsfreier Weg im Gelenkraum von qa zu einem der Ziele (zwei Suchbäume, die
    aufeinander zuwachsen; der Zielbaum hat eine Wurzel je Ziel). Grob geprüft; die geglätteten
    Stützpunkte prüft `_check_frames` danach fein. Fester Zufallsstartwert: gleiche Szene,
    gleiche Bahn. Liefert (Zielindex, Weg ohne Startstellung) oder None."""
    rng = np.random.default_rng(seed)
    lo, hi = geom.bounds
    a = ([np.asarray(qa, float)], [-1])  # wächst von qa aus
    b = ([np.asarray(q, float) for q in goals], [-1] * len(goals))  # wächst von den Zielen aus

    def extend(tree, q):
        nodes, parent = tree
        d = np.abs(np.asarray(nodes) - q).max(axis=1)
        i = int(d.argmin())
        reached = d[i] <= step
        new = q if reached else nodes[i] + (q - nodes[i]) * step / d[i]
        if not _edge_free(geom, nodes[i], new, max_step):
            return None, False
        nodes.append(new)
        parent.append(i)
        return len(nodes) - 1, reached

    def branch(tree, i):
        nodes, parent = tree
        out = []
        while True:
            out.append(nodes[i])
            if parent[i] == -1:
                return out, i  # i = Wurzel
            i = parent[i]

    grow, other = a, b
    for _ in range(iters):
        if time.monotonic() > deadline:
            return None
        ig, _ = extend(grow, rng.uniform(lo, hi))
        if ig is not None:
            while (res := extend(other, grow[0][ig]))[0] is not None:
                io, reached = res
                if reached:  # Bäume verbunden
                    ia, ib = (ig, io) if grow is a else (io, ig)
                    to_start, to_goal = branch(a, ia)[0], branch(b, ib)
                    path = to_start[::-1] + to_goal[0][1:]
                    return to_goal[1], path[1:]
        grow, other = other, grow
    return None


def _shortcut(geom: ArmGeometry, q0, path, max_step: float = 0.03):
    """Stützpunkte weglassen, solange die direkte synchrone Fahrt frei bleibt."""
    pts = [np.asarray(q0, float)] + [np.asarray(q, float) for q in path]
    out, i = [], 0
    while i < len(pts) - 1:
        j = len(pts) - 1
        while j > i + 1 and not _edge_free(geom, pts[i], pts[j], max_step):
            j -= 1
        out.append(pts[j])
        i = j
    return out


def plan_motion(geom: ArmGeometry, target_mm, normal, insertion_depth: float | None = None,
                q_start=None, move_steps: int = 36, insert_steps: int = 16,
                time_limit: float = 3.5):
    """Job 1: Istlage (sonst Park) -> Vorpunkt hoch über dem Dom -> senkrecht auf den
    Anfahrpunkt -> senkrecht eintauchen.

    Beide Armstellungen (Ellenbogen links/rechts) werden probiert: Beim Eintauchen darf z. B. der
    Rohrbogen an J4 nicht über dem Domdeckel stehen. Die Schwenkbewegung endet über dem Vorpunkt;
    führt die direkte Fahrt durch ein Hindernis, geht es in sicherer Höhe oder seitlich herum.
    `time_limit` [s] begrenzt die Suche nach Umwegen (Zeitüberwachung der SPS: 5 s).
    """
    deadline = time.monotonic() + time_limit
    center = np.asarray(target_mm, dtype=float) / 1000.0
    n = np.asarray(normal, dtype=float)
    n /= np.linalg.norm(n)
    above = center + n * geom.approach_height
    depth = geom.insertion_depth if insertion_depth is None else insertion_depth
    inside = center - n * depth
    q0 = geom.park if q_start is None else np.asarray(q_start, dtype=float)

    plan = {"park": forward(geom, geom.park).round(4).tolist(), "ok": False,
            "insertion_depth": depth, "code": 30}
    candidates = inverse_candidates(geom, above)
    if not candidates:
        plan["reason"] = "Anfahrpunkt nicht erreichbar, Arbeitsraum oder Achsgrenzen prüfen"
        return plan
    err = None
    lifts = sorted({min(v, geom.approach_lift) for v in (geom.approach_lift, 0.35, 0.2, 0.1)},
                   reverse=True)
    options = []  # (q_above, Eintauchen, Vorpunkt, Absenken) je Armstellung und Vorhubhöhe
    for q_above in candidates:
        q_insert, insert, err = _line(geom, q_above, above, inside, insert_steps, "Eintauchen")
        if err:
            continue
        for lift in lifts:
            pre = inverse(geom, above + n * lift, q0=q_above)
            if not pre.ok:
                continue
            q_down, down, err = _line(geom, pre.q, above + n * lift, above, 8, "Absenken")
            if not err:
                options.append((q_above, q_insert, insert, lift, pre.q, q_down, down))
    # kartesische Umwege nur zum höchsten Vorpunkt je Armstellung (dort ist am meisten Platz)
    highest = [o for i, o in enumerate(options)
               if i == 0 or o[0] is not options[i - 1][0]]

    def done(option, vias, q_move, move):
        q_above, q_insert, insert, lift, _, q_down, down = option
        q_down[-1] = q_above  # exakt auf den geprüften Eintauchbeginn
        plan.update(move_vias=[q.tolist() for q in vias + [q_above]], approach_lift=lift)
        return _result(geom, plan, q_move + q_down, move + down, q_insert, insert)

    def transit(o, routes):
        return _transit(geom, q0, o[4], above + n * o[3], (above + n * o[3])[2], move_steps,
                        "Anfahrt", around=center, routes=routes, search=False,
                        deadline=deadline)

    for o in options:  # 1. direkte Fahrt (ggf. mit angehobenem Ausleger)
        vias, q_move, move, err = transit(o, False)
        if not err:
            return done(o, vias, q_move, move)
    # 2. Suche im Gelenkraum zu allen möglichen Vorpunkten gleichzeitig (60 % der Restzeit)
    budget = time.monotonic() + 0.6 * max(0.0, deadline - time.monotonic())
    found = _search(geom, q0, [o[4] for o in options], budget, "Anfahrt") if options else None
    if found:
        k, frames, q_move, move = found
        return done(options[k], frames, q_move, move)
    for o in highest:  # 3. kartesische Umwege über sichere Höhe / seitlich am Dom vorbei
        vias, q_move, move, err = transit(o, True)
        if not err:
            return done(o, vias, q_move, move)
    plan.update(reason=err or "Kein kollisionsfreier Weg gefunden",
                code=31 if err and "Kollision" in err else 30)
    return plan


def plan_correction(geom: ArmGeometry, q_actual, tip_measured, target_mm, normal,
                    insertion_depth: float, insert_steps: int = 16,
                    horizontal_only: bool = True):
    """Job 2: Auslass über dem Dom nachgemessen -> korrigierte Anfahrstellung und Eintauchbahn.

    Der Unterschied zwischen gemessenem Auslassende und Modell (Getriebespiel, Durchbiegung,
    Kalibrierung) wird für die restliche Bahn ausgeglichen. Standardmäßig nur waagerecht: Das
    Rohrende ist von oben schlecht zu sehen, und die Höhe ist beim Eintauchen unkritisch.
    """
    q_actual = np.asarray(q_actual, dtype=float)
    center = np.asarray(target_mm, dtype=float) / 1000.0
    n = np.asarray(normal, dtype=float)
    n /= np.linalg.norm(n)
    above = center + n * geom.approach_height
    inside = center - n * insertion_depth
    offset = np.asarray(tip_measured, dtype=float) - tip(geom, q_actual)
    if horizontal_only:
        offset[2] = 0.0

    plan = {"park": forward(geom, geom.park).round(4).tolist(), "ok": False,
            "insertion_depth": insertion_depth, "code": 30,
            "model_offset_mm": (offset * 1000).round(1).tolist(),
            "correction_mm": ((above - np.asarray(tip_measured))[:2] * 1000).round(1).tolist()}
    q_insert, insert, err = _line(geom, q_actual, above, inside, insert_steps,
                                  "Eintauchen nach Korrektur", offset=offset)
    if err:
        plan.update(reason=err, code=31 if "Kollision" in err else 30)
        return plan
    move = [forward(geom, q_actual), insert[0]]
    return _result(geom, plan, [q_actual, q_insert[0]], move, q_insert, insert)


def plan_retract(geom: ArmGeometry, q_start, lift: float, lift_steps: int = 8,
                 move_steps: int = 36, fallback=None, time_limit: float = 3.5):
    """Job 3: senkrecht aus dem Dom heraus (so hoch wie erreichbar, höchstens `lift`), dann
    kollisionsfrei in die Parkstellung.

    `fallback`: Stützpunkte der Anfahrt aus Job 1 (Start bis zum Vorpunkt senkrecht über dem
    Dom). Findet die Planung keinen Weg, fährt der Arm senkrecht auf den Vorpunkt und diesen
    geprüften Weg rückwärts.
    """
    q_start = np.asarray(q_start, dtype=float)
    p0 = tip(geom, q_start)
    plan = {"park": forward(geom, geom.park).round(4).tolist(), "ok": False, "code": 30}
    deadline = time.monotonic() + time_limit
    result = _retract_new(geom, q_start, p0, lift, lift_steps, move_steps, plan, deadline)
    if result["ok"] or not fallback:
        return result
    back = _retract_reverse(geom, q_start, p0, fallback, lift_steps, dict(plan))
    return back if back["ok"] else result


def _retract_reverse(geom, q_start, p0, fallback, lift_steps, plan):
    frames = [np.asarray(q, float) for q in reversed(fallback)]
    h = tip(geom, frames[0])[2] - p0[2]
    q_lift, lift_pts, err = _line(geom, q_start, p0, p0 + [0, 0, max(h, 0.0)], lift_steps,
                                  "Herausfahren")
    if err:
        plan.update(reason=err)
        return plan
    if np.abs(frames[-1] - geom.park).max() > 1e-6:
        frames.append(geom.park)
    qs, pts, err = _check_frames(geom, q_lift[-1], frames, "Rückfahrt (Anfahrweg rückwärts)")
    if err:
        plan.update(reason=err, code=31)
        return plan
    plan = _result(geom, plan, qs, pts, [], [])
    plan.update(move_vias=[q.tolist() for q in frames], q_lift=[q.tolist() for q in q_lift],
                lift=[m.round(4).tolist() for m in lift_pts], reversed=True)
    return plan


def _retract_new(geom, q_start, p0, lift, lift_steps, move_steps, plan, deadline):
    err = "Herausfahren nicht möglich"
    for h in np.linspace(lift, min(lift, 0.3), 5):
        q_lift, lift_pts, err = _line(geom, q_start, p0, p0 + [0, 0, h], lift_steps,
                                      "Herausfahren")
        if not err:
            break
    if err:
        plan.update(reason=err, code=31 if "Kollision" in err else 30)
        return plan
    top = tip(geom, q_lift[-1])
    vias, q_move, move, err = _transit(geom, q_lift[-1], geom.park, tip(geom, geom.park),
                                       top[2], move_steps, "Rückfahrt", around=p0,
                                       deadline=deadline)
    if err:
        plan.update(reason=err, code=31)
        return plan
    plan = _result(geom, plan, q_move, move, [], [])
    plan.update(move_vias=[q.tolist() for q in vias], q_lift=[q.tolist() for q in q_lift],
                lift=[m.round(4).tolist() for m in lift_pts])
    return plan


def pick(seq, n: int) -> list:
    """n gleichmäßig verteilte Elemente inkl. letztem (ohne erstes = Startstellung)."""
    if not seq:
        return []
    idx = np.unique(np.linspace(0, len(seq) - 1, n + 1).round().astype(int))[1:]
    return [seq[i] for i in idx]
