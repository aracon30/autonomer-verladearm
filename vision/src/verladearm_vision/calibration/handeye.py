"""Hand-Auge-Kalibrierung (Sensor fest über der Station, "eye-to-hand").

Der Arm fährt die Markierungsscheibe am Auslass an mehrere Stellen im Arbeitsraum. Je Stellung:
- Lage des Auslassendes in Armbasis-Koordinaten aus den Servo-Istwinkeln (Vorwärtsrechnung)
- Lage derselben Stelle in Sensorkoordinaten aus der Punktwolke (Markierungsscheibe)
Aus den Punktpaaren folgt die starre Transformation Sensor -> Armbasis (Kabsch/SVD).

Die Scheibe wird mit Hilfe einer groben Anfangsschätzung (gemessene Montagelage) gesucht; nach dem
ersten Lösen wird mit der verbesserten Transformation erneut gesucht.
"""

from dataclasses import dataclass, field

import numpy as np

from verladearm_vision.detection import DetectionError, OutletConfig, detect_outlet
from verladearm_vision.kinematics import JOINTS, ArmGeometry, tip


def solve_rigid(p_sensor: np.ndarray, p_arm: np.ndarray) -> np.ndarray:
    """4x4-Matrix T mit p_arm ≈ R p_sensor + t (kleinste Quadrate, ohne Spiegelung)."""
    ps, pa = np.asarray(p_sensor, float), np.asarray(p_arm, float)
    cs, ca = ps.mean(axis=0), pa.mean(axis=0)
    u, _, vt = np.linalg.svd((ps - cs).T @ (pa - ca))
    d = np.sign(np.linalg.det(vt.T @ u.T))
    r = vt.T @ np.diag([1, 1, d]) @ u.T
    t = np.eye(4)
    t[:3, :3], t[:3, 3] = r, ca - r @ cs
    return t


def apply(t: np.ndarray, p: np.ndarray) -> np.ndarray:
    return np.asarray(p) @ t[:3, :3].T + t[:3, 3]


@dataclass
class Sample:
    servo_deg: tuple
    arm: np.ndarray  # Auslassende laut Kinematik [m, Armbasis]
    points: np.ndarray  # Punktwolke [m, Sensor]
    sensor: np.ndarray | None = None  # gemessenes Auslassende [m, Sensor]
    error: str = ""


@dataclass
class HandEyeCalibration:
    geom: ArmGeometry
    guess: np.ndarray  # grobe Transformation Sensor -> Armbasis (4x4)
    outlet_cfg: OutletConfig = field(default_factory=OutletConfig)
    samples: list = field(default_factory=list)

    def _measure(self, s: Sample, t: np.ndarray):
        arm_pts = apply(t, s.points)
        try:
            # Suchfenster: knapp unterhalb bis 1 m oberhalb des erwarteten Auslassendes
            found = detect_outlet(arm_pts, s.arm - [0, 0, 0.3], cfg=self.outlet_cfg)
        except DetectionError as e:
            s.sensor, s.error = None, str(e)
            return
        s.sensor, s.error = apply(np.linalg.inv(t), found), ""

    def add(self, points_sensor: np.ndarray, servo_deg) -> Sample:
        q = np.array([self.geom.joints[k].to_model(v) for k, v in zip(JOINTS, servo_deg,
                                                                        strict=True)])
        s = Sample(tuple(float(v) for v in servo_deg), tip(self.geom, q), np.asarray(points_sensor))
        self._measure(s, self.guess)
        self.samples.append(s)
        return s

    def solve(self, iterations: int = 3) -> dict:
        t = self.guess
        for _ in range(iterations):
            ok = [s for s in self.samples if s.sensor is not None]
            if len(ok) < 3:
                raise ValueError(f"Nur {len(ok)} gültige Stellungen, mindestens 3 (besser 8) nötig")
            t = solve_rigid([s.sensor for s in ok], [s.arm for s in ok])
            for s in self.samples:  # mit besserer Transformation neu suchen
                self._measure(s, t)
        ok = [s for s in self.samples if s.sensor is not None]
        t = solve_rigid([s.sensor for s in ok], [s.arm for s in ok])
        res = np.linalg.norm(apply(t, [s.sensor for s in ok]) - [s.arm for s in ok], axis=1)
        arm = np.array([s.arm for s in ok])
        spread = np.linalg.svd(arm - arm.mean(axis=0), compute_uv=False)
        warnings = []
        if len(ok) < 6:
            warnings.append("Weniger als 6 Stellungen: Ergebnis wenig abgesichert")
        if spread[1] < 0.3:
            warnings.append("Stellungen liegen fast auf einer Linie: im Arbeitsraum verteilen")
        if np.ptp(arm[:, 2]) < 0.3:
            warnings.append("Höhen kaum verschieden: Stellungen in mindestens 2 Höhen anfahren")
        if res.max() > 0.01:
            warnings.append("Restfehler über 10 mm: Maße, Nullstellungen oder Pendeln prüfen")
        return {"matrix": t, "residuals_m": res, "used": len(ok), "total": len(self.samples),
                "warnings": warnings}


def suggest_poses(geom: ArmGeometry, lo, hi, heights=2) -> list:
    """Stellungen (Servo-Grad) an den Ecken und in der Mitte des Arbeitsraums, in mehreren Höhen."""
    from verladearm_vision.kinematics import collision, forward, inverse

    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    poses = []
    for z in np.linspace(lo[2] + 0.3, hi[2] + 0.3, heights):
        for x, y in [(lo[0], lo[1]), (lo[0], hi[1]), (hi[0], lo[1]), (hi[0], hi[1]),
                     ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)]:
            res = inverse(geom, [x, y, z])
            if res.ok and not collision(geom, forward(geom, res.q)):
                poses.append(tuple(geom.to_servo(res.q)))
    return poses
