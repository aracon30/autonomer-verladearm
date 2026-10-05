import numpy as np
import pytest

from verladearm_vision.kinematics import (
    ArmGeometry,
    forward,
    inverse,
    plan_motion,
    product_insertion_depth,
    tip,
    validate,
)


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
    assert d[2] == pytest.approx(-1.0)  # Fallrohr senkrecht: Auslass hängt senkrecht
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


def test_servo_nullstellung_und_drehrichtung():
    g = ArmGeometry(joints={
        "q1": {"min": 60, "max": 300, "park": 250, "zero": 180, "direction": -1},
        "q2": {"min": -170, "max": 170, "park": -150},
        "q3": {"min": -35, "max": 35, "park": 10},
    })
    # Servo 250° bei Null 180° und umgekehrter Richtung = Modell -70°
    assert np.degrees(g.park[0]) == pytest.approx(-70)
    lo, hi = g.bounds
    assert np.degrees([lo[0], hi[0]]) == pytest.approx([-120, 120])
    assert g.to_servo(g.park)[0] == pytest.approx(250)


def test_hindernis_blockiert_bahn():
    free = ArmGeometry()
    target = [3100.0, -200.0, -1500.0]
    assert plan_motion(free, target, [0, 0, 1])["ok"]
    # Quader genau über dem Anfahrweg des äußeren Auslegers
    blocked = ArmGeometry(obstacles=[{"name": "Stütze", "min": [2.9, -0.4, -1.3],
                                      "max": [3.3, 0.0, -0.9]}])
    plan = plan_motion(blocked, target, [0, 0, 1])
    assert not plan["ok"] and "Stütze" in plan["reason"]


def test_parameterpruefung():
    assert validate(ArmGeometry()) == []
    bad = ArmGeometry(outer_length=0, joints={
        "q1": {"min": 10, "max": -10, "park": 0},
        "q2": {"min": -170, "max": 170, "park": 180},
        "q3": {"min": -35, "max": 35, "park": 0, "direction": 2},
    })
    problems = " | ".join(validate(bad))
    for text in ("outer_length", "q1: min", "q2: Parkstellung", "q3: direction"):
        assert text in problems


def test_eintauchtiefe_je_produkt():
    products = {"default": {"insertion_depth": 0.4}, 2: {"insertion_depth": 0.7}}
    assert product_insertion_depth(products, 2, 0.3) == 0.7
    assert product_insertion_depth(products, 5, 0.3) == 0.4
    assert product_insertion_depth(None, 5, 0.3) == 0.3


def test_korrektur_gleicht_modellfehler_aus():
    from verladearm_vision.kinematics import plan_correction

    g = ArmGeometry()
    target = np.array([3.1, -0.2, -1.5])
    q = inverse(g, target + [0, 0, g.approach_height]).q
    true_error = np.radians([0.3, -0.2, 0.0])
    measured = tip(g, q + true_error)  # reale Lage weicht vom Modell ab
    plan = plan_correction(g, q, measured, target * 1000, [0, 0, 1], 0.4)
    assert plan["ok"]
    corrected = tip(g, np.array(plan["q_insert"][0]) + true_error)
    assert np.hypot(*(corrected - target)[:2]) < 0.002


def test_rueckfahrt_aus_dem_dom():
    from verladearm_vision.kinematics import plan_retract

    g = ArmGeometry()
    q = inverse(g, [3.1, -0.2, -1.9]).q
    plan = plan_retract(g, q, lift=0.7)
    assert plan["ok"]
    lifted = tip(g, np.array(plan["q_lift"][-1]))
    assert np.allclose(lifted, tip(g, q) + [0, 0, 0.7], atol=0.002)
    assert np.allclose(plan["q_move"][-1], g.park)


def test_geneigtes_fallrohr_kippt_den_auslass():
    from verladearm_vision.kinematics import outlet_axis

    g = ArmGeometry(drop_tilt_deg=3.0)
    tilt = np.degrees(np.arccos(outlet_axis(g, [0.3, 1.2, 0.2])[2]))
    assert 0.5 < tilt < 3.5
    assert outlet_axis(ArmGeometry(), [0.3, 1.2, 0.2]) == pytest.approx([0, 0, 1])


def test_arbeitsraumraster_bleibt_in_den_grenzen():
    from verladearm_vision.commissioning import workspace_grid

    cfg = {"commissioning": {"workspace_min": [2.6, -0.6, -2.3],
                             "workspace_max": [3.6, 0.6, -0.5], "step": 0.5}}
    g = workspace_grid(cfg)
    assert g[:, 2].max() == pytest.approx(-0.5) and g[:, 2].min() == pytest.approx(-2.3)
    assert np.all(g <= np.array([3.6, 0.6, -0.5]) + 1e-9)


def test_hindernis_mit_vertauschten_ecken_wirkt_trotzdem():
    """Vertauschte min/max (z. B. z-Werte) dürfen das Hindernis nicht unsichtbar machen."""
    from verladearm_vision.kinematics import ArmGeometry, collision

    line = np.array([[3.0, 0.0, -2.0], [3.0, 0.0, 2.0]])
    for o in ({"name": "Box", "min": [2, -1, 1], "max": [4, 1, -1]},
              {"name": "Box", "min": [4, 1, 1], "max": [2, -1, -1]},
              {"name": "Rohr", "form": "zylinder", "p0": [3, 0, 0], "axis": [0, 0, 1],
               "radius": -0.3, "half_length": -1.0}):
        assert collision(ArmGeometry(obstacles=[o]), line) is not None


def test_fallleitung_eigener_abstand_unabhaengig_von_clearance():
    from verladearm_vision.config import load_config
    from verladearm_vision.kinematics import FEED_NAME, validate

    arm = load_config("vision/config/anlagen/heta_prototyp.yaml")["arm"]
    g = ArmGeometry(**dict(arm, clearance=0.5))  # großer Mindestabstand darf J1 nicht sperren
    assert validate(g) == []
    feed = next(o for o in g.obstacles if o.name == FEED_NAME)
    pts = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, g.flange_offset - 0.01],  # Arm unter dem Flansch
                    [0.15, 0.0, 0.8], [0.0, 0.0, g.flange_offset + 1.0]])  # an der Fallleitung
    assert feed.contains(pts, g.clearance).tolist() == [False, False, True, True]


def test_selbstkollision_aeusserer_gegen_inneren_ausleger():
    from verladearm_vision.config import load_config
    from verladearm_vision.kinematics import SELF_NAME, collision, first_collision, forward_many

    g = ArmGeometry(**load_config("vision/config/anlagen/heta_prototyp.yaml")["arm"])
    gefaltet = np.radians([-80, -170, 0])  # Parkstellung: neben dem inneren Ausleger, frei
    ueber_kreuz = np.radians([-80, -180, 30])  # J3 angehoben: trifft den inneren Ausleger
    assert collision(g, forward(g, gefaltet)) is None
    assert collision(g, forward(g, ueber_kreuz)) == SELF_NAME
    qs = gefaltet + np.linspace(0, 1, 20)[:, None] * (ueber_kreuz - gefaltet)
    i, name = first_collision(g, forward_many(g, qs))
    assert name == SELF_NAME and 0 < i < 19
