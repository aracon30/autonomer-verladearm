"""Simulierter Sensor für Tests ohne Hardware (source.type: sim).

Erzeugt zu jeder Verladung (Job 1) einen neuen Tankwagen (Lkw oder Kesselwagen) an zufälliger
Stelle und rendert zusätzlich Auslegerende und Auslass in der tatsächlichen Stellung des Arms.
`joint_error_deg` simuliert den Unterschied zwischen gemeldetem Servowinkel und realer Gelenklage
(Getriebespiel, Durchbiegung), damit das Nachmessen in Job 2 etwas zu korrigieren hat.
Am Auslass sitzt eine Markierungsscheibe (siehe detection/outlet.py); `marker_radius: null`
simuliert einen Auslass ohne Scheibe. Verdeckungen werden nicht simuliert.
"""

import numpy as np

from verladearm_vision.calibration import SensorToArm
from verladearm_vision.kinematics import JOINTS, ArmGeometry, forward
from verladearm_vision.synthetic import make_tank_vehicle

# Höhe Oberkante Domkragen über Fahrbahn [m]
RIM_HEIGHT = {"lkw": (3.35, 3.6), "kesselwagen": (4.35, 4.55)}


class SimulatedScene:
    def __init__(self, geom: ArmGeometry, transform: SensorToArm, vehicles=("lkw", "kesselwagen"),
                 joint_error_deg=(0.0, 0.0, 0.0), dome_spread=0.35, marker_radius=0.125,
                 marker_offset=0.15, seed=None):
        self.geom, self.transform = geom, transform
        self.vehicles = list(vehicles)
        self.joint_error = np.radians(np.asarray(joint_error_deg, dtype=float))
        self.dome_spread = dome_spread
        self.marker_radius, self.marker_offset = marker_radius, marker_offset
        self.rng = np.random.default_rng(seed)
        self.inv = np.linalg.inv(transform.T)
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
            self.q_true = q + self.joint_error

    def _new_vehicle(self):
        kind = self.vehicles[self.count % len(self.vehicles)]
        self.count += 1
        sensor_z = self.transform.point(np.zeros(3))[2]  # Armbasis, z oben
        rim_z = -self.geom.base_height + self.rng.uniform(*RIM_HEIGHT[kind])
        dx, dy = self.rng.uniform(-self.dome_spread, self.dome_spread, 2)
        self.tank = make_tank_vehicle(kind, center_xy=(dx, dy), height=sensor_z - rim_z,
                                      seed=int(self.rng.integers(1 << 30)))
        self.kind = kind

    def _arm_points(self, q, spacing=0.012, radius=(0.075, 0.075, 0.06)):
        pts = forward(self.geom, q)
        sensor = self.transform.point(np.zeros(3))
        out = []
        for (a, b), r in zip(((pts[3], pts[4]), (pts[4], pts[5]), (pts[5], pts[6])), radius,
                             strict=True):
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
            ang = self.rng.uniform(0, 2 * np.pi, 1500)
            rr = np.sqrt(self.rng.uniform(radius[2] ** 2, self.marker_radius ** 2, 1500))
            z = pts[6][2] + self.marker_offset
            out.append(np.column_stack([pts[6][0] + rr * np.cos(ang), pts[6][1] + rr * np.sin(ang),
                                        np.full(1500, z)]))
        return np.vstack(out)

    def grab(self) -> np.ndarray:
        if self.tank is None:
            self._new_vehicle()
        parts = [self.tank]
        if self.q_true is not None:
            arm = self._arm_points(self.q_true)
            arm_sensor = arm @ self.inv[:3, :3].T + self.inv[:3, 3]
            parts.append(arm_sensor + self.rng.normal(0, 0.003, arm_sensor.shape))
        return np.vstack(parts)
