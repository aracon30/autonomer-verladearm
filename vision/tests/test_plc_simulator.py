"""SPS-Simulator im Bedienmodus: Startbedingungen und Verriegelungen (Vorlage für die SPS)."""

import asyncio
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from verladearm_vision.config import load_config
from verladearm_vision.kinematics import ArmGeometry

ROOT = Path(__file__).parents[2]
spec = importlib.util.spec_from_file_location("plc_simulator", ROOT / "tools" / "plc_simulator.py")
sim_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim_mod)


class FakeNode:
    def __init__(self, value=0):
        self.value = value

    async def write_value(self, v):
        self.value = v.Value

    async def read_value(self):
        return self.value


def make_sim():
    cfg = load_config(ROOT / "vision" / "config" / "anlagen" / "beispiel.yaml")
    var = {n: FakeNode() for n in sim_mod.VARIABLES}
    var["Ready"].value = True
    return sim_mod.PlcSim(None, var, ArmGeometry(**cfg["arm"]), 25.0, 0.0, time_scale=0.0)


def run(coro):
    return asyncio.run(coro)


def test_start_nur_mit_allen_freigaben(capsys):
    sim = make_sim()

    async def scenario():
        missing = await sim.start_checks()
        assert "Lichtschranke belegt (Fahrzeug)" in missing
        assert "Produkt gewählt (p <nr>)" in missing
        await sim.command("n")  # Fahrzeug, Treppe aus und zurück
        await sim.command("p 1")
        await sim.command("f")
        assert await sim.start_checks() == []
        sim.var["Ready"].value = False
        assert await sim.start_checks() == ["Vision-Dienst bereit (Ready)"]

    run(scenario())


def test_handbetrieb_und_verriegelungen(capsys):
    sim = make_sim()

    async def scenario():
        await sim.command("j 1 +5")
        assert "Nur im Handbetrieb" in capsys.readouterr().out
        await sim.command("h")
        await sim.command("b 3 5")
        assert "Bremse lüften gesperrt" in capsys.readouterr().out
        await sim.command("b 1 +4")  # Bremse lüften, von Hand schieben
        await sim.task
        assert sim.actual[0] == pytest.approx(sim.park[0] + 4)
        await sim.command("t")  # Arm nicht in Park: Treppe verriegelt
        assert "verriegelt" in capsys.readouterr().out and sim.stairs_home
        await sim.command("j 1 -4")
        await sim.task
        await sim.command("t")
        assert not sim.stairs_home  # in Parkstellung darf die Treppe ausfahren

    run(scenario())


def test_bewegung_stoppt_bei_verriegelung():
    sim = make_sim()
    sim.light_barrier = True

    async def scenario():
        target = sim.park + np.array([20.0, 0.0, 0.0])
        sim.light_barrier = False  # Fahrzeug weg
        with pytest.raises(sim_mod.Abort, match="Lichtschranke"):
            await sim.move_to(target)
        await sim.move_to(target, auto="park")  # Rückfahrt darf ohne Fahrzeug
        sim.stop = True
        with pytest.raises(sim_mod.Abort, match="Stopp"):
            await sim.move_to(sim.park, auto=False)

    run(scenario())


def make_filling_sim(**fill):
    """Arm steht im Dom eines Lkw, Auslass ca. 20 cm über dem Tankboden; Nachzieh-Tabelle
    senkrecht über dem Eintauchpunkt."""
    from verladearm_vision.kinematics import plan_motion

    cfg = load_config(ROOT / "vision" / "config" / "anlagen" / "simulation.yaml")
    geom = ArmGeometry(**cfg["arm"])
    var = {n: FakeNode() for n in sim_mod.VARIABLES}
    rim = 3.6 - geom.base_height  # Domrand 3,6 m über Fahrbahn
    depth = cfg["products"]["default"]["insertion_depth"]
    plan = plan_motion(geom, [3000, 0, rim * 1000], [0, 0, 1], insertion_depth=depth)
    assert plan["ok"], plan["reason"]
    wps = [geom.to_servo(np.array(q)) for q in plan["q_insert"]]
    sim = sim_mod.PlcSim(None, var, geom, 25.0, 0.0, time_scale=0.0,
                         fill={**cfg["filling"], **fill})
    sim.light_barrier = True
    sim.rim_z = rim
    sim.actual = np.array(wps[-1], float)
    sim.set_table(wps)
    return sim


def _spiegel(sim, chambers=1):
    f = sim.fill
    length = f["chamber_length"] * chambers
    v0 = sim.chamber_volume(f["start_level"], length)
    return sim.rim_z - f["depth_below_rim"] + sim.level_for(v0 + sim.volume, length)


def test_kammervolumen_liegender_zylinder():
    sim = make_filling_sim()
    full = sim.chamber_volume(2.2, 2.5)
    assert full == pytest.approx(np.pi * 1.1**2 * 2.5)
    assert sim.chamber_volume(1.1, 2.5) == pytest.approx(full / 2)
    assert sim.level_for(full / 2, 2.5) == pytest.approx(1.1, abs=1e-6)


def test_befuellen_mit_einem_grenzschalter_bis_ende_leitstelle(capsys):
    sim = make_filling_sim()
    bottom = sim.rim_z - sim.fill["depth_below_rim"]
    assert sim.tip_z() - bottom == pytest.approx(0.22, abs=0.03)  # ca. 20 cm über dem Boden
    run(sim.fill_tank(interactive=False))
    out = capsys.readouterr().out
    assert "Leitstelle: Menge erreicht" in out and sim.end_reason == "Leitstelle"
    assert not sim.valve_open and not sim.pump_on
    assert 25 <= sim.lifts <= 45  # Hub 5 cm über ca. 1,7 m Füllhöhe
    hs, step = sim.fill["sensor_height"], sim.fill["lift_step"]
    eingetaucht = _spiegel(sim) - sim.tip_z()
    assert hs - step - 0.01 <= eingetaucht <= hs + 0.005  # Auslass ca. 7–12 cm unter dem Spiegel
    assert _spiegel(sim) < sim.rim_z - sim.fill["max_below_rim"]  # Ebene 2 nicht nötig


def test_maximalhoehe_wenn_leitstelle_nicht_beendet(capsys):
    sim = make_filling_sim()
    sim.plant_ok = False
    run(sim.fill_tank(interactive=False))  # keine Störung: Ebene 2 beendet die Füllung
    out = capsys.readouterr().out
    assert "Maximalhöhe erreicht" in out and "Befüllung stoppen" in out
    assert out.index("Pumpe ab") < out.index("Absperrklappe ZU")  # erst Pumpe aus, dann Klappe
    assert not sim.valve_open and not sim.pump_on
    assert _spiegel(sim) < sim.rim_z - sim.fill["overfill_below_rim"]  # Ebene 3 spricht nicht an


def test_grenzschalter_bleibt_nass_ist_stoerung(capsys):
    sim = make_filling_sim()
    sim.sensor_stuck = True
    with pytest.raises(sim_mod.Abort, match="weiter nass"):
        run(sim.fill_tank(interactive=False))
    out = capsys.readouterr().out
    assert sim.lifts == 1 and not sim.valve_open and not sim.pump_on
    assert out.index("Pumpe ab") < out.index("Absperrklappe ZU")


def test_ueberfuellsicherung_als_letzte_ebene():
    sim = make_filling_sim(max_below_rim=0.1)  # Maximalhöhe falsch eingestellt
    sim.plant_ok = False
    with pytest.raises(sim_mod.Abort, match="Überfüllsicherung.*Pumpe aus"):
        run(sim.fill_tank(interactive=False))
    assert not sim.valve_open and not sim.pump_on
