import numpy as np
import pytest

from verladearm_vision.kinematics import ArmGeometry, forward, inverse, plan_motion, tip


def test_grundstellung():
    g = ArmGeometry()
    p = forward(g, [0, 0, 0])
    inc = np.radians(g.incline_deg)
    assert np.allclose(p[1], [g.inner_length * np.cos(inc), 0, -g.inner_length * np.sin(inc)])
    assert p[3][1] == pytest.approx(-g.offset_right)  # Winkel nach rechts
    assert p[5][1] == pytest.approx(0, abs=1e-9)  # nach links zurück auf die Mittellinie
    assert np.allclose(p[6] - p[5], [0, 0, -g.outlet_length])  # Auslass hängt senkrecht


@pytest.mark.parametrize("q3", np.radians([-30, -10, 10, 30]))
def test_auslass_bleibt_senkrecht_beim_heben(q3):
    g = ArmGeometry()
    p = forward(g, [0.3, -1.2, q3])
    d = (p[6] - p[5]) / g.outlet_length
    assert d[2] < -0.998  # max. ~3,6° Abweichung durch das Gefälle
    assert np.linalg.norm(d) == pytest.approx(1)


def test_j3_hebt_den_ausleger():
    g = ArmGeometry()
    assert tip(g, [0, 0, np.radians(20)])[2] > tip(g, [0, 0, 0])[2] + 0.5


def test_rueckwaertsrechnung_trifft_erreichbare_ziele():
    g = ArmGeometry()
    lo, hi = g.bounds
    rng = np.random.default_rng(1)
    for _ in range(20):
        q = rng.uniform(lo * 0.8, hi * 0.8)
        target = tip(g, q)
        res = inverse(g, target)
        assert res.ok, (np.degrees(q), res.error)
        assert np.linalg.norm(tip(g, res.q) - target) < 0.001
        assert np.all(res.q >= lo - 1e-9) and np.all(res.q <= hi + 1e-9)


def test_ausser_reichweite():
    assert not inverse(ArmGeometry(), [8.0, 0.0, -1.0]).ok


def test_bahnplanung():
    g = ArmGeometry()
    plan = plan_motion(g, [3100.0, -200.0, -1500.0], [0, 0, 1])
    assert plan["ok"]
    assert np.allclose(plan["move"][0], forward(g, g.park), atol=1e-3)
    end = np.array(plan["insert"][-1][-1])
    assert np.allclose(end, [3.1, -0.2, -1.5 - g.insertion_depth], atol=0.002)
    # Eintauchen senkrecht: Auslassende bleibt über der Öffnung
    xy = np.array([s[-1][:2] for s in plan["insert"]])
    assert np.abs(xy - [3.1, -0.2]).max() < 0.002
