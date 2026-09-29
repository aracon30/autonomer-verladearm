import numpy as np
import pytest

from verladearm_vision.calibration import SensorToArm
from verladearm_vision.detection import DetectionError, detect_opening
from verladearm_vision.detection.opening import ERR_MULTIPLE_OPENINGS, ERR_NO_OPENING
from verladearm_vision.synthetic import make_tank_roof


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
