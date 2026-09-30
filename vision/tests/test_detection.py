import numpy as np
import pytest

from verladearm_vision.calibration import SensorToArm
from verladearm_vision.detection import DetectionError, detect_opening
from verladearm_vision.detection.opening import ERR_MULTIPLE_OPENINGS, ERR_NO_OPENING
from verladearm_vision.synthetic import make_tank_roof, make_tank_vehicle


@pytest.mark.parametrize("cx, cy, h", [(0.0, 0.0, 3.5), (0.3, -0.2, 3.0), (-0.35, 0.25, 4.0)])
def test_findet_oeffnung(cx, cy, h):
    op = detect_opening(make_tank_roof(center_xy=(cx, cy), height=h))
    assert np.hypot(op.center[0] - cx, op.center[1] - cy) < 0.01  # < 10 mm
    assert abs(op.center[2] - h) < 0.01
    assert abs(op.diameter - 0.5) < 0.03
    assert op.normal[2] < -0.99  # zeigt zum Sensor (nach oben)
    assert op.confidence > 0.8


def test_geneigte_flaeche():
    op = detect_opening(make_tank_roof(center_xy=(0.1, 0.1), tilt_deg=5))
    assert np.hypot(op.center[0] - 0.1, op.center[1] - 0.1) < 0.015


def test_keine_oeffnung():
    with pytest.raises(DetectionError) as e:
        detect_opening(make_tank_roof(openings=0))
    assert e.value.code == ERR_NO_OPENING


def test_mehrere_oeffnungen():
    with pytest.raises(DetectionError) as e:
        detect_opening(make_tank_roof(center_xy=(0.4, 0.0), size=2.4, openings=2))
    assert e.value.code == ERR_MULTIPLE_OPENINGS


def test_kalibrierung():
    T = np.eye(4)
    T[:3, 3] = [1.0, 2.0, 3.0]
    t = SensorToArm(T)
    assert np.allclose(t.point(np.zeros(3)), [1, 2, 3])
    assert np.allclose(t.direction(np.array([0, 0, 2.0])), [0, 0, 1])


@pytest.mark.parametrize("kind, radius", [("lkw", 1.1), ("kesselwagen", 1.5)])
@pytest.mark.parametrize("cx, cy, h", [(0.0, 0.0, 3.6), (0.35, -0.3, 2.8)])
def test_runder_tank_mit_domkragen(kind, radius, cx, cy, h):
    op = detect_opening(make_tank_vehicle(kind, center_xy=(cx, cy), height=h))
    assert np.hypot(op.center[0] - cx, op.center[1] - cy) < 0.01
    assert abs(op.center[2] - h) < 0.01  # Oberkante Domkragen
    assert abs(op.diameter - 0.5) < 0.03
    assert op.normal[2] < -0.99
    assert op.tank_radius == pytest.approx(radius, rel=0.05)
    assert abs(op.tank_axis[1]) > 0.99  # Tankachse entlang Sensor-y


@pytest.mark.parametrize("kind", ["lkw", "kesselwagen"])
def test_runder_tank_deckel_geschlossen(kind):
    with pytest.raises(DetectionError) as e:
        detect_opening(make_tank_vehicle(kind, lid_closed=True))
    assert e.value.code == ERR_NO_OPENING


def test_runder_tank_zwei_dome():
    with pytest.raises(DetectionError) as e:
        detect_opening(make_tank_vehicle("lkw", center_xy=(0.0, 0.8), openings=2))
    assert e.value.code == ERR_MULTIPLE_OPENINGS


def test_ebenes_dach_ohne_tankradius():
    assert detect_opening(make_tank_roof()).tank_radius is None


def _disc(center, axis, r_out, r_in=0.06, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    u = np.cross(axis, [1.0, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    ang = rng.uniform(0, 2 * np.pi, n)
    rr = np.sqrt(rng.uniform(r_in ** 2, r_out ** 2, n))
    return center + (rr * np.cos(ang))[:, None] * u + (rr * np.sin(ang))[:, None] * v


def test_flansch_weit_oben_mit_schraeger_rohrachse():
    from verladearm_vision.detection import OutletConfig, detect_outlet

    cfg = OutletConfig(marker_radius=0.11, marker_offset=0.823)
    dome = np.array([3.0, 0.0, -2.0])
    tip = dome + [0.01, -0.02, 0.3]
    axis = np.array([np.sin(np.radians(2.5)), 0.0, np.cos(np.radians(2.5))])  # 2,5° schräg
    pts = _disc(tip + 0.823 * axis, axis, 0.11)
    found = detect_outlet(pts, dome, cfg=cfg, axis=axis)
    assert np.linalg.norm(found - tip) < 0.004
    vertical = detect_outlet(pts, dome, cfg=cfg)  # senkrecht angenommen: ca. 36 mm daneben
    assert np.hypot(*(vertical - tip)[:2]) > 0.03


def test_flansch_stark_verdeckt_rohrachse_hilft():
    """Nur ein kurzes Stück Flanschrand sichtbar, das Rohr darüber aber schon."""
    from verladearm_vision.detection import OutletConfig, detect_marker

    cfg = OutletConfig(marker_radius=0.11, marker_offset=0.823, pipe_radius=0.057)
    rng = np.random.default_rng(3)
    m = np.array([2.9, 0.2, -1.0])
    disc = _disc(m, [0, 0, 1], 0.11, r_in=0.057, n=3000, seed=4)
    ang = np.degrees(np.arctan2(*(disc[:, :2] - m[:2]).T[::-1]))
    disc = disc[(ang > 150) | (ang < -160)]  # nur ca. 50° des Flansches sichtbar
    h = rng.uniform(0.03, 0.5, 800)
    a = rng.uniform(-np.pi / 2, np.pi / 2, 800)  # dem Sensor zugewandte Rohrhälfte
    pipe = np.column_stack([m[0] + 0.057 * np.cos(a), m[1] + 0.057 * np.sin(a), m[2] + h])
    pts = np.vstack([disc, pipe]) + rng.normal(0, 0.002, (len(disc) + len(pipe), 3))
    found = detect_marker(pts, m - [0, 0, 1.1], cfg, expected=m + [0.025, -0.02, 0.0])
    assert np.hypot(*(found - m)[:2]) < 0.004
