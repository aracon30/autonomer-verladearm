"""Hindernisse aus der Messung (Tank, Domkragen, offener Deckel) und kollisionsfreie Bahnen."""

import time
from pathlib import Path

import numpy as np
import pytest

from verladearm_vision.calibration import SensorToArm
from verladearm_vision.config import load_config
from verladearm_vision.detection import OutletConfig, detect_opening
from verladearm_vision.kinematics import (
    JOINTS,
    ArmGeometry,
    CylinderObstacle,
    Obstacle,
    OrientedBoxObstacle,
    collision,
    forward,
    plan_retract,
    tip,
)
from verladearm_vision.plc import Request
from verladearm_vision.scene import build_obstacles
from verladearm_vision.service.main import VisionService
from verladearm_vision.synthetic import make_tank_vehicle

BEISPIEL = Path(__file__).parents[1] / "config" / "anlagen" / "beispiel.yaml"


def test_quader_mit_durchgang():
    box = Obstacle("Tank", [-1, -1, -3], [1, 1, 0], passage=(0.2, 0.0, 0.1), clearance=0.05)
    pts = np.array([[0.5, 0.5, -1], [0.2, 0.0, -1], [0.2, 0.0, 0.03], [1.04, 0, -1], [2, 0, -1]])
    assert box.contains(pts, 0.0).tolist() == [True, False, False, True, False]


def test_gedrehter_quader():
    a = np.radians(45)
    box = OrientedBoxObstacle("Deckel", [0, 0, 0], [[np.cos(a), np.sin(a), 0],
                                                    [-np.sin(a), np.cos(a), 0], [0, 0, 1]],
                              [0.5, 0.05, 0.3], clearance=0.0)
    pts = np.array([[0.3, 0.3, 0], [0.3, -0.3, 0], [0.0, 0.0, 0.35]])
    assert box.contains(pts, 0.0).tolist() == [True, False, False]


def test_zylinder_mit_durchgang():
    tank = CylinderObstacle("Tank", [0, 0, 0], [0, 1, 0], 1.0, 5.0, passage=(0, 0, 0.2),
                            clearance=0.1)
    pts = np.array([[0.5, 0, 0.5], [0, 0, 1.05], [0, 0, 0.9], [0, 5.05, 0], [0, 6, 0],
                    [0.8, 0, 0.8]])
    assert tank.contains(pts, 0.0).tolist() == [True, False, False, True, False, False]


def _scene(kind, az_sensor, seed):
    cfg = load_config(BEISPIEL)
    t = SensorToArm(np.asarray(cfg["calibration"]["matrix"], float))
    pts = make_tank_vehicle(kind, center_xy=(0.1, -0.2), height=3.2 if kind == "lkw" else 2.3,
                            lid_azimuth_deg=az_sensor, seed=seed)
    return t, pts


@pytest.mark.parametrize("kind", ["lkw", "kesselwagen"])
@pytest.mark.parametrize("az", [-150, -60, 20, 110])
def test_deckel_erkannt(kind, az):
    t, pts = _scene(kind, az, seed=abs(az))
    op = detect_opening(pts)
    obstacles, info = build_obstacles(op, t, pts, OutletConfig())
    assert [o.name for o in obstacles] == ["Tankkörper", "Domkragen", "Domdeckel"]
    d = t.direction(np.array([np.cos(np.radians(az)), np.sin(np.radians(az)), 0.0]))
    expected = np.degrees(np.arctan2(d[1], d[0]))
    diff = (info["deckel"]["azimuth_deg"] - expected + 180) % 360 - 180
    assert abs(diff) < 5
    assert 0.3 < info["deckel"]["height_m"] < 0.8
    # Durchgang durch die Öffnung bleibt frei, Tank daneben nicht
    center = t.point(op.center)
    tank, collar = obstacles[0], obstacles[1]
    probe = np.array([center - [0, 0, 0.3], center + [0.4, 0, -0.3]])
    assert tank.contains(probe, 0.0).tolist() == [False, True]
    assert not collar.contains(probe[:1], 0.0).any()


def test_ohne_deckel_kein_deckelhindernis():
    t, pts = _scene("lkw", None, seed=3)
    obstacles, info = build_obstacles(detect_opening(pts), t, pts, OutletConfig())
    assert "deckel" not in info
    assert "Domdeckel" not in [o.name for o in obstacles]


def _servo_path(s, waypoints, q_from):
    """Gelenklineare Fahrt wie in der SPS; Eckpunkte fein abgetastet."""
    q_prev = np.asarray(q_from, float)
    for w in waypoints:
        q = np.array([s.geom.joints[k].to_model(v) for k, v in zip(JOINTS, w, strict=True)])
        for u in np.linspace(0, 1, 30):
            yield forward(s.geom, q_prev + (q - q_prev) * u)
        q_prev = q


@pytest.mark.parametrize("seed", [0, 3, 5])
def test_bahnen_stossen_nicht_an(seed):
    cfg = load_config(BEISPIEL)
    cfg["source"] = {"type": "sim", "seed": seed, "joint_error_deg": [0.3, -0.25, 0.2]}
    cfg["recording"] = {"enabled": False}
    cfg["snapshot"] = {"path": None}
    s = VisionService(cfg)
    park = tuple(s.geom.joints[k].park for k in JOINTS)
    done = 0
    for _ in range(4):  # abwechselnd Lkw und Kesselwagen, Deckel in zufälliger Richtung
        r1 = s(Request(job=1, actual_deg=park, axes_homed=True))
        if not r1.ok:  # nur ehrliche Absagen: Deckel oder Tank im Weg
            assert r1.error_code == 31
            continue
        names = [o.name for o in s.last["obstacles"]]
        assert "Domdeckel" in names and "Tankkörper" in names
        scene = s._scene_geom()
        q_park = np.array(s.geom.park)
        for pts in _servo_path(s, r1.waypoints, q_park):
            assert collision(scene, pts) is None
        r3 = s(Request(job=3, actual_deg=r1.waypoints[-1], axes_homed=True))
        assert r3.ok
        q_in = np.array([s.geom.joints[k].to_model(v)
                         for k, v in zip(JOINTS, r1.waypoints[-1], strict=True)])
        for pts in _servo_path(s, r3.waypoints, q_in):
            assert collision(scene, pts) is None
        done += 1
    assert done >= 3


def test_rueckfahrt_rueckwaerts_als_ausweg(monkeypatch):
    """Findet die Planung keinen neuen Weg, fährt der Arm die geprüfte Anfahrt rückwärts."""
    import verladearm_vision.kinematics as k

    g = ArmGeometry()
    pre = k.inverse(g, [2.6, -0.2, -0.3])
    assert pre.ok
    q_in, _, err = k._line(g, pre.q, tip(g, pre.q), tip(g, pre.q) - [0, 0, 0.8], 8, "Eintauchen")
    assert not err
    approach = [g.park.tolist(), (g.park + [0, 0, 0.3]).tolist(), pre.q.tolist()]
    monkeypatch.setattr(k, "_retract_new", lambda *a: dict(a[-2], reason="kein Weg", code=31))
    plan = plan_retract(g, q_in[-1], lift=1.0, fallback=approach)
    assert plan["ok"] and plan["reversed"]
    assert np.allclose(tip(g, plan["q_lift"][-1]), tip(g, pre.q), atol=0.003)  # senkrecht hoch
    assert np.allclose(plan["move_vias"][-1], g.park)
    assert not plan_retract(g, q_in[-1], lift=1.0)["ok"]  # ohne Anfahrweg kein Ausweg


def test_hindernisformen_aus_anlagendatei():
    g = ArmGeometry(obstacles=[
        {"name": "Geländer", "min": [0, 0, 0], "max": [1, 1, 1]},
        {"name": "Rundstütze", "form": "zylinder", "p0": [0, 0, 0], "axis": [0, 0, 1],
         "radius": 0.15, "half_length": 3.0},
        {"name": "Leiter", "form": "quader_gedreht", "center": [0, 0, 0],
         "axes": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "half": [0.3, 0.05, 1.0]},
    ])
    assert [type(o) for o in g.obstacles] == [Obstacle, CylinderObstacle, OrientedBoxObstacle]
    with pytest.raises(ValueError, match="unbekannte Form"):
        ArmGeometry(obstacles=[{"name": "X", "form": "kugel"}])


def test_suche_im_gelenkraum_umfaehrt_hindernis():
    import verladearm_vision.kinematics as k

    g = ArmGeometry()
    q0, goal = g.park, g.park + np.array([-1.2, 0.3, 0.0])
    mid = forward(g, (q0 + goal) / 2)[-1]  # Auslassende auf halber direkter Strecke
    geom = g.with_obstacles([Obstacle("Block", mid - 0.3, mid + 0.3)])
    assert k._joint_move(geom, q0, goal, 20, "direkt")[2]  # direkt kollidiert
    unreachable = goal + np.array([0.0, 0.0, 5.0])  # außerhalb der Achsgrenzen
    found = k._search(geom, q0, [unreachable, goal], time.monotonic() + 10, "Test")
    assert found is not None
    idx, frames, _, pts = found
    assert idx == 1 and np.allclose(frames[-1], goal) and len(frames) <= 8
    assert all(collision(geom, p) is None for p in pts)
