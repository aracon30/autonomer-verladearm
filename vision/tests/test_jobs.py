"""Aufträge der SPS (InterfaceVersion 2) mit simuliertem Sensor und Getriebespiel."""

from pathlib import Path

import numpy as np
import pytest

from verladearm_vision.config import load_config
from verladearm_vision.detection import OutletConfig, detect_outlet
from verladearm_vision.kinematics import JOINTS, ArmGeometry, forward, tip
from verladearm_vision.plc import Request
from verladearm_vision.service.main import VisionService

BEISPIEL = Path(__file__).parents[1] / "config" / "anlagen" / "beispiel.yaml"


def make_service(seed=0, error=(0.3, -0.25, 0.2), marker=0.125):
    cfg = load_config(BEISPIEL)
    cfg["source"] = {"type": "sim", "seed": seed, "joint_error_deg": list(error),
                     "marker_radius": marker}
    cfg["outlet"] = {"marker_radius": marker}
    cfg["recording"] = {"enabled": False}  # keine Dateien im Arbeitsverzeichnis
    cfg["snapshot"] = {"path": None}
    return VisionService(cfg)


def model(s, servo):
    return np.array([s.geom.joints[k].to_model(v) for k, v in zip(JOINTS, servo, strict=True)])


def park(s):
    return tuple(s.geom.joints[k].park for k in JOINTS)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_messen_nachmessen_rueckfahrt(seed):
    s = make_service(seed)
    r1 = s(Request(job=1, actual_deg=park(s), axes_homed=True))
    assert r1.ok and 1 <= r1.approach_index < len(r1.waypoints) <= 16
    target = np.array(r1.target_mm) / 1000.0
    above = r1.waypoints[r1.approach_index - 1]
    err = s.source.joint_error

    before = np.hypot(*(tip(s.geom, model(s, above) + err) - target)[:2])
    r2 = s(Request(job=2, actual_deg=above, axes_homed=True))
    assert r2.ok and r2.approach_index == 1
    after = np.hypot(*(tip(s.geom, model(s, r2.waypoints[0]) + err) - target)[:2])
    inside = tip(s.geom, model(s, r2.waypoints[-1]) + err)
    assert before > 0.015  # simuliertes Getriebespiel ist messbar
    assert after < 0.005  # nach Korrektur < 5 mm
    assert np.hypot(*(inside - target)[:2]) < 0.008
    assert inside[2] < target[2] - 0.3  # eingetaucht

    r3 = s(Request(job=3, actual_deg=r2.waypoints[-1], axes_homed=True))
    assert r3.ok and r3.approach_index == 0
    assert np.allclose(r3.waypoints[-1], park(s), atol=0.01)


def test_fehlercodes():
    s = make_service()
    assert s(Request(job=1, actual_deg=park(s), axes_homed=False)).error_code == 32
    assert s(Request(job=1, actual_deg=(500, 0, 0), axes_homed=True)).error_code == 32
    assert s(Request(job=2, actual_deg=park(s), axes_homed=True)).error_code == 34
    assert s(Request(job=7, actual_deg=park(s), axes_homed=True)).error_code == 91


def test_fehlgeschlagene_planung_hinterlaesst_keinen_jobkontext(monkeypatch):
    s = make_service()
    monkeypatch.setattr(
        "verladearm_vision.service.main.plan_motion",
        lambda *args, **kwargs: {"ok": False, "code": 31, "reason": "kein Weg"},
    )

    result = s(Request(job=1, actual_deg=park(s), axes_homed=True))

    assert result.error_code == 31
    assert s.last is None
    assert s(Request(job=2, actual_deg=park(s), axes_homed=True)).error_code == 34


def test_auslass_ohne_scheibe_von_der_seite():
    geom = ArmGeometry()
    pts = forward(geom, np.radians([-45, -90, 10]))
    a, b = pts[5], pts[6]
    rng = np.random.default_rng(0)
    sensor = np.array([a[0] + 1.0, a[1], a[2] + 2.0])  # schräg von der Seite
    t = rng.uniform(0, 1, 4000)
    ang = rng.uniform(0, 2 * np.pi, 4000)
    axis = (b - a) / np.linalg.norm(b - a)
    u = np.cross(axis, [1.0, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    normal = np.outer(np.cos(ang), u) + np.outer(np.sin(ang), v)
    p = a + np.outer(t, b - a) + 0.06 * normal
    p = p[np.einsum("ij,ij->i", normal, sensor - p) > 0]
    dome = b - [0, 0, 0.3]
    found = detect_outlet(p, dome, sensor, OutletConfig(marker_radius=None))
    assert np.hypot(*(found - b)[:2]) < 0.005


def _path_collision(geom, servo_waypoints, start_servo, s):
    """Gelenkraum-Fahrt wie die SPS (alle Achsen synchron, linear) gegen `geom` prüfen."""
    from verladearm_vision.kinematics import first_collision, forward_many

    qs = [model(s, start_servo)] + [model(s, w) for w in servo_waypoints]
    for a, b in zip(qs[:-1], qs[1:], strict=True):
        t = np.linspace(0, 1, 60)[:, None]
        hit, name = first_collision(geom, forward_many(geom, a + t * (b - a)))
        if hit is not None:
            return name
    return None


@pytest.mark.parametrize("seed", [0, 1, 2, 3])
def test_rueckfahrt_ohne_jobkontext_misst_hindernisse_neu(seed):
    """Nach Handbetrieb/Neustart: Job 3 ohne Messung aus Job 1 nimmt Tank und Deckel neu auf."""
    s = make_service(seed)
    r1 = s(Request(job=1, actual_deg=park(s), axes_homed=True))
    r2 = s(Request(job=2, actual_deg=r1.waypoints[r1.approach_index - 1], axes_homed=True))
    assert r1.ok and r2.ok
    real = s.geom.with_obstacles(s.last["obstacles"])  # Tank, Kragen, Deckel aus Job 1
    inside = r2.waypoints[-1]
    s.last = None  # z. B. Dienst neu gestartet oder Arm von Hand in den Dom gefahren

    r3 = s(Request(job=3, actual_deg=inside, axes_homed=True))
    assert r3.ok, r3.message
    assert s._info["rueckfahrt_neu_gemessen"]["quader"] > 0
    assert np.allclose(r3.waypoints[-1], park(s), atol=0.01)
    assert _path_collision(real, r3.waypoints, inside, s) is None


def test_rueckfahrt_misst_neu_wenn_auslass_woanders_steht():
    s = make_service()
    r1 = s(Request(job=1, actual_deg=park(s), axes_homed=True))
    assert r1.ok
    s.last["target_mm"] = (s.last["target_mm"][0] + 1500.0, *s.last["target_mm"][1:])
    s(Request(job=3, actual_deg=r1.waypoints[r1.approach_index - 1], axes_homed=True))
    assert "neben dem gemessenen Dom" in s._info["rueckfahrt_neu_gemessen"]["grund"]


def test_rueckfahrt_ohne_kontext_und_ohne_kamera_wird_abgelehnt(monkeypatch):
    s = make_service()

    def no_camera():
        raise RuntimeError("Visionary-T Mini nicht verbunden")

    monkeypatch.setattr(s.source, "grab", no_camera)
    r = s(Request(job=3, actual_deg=park(s), axes_homed=True))
    assert not r.ok and r.error_code == 90 and "Handbetrieb" in r.message
