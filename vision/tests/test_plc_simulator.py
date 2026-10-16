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
    """Arm steht eingetaucht im Dom; Nachzieh-Tabelle senkrecht über dem Eintauchpunkt."""
    from verladearm_vision.kinematics import plan_motion

    cfg = load_config(ROOT / "vision" / "config" / "anlagen" / "simulation.yaml")
    geom = ArmGeometry(**cfg["arm"])
    var = {n: FakeNode() for n in sim_mod.VARIABLES}
    rim = -1.6
    plan = plan_motion(geom, [3100, 0, rim * 1000], [0, 0, 1], insertion_depth=1.1)
    assert plan["ok"]
    wps = [geom.to_servo(np.array(q)) for q in plan["q_insert"]]
    sim = sim_mod.PlcSim(None, var, geom, 25.0, 0.0, time_scale=0.0,
                         fill={**cfg["filling"], **fill})
    sim.light_barrier = True
    sim.rim_z = rim
    sim.actual = np.array(wps[-1], float)
    sim.set_table(wps)
    return sim


def test_befuellen_mit_nachziehen_bis_sollmenge(capsys):
    sim = make_filling_sim()
    z0 = sim.tip_z()
    run(sim.fill_tank(interactive=False))
    out = capsys.readouterr().out
    assert "Sollmenge" in out and "Nachziehen um" in out and not sim.valve_open
    f = sim.fill
    spiegel = sim.rim_z - f["depth_below_rim"] + f["start_level"] + sim.volume / f["chamber_area"]
    eingetaucht = spiegel - sim.tip_z()
    assert sim.tip_z() > z0 + 0.3  # Arm wurde nachgezogen
    assert f["immersion"][0] - 0.02 <= eingetaucht <= f["immersion"][1]  # knapp unter Spiegel


def test_ueberfuellsicherung_bei_ausgefallenem_durchflusssensor():
    sim = make_filling_sim()
    sim.flow_ok = False
    with pytest.raises(sim_mod.Abort, match="Überfüllsicherung"):
        run(sim.fill_tank(interactive=False))
    assert not sim.valve_open
    f = sim.fill
    spiegel = sim.rim_z - f["depth_below_rim"] + f["start_level"] + sim.volume / f["chamber_area"]
    assert spiegel >= sim.rim_z - f["overfill_below_rim"]
