"""Simulierter Sensor für Tests ohne Hardware (source.type: sim).

Erzeugt zu jeder Verladung (Job 1) einen neuen Tankwagen (Lkw oder Kesselwagen) an zufälliger
Stelle und rendert zusätzlich den ganzen Arm in seiner tatsächlichen Stellung (Rohrdurchmesser
`arm.pipe_diameter`) sowie die Bauform am Haltepunkt (Fallleitung von oben bzw. Säule).
`joint_error_deg` simuliert den Unterschied zwischen gemeldetem Servowinkel und realer Gelenklage
(Getriebespiel, Durchbiegung), damit das Nachmessen in Job 2 etwas zu korrigieren hat.
Am Auslass sitzt eine Markierungsscheibe (siehe detection/outlet.py); `marker_radius: null`
simuliert einen Auslass ohne Scheibe. Die Markierung wird von Rohrführung und Drehgelenk J4 aus
Sicht des Sensors teilweise verdeckt (wie am realen Arm); andere Verdeckungen werden nicht
simuliert.
`backlash_deg` simuliert das Getriebespiel je Achse (aus dem Abschnitt `drives` der
Anlagendatei): Das Gelenk bleibt je nach letzter Fahrtrichtung um die halbe Spielweite zurück,
Hubachsen (`backlash_preload`) hängen immer um die halbe Spielweite tiefer.
"""

import numpy as np

from verladearm_vision.calibration import SensorToArm
from verladearm_vision.drives import Backlash
from verladearm_vision.kinematics import JOINTS, ArmGeometry, fixed_parts, forward
from verladearm_vision.synthetic import make_tank_vehicle

# Höhe Oberkante Domkragen über Fahrbahn [m]
RIM_HEIGHT = {"lkw": (3.35, 3.6), "kesselwagen": (4.35, 4.55)}


def _segment_distance(p, s, a, b) -> np.ndarray:
    """Kleinster Abstand zwischen den Strecken p_i→s (Sichtlinien) und a→b (Rohrachse)."""
    d1, d2, r = s - p, b - a, p - a
    aa, e = np.einsum("ij,ij->i", d1, d1), d2 @ d2
    bb, c, f = d1 @ d2, np.einsum("ij,ij->i", d1, r), r @ d2
    den = aa * e - bb * bb
    sp = np.where(den > 1e-12, np.clip((bb * f - c * e) / np.where(den > 1e-12, den, 1), 0, 1), 0)
    t = (bb * sp + f) / e
    lo, hi = t < 0, t > 1
    sp = np.where(lo, np.clip(-c / aa, 0, 1), np.where(hi, np.clip((bb - c) / aa, 0, 1), sp))
    t = np.clip(t, 0, 1)
    return np.linalg.norm(p + d1 * sp[:, None] - (a + d2 * t[:, None]), axis=1)


class SimulatedScene:
    def __init__(self, geom: ArmGeometry, transform: SensorToArm, vehicles=("lkw", "kesselwagen"),
                 joint_error_deg=(0.0, 0.0, 0.0), dome_spread=0.35, marker_radius=0.125,
                 marker_offset=0.8, empty=False, sensor_matrix=None, lid=True,
                 backlash_deg=(0.0, 0.0, 0.0), backlash_preload=(False, False, True),
                 pipe_radius=0.06, domes=("offen", "armatur"), walkways=0.5, foreign=0.0,
                 seed=None):
        self.geom, self.transform = geom, transform
        self.vehicles = list(vehicles)
        self.joint_error = np.radians(np.asarray(joint_error_deg, dtype=float))
        self.backlash = Backlash(backlash_deg, backlash_preload,
                                 [geom.joints[k].direction for k in JOINTS])
        self.offset = self.joint_error.copy()  # aktuelle Abweichung Gelenk − Modell [rad]
        self.dome_spread = dome_spread
        self.marker_radius, self.marker_offset = marker_radius, marker_offset
        self.pipe_radius = pipe_radius  # Auslassrohr
        self.rng = np.random.default_rng(seed)
        # eigener Zufall für das Messrauschen: die Fahrzeugfolge hängt so nicht davon ab,
        # wie viele Punkte vom Arm sichtbar sind
        self.noise = np.random.default_rng(None if seed is None else seed + 7919)
        # sensor_matrix: tatsächliche Montagelage (Sensor -> Armbasis), falls sie von der
        # Konfiguration abweichen soll (Test der Kalibrierung)
        self.true_t = np.asarray(sensor_matrix, float) if sensor_matrix is not None else transform.T
        self.inv = np.linalg.inv(self.true_t)
        self.empty = empty  # leere Station (Kalibrierung): kein Tankwagen
        self.lid = lid  # offener Domdeckel in zufälliger Richtung
        self.domes = list(domes)  # Dombauarten, zufällig je Fahrzeug
        self.walkways = walkways  # Anteil Fahrzeuge mit Laufstegen am Dom
        self.truth = None  # Sollwerte der Öffnung (Armbasis): center, diameter, dome
        self.foreign = foreign  # Anteil Fahrzeuge mit Fremdkörper daneben (Leiter, Pfosten …)
        self.objects = []  # Fremdkörper als Quader (min, max) in Armbasis-Koordinaten
        self.tank = None
        self.q_true = None
        self.count = 0

    def prepare(self, job: int, servo_deg=None):
        """Vom Vision-Dienst vor jeder Aufnahme aufgerufen."""
        if job in (0, 1) or self.tank is None:
            self._new_vehicle()
        if servo_deg is not None:
            q = np.array([self.geom.joints[k].to_model(v) for k, v in zip(JOINTS, servo_deg,
                                                                            strict=True)])
            self.offset = self.joint_error + np.radians(self.backlash(servo_deg))
            self.q_true = q + self.offset

    def _new_vehicle(self):
        kind = self.vehicles[self.count % len(self.vehicles)]
        self.count += 1
        sensor_z = self.transform.point(np.zeros(3))[2]  # Armbasis, z oben
        rim_z = -self.geom.base_height + self.rng.uniform(*RIM_HEIGHT[kind])
        dx, dy = self.rng.uniform(-self.dome_spread, self.dome_spread, 2)
        lid_az = float(self.rng.uniform(-180, 180)) if self.lid else None
        dome = self.domes[int(self.rng.integers(len(self.domes)))]
        walk = bool(self.rng.uniform() < self.walkways)
        tank_s, info = make_tank_vehicle(kind, center_xy=(dx, dy), height=sensor_z - rim_z,
                                         lid_azimuth_deg=lid_az,
                                         lid_open_deg=float(self.rng.uniform(95, 115)),
                                         dome=dome, walkways=walk,
                                         seed=int(self.rng.integers(1 << 30)), return_info=True)
        self.tank = tank_s  # Sensorkoordinaten; Sollwert über die tatsächliche Sensorlage
        c = self.true_t[:3, :3] @ info["center"] + self.true_t[:3, 3]
        self.truth = {"center": c,
                      "diameter": info["diameter"], "dome": dome, "walkways": walk}
        self.kind = kind
        self.objects = []
        if self.foreign and self.rng.uniform() < self.foreign:
            self.place_object()

    def _arm_points(self, q, spacing=0.012):
        pts = forward(self.geom, q)
        sensor = self.true_t[:3, 3]
        r_arm = self.geom.pipe_diameter / 2
        radius = (r_arm, r_arm, r_arm, r_arm, r_arm, self.pipe_radius)
        out = []
        segments = [((pts[i], pts[i + 1]), radius[i]) for i in range(6)]
        segments += [((a, b), r) for a, b, r, _ in fixed_parts(self.geom)]
        for (a, b), r in segments:
            axis = b - a
            length = np.linalg.norm(axis)
            axis /= length
            helper = np.array([0, 0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0, 0])
            u = np.cross(axis, helper)
            u /= np.linalg.norm(u)
            v = np.cross(axis, u)
            t = np.arange(0, length, spacing)
            ang = np.linspace(0, 2 * np.pi, max(12, int(2 * np.pi * r / spacing)), endpoint=False)
            tt, aa = np.meshgrid(t, ang)
            normal = np.cos(aa)[..., None] * u + np.sin(aa)[..., None] * v
            p = a + tt[..., None] * axis + r * normal
            visible = np.einsum("...i,...i->...", normal, sensor - p) > 0  # dem Sensor zugewandt
            out.append(p[visible])
        if self.marker_radius:  # Oberseite der Markierungsscheibe
            ang = self.noise.uniform(0, 2 * np.pi, 1500)
            rr = np.sqrt(self.noise.uniform(self.pipe_radius ** 2, self.marker_radius ** 2, 1500))
            axis = (pts[5] - pts[6]) / np.linalg.norm(pts[5] - pts[6])
            m = pts[6] + self.marker_offset * axis  # Mitte der Markierung auf der Rohrachse
            u = np.cross(axis, [1.0, 0.0, 0.0])
            u /= np.linalg.norm(u)
            v = np.cross(axis, u)  # Scheibe/Flansch rechtwinklig zum Rohr
            disc = m + (rr * np.cos(ang))[:, None] * u + (rr * np.sin(ang))[:, None] * v
            side = (pts[4] - pts[5]) / np.linalg.norm(pts[4] - pts[5])
            blockers = [(pts[3], pts[4], r_arm), (pts[4], pts[5], r_arm),
                        (m, pts[5], self.pipe_radius),  # Auslassrohr über der Markierung
                        (pts[5] + 0.12 * side, pts[5] + 0.17 * side, 0.11)]  # Flansch J4
            hidden = np.zeros(len(disc), bool)
            for a, b, r in blockers:
                hidden |= _segment_distance(disc, sensor, a, b) < r - 0.002
            out.append(disc[~hidden])
        return np.vstack(out)

    def place_object(self, lo=None, hi=None):
        """Fremdkörper (Quader) in die Szene stellen; ohne Angabe zufällig neben den Tank."""
        if lo is None:
            ground = -self.geom.base_height
            c = self.truth["center"] if self.truth else np.array([3.0, 0.0, 0.0])
            side = self.rng.choice([-1.0, 1.0])
            w = self.rng.uniform(0.25, 0.6, 2)
            x = c[0] + side * self.rng.uniform(1.8, 2.6)
            y = c[1] + self.rng.uniform(-2.0, 2.0)
            top = ground + self.rng.uniform(1.5, 4.5)
            lo, hi = [x - w[0] / 2, y - w[1] / 2, ground], [x + w[0] / 2, y + w[1] / 2, top]
        self.objects.append((np.asarray(lo, float), np.asarray(hi, float)))

    def _object_points(self, spacing=0.02):
        out = []
        for lo, hi in self.objects:
            gx = np.arange(lo[0], hi[0], spacing)
            gy = np.arange(lo[1], hi[1], spacing)
            mx, my = np.meshgrid(gx, gy)
            out.append(np.column_stack([mx.ravel(), my.ravel(), np.full(mx.size, hi[2])]))
            zs = np.arange(lo[2], hi[2], spacing * 2)
            for xa in (lo[0], hi[0]):
                mz, mm = np.meshgrid(zs, gy)
                out.append(np.column_stack([np.full(mz.size, xa), mm.ravel(), mz.ravel()]))
            for ya in (lo[1], hi[1]):
                mz, mm = np.meshgrid(zs, gx)
                out.append(np.column_stack([mm.ravel(), np.full(mz.size, ya), mz.ravel()]))
        return np.vstack(out) if out else np.zeros((0, 3))

    def grab(self) -> np.ndarray:
        if self.tank is None:
            self._new_vehicle()
        parts = [] if self.empty else [self.tank]
        if self.objects:  # Fremdkörper: Armbasis -> Sensor
            obj = self._object_points()
            parts.append(obj @ self.inv[:3, :3].T + self.inv[:3, 3])
        if self.q_true is not None:
            arm = self._arm_points(self.q_true)
            arm_sensor = arm @ self.inv[:3, :3].T + self.inv[:3, 3]
            parts.append(arm_sensor + self.noise.normal(0, 0.003, arm_sensor.shape))
        return np.vstack(parts)
