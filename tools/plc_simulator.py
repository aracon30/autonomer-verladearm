"""Simuliert die SPS-Seite (OPC-UA-Server mit DB_Vision, InterfaceVersion 3).

Ablauf je Verladung wie im echten SPS-Programm vorgesehen (docs/schnittstelle.md):
Job 1 (messen, planen) -> Fahrt bis über den Dom -> Job 2 (nachmessen, korrigieren) ->
Eintauchen -> Befüllen mit Nachziehen -> Job 3 (Rückfahrt planen) -> Park.
Mehrere Dome: Der Auftrag ist eine Liste von Füllschritten (DomeNo, Menge). Tank mit
Schwallwänden = ein Schritt mit DomeNo 0 (automatisch); Mehrkammer = je Kammer ein Schritt
(DomeNo 1, 2, … von vorn), dazwischen senkrecht heraus und Job 1 vom vorigen Dom aus.
Im Dauertest wechseln beide Bauarten ab; die Zahl der Kammern nimmt der Simulator aus
DomeCount (an der Anlage kommt sie aus dem Auftrag der Leitstelle).
Achsen fahren synchron; die Istwinkel gehen an den PC zurück.
Mit Abschnitt `drives` in der Anlagendatei fährt jede Achse wie mit SEW MOVIKIT Positioning
Drive: Die SPS gibt je Stützpunkt Zielposition, Geschwindigkeit und Beschleunigung im Verhältnis
zum Weg vor (gleiche Ruckzeit), die langsamste Achse bestimmt die Fahrzeit (`--prozessdaten`
zeigt die Vorgaben je Achse).

Befüllen (Abschnitt `filling`, docs/fuellstand_ueberfuellsicherung.md): Absperrklappe auf, der
Durchflusssensor zählt die Menge, der Spiegel steigt. Der Messstab an der Lanze meldet, wie tief
der Auslass eingetaucht ist; ab der oberen Grenze zieht die SPS den Arm senkrecht nach (entlang
der Eintauch-Stützpunkte aus Job 2). Sollmenge erreicht -> Klappe zu, Abtropfen, Rückfahrt.
Die Überfüllsicherung an der aufliegenden Lanze (feste Länge unter dem Domrand) schließt die
Klappe unabhängig davon (Test: Befehl `u`, Durchflusssensor fällt aus).

Zwei Betriebsarten des Simulators:
- Dauertest (Standard): Verladung auf Verladung ohne Bediener.
- `--bedienen`: Bedienung wie an der echten Anlage über Befehle im Terminal – Fahrzeug,
  Klapptreppe, Lichtschranke, Produktwahl, Start, „Beladung beendet“, Stopp, Handbetrieb
  (Tippen, Bremse lüften und von Hand schieben), „Automatisch in Parkstellung“. Befehl `?`
  zeigt die Hilfe. Vorlage für das SPS-Programm (Verriegelungen, Schrittfolge).

Terminal 1:  python tools/plc_simulator.py --config vision/config/anlagen/beispiel.yaml [--bedienen]
Terminal 2:  python -m verladearm_vision.service.main --config <Anlage mit source: sim>
"""

import argparse
import asyncio
import logging
import sys

import numpy as np
from asyncua import Server, ua

from verladearm_vision.config import load_config
from verladearm_vision.drives import Drives, profile
from verladearm_vision.kinematics import JOINTS, ArmGeometry, pick, plan_motion, tip
from verladearm_vision.plc import VARIABLES

NS_URI = "http://www.siemens.com/simatic-s7-opcua"
STATUS_NODE = '"Simulator"."Bedienstatus"'  # nur im Simulator: Anzeige im Live-Viewer
JOG_FACTOR = 0.2  # Tippen im Handbetrieb mit reduzierter Geschwindigkeit
HAND_SPEED = 2.0  # °/s, Arm von Hand geschoben (Bremse gelüftet)
FILL_STEP = 2.0  # s Befüllzeit je Rechenschritt
# Befüllung, falls die Anlagendatei keinen Abschnitt `filling` hat (Werte siehe simulation.yaml)
FILL_DEFAULTS = dict(flow=60.0, chamber_area=5.0, depth_below_rim=2.3, start_level=0.05,
                     target_volume=8.5, immersion=(0.02, 0.05), overfill_below_rim=0.40,
                     speedup=10.0)

HELP = """Befehle (Eingabe + Enter):
  n              neues Fahrzeug: fährt vor, Klapptreppe aus, Dom öffnen, Treppe zurück
  l              Lichtschranke umschalten (Fahrzeug da / weg)
  t              Klapptreppe umschalten (ausgefahren / Ruhelage)
  p <nr>         Produkt wählen (Eintauchtiefe), z. B. p 1
  k <dom> ...    Kammern des Auftrags: k 0 = Tank mit Schwallwänden (ein Dom, automatisch),
                 k 1 2 3 = Mehrkammer, Dome von vorn nacheinander (Menge je Kammer gleich)
  f              „Fahrzeug bereit“ bestätigen
  s              Start „Automatisch beladen“
  e              Beladung vorzeitig beenden (Klappe zu) -> Arm fährt in die Parkstellung
  u              Durchflusssensor fällt aus (Test Überfüllsicherung)
  x              Stopp (Bewegung anhalten)
  h              Betriebsart Hand / Automatik umschalten
  j <achse> <°>  Hand: Achse tippen, z. B. j 3 +5
  b <achse> <°>  Hand: Bremse lüften und von Hand schieben (nur J1/J2), z. B. b 2 -20
  d              Hand-Demo: Arm wie von Hand in den Dom führen (für z testen)
  z              „Automatisch in Parkstellung“ (Job 3, aus jeder Lage)
  ?              Hilfe und Zustand      q  beenden"""


class Abort(Exception):
    """Bewegung durch Stopp oder Verriegelung abgebrochen."""


def default_value(vtype, length):
    v = False if vtype == ua.VariantType.Boolean else 0.0 if vtype == ua.VariantType.Float else 0
    return [v] * length if length else v


class PlcSim:
    def __init__(self, server, var, geom: ArmGeometry, speed: float, interval: float,
                 drives: Drives | None = None, time_scale: float = 1.0, fill: dict | None = None,
                 show_pd: bool = False):
        self.server, self.var, self.geom = server, var, geom
        self.speed, self.interval = speed, interval
        self.drives = drives if drives and drives.configured else None
        self.time_scale = time_scale  # < 1: schneller als Echtzeit (nur Anzeige)
        self.moved = 0.0  # Fahrzeit der laufenden Verladung [s, Echtzeit der Antriebe]
        self.show_pd = show_pd  # Vorgaben an die Umrichter je Fahrt ausgeben
        self.fill = {**FILL_DEFAULTS, **(fill or {})}
        self.flow_ok = True  # Durchflusssensor in Ordnung
        self.valve_open = False  # Absperrklappe
        self.volume = 0.0  # Menge laut Durchflusssensor [m³]
        self.rim_z = None  # Domrand aus Job 1 [m, Armbasis]
        self.table = None  # Eintauch-Stützpunkte aus Job 2 (Servo-Grad) und Höhe des Auslasses
        self.park = np.array([geom.joints[k].park for k in JOINTS], dtype=float)
        self.actual = self.park.copy()
        self.product = 0
        self.domes = [0]  # Auftrag: DomeNo je Füllschritt (0 = automatisch, ein Schritt)
        self.dome_no = 0
        self.multi_test = False  # Dauertest: abwechselnd Schwallwände / Mehrkammer
        # Bedienung und Verriegelungen (im Dauertest immer erfüllt)
        self.mode = "Automatik"
        self.vehicle_ready = False
        self.product_chosen = False
        self.stairs_home = True  # Klapptreppe in Ruhelage (Endschalter)
        self.light_barrier = False  # Lichtschranke Stellplatz belegt
        self.stop = False
        self.phase = "bereit"
        self.task = None  # laufender Automatikablauf
        self.loading_done = asyncio.Event()
        self.status_node = None
        self.last_status = ""

    async def write(self, name, value):
        vtype, _, length = VARIABLES[name]
        await self.var[name].write_value(ua.Variant(value, vtype))

    async def read(self, name):
        return await self.var[name].read_value()

    async def heartbeat(self):
        n = 0
        while True:
            n = (n + 1) % 32767
            await self.write("HeartbeatPLC", n)
            await asyncio.sleep(0.1)

    async def publish_actual(self):
        for k, v in zip(("ActualJ1", "ActualJ2", "ActualJ3"), self.actual, strict=True):
            await self.write(k, float(v))

    def in_park(self) -> bool:
        return bool(np.abs(self.actual - self.park).max() < 0.5)

    def interlock(self, auto=True) -> str | None:
        """Verriegelungen während einer Bewegung; Text = Grund für den Halt.

        auto=True: Automatik (Stopp, Lichtschranke, Klapptreppe) · "park": Rückfahrt in die
        Parkstellung (Stopp, Klapptreppe; Fahrzeug darf schon weg sein) · False: Handbetrieb."""
        if self.stop:
            return "Stopp gedrückt"
        if auto is True and not self.light_barrier:
            return "Lichtschranke frei – Fahrzeug weg?"
        if auto and not self.stairs_home:
            return "Klapptreppe nicht in Ruhelage"
        return None

    async def move_to(self, target, slow=False, factor=None, auto=True, hand_speed=None):
        """Synchron: alle Achsen starten und enden gemeinsam, weiches Anfahren und Bremsen."""
        target = np.asarray(target, dtype=float)
        lo = [self.geom.joints[k].min for k in JOINTS]
        hi = [self.geom.joints[k].max for k in JOINTS]
        target = np.clip(target, lo, hi)  # Software-Endlagen
        start = self.actual.copy()
        factor = factor or (0.3 if slow else 1.0)  # Eintauchen und Herausfahren langsam
        motion = None
        if hand_speed:
            duration = max(np.abs(target - start).max() / hand_speed, 0.2)
        elif self.drives:  # wie Positioning Drive: alle Achsen kommen gleichzeitig an
            motion = self.drives.sync(start, target, factor)
            duration = max(motion.duration, 0.2)
            if self.show_pd:
                self.print_pd(motion)
        else:
            duration = max(np.abs(target - start).max() / (self.speed * factor) * 1.5, 0.2)
        self.moved += duration
        shown = duration * self.time_scale
        steps = max(int(shown / 0.05), 1)
        for i in range(1, steps + 1):
            if reason := self.interlock(auto):
                await self.publish_actual()
                raise Abort(reason)
            u = motion.fraction(duration * i / steps) if motion else profile(i / steps)
            self.actual = start + (target - start) * u
            await self.publish_actual()
            await asyncio.sleep(shown / steps)
        return duration

    def print_pd(self, motion):
        """Vorgaben an die Umrichter (MOVIKIT Positioning Drive, PA 2–4 und 7/8)."""
        parts = []
        for k, label, t, v, a in zip(JOINTS, ("J1", "J2", "J3"), motion.target, motion.speed,
                                     motion.accel, strict=True):
            n = v * self.drives.axes[k].ratio / 6.0  # Motordrehzahl [1/min]
            parts.append(f"{label} Ziel {t:7.2f}° v {v:5.2f} °/s ({n:5.0f} 1/min) a {a:5.2f} °/s²")
        print(f"  PD {motion.duration:5.1f} s, Ruck {motion.jerk_time * 1000:.0f} ms | "
              + " | ".join(parts))

    # --- Befüllen ------------------------------------------------------------------------------
    def tip_z(self) -> float:
        """Höhe des Auslassendes [m] aus den Istwinkeln (Vorwärtsrechnung)."""
        q = [self.geom.joints[k].to_model(v) for k, v in zip(JOINTS, self.actual, strict=True)]
        return float(tip(self.geom, np.array(q))[2])

    def set_table(self, wps):
        """Nachzieh-Tabelle: Eintauch-Stützpunkte aus Job 2 mit Höhe des Auslassendes."""
        z = []
        for wp in wps:
            q = [self.geom.joints[k].to_model(v) for k, v in zip(JOINTS, wp, strict=True)]
            z.append(float(tip(self.geom, np.array(q))[2]))
        order = np.argsort(z)
        self.table = (np.asarray(wps, float)[order], np.asarray(z)[order])

    def table_at(self, z: float):
        """Servowinkel, mit denen der Auslass senkrecht über dem Eintauchpunkt auf Höhe z steht
        (zwischen den Stützpunkten linear im Gelenkraum); None über dem Anfahrpunkt."""
        wps, heights = self.table
        if z > heights[-1] + 1e-3:
            return None
        return np.array([np.interp(z, heights, wps[:, j]) for j in range(3)])

    async def fill_tank(self, interactive: bool, target_volume: float | None = None):
        """Befüllen mit Nachziehen; Ende über Sollmenge, Überfüllsicherung unabhängig davon."""
        f = dict(self.fill)
        if target_volume is not None:
            f["target_volume"] = target_volume
        rim = self.rim_z
        base = rim - f["depth_below_rim"] + f["start_level"]  # Spiegel zu Beginn
        lo, hi = f["immersion"]
        switch = rim - f["overfill_below_rim"]  # Schaltpunkt der Überfüllsicherung
        self.volume, self.valve_open = 0.0, True
        print("  Absperrklappe AUF")

        def level():
            return base + self.volume / f["chamber_area"]

        try:
            while True:
                if self.stop:
                    raise Abort("Stopp gedrückt")
                if interactive and self.loading_done.is_set():
                    print("  Beladung von Hand beendet")
                    break
                self.volume += f["flow"] / 3600 * FILL_STEP
                spiegel = level()
                immersion = max(spiegel - self.tip_z(), 0.0)  # Messstab: benetzte Länge
                if spiegel >= switch:
                    raise Abort(f"Überfüllsicherung ausgelöst ({rim - spiegel:.2f} m unter "
                                "Domrand) – Klappe zu")
                if self.flow_ok and self.volume >= f["target_volume"]:
                    print(f"  Sollmenge {f['target_volume']:g} m³ erreicht")
                    break
                if immersion > hi:  # nachziehen, Auslass bleibt knapp unter dem Spiegel
                    target = self.table_at(spiegel - lo)
                    if target is None:
                        raise Abort("Nachziehen am Anfahrpunkt angekommen – Klappe zu")
                    z0 = self.tip_z()
                    t = await self.move_to(target, slow=True)
                    self.volume += f["flow"] / 3600 * t  # Klappe bleibt beim Nachziehen auf
                    print(f"  Nachziehen um {(self.tip_z() - z0) * 1000:.0f} mm "
                          f"(Spiegel {rim - level():.2f} m unter Domrand)")
                self.phase = (f"Beladung läuft: {self.volume:.1f} / {f['target_volume']:g} m³, "
                              f"Spiegel {rim - spiegel:.2f} m unter Domrand, Auslass "
                              f"{immersion * 1000:.0f} mm eingetaucht"
                              + ("" if self.flow_ok else " – DURCHFLUSSSENSOR AUSGEFALLEN"))
                await asyncio.sleep(FILL_STEP * self.time_scale / f["speedup"])
        finally:
            self.valve_open = False
            print(f"  Absperrklappe ZU ({self.volume:.2f} m³)")

    async def job(self, job: int):
        """Auftrag an den Vision-PC, Handshake nach docs/schnittstelle.md."""
        await self.write("Job", job)
        await self.write("ProductId", self.product)
        await self.write("DomeNo", self.dome_no)
        await self.write("Trigger", True)
        for _ in range(100):  # 5 s Zeitüberwachung
            if await self.read("Done"):
                break
            await asyncio.sleep(0.05)
        else:
            await self.write("Trigger", False)
            return None, "Zeitüberschreitung, kein Ergebnis"
        out = {n: await self.read(n) for n in ("Error", "ErrorCode", "WaypointCount",
                                               "WaypointsJ1", "WaypointsJ2", "WaypointsJ3",
                                               "ApproachIndex", "CorrectionX", "CorrectionY",
                                               "TargetX", "TargetY", "TargetZ",
                                               "NormalX", "NormalY", "NormalZ",
                                               "DomeCount", "DomeSelected")}
        await self.write("Trigger", False)
        while await self.read("Done"):
            await asyncio.sleep(0.05)
        if out["Error"]:
            return None, f"Fehler {out['ErrorCode']}"
        n = out["WaypointCount"]
        wps = np.column_stack([out["WaypointsJ1"][:n], out["WaypointsJ2"][:n],
                               out["WaypointsJ3"][:n]])
        lo = [self.geom.joints[k].min for k in JOINTS]
        hi = [self.geom.joints[k].max for k in JOINTS]
        if n and (np.any(wps < lo) or np.any(wps > hi)):  # Plausibilitätsprüfung der SPS
            return None, "Stützpunkt außerhalb der Achsgrenzen"
        return (wps, out), None

    # --- Anzeige ---------------------------------------------------------------------------
    def status(self) -> str:
        light = "grün" if self.in_park() and not self.busy() else "rot"
        prod = f"Produkt {self.product}" if self.product_chosen else "kein Produkt"
        return (f"{self.mode} | {prod} | Fahrzeug {'bereit' if self.vehicle_ready else '-'} | "
                f"Treppe {'Ruhelage' if self.stairs_home else 'AUSGEFAHREN'} | "
                f"Lichtschranke {'belegt' if self.light_barrier else 'frei'} | Ampel {light} | "
                f"{self.phase}")

    async def show(self):
        text = self.status()
        if text != self.last_status:
            self.last_status = text
            if self.status_node is not None:
                await self.status_node.write_value(ua.Variant(text, ua.VariantType.String))

    def set_phase(self, text):
        self.phase = text
        print(f"> {text}")

    def busy(self) -> bool:
        return self.task is not None and not self.task.done()

    async def fault(self, text):
        await self.write("ArmState", 9)
        self.set_phase(f"Störung: {text} – Hand (h) oder Parkstellung (z)")

    # --- Automatik ---------------------------------------------------------------------------
    async def sequence(self, interactive: bool):
        """Automatisch beladen: je Füllschritt Job 1 -> über Dom -> Job 2 -> eintauchen ->
        Beladung -> (nächste Kammer: senkrecht heraus) ... -> Job 3 -> Park."""
        self.moved = 0.0
        steps = list(self.domes)  # DomeNo je Füllschritt; None = alle offenen (Dauertest)
        try:
            await self.write("ArmState", 0)
            k = 0
            while k < len(steps):
                self.dome_no = steps[k] or 0
                label = f"Kammer {k + 1}/{len(steps)}: " if len(steps) > 1 else ""
                self.set_phase(f"Job 1: {label}Dom {self.dome_no or 'automatisch'} messen, "
                               "Bahn planen")
                res, err = await self.job(1)
                if err:
                    return await self.fault(f"Job 1: {err}")
                wps, out = res
                if steps[k] is None:  # Dauertest Mehrkammer: alle offenen Dome von vorn
                    steps = list(range(1, out["DomeCount"] + 1))
                    self.dome_no = steps[0]
                    res, err = await self.job(1)
                    if err:
                        return await self.fault(f"Job 1: {err}")
                    wps, out = res
                a = out["ApproachIndex"]
                self.rim_z = out["TargetZ"] / 1000.0
                print(f"  Dom {out['DomeSelected']} von {out['DomeCount']} offenen bei "
                      f"{out['TargetX']:.0f} / {out['TargetY']:.0f} / {out['TargetZ']:.0f} mm, "
                      f"{len(wps)} Stützpunkte, über Dom = Nr. {a}")
                await self.write("ArmState", 1)
                self.set_phase(f"{label}fährt über den Dom")
                for wp in wps[:a]:
                    await self.move_to(wp)
                await self.write("ArmState", 2)
                await asyncio.sleep(0.5)  # Beruhigungszeit (Auslass pendelt frei)

                self.set_phase(f"{label}Job 2: Auslass nachmessen")
                res, err = await self.job(2)
                if err:
                    print(f"  Job 2: {err} -> Abbruch, Rückfahrt")
                    break
                wps, out = res
                print(f"  Korrektur {out['CorrectionX']:+.1f} / {out['CorrectionY']:+.1f} mm")
                self.set_phase(f"{label}taucht ein")
                await self.move_to(wps[0])
                for wp in wps[1:]:
                    await self.move_to(wp, slow=True)
                self.set_table(wps)
                await self.write("ArmState", 3)
                self.loading_done.clear()
                self.set_phase(f"{label}Beladung läuft"
                               + (" – vorzeitig beenden: e" if interactive else ""))
                await self.fill_tank(interactive, self.fill["target_volume"] / len(steps))
                self.set_phase(f"{label}Abtropfen")
                await asyncio.sleep(2.0 * self.time_scale)
                k += 1
                if k < len(steps):  # nächste Kammer: senkrecht heraus bis über den Dom
                    self.set_phase(f"{label}fährt senkrecht heraus, weiter zur nächsten Kammer")
                    await self.move_to(self.table[0][-1], slow=True)
                    await self.write("ArmState", 2)
            await self.park_auto()
        except Abort as e:
            await self.fault(str(e))

    async def park_auto(self):
        """Job 3: Rückfahrt planen lassen und in die Parkstellung fahren (aus jeder Lage)."""
        self.set_phase("Job 3: Rückfahrt planen")
        res, err = await self.job(3)
        if err:
            return await self.fault(f"Job 3: {err}, Arm im Handbetrieb zurückfahren")
        await self.write("ArmState", 1)
        self.set_phase("fährt in die Parkstellung")
        for i, wp in enumerate(res[0]):
            await self.move_to(wp, slow=i < 2, auto="park")
        await self.write("ArmState", 0)
        self.vehicle_ready = False
        self.set_phase(f"Parkstellung (Fahrzeit der Antriebe {self.moved:.0f} s) – "
                       "Fahrzeug darf wegfahren")

    async def cycle(self):
        """Dauertest: eine Verladung ohne Bediener."""
        self.light_barrier = self.vehicle_ready = self.product_chosen = True
        # abwechselnd: Tank mit Schwallwänden (ein Dom, automatisch) / Mehrkammer (alle Dome)
        self.domes = [None] if self.multi_test else [0]
        print("Auftrag: " + ("Mehrkammer, alle offenen Dome von vorn" if self.multi_test
                             else "Kammern verbunden, ein Dom automatisch"))
        await self.sequence(interactive=False)
        self.multi_test = not self.multi_test
        self.product = (self.product + 1) % 3

    # --- Bedienung ---------------------------------------------------------------------------
    def start_task(self, coro):
        self.stop, self.moved = False, 0.0

        async def guarded():
            try:
                await coro
            except Abort as e:
                await self.fault(str(e))

        self.task = asyncio.create_task(guarded())

    async def start_checks(self) -> list[str]:
        missing = []
        if self.mode != "Automatik":
            missing.append("Betriebsart Automatik")
        if not self.in_park():
            missing.append("Arm in Parkstellung")
        if not self.stairs_home:
            missing.append("Klapptreppe in Ruhelage")
        if not self.light_barrier:
            missing.append("Lichtschranke belegt (Fahrzeug)")
        if not self.product_chosen:
            missing.append("Produkt gewählt (p <nr>)")
        if not self.vehicle_ready:
            missing.append("Fahrzeug bereit bestätigt (f)")
        if not await self.read("Ready"):
            missing.append("Vision-Dienst bereit (Ready)")
        return missing

    async def hand_to_dome(self):
        """Demo: Bediener führt den Arm von Hand in den Dom (J1/J2 geschoben, J3 getippt)."""
        self.set_phase("Hand-Demo: Dom messen (Job 0)")
        res, err = await self.job(0)
        if err:
            return self.set_phase(f"Hand-Demo: {err}")
        out = res[1]
        target = (out["TargetX"], out["TargetY"], out["TargetZ"])
        normal = (out["NormalX"], out["NormalY"], out["NormalZ"])
        q0 = np.array([self.geom.joints[k].to_model(v) for k, v in zip(JOINTS, self.actual,
                                                                        strict=True)])
        plan = plan_motion(self.geom, target, normal, insertion_depth=0.4, q_start=q0)
        if not plan["ok"]:
            return self.set_phase(f"Hand-Demo: {plan['reason']}")
        self.set_phase("Hand-Demo: Arm wird von Hand über den Dom geführt und abgesenkt")
        await self.write("ArmState", 1)
        for q in pick(plan["q_move"], 4) + pick(plan["q_insert"], 3):
            await self.move_to(self.geom.to_servo(q), factor=JOG_FACTOR, auto=False)
        await self.write("ArmState", 3)
        self.set_phase("Hand-Demo: Arm steht im Dom (ohne Job 1). Weiter mit z")

    async def command(self, line: str):
        parts = line.strip().split()
        if not parts:
            return
        cmd, args = parts[0].lower(), parts[1:]
        busy = self.busy()
        if cmd == "q":
            raise KeyboardInterrupt
        if cmd in ("?", "hilfe", "status"):
            print(HELP)
            print(f"Zustand: {self.status()}")
        elif cmd == "x":
            self.stop = True
            print("Stopp")
        elif cmd == "e":
            if busy and self.phase.startswith("Beladung läuft"):
                self.loading_done.set()
            else:
                print("Keine Beladung aktiv")
        elif cmd == "u":
            self.flow_ok = not self.flow_ok
            print("Durchflusssensor " + ("in Ordnung" if self.flow_ok else
                                         "AUSGEFALLEN – Sollmenge wird nicht erkannt"))
        elif cmd == "l":
            self.light_barrier = not self.light_barrier
            print(f"Lichtschranke {'belegt' if self.light_barrier else 'frei'}")
            if not self.light_barrier and not busy:
                self.vehicle_ready = False
        elif busy:
            print(f"Läuft gerade ({self.phase}) – erst Stopp (x) oder abwarten")
        elif cmd == "n":
            if not self.in_park():
                return print("Arm nicht in Parkstellung")
            self.light_barrier, self.vehicle_ready, self.product_chosen = True, False, False
            self.stairs_home = False
            self.set_phase("Fahrzeug steht, Klapptreppe ausgefahren, Fahrer öffnet den Dom")
            await asyncio.sleep(1.0)
            self.stairs_home = True
            self.set_phase("Klapptreppe in Ruhelage – Produkt wählen (p), bestätigen (f), "
                           "starten (s)")
        elif cmd == "t":
            if not self.in_park():
                return print("Klapptreppe verriegelt: Arm nicht in Parkstellung")
            self.stairs_home = not self.stairs_home
            print(f"Klapptreppe {'Ruhelage' if self.stairs_home else 'ausgefahren'}")
        elif cmd == "p" and args:
            self.product, self.product_chosen = int(args[0]), True
            print(f"Produkt {self.product} gewählt")
        elif cmd == "k" and args:
            domes = [int(a) for a in args]
            if any(d < 0 for d in domes) or (0 in domes and len(domes) > 1):
                return print("k 0 (verbunden) oder k 1 2 3 (Mehrkammer, Dome von vorn)")
            self.domes = domes
            print("Auftrag: " + ("Kammern verbunden, ein Dom automatisch" if domes == [0]
                                 else f"Mehrkammer, Dome {', '.join(args)} nacheinander"))
        elif cmd == "f":
            self.vehicle_ready = True
            print("Fahrzeug bereit")
        elif cmd == "s":
            if missing := await self.start_checks():
                print("Start nicht möglich, fehlt: " + ", ".join(missing))
            else:
                self.start_task(self.sequence(interactive=True))
        elif cmd == "h":
            self.mode = "Hand" if self.mode == "Automatik" else "Automatik"
            print(f"Betriebsart {self.mode}")
        elif cmd in ("j", "b") and len(args) == 2:
            if self.mode != "Hand":
                return print("Nur im Handbetrieb (h)")
            axis, delta = int(args[0]), float(args[1])
            if axis not in (1, 2, 3):
                return print("Achse 1, 2 oder 3")
            if cmd == "b" and axis == 3:
                return print("J3: Bremse lüften gesperrt (Last hängt an der Schnecke, "
                             "Selbsthemmung nicht zugesichert – Arm könnte absacken). "
                             "Nur tippen: j 3 <°>")
            target = self.actual.copy()
            target[axis - 1] += delta
            if cmd == "j":
                self.start_task(self.move_to(target, factor=JOG_FACTOR, auto=False))
            else:
                print(f"Bremse J{axis} gelüftet, Arm wird von Hand geschoben")
                self.start_task(self.move_to(target, auto=False, hand_speed=HAND_SPEED))
        elif cmd == "d":
            if self.mode != "Hand":
                return print("Nur im Handbetrieb (h)")
            self.start_task(self.hand_to_dome())
        elif cmd == "z":
            if not self.stairs_home:
                return print("Klapptreppe nicht in Ruhelage")
            self.start_task(self.park_auto())
        else:
            print("Unbekannt – ? zeigt die Befehle")

    async def watch(self):
        """Überwachung wie in der SPS: Fahrzeug weg bei eingetauchtem Arm, Anzeige."""
        while True:
            if (self.busy() and self.phase.startswith("Beladung läuft")
                    and not self.light_barrier):
                self.task.cancel()
                await self.fault("Lichtschranke frei bei eingetauchtem Arm – Fahrzeug weg?")
            await self.show()
            await asyncio.sleep(0.2)

    async def console(self):
        loop = asyncio.get_running_loop()
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:  # keine Eingabe mehr (Datei/Pipe zu Ende)
                await asyncio.Event().wait()
            try:
                await self.command(line)
            except ValueError:
                print("Zahl erwartet – ? zeigt die Befehle")

    async def run(self, interactive: bool = False):
        asyncio.create_task(self.heartbeat())
        await self.publish_actual()
        await asyncio.sleep(1.0)
        await self.write("AxesHomed", True)  # Multiturn-Absolutwertgeber: Lage sofort gültig
        print("Achsen bereit (Absolutwertgeber)")
        if interactive:
            asyncio.create_task(self.watch())
            print(HELP)
            print("Typischer Ablauf: n, p 1, f, s ... e")
            await self.console()
            return
        while True:
            if not await self.read("Ready"):
                print("Warte auf Vision-Dienst (Ready) ...")
                await asyncio.sleep(1.0)
                continue
            await self.cycle()
            await asyncio.sleep(self.interval)


async def main(args):
    cfg = load_config(args.config) if args.config else {}
    geom = ArmGeometry(**cfg.get("arm", {}))
    drives = Drives.from_config(cfg.get("drives"))
    if drives.configured:
        for k, d in drives.axes.items():
            print(f"{k}: {d.motor or '-'}, i = {d.ratio:g}, max. {d.speed_max:.1f} °/s, "
                  f"Rampe {d.accel_time:g} s, Spiel {d.backlash:g}°")
    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://0.0.0.0:{args.port}/")
    server.set_server_name("SPS-Simulator Verladearm")
    idx = await server.register_namespace(NS_URI)
    db = await server.nodes.objects.add_object(ua.NodeId('"DB_Vision"', idx), "DB_Vision")
    var = {}
    for name, (vtype, _, length) in VARIABLES.items():
        node = await db.add_variable(ua.NodeId(f'"DB_Vision"."{name}"', idx), name,
                                     ua.Variant(default_value(vtype, length), vtype))
        await node.set_writable()
        var[name] = node
    sim_obj = await server.nodes.objects.add_object(ua.NodeId('"Simulator"', idx), "Simulator")
    status = await sim_obj.add_variable(ua.NodeId(STATUS_NODE, idx), "Bedienstatus",
                                        ua.Variant("", ua.VariantType.String))
    async with server:
        print(f"SPS-Simulator läuft auf opc.tcp://127.0.0.1:{args.port}/ (Strg+C beendet)")
        sim = PlcSim(server, var, geom, args.speed, args.interval, drives, args.zeitraffer,
                     fill=cfg.get("filling"), show_pd=args.prozessdaten)
        sim.status_node = status
        await sim.run(interactive=args.bedienen)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", help="Anlagendatei (Achsgrenzen, Parkstellung)")
    p.add_argument("--interval", type=float, default=3.0, help="Pause zwischen Verladungen [s]")
    p.add_argument("--speed", type=float, default=25.0,
                   help="Achsgeschwindigkeit ohne Antriebsdaten (drives) [°/s]")
    p.add_argument("--zeitraffer", type=float, default=1.0,
                   help="Fahrten schneller zeigen, z. B. 0.25 = vierfach (Fahrzeit bleibt echt)")
    p.add_argument("--port", type=int, default=4840)
    p.add_argument("--prozessdaten", action="store_true",
                   help="Vorgaben an die Umrichter (Ziel, v, a) je Fahrt ausgeben")
    p.add_argument("--bedienen", action="store_true",
                   help="Bedienung über Befehle im Terminal statt Dauertest (? = Hilfe)")
    logging.basicConfig(level=logging.ERROR)
    try:
        asyncio.run(main(p.parse_args()))
    except KeyboardInterrupt:
        pass
