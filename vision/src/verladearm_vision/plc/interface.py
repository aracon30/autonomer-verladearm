"""OPC-UA-Client zur SPS: Handshake, Heartbeat, Aufträge (Jobs), Messergebnis und Stützpunkte.

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

INTERFACE_VERSION = 2
ERR_INTERNAL = 90
MAX_WAYPOINTS = 16

# Aufträge der SPS (Job)
JOB_MEASURE_PLAN = 1  # Dom messen, Bahn Istlage -> über Dom -> eingetaucht planen
JOB_CORRECT = 2  # Auslass über dem Dom nachmessen, korrigierte Bahn planen
JOB_RETRACT = 3  # Rückfahrt Istlage -> Park planen

_B, _I, _D, _R = (
    ua.VariantType.Boolean, ua.VariantType.Int16, ua.VariantType.Int32, ua.VariantType.Float
)

# Name: (Datentyp, Richtung aus Sicht der SPS, Feldlänge; 0 = Einzelwert)
VARIABLES: dict[str, tuple[ua.VariantType, str, int]] = {
    "HeartbeatPLC": (_I, "in", 0),
    "Trigger": (_B, "in", 0),
    "Job": (_I, "in", 0),
    "ProductId": (_I, "in", 0),
    "Reset": (_B, "in", 0),
    "ActualJ1": (_R, "in", 0),
    "ActualJ2": (_R, "in", 0),
    "ActualJ3": (_R, "in", 0),
    "AxesHomed": (_B, "in", 0),
    "ArmState": (_I, "in", 0),
    "HeartbeatPC": (_I, "out", 0),
    "Ready": (_B, "out", 0),
    "Busy": (_B, "out", 0),
    "Done": (_B, "out", 0),
    "Error": (_B, "out", 0),
    "ErrorCode": (_I, "out", 0),
    "ResultId": (_D, "out", 0),
    "TargetX": (_R, "out", 0),
    "TargetY": (_R, "out", 0),
    "TargetZ": (_R, "out", 0),
    "NormalX": (_R, "out", 0),
    "NormalY": (_R, "out", 0),
    "NormalZ": (_R, "out", 0),
    "DiameterMm": (_R, "out", 0),
    "Confidence": (_R, "out", 0),
    "WaypointCount": (_I, "out", 0),
    "WaypointsJ1": (_R, "out", MAX_WAYPOINTS),
    "WaypointsJ2": (_R, "out", MAX_WAYPOINTS),
    "WaypointsJ3": (_R, "out", MAX_WAYPOINTS),
    "ApproachIndex": (_I, "out", 0),
    "CorrectionX": (_R, "out", 0),
    "CorrectionY": (_R, "out", 0),
    "InterfaceVersion": (_I, "out", 0),
}


@dataclass
class Request:
    """Auftrag der SPS zum Zeitpunkt des Triggers."""

    job: int = JOB_MEASURE_PLAN
    product_id: int = 0
    actual_deg: tuple = (0.0, 0.0, 0.0)  # Servo-Istwinkel J1..J3
    axes_homed: bool = False
    arm_state: int = 0


@dataclass
class MeasureResult:
    ok: bool
    error_code: int = 0
    target_mm: tuple = (0.0, 0.0, 0.0)
    normal: tuple = (0.0, 0.0, 1.0)
    diameter_mm: float = 0.0
    confidence: float = 0.0
    waypoints: list = field(default_factory=list)  # [(J1, J2, J3) Servo-Grad, ...]
    approach_index: int = 0  # 1-basiert: Stützpunkt "über dem Dom"; 0 = keiner
    correction_mm: tuple = (0.0, 0.0)
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
        self._client = None

    def _datavalue(self, name: str, value) -> ua.DataValue:
        vtype, _, length = VARIABLES[name]
        conv = float if vtype == _R else bool if vtype == _B else int
        if length:
            value = [conv(v) for v in list(value)[:length]]
            value += [conv(0)] * (length - len(value))
        else:
            value = conv(value)
        return ua.DataValue(ua.Variant(value, vtype))

    async def _write(self, **values):
        """Schreibt mehrere Variablen in einem OPC-UA-Aufruf."""
        await self._client.write_values(
            [self._nodes[n] for n in values],
            [self._datavalue(n, v) for n, v in values.items()],
        )

    async def _write_result(self, r: MeasureResult, result_id: int):
        wp = r.waypoints[:MAX_WAYPOINTS] if r.ok else []
        if len(r.waypoints) > MAX_WAYPOINTS:
            log.error("%d Stützpunkte, nur %d übertragbar", len(r.waypoints), MAX_WAYPOINTS)
        await self._write(
            TargetX=r.target_mm[0], TargetY=r.target_mm[1], TargetZ=r.target_mm[2],
            NormalX=r.normal[0], NormalY=r.normal[1], NormalZ=r.normal[2],
            DiameterMm=r.diameter_mm, Confidence=r.confidence,
            WaypointCount=len(wp),
            WaypointsJ1=[w[0] for w in wp], WaypointsJ2=[w[1] for w in wp],
            WaypointsJ3=[w[2] for w in wp],
            ApproachIndex=r.approach_index if r.ok else 0,
            CorrectionX=r.correction_mm[0], CorrectionY=r.correction_mm[1],
            ErrorCode=r.error_code, ResultId=result_id, Error=not r.ok,
        )
        # Done erst nach den Ergebniswerten, damit die SPS nie halbe Ergebnisse übernimmt
        await self._write(Done=True, Busy=False)

    async def run(self, measure: Callable[[Request], MeasureResult], retry_s: float = 3.0):
        """Verbindet sich mit der SPS und bedient den Handshake bis zum Abbruch.

        Ist die SPS (noch) nicht erreichbar oder bricht die Verbindung ab, wird nach `retry_s`
        erneut verbunden – der Dienst beendet sich deshalb nicht."""
        self._result_id = getattr(self, "_result_id", 0)
        while True:
            try:
                await self._session(measure)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # Verbindungsfehler, SPS neu gestartet, Netz weg
                self._client = None
                log.warning("SPS %s nicht erreichbar (%s: %s), neuer Versuch in %.0f s",
                            self.url, type(e).__name__, e, retry_s)
                await asyncio.sleep(retry_s)

    async def _session(self, measure: Callable[[Request], MeasureResult]):
        async with Client(url=self.url) as client:
            self._client = client
            ns = await client.get_namespace_index(self.namespace_uri)
            self._nodes = {
                n: client.get_node(self.node_template.format(ns=ns, name=n)) for n in VARIABLES
            }
            log.info("Verbunden mit %s (ns=%s)", self.url, ns)

            await self._write(
                InterfaceVersion=INTERFACE_VERSION, Busy=False, Done=False, Error=False
            )

            names = ("Trigger", "Reset", "HeartbeatPLC", "Job", "ProductId",
                     "ActualJ1", "ActualJ2", "ActualJ3", "AxesHomed", "ArmState")
            inputs = [self._nodes[n] for n in names]
            hb_pc, last_hb_plc, last_change = 0, None, time.monotonic()
            ready, done_pending = False, False
            loop = asyncio.get_running_loop()

            while True:
                v = dict(zip(names, await client.read_values(inputs), strict=True))
                trigger, reset, hb_plc = v["Trigger"], v["Reset"], v["HeartbeatPLC"]
                now = time.monotonic()
                if hb_plc != last_hb_plc:
                    last_hb_plc, last_change = hb_plc, now

                hb_pc = (hb_pc + 1) % 32767
                plc_alive = now - last_change < self.heartbeat_timeout_s
                # Ready nur mit SPS-Heartbeat und bereitem Sensor (Kamera startet z. B. noch)
                sensor_ok = bool(getattr(measure, "ready", True))
                if (plc_alive and sensor_ok) != ready:
                    ready = plc_alive and sensor_ok
                    await self._write(HeartbeatPC=hb_pc, Ready=ready)
                    if ready:
                        log.info("Bereit (SPS-Heartbeat OK, Sensor bereit)")
                    else:
                        log.warning("Nicht bereit: %s", "SPS-Heartbeat ausgefallen"
                                    if not plc_alive else "Sensor nicht verbunden")
                else:
                    await self._write(HeartbeatPC=hb_pc)
                if not ready:
                    await asyncio.sleep(self.cycle_s)
                    continue

                if reset:
                    await self._write(Error=False, ErrorCode=0)

                if trigger and not done_pending:
                    await self._write(Error=False, Busy=True)
                    req = Request(
                        job=int(v["Job"]), product_id=int(v["ProductId"]),
                        actual_deg=(float(v["ActualJ1"]), float(v["ActualJ2"]),
                                    float(v["ActualJ3"])),
                        axes_homed=bool(v["AxesHomed"]), arm_state=int(v["ArmState"]),
                    )
                    try:
                        result = await loop.run_in_executor(None, measure, req)
                    except Exception:
                        log.exception("Messung fehlgeschlagen")
                        result = MeasureResult(ok=False, error_code=ERR_INTERNAL)
                    self._result_id += 1
                    await self._write_result(result, self._result_id)
                    done_pending = True
                    log.info("Job %d -> Ergebnis %d: %s", req.job, self._result_id, result)
                elif not trigger and done_pending:
                    await self._write(Done=False)
                    done_pending = False

                await asyncio.sleep(self.cycle_s)
