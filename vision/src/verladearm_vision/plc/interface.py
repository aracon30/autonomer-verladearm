"""OPC-UA-Client zur SPS: Handshake, Heartbeat, Übergabe der Zielkoordinate.

Vertrag siehe docs/schnittstelle.md. Die SPS ist OPC-UA-Server (z. B. S7-1500),
dieser Dienst ist Client und schreibt/liest den Datenbaustein DB_Vision.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from asyncua import Client, ua

log = logging.getLogger(__name__)

INTERFACE_VERSION = 1
ERR_INTERNAL = 90

_B, _I, _D, _R = (
    ua.VariantType.Boolean, ua.VariantType.Int16, ua.VariantType.Int32, ua.VariantType.Float
)

# Name: (Datentyp, Richtung)  – Richtung aus Sicht der SPS
VARIABLES: dict[str, tuple[ua.VariantType, str]] = {
    "HeartbeatPLC": (_I, "in"),
    "Trigger": (_B, "in"),
    "ProductId": (_I, "in"),
    "Reset": (_B, "in"),
    "HeartbeatPC": (_I, "out"),
    "Ready": (_B, "out"),
    "Busy": (_B, "out"),
    "Done": (_B, "out"),
    "Error": (_B, "out"),
    "ErrorCode": (_I, "out"),
    "ResultId": (_D, "out"),
    "TargetX": (_R, "out"),
    "TargetY": (_R, "out"),
    "TargetZ": (_R, "out"),
    "NormalX": (_R, "out"),
    "NormalY": (_R, "out"),
    "NormalZ": (_R, "out"),
    "DiameterMm": (_R, "out"),
    "Confidence": (_R, "out"),
    "InterfaceVersion": (_I, "out"),
}


@dataclass
class MeasureResult:
    ok: bool
    error_code: int = 0
    target_mm: tuple = (0.0, 0.0, 0.0)
    normal: tuple = (0.0, 0.0, 1.0)
    diameter_mm: float = 0.0
    confidence: float = 0.0
    message: str = field(default="", repr=False)


class PlcInterface:
    def __init__(
        self,
        url: str,
        namespace_uri: str,
        node_template: str,
        cycle_s: float = 0.05,
        heartbeat_timeout_s: float = 1.0,
    ):
        self.url = url
        self.namespace_uri = namespace_uri
        self.node_template = node_template
        self.cycle_s = cycle_s
        self.heartbeat_timeout_s = heartbeat_timeout_s
        self._nodes = {}

    async def _write(self, name: str, value):
        vtype = VARIABLES[name][0]
        await self._nodes[name].write_value(ua.DataValue(ua.Variant(value, vtype)))

    async def _write_result(self, r: MeasureResult, result_id: int):
        values = {
            "TargetX": r.target_mm[0], "TargetY": r.target_mm[1], "TargetZ": r.target_mm[2],
            "NormalX": r.normal[0], "NormalY": r.normal[1], "NormalZ": r.normal[2],
            "DiameterMm": r.diameter_mm, "Confidence": r.confidence,
            "ErrorCode": r.error_code, "ResultId": result_id,
        }
        for name, value in values.items():
            await self._write(name, float(value) if VARIABLES[name][0] == _R else int(value))
        await self._write("Error", not r.ok)
        await self._write("Done", True)
        await self._write("Busy", False)

    async def run(self, measure: Callable[[int], MeasureResult]):
        """Verbindet sich mit der SPS und bedient den Handshake bis zum Abbruch."""
        async with Client(url=self.url) as client:
            ns = await client.get_namespace_index(self.namespace_uri)
            self._nodes = {
                n: client.get_node(self.node_template.format(ns=ns, name=n)) for n in VARIABLES
            }
            log.info("Verbunden mit %s (ns=%s)", self.url, ns)

            await self._write("InterfaceVersion", INTERFACE_VERSION)
            for flag in ("Busy", "Done", "Error"):
                await self._write(flag, False)

            inputs = [self._nodes[n] for n in ("Trigger", "Reset", "ProductId", "HeartbeatPLC")]
            hb_pc, last_hb_plc, last_change = 0, None, time.monotonic()
            ready, done_pending, result_id = False, False, 0
            loop = asyncio.get_running_loop()

            while True:
                trigger, reset, product_id, hb_plc = await client.read_values(inputs)
                now = time.monotonic()
                if hb_plc != last_hb_plc:
                    last_hb_plc, last_change = hb_plc, now

                hb_pc = (hb_pc + 1) % 32767
                await self._write("HeartbeatPC", hb_pc)

                plc_alive = now - last_change < self.heartbeat_timeout_s
                if plc_alive != ready:
                    ready = plc_alive
                    await self._write("Ready", ready)
                    log.log(logging.INFO if ready else logging.WARNING,
                            "SPS-Heartbeat %s", "OK" if ready else "ausgefallen")
                if not ready:
                    await asyncio.sleep(self.cycle_s)
                    continue

                if reset:
                    await self._write("Error", False)
                    await self._write("ErrorCode", 0)

                if trigger and not done_pending:
                    await self._write("Error", False)
                    await self._write("Busy", True)
                    try:
                        result = await loop.run_in_executor(None, measure, int(product_id))
                    except Exception:
                        log.exception("Messung fehlgeschlagen")
                        result = MeasureResult(ok=False, error_code=ERR_INTERNAL)
                    result_id += 1
                    await self._write_result(result, result_id)
                    done_pending = True
                    log.info("Ergebnis %d: %s", result_id, result)
                elif not trigger and done_pending:
                    await self._write("Done", False)
                    done_pending = False

                await asyncio.sleep(self.cycle_s)
