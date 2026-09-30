"""Simuliert die SPS-Seite (OPC-UA-Server mit DB_Vision, InterfaceVersion 2).

Ablauf je Verladung wie im echten SPS-Programm vorgesehen (docs/schnittstelle.md):
Referenzfahrt -> Job 1 (messen, planen) -> Fahrt bis über den Dom -> Job 2 (nachmessen,
korrigieren) -> Eintauchen -> Befüllung (nur Wartezeit) -> Job 3 (Rückfahrt planen) -> Park.
Achsen fahren synchron mit weichem Anfahren und Bremsen; die Istwinkel gehen an den PC zurück.
Mit Abschnitt `drives` in der Anlagendatei gelten die Geschwindigkeiten und Rampen der echten
Antriebe (Motor, Übersetzung, Grenzen); die langsamste Achse bestimmt die Fahrzeit je Stützpunkt.

Terminal 1:  python tools/plc_simulator.py --config vision/config/anlagen/beispiel.yaml
Terminal 2:  python -m verladearm_vision.service.main --config <Anlage mit source: sim>
"""

import argparse
import asyncio
import logging

import numpy as np
from asyncua import Server, ua

from verladearm_vision.config import load_config
from verladearm_vision.drives import Drives, profile
from verladearm_vision.kinematics import JOINTS, ArmGeometry
from verladearm_vision.plc import VARIABLES

NS_URI = "http://www.siemens.com/simatic-s7-opcua"


def default_value(vtype, length):
    v = False if vtype == ua.VariantType.Boolean else 0.0 if vtype == ua.VariantType.Float else 0
    return [v] * length if length else v


class PlcSim:
    def __init__(self, server, var, geom: ArmGeometry, speed: float, interval: float,
                 drives: Drives | None = None, time_scale: float = 1.0):
        self.server, self.var, self.geom = server, var, geom
        self.speed, self.interval = speed, interval
        self.drives = drives if drives and drives.configured else None
        self.time_scale = time_scale  # < 1: schneller als Echtzeit (nur Anzeige)
        self.moved = 0.0  # Fahrzeit der laufenden Verladung [s, Echtzeit der Antriebe]
        self.park = np.array([geom.joints[k].park for k in JOINTS], dtype=float)
        self.actual = self.park.copy()
        self.product = 0

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

    async def move_to(self, target, slow=False):
        """Synchron: alle Achsen starten und enden gemeinsam, weiches Anfahren und Bremsen."""
        target = np.asarray(target, dtype=float)
        start = self.actual.copy()
        factor = 0.3 if slow else 1.0  # Eintauchen und Herausfahren langsam
        if self.drives:  # echte Antriebe: langsamste Achse bestimmt, alle kommen gleichzeitig an
            duration = max(self.drives.sync_time(start, target, factor), 0.2)
        else:
            duration = max(np.abs(target - start).max() / (self.speed * factor) * 1.5, 0.2)
        self.moved += duration
        shown = duration * self.time_scale
        steps = max(int(shown / 0.05), 1)
        for i in range(1, steps + 1):
            self.actual = start + (target - start) * profile(i / steps)
            await self.publish_actual()
            await asyncio.sleep(shown / steps)

    async def job(self, job: int):
        """Auftrag an den Vision-PC, Handshake nach docs/schnittstelle.md."""
        await self.write("Job", job)
        await self.write("ProductId", self.product)
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
                                               "TargetX", "TargetY", "TargetZ")}
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

    async def cycle(self):
        self.moved = 0.0
        await self.write("ArmState", 0)
        res, err = await self.job(1)
        if err:
            print(f"Job 1: {err}")
            return
        wps, out = res
        a = out["ApproachIndex"]
        print(f"Job 1: Dom bei {out['TargetX']:.0f} / {out['TargetY']:.0f} / "
              f"{out['TargetZ']:.0f} mm, {len(wps)} Stützpunkte, über Dom = Nr. {a}")
        await self.write("ArmState", 1)
        for wp in wps[:a]:
            await self.move_to(wp)
        await self.write("ArmState", 2)
        await asyncio.sleep(0.5)  # Beruhigungszeit (Auslass pendelt frei)

        res, err = await self.job(2)
        if err:
            print(f"Job 2: {err} -> Abbruch, Rückfahrt")
        else:
            wps, out = res
            print(f"Job 2: Korrektur {out['CorrectionX']:+.1f} / {out['CorrectionY']:+.1f} mm")
            await self.move_to(wps[0])
            for wp in wps[1:]:
                await self.move_to(wp, slow=True)
            await self.write("ArmState", 3)
            print("Befüllung (simuliert) ...")
            await asyncio.sleep(2.0)

        res, err = await self.job(3)
        if err:
            print(f"Job 3: {err} -> Arm bleibt stehen, Handbetrieb nötig")
            await self.write("ArmState", 9)
            return
        await self.write("ArmState", 1)
        for i, wp in enumerate(res[0]):
            await self.move_to(wp, slow=i < 2)
        await self.write("ArmState", 0)
        print(f"Parkstellung erreicht (Fahrzeit der Antriebe gesamt {self.moved:.0f} s)")
        self.product = (self.product + 1) % 3

    async def run(self):
        asyncio.create_task(self.heartbeat())
        await self.publish_actual()
        await asyncio.sleep(1.0)
        await self.write("AxesHomed", True)  # Referenzfahrt auf Endlagenschalter (simuliert)
        print("Achsen referenziert")
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
    async with server:
        print(f"SPS-Simulator läuft auf opc.tcp://127.0.0.1:{args.port}/ (Strg+C beendet)")
        await PlcSim(server, var, geom, args.speed, args.interval, drives,
                     args.zeitraffer).run()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", help="Anlagendatei (Achsgrenzen, Parkstellung)")
    p.add_argument("--interval", type=float, default=3.0, help="Pause zwischen Verladungen [s]")
    p.add_argument("--speed", type=float, default=25.0,
                   help="Achsgeschwindigkeit ohne Antriebsdaten (drives) [°/s]")
    p.add_argument("--zeitraffer", type=float, default=1.0,
                   help="Fahrten schneller zeigen, z. B. 0.25 = vierfach (Fahrzeit bleibt echt)")
    p.add_argument("--port", type=int, default=4840)
    logging.basicConfig(level=logging.ERROR)
    try:
        asyncio.run(main(p.parse_args()))
    except KeyboardInterrupt:
        pass
