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
