"""Ersteinrichtung: Anlagendatei im Dialog anlegen."""

import numpy as np

from verladearm_vision.config import load_config
from verladearm_vision.einrichtung import Dialog, run
from verladearm_vision.kinematics import ArmGeometry, validate


def scripted(answers):
    """Antworten der Reihe nach, sobald der Fragetext passt; sonst Enter (Vorschlag)."""
    todo, asked, printed = list(answers), [], []

    def ask(prompt):
        asked.append(prompt)
        if todo and todo[0][0] in prompt:
            return todo.pop(0)[1]
        return ""

    return Dialog(ask, printed.append), todo, asked, printed


def test_neue_anlage_aus_vorlage(tmp_path):
    d, todo, asked, printed = scripted([
        ("Anlage / Station", "Lich Station 3"),
        ("Innerer Ausleger", "abc"),  # ungültig -> erneute Frage
        ("Innerer Ausleger", "25"),  # unplausibel
        ("Innerer Ausleger", "2,35"),
        ("Äußerer Ausleger", "2,6"),
        ("Weiteres Hindernis", "j"),
        ("Bezeichnung", "Mast"),
        ("Form", "z"),
        ("Mitte x y", "1,5 -2"),
        ("Weiteres Hindernis", "n"),
        ("Weiteres Produkt", "j"),
        ("ProductId", "7"),
        ("Bezeichnung", "Harz"),
        ("Eintauchtiefe", "0,9"),
    ])
    target = tmp_path / "lich_station3.yaml"
    assert run(d, target) == target
    assert not todo, f"nicht gestellt: {todo}"
    assert any("unplausibel" in p for p in printed)

    cfg = load_config(target)  # extends zeigt auf default.yaml
    arm = cfg["arm"]
    assert arm["inner_length"] == 2.35 and arm["outer_length"] == 2.6
    assert arm["joints"]["q1"]["park"] == 70  # Vorschlag aus der Vorlage übernommen
    assert cfg["products"][7] == {"name": "Harz", "insertion_depth": 0.9}
    assert "detection" in cfg and cfg["plc"]["namespace_uri"]  # Rest aus default.yaml
    geom = ArmGeometry(**arm)
    assert not validate(geom)
    assert [o.name for o in geom.obstacles][-1] == "Mast"
    assert geom.obstacles[-1].radius == 0.15
    assert "Lich Station 3" in target.read_text(encoding="utf-8")


def test_servowerte_aus_der_sps(tmp_path):
    # Nullstellung, dann je Achse vorher/nachher (J1 dreht negativ), dann Parkstellung
    readings = iter([(10.0, -5.0, 2.0),
                     (10.0, -5.0, 2.0), (4.0, -5.0, 2.0),
                     (4.0, -5.0, 2.0), (4.0, 3.0, 2.0),
                     (4.0, 3.0, 2.0), (4.0, 3.0, 9.0),
                     (60.0, -140.0, 12.0)])
    d, _, asked, _ = scripted([])
    target = tmp_path / "a.yaml"
    run(d, target, reader=lambda plc: next(readings))
    j = load_config(target)["arm"]["joints"]
    assert (j["q1"]["zero"], j["q2"]["zero"], j["q3"]["zero"]) == (10.0, -5.0, 2.0)
    assert (j["q1"]["direction"], j["q2"]["direction"], j["q3"]["direction"]) == (-1, 1, 1)
    assert (j["q1"]["park"], j["q2"]["park"], j["q3"]["park"]) == (60.0, -140.0, 12.0)
    assert not any("Drehrichtung: +1" in a for a in asked)  # nicht mehr gefragt


def test_vorhandene_anlage_bearbeiten(tmp_path):
    target = tmp_path / "a.yaml"
    run(scripted([("Höhe Oberkante Schnittstellenflansch", "6,6"),
                  ("Höhendifferenz", "0,4")])[0], target)
    d, _, asked, _ = scripted([])
    run(d, target)  # alles mit Enter: Werte bleiben
    cfg = load_config(target)
    assert cfg["arm"]["base_height"] == 6.2  # 6,6 − 0,4: Rohrmitte innerer Ausleger auf J1
    assert cfg["arm"]["flange_height"] == 6.6 and cfg["arm"]["flange_offset"] == 0.4
    assert len(cfg["arm"]["obstacles"]) == 2
    assert np.allclose(cfg["calibration"]["matrix"][0], [1, 0, 0, 3.0])


def test_nicht_speichern(tmp_path):
    d, *_ = scripted([("Anlagendatei schreiben", "n")])
    assert run(d, tmp_path / "a.yaml") is None
    assert not (tmp_path / "a.yaml").exists()


def test_referenz_und_weitere_abschnitte_bleiben_erhalten(tmp_path):
    target = tmp_path / "a.yaml"
    run(scripted([("Außendurchmesser Markierungsscheibe", "0,22"),
                  ("Oberkante Referenz", "0,823")])[0], target)
    # von Hand ergänzter Abschnitt, den der Dialog nicht kennt
    text = target.read_text(encoding="utf-8")
    target.write_text(text + "\ndrives:\n  q3: {ratio: 1457.6, speed_limit: 6}\n", encoding="utf-8")
    run(scripted([])[0], target)  # erneut, alles mit Enter
    cfg = load_config(target)
    assert cfg["outlet"] == {"marker_radius": 0.11, "marker_offset": 0.823}
    assert cfg["drives"]["q3"] == {"ratio": 1457.6, "speed_limit": 6}
