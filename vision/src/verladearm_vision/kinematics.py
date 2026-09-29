"""Kinematik des Verladearms (Vorwärts- und Rückwärtsrechnung).

Aufbau vom Haltepunkt zum Auslass:
    J1  Servo, dreht um die senkrechte Achse am Haltepunkt (links/rechts)
        innerer Ausleger, `incline_deg` fallend, Länge `inner_length`
        90°-Winkel nach unten, Fallrohr `drop`
    J2  Servo, dreht um die Achse des Fallrohrs (links/rechts)
        90°-Winkel nach rechts, Rohr `offset_right`
    J3  Servo, dreht um die Achse dieses Rohrs (Ausleger heben/senken)
        90°-Winkel nach vorne, äußerer Ausleger `outer_length` (bei J3 = 0 ebenfalls fallend)
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


@dataclass
class Obstacle:
    """Sperrbereich als Quader in Armbasis-Koordinaten [m]."""

    name: str
    min: list
    max: list


def _default_joints():
    return {
        "q1": {"min": -120, "max": 120, "park": 70},
        "q2": {"min": -170, "max": 170, "park": -150},
        "q3": {"min": -35, "max": 50, "park": 10},
    }


@dataclass
class ArmGeometry:
    base_height: float = 5.0  # Höhe J1 über Fahrbahn [m]
    incline_deg: float = 3.0
    inner_length: float = 2.2
    drop: float = 0.5
    offset_right: float = 0.35
    outer_length: float = 2.4
    offset_left: float = 0.35
    outlet_length: float = 1.2
    joints: dict = field(default_factory=_default_joints)
    obstacles: list = field(default_factory=list)
    clearance: float = 0.15  # Mindestabstand Rohrachse zu Hindernissen [m]
    approach_height: float = 0.3  # Anfahrpunkt über der Domöffnung [m]
    insertion_depth: float = 0.4  # Eintauchtiefe, wenn für das Produkt nichts hinterlegt ist [m]

    def __post_init__(self):
        self.joints = {
            k: j if isinstance(j, Joint) else Joint(**j) for k, j in self.joints.items()
        }
        self.obstacles = [o if isinstance(o, Obstacle) else Obstacle(**o) for o in self.obstacles]

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


def product_insertion_depth(products: dict | None, product_id: int, fallback: float) -> float:
    """Eintauchtiefe für ProductId aus der Produkttabelle (Eintrag `default` als Rückfall)."""
    products = products or {}
    entry = products.get(product_id) or products.get(str(product_id)) or products.get("default")
    return float((entry or {}).get("insertion_depth", fallback))


def collision(geom: ArmGeometry, pts, step: float = 0.05) -> str | None:
    """Name des ersten Hindernisses, dem die Rohrführung näher als `clearance` kommt."""
    if not geom.obstacles:
        return None
    pts = np.asarray(pts)
    samples = [pts[:1]]
    for a, b in zip(pts[:-1], pts[1:], strict=True):
        n = max(2, int(np.ceil(np.linalg.norm(b - a) / step)) + 1)
        samples.append(a + np.linspace(0, 1, n)[:, None] * (b - a))
    samples = np.vstack(samples)
    for o in geom.obstacles:
        lo = np.asarray(o.min) - geom.clearance
        hi = np.asarray(o.max) + geom.clearance
        if np.any(np.all((samples >= lo) & (samples <= hi), axis=1)):
            return o.name
    return None


def validate(geom: ArmGeometry) -> list[str]:
    """Plausibilitätsprüfung der Parameter; leere Liste = in Ordnung."""
    problems = []
    for name in ("inner_length", "drop", "offset_right", "outer_length", "offset_left",
                 "outlet_length", "base_height"):
        if getattr(geom, name) <= 0:
            problems.append(f"{name} muss größer 0 sein")
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
        if np.any(np.asarray(o.min) >= np.asarray(o.max)):
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
    r = r @ _ry(_HALF_PI)  # Winkel nach unten
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


def tip(geom: ArmGeometry, q) -> np.ndarray:
    return forward(geom, q)[-1]


@dataclass
class IkResult:
    ok: bool
    q: np.ndarray
    error: float  # Restabstand zum Ziel [m]


def inverse(geom: ArmGeometry, target, q0=None, tol: float = 0.002) -> IkResult:
    """Gelenkwinkel, mit denen das Auslassende auf `target` steht (innerhalb der Achsgrenzen).

    Numerisch; mit `q0` wird die nächstgelegene Lösung bevorzugt (stetige Bahnen).
    Ohne `q0` werden mehrere Startwerte probiert und die Lösung nahe der Parkstellung gewählt.
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
        sol = least_squares(residual, s, bounds=(lo, hi), xtol=1e-10, ftol=1e-10)
        err = float(np.linalg.norm(sol.fun))
        cost = err + (0.0 if q0 is not None else 1e-3 * np.linalg.norm(sol.x - geom.park))
        if best is None or cost < best[0]:
            best = (cost, sol.x, err)
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


def _joint_move(geom: ArmGeometry, q_from, q_to, steps: int, what: str):
    """Synchrone Gelenkbewegung (alle Achsen starten und enden gemeinsam) mit Kollisionsprüfung."""
    qs = [q_from + (q_to - q_from) * u for u in np.linspace(0, 1, steps)]
    pts = [forward(geom, q) for q in qs]
    for p in pts:
        if hit := collision(geom, p):
            return qs, pts, f"Kollision mit {hit} ({what})"
    return qs, pts, None


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


def plan_motion(geom: ArmGeometry, target_mm, normal, insertion_depth: float | None = None,
                q_start=None, move_steps: int = 36, insert_steps: int = 16):
    """Job 1: aktuelle Stellung (sonst Park) -> Anfahrpunkt über dem Dom -> Eintauchpunkt.

    Anfahrt als synchrone Gelenkbewegung, Eintauchen als senkrechte Bahn des Auslassendes.
    Liefert Gelenkwinkel und Eckpunkte der Rohrführung je Stützpunkt.
    """
    center = np.asarray(target_mm, dtype=float) / 1000.0
    n = np.asarray(normal, dtype=float)
    n /= np.linalg.norm(n)
    above = center + n * geom.approach_height
    depth = geom.insertion_depth if insertion_depth is None else insertion_depth
    inside = center - n * depth
    q0 = geom.park if q_start is None else np.asarray(q_start, dtype=float)

    plan = {"park": forward(geom, geom.park).round(4).tolist(), "ok": False,
            "insertion_depth": depth, "code": 30}
    first = inverse(geom, above)
    if not first.ok:
        plan["reason"] = (
            f"Anfahrpunkt nicht erreichbar (Abstand {first.error * 1000:.0f} mm), "
            "Arbeitsraum oder Achsgrenzen prüfen"
        )
        return plan
    q_move, move, err = _joint_move(geom, q0, first.q, move_steps, "Anfahrt")
    if err:
        plan.update(reason=err, code=31)
        return plan
    q_insert, insert, err = _line(geom, first.q, above, inside, insert_steps, "Eintauchen")
    if err:
        plan.update(reason=err, code=31 if "Kollision" in err else 30)
        return plan
    return _result(geom, plan, q_move, move, q_insert, insert)


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
                 move_steps: int = 36):
    """Job 3: senkrecht um `lift` aus dem Dom heraus, dann synchron in die Parkstellung."""
    q_start = np.asarray(q_start, dtype=float)
    p0 = tip(geom, q_start)
    plan = {"park": forward(geom, geom.park).round(4).tolist(), "ok": False, "code": 30}
    q_lift, lift_pts, err = _line(geom, q_start, p0, p0 + [0, 0, lift], lift_steps, "Herausfahren")
    if err:
        plan.update(reason=err, code=31 if "Kollision" in err else 30)
        return plan
    q_move, move, err = _joint_move(geom, q_lift[-1], geom.park, move_steps, "Rückfahrt")
    if err:
        plan.update(reason=err, code=31)
        return plan
    plan = _result(geom, plan, q_move, move, [], [])
    plan.update(q_lift=[q.tolist() for q in q_lift], lift=[m.round(4).tolist() for m in lift_pts])
    return plan


def pick(seq, n: int) -> list:
    """n gleichmäßig verteilte Elemente inkl. letztem (ohne erstes = Startstellung)."""
    if not seq:
        return []
    idx = np.unique(np.linspace(0, len(seq) - 1, n + 1).round().astype(int))[1:]
    return [seq[i] for i in idx]
