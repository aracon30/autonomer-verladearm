import io
from pathlib import Path

from verladearm_vision.commissioning import check
from verladearm_vision.config import load_config

BEISPIEL = Path(__file__).parents[1] / "config" / "anlagen" / "beispiel.yaml"


def test_anlagendatei_erbt_von_default(tmp_path):
    (tmp_path / "base.yaml").write_text(
        "arm:\n  inner_length: 2.2\n  joints:\n    q1: {min: -120, max: 120, park: 70}\n"
        "plc:\n  url: opc.tcp://sim\n", encoding="utf-8")
    (tmp_path / "anlage.yaml").write_text(
        "extends: base.yaml\narm:\n  joints:\n    q1: {park: 0}\n", encoding="utf-8")
    cfg = load_config(tmp_path / "anlage.yaml")
    assert cfg["arm"]["inner_length"] == 2.2
    assert cfg["arm"]["joints"]["q1"] == {"min": -120, "max": 120, "park": 0}
    assert cfg["plc"]["url"] == "opc.tcp://sim"
    assert "extends" not in cfg


def test_beispielanlage_besteht_pruefung():
    cfg = load_config(BEISPIEL)
    cfg["commissioning"]["step"] = 0.5  # grob, damit der Test schnell bleibt
    out = io.StringIO()
    assert check(cfg, "beispiel", out), out.getvalue()
    assert "Stütze Überdachung" in out.getvalue()


def test_pruefung_meldet_falsche_parameter():
    cfg = load_config(BEISPIEL)
    cfg["arm"]["joints"]["q3"]["park"] = 90
    out = io.StringIO()
    assert not check(cfg, "beispiel", out)
    assert "q3: Parkstellung" in out.getvalue()
