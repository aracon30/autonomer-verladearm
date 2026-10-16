"""Antriebsmodell: Geschwindigkeit, Fahrzeit, synchrones Fahren, Getriebespiel."""

from pathlib import Path

import numpy as np
import pytest

from verladearm_vision.config import load_config
from verladearm_vision.drives import Backlash, Drive, Drives
from verladearm_vision.service.main import build_source

ANLAGEN = Path(__file__).parents[1] / "config" / "anlagen"


def test_hoechstgeschwindigkeit_aus_motor_und_uebersetzung():
    j3 = Drive(motor_speed=1440, ratio=42.87 * 34)
    assert j3.speed_max == pytest.approx(1440 / 1457.58 * 6, rel=1e-4)  # knapp 6 °/s
    assert Drive(motor_speed=2000, ratio=94.44, speed_limit=6).speed_max == 6


def test_fahrzeit_trapez_und_dreieck():
    d = Drive(speed_limit=6, accel_time=2)  # a = 3 °/s²
    assert d.move_time(90) == pytest.approx(90 / 6 + 2)  # Rampen kosten je halbe Rampenzeit
    assert d.move_time(3) == pytest.approx(2 * np.sqrt(3 / 3))  # v max nicht erreicht
    assert d.move_time(0) == 0
    assert d.move_time(90, 0.3) > d.move_time(90)


def test_langsamste_achse_bestimmt_synchrone_fahrzeit():
    drives = Drives.from_config({"q1": {"speed_limit": 6, "accel_time": 4},
                                 "q2": {"speed_limit": 6, "accel_time": 2},
                                 "q3": {"speed_limit": 3, "accel_time": 1}})
    t = drives.sync_time([0, 0, 0], [60, 120, 30])
    assert t == pytest.approx(max(60 / 6 + 4, 120 / 6 + 2, 30 / 3 + 1))


def test_getriebespiel_richtung_und_hubachse():
    bl = Backlash([0.2, 0.2, 0.2], [False, False, True], servo_direction=[1, -1, 1])
    bl([0, 0, 0])
    off = bl([10, 10, 5])  # J1 im Modell positiv, J2 negativ (direction −1)
    assert off == pytest.approx([-0.1, 0.1, -0.1])  # bleibt zurück; J3 hängt immer tiefer
    off = bl([5, 12, 1])
    assert off == pytest.approx([0.1, 0.1, -0.1])
    assert bl([5, 12, 1]) == pytest.approx(off)  # Stillstand: Richtung bleibt


def test_heta_prototyp_antriebe_in_simulation():
    cfg = load_config(ANLAGEN / "simulation.yaml")
    drives = Drives.from_config(cfg["drives"])
    assert drives.configured
    assert drives.axes["q3"].gravity_preload and drives.axes["q3"].brake
    assert all(d.speed_max <= 6.0 for d in drives.axes.values())  # IMO: max. 1 1/min
    src = build_source(cfg["source"], cfg)
    assert src.backlash.half == pytest.approx(drives.backlash() / 2)


def test_synchronfahrt_wie_positioning_drive():
    """Vorgaben proportional zum Weg, Grenzen je Achse eingehalten, gleiches Profil."""
    drives = Drives.from_config({"q1": {"speed_limit": 6, "accel_time": 4, "jerk_time": 0.3},
                                 "q2": {"speed_limit": 6, "accel_time": 2, "jerk_time": 0.3},
                                 "q3": {"speed_limit": 6, "accel_time": 1.5, "jerk_time": 0.3}})
    start, target = np.array([0.0, 0.0, 0.0]), np.array([60.0, -30.0, 10.0])
    m = drives.sync(start, target)
    d = np.abs(target - start)
    assert m.speed / d == pytest.approx(np.full(3, m.speed[0] / d[0]))  # proportional
    assert m.accel / d == pytest.approx(np.full(3, m.accel[0] / d[0]))
    for k, v, a in zip(("q1", "q2", "q3"), m.speed, m.accel, strict=True):
        assert v <= drives.axes[k].speed_max + 1e-9 and a <= drives.axes[k].accel + 1e-9
    assert m.duration == pytest.approx(60 / 6 + 4 + 0.3)  # J1 bestimmt, Ruckzeit kommt dazu
    assert m.fraction(0) == 0 and m.fraction(m.duration) == pytest.approx(1)
    u = [m.fraction(t) for t in np.linspace(0, m.duration, 50)]
    assert np.all(np.diff(u) >= -1e-12)  # stetig vorwärts
    assert m.fraction(m.duration / 2) == pytest.approx(0.5, abs=0.01)  # symmetrisch


def test_synchronfahrt_kurzer_weg_dreieck():
    drives = Drives.from_config({k: {"speed_limit": 6, "accel_time": 2} for k in ("q1", "q2",
                                                                                 "q3")})
    m = drives.sync([0, 0, 0], [3, 1, 0])  # v max wird nicht erreicht
    assert m.duration == pytest.approx(2 * np.sqrt(3 / 3))
    assert m.speed[0] < 6
