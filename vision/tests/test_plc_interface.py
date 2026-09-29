"""Handshake InterfaceVersion 2 über OPC UA gegen einen Testserver (Stützpunkt-Felder)."""

import asyncio

from asyncua import Server, ua

from verladearm_vision.plc import VARIABLES, MeasureResult, PlcInterface, Request

PORT = 48473
NS = "urn:test-plc"


def test_auftrag_und_stuetzpunkte_ueber_opcua():
    received = []

    def measure(req: Request) -> MeasureResult:
        received.append(req)
        return MeasureResult(ok=True, target_mm=(3100.0, -200.0, -1500.0),
                             waypoints=[(10.0, -20.0, 5.0), (11.0, -21.0, 4.0)],
                             approach_index=1, correction_mm=(2.5, -1.0))

    async def scenario():
        server = Server()
        await server.init()
        server.set_endpoint(f"opc.tcp://127.0.0.1:{PORT}/")
        idx = await server.register_namespace(NS)
        db = await server.nodes.objects.add_object(ua.NodeId('"DB_Vision"', idx), "DB_Vision")
        var = {}
        for name, (vtype, _, length) in VARIABLES.items():
            default = False if vtype == ua.VariantType.Boolean else 0
            default = [default] * length if length else default
            var[name] = await db.add_variable(ua.NodeId(f'"DB_Vision"."{name}"', idx), name,
                                              ua.Variant(default, vtype))
            await var[name].set_writable()

        async def write(name, value):
            await var[name].write_value(ua.Variant(value, VARIABLES[name][0]))

        async with server:
            plc = PlcInterface(f"opc.tcp://127.0.0.1:{PORT}/", NS,
                               'ns={ns};s="DB_Vision"."{name}"', cycle_s=0.02)
            task = asyncio.create_task(plc.run(measure))
            try:
                hb = 0
                for step in range(300):
                    hb += 1
                    await write("HeartbeatPLC", hb)
                    if step == 20:
                        assert await var["Ready"].read_value()
                        assert await var["InterfaceVersion"].read_value() == 2
                        await write("Job", 1)
                        await write("ProductId", 2)
                        await write("ActualJ1", 70.0)
                        await write("AxesHomed", True)
                        await write("Trigger", True)
                    if step > 20 and await var["Done"].read_value():
                        break
                    await asyncio.sleep(0.02)
                return {n: await var[n].read_value() for n in
                        ("Error", "WaypointCount", "WaypointsJ1", "WaypointsJ3",
                         "ApproachIndex", "CorrectionX", "TargetX", "ResultId")}
            finally:
                task.cancel()

    out = asyncio.run(scenario())
    assert received and received[0].job == 1 and received[0].product_id == 2
    assert received[0].axes_homed and abs(received[0].actual_deg[0] - 70.0) < 1e-4
    assert not out["Error"] and out["ResultId"] == 1
    assert out["WaypointCount"] == 2 and out["ApproachIndex"] == 1
    assert out["WaypointsJ1"][:3] == [10.0, 11.0, 0.0] and len(out["WaypointsJ1"]) == 16
    assert out["WaypointsJ3"][:2] == [5.0, 4.0]
    assert abs(out["CorrectionX"] - 2.5) < 1e-6 and out["TargetX"] == 3100.0
