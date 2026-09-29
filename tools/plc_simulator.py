"""Simuliert die SPS-Seite (OPC-UA-Server mit DB_Vision) für Entwicklung ohne echte SPS.

Terminal 1:  python tools/plc_simulator.py
Terminal 2:  python -m verladearm_vision.service.main
"""

import argparse
import asyncio
import logging

from asyncua import Server, ua

from verladearm_vision.plc import VARIABLES

NS_URI = "http://www.siemens.com/simatic-s7-opcua"
DEFAULTS = {ua.VariantType.Boolean: False, ua.VariantType.Float: 0.0}


async def main(interval: float, port: int):
    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://0.0.0.0:{port}/")
    server.set_server_name("SPS-Simulator Verladearm")
    idx = await server.register_namespace(NS_URI)
    db = await server.nodes.objects.add_object(ua.NodeId('"DB_Vision"', idx), "DB_Vision")

    var = {}
    for name, (vtype, _) in VARIABLES.items():
        node = await db.add_variable(
            ua.NodeId(f'"DB_Vision"."{name}"', idx), name, DEFAULTS.get(vtype, 0), varianttype=vtype
        )
        await node.set_writable()
        var[name] = node

    async def write(name, value):
        await var[name].write_value(ua.Variant(value, VARIABLES[name][0]))

    async def heartbeat():
        n = 0
        while True:
            n = (n + 1) % 32767
            await write("HeartbeatPLC", n)
            await asyncio.sleep(0.1)

    async with server:
        print(f"SPS-Simulator läuft auf opc.tcp://127.0.0.1:{port}/ (Strg+C beendet)")
        asyncio.create_task(heartbeat())
        while True:
            await asyncio.sleep(interval)
            if not await var["Ready"].read_value():
                print("Warte auf Vision-Dienst (Ready) ...")
                continue
            await write("ProductId", 1)
            await write("Trigger", True)
            for _ in range(200):
                if await var["Done"].read_value():
                    break
                await asyncio.sleep(0.05)
            else:
                print("Timeout: kein Ergebnis")
                await write("Trigger", False)
                continue
            if await var["Error"].read_value():
                print(f"Fehler, Code {await var['ErrorCode'].read_value()}")
            else:
                vals = [await var[n].read_value() for n in ("TargetX", "TargetY", "TargetZ")]
                d = await var["DiameterMm"].read_value()
                c = await var["Confidence"].read_value()
                rid = await var["ResultId"].read_value()
                print(f"#{rid} Ziel [mm]: {vals[0]:.1f} / {vals[1]:.1f} / {vals[2]:.1f}"
                      f"  Ø {d:.0f} mm  Konfidenz {c:.2f}")
            await write("Trigger", False)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--interval", type=float, default=3.0, help="Sekunden zwischen Messungen")
    p.add_argument("--port", type=int, default=4840)
    a = p.parse_args()
    logging.basicConfig(level=logging.ERROR)
    try:
        asyncio.run(main(a.interval, a.port))
    except KeyboardInterrupt:
        pass
