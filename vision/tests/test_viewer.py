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
