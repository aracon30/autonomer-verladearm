import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import numpy as np

from verladearm_vision.synthetic import make_tank_roof
from verladearm_vision.viewer.__main__ import FrameProducer, make_handler


def _cfg(folder):
    return {
        "source": {"type": "file", "path": str(folder)},
        "calibration": {"matrix": np.eye(4).tolist()},
    }


def test_frame_mit_und_ohne_oeffnung(tmp_path):
    np.save(tmp_path / "a.npy", make_tank_roof(center_xy=(0.2, -0.1)))
    np.save(tmp_path / "b.npy", make_tank_roof(openings=0))
    producer = FrameProducer(_cfg(tmp_path), max_points=5000)

    ok = producer.next_frame()
    assert ok["result"]["ok"]
    assert abs(ok["result"]["target_mm"][0] - 200) < 10
    assert len(ok["points"]) == 3 * 5000

    err = producer.next_frame()
    assert not err["result"]["ok"]
    assert err["result"]["error_code"] == 20


def test_http_server(tmp_path):
    np.save(tmp_path / "a.npy", make_tank_roof())
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(FrameProducer(_cfg(tmp_path))))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert b"Verladearm Live" in urllib.request.urlopen(base + "/").read()
        frame = json.loads(urllib.request.urlopen(base + "/api/frame").read())
        assert frame["id"] == 1 and frame["result"]["ok"]
    finally:
        server.shutdown()


def test_plc_monitor_liest_db_vision(tmp_path):
    import asyncio
    import time

    from asyncua import Server, ua

    from verladearm_vision.plc import VARIABLES
    from verladearm_vision.viewer.__main__ import PlcMonitor

    port = 48471
    values = {
        "Ready": True, "ResultId": 3, "Error": False, "ErrorCode": 0,
        "TargetX": 218.3, "TargetY": -48.4, "TargetZ": 3858.6,
        "NormalX": 0.0, "NormalY": 0.0, "NormalZ": -1.0,
        "DiameterMm": 486.1, "Confidence": 0.88,
    }
    started, stop = threading.Event(), threading.Event()

    async def serve():
        server = Server()
        await server.init()
        server.set_endpoint(f"opc.tcp://127.0.0.1:{port}/")
        idx = await server.register_namespace("urn:test")
        db = await server.nodes.objects.add_object(ua.NodeId('"DB_Vision"', idx), "DB_Vision")
        for name, (vtype, _) in VARIABLES.items():
            default = False if vtype == ua.VariantType.Boolean else 0
            await db.add_variable(ua.NodeId(f'"DB_Vision"."{name}"', idx), name,
                                  ua.Variant(values.get(name, default), vtype))
        async with server:
            started.set()
            while not stop.is_set():
                await asyncio.sleep(0.05)

    threading.Thread(target=lambda: asyncio.run(serve()), daemon=True).start()
    assert started.wait(10)

    points = make_tank_roof()
    np.save(tmp_path / "last.npy", points)
    monitor = PlcMonitor({
        "plc": {"url": f"opc.tcp://127.0.0.1:{port}/", "namespace_uri": "urn:test",
                "node_template": 'ns={ns};s="DB_Vision"."{name}"'},
        "snapshot": {"path": str(tmp_path / "last.npy")},
        "calibration": {"matrix": np.eye(4).tolist()},
    }, max_points=1000, poll_s=0.05)
    monitor.start()
    try:
        deadline = time.time() + 10
        while not monitor.state()["connected"] and time.time() < deadline:
            time.sleep(0.05)
        state = monitor.state()
        assert state["connected"] and state["signals"]["ResultId"] == 3
        frame = monitor.next_frame()
        assert frame["id"] == 3 and frame["result"]["ok"]
        assert frame["result"]["target_mm"] == [218.3, -48.4, 3858.6]
        assert frame["n_points"] == len(points) and len(frame["points"]) == 3000
    finally:
        stop.set()
