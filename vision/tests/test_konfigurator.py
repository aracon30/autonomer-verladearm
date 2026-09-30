"""Konfigurator im Browser: Laden, Prüfen, Speichern, HTTP-Schnittstelle."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from verladearm_vision.config import load_config
from verladearm_vision.konfigurator.__main__ import (
    commissioning,
    load_station,
    make_handler,
    preview,
    save_station,
)


def test_laden_und_vorschau():
    d = load_station("heta_prototyp")
    assert d["exists"] and d["outlet"]["marker_offset"] == 0.823
    assert d["drives"]["q3"]["ratio"] == 1457.6
    p = preview(d)
    assert p["ok"] and not p["problems"]
    assert len(p["park"]) == 7 and p["reach"][1] > 4.5


def test_vorschau_meldet_fehler():
    d = load_station("heta_prototyp")
    d["arm"]["joints"]["q1"]["min"] = 200  # min > max
    assert not preview(d)["ok"]


def test_speichern_mit_sicherung_und_ohne_verlust(tmp_path):
    d = load_station("heta_prototyp")
    d["arm"]["inner_length"] = 2.5
    d["products"]["7"] = {"name": "Harz", "insertion_depth": 0.9}
    d["arm"]["obstacles"].append({"name": "Stütze", "form": "zylinder", "p0": [-3, -3, -2.5],
                                  "axis": [0, 0, 1], "radius": 0.15, "half_length": 3.0})
    path = save_station(d, "neu_1", tmp_path, backup=tmp_path / "bak")
    save_station(d, "neu_1", tmp_path, backup=tmp_path / "bak")  # zweites Mal: Sicherung
    cfg = load_config(path)
    assert cfg["arm"]["inner_length"] == 2.5 and cfg["products"][7]["insertion_depth"] == 0.9
    assert cfg["outlet"] == {"marker_radius": 0.11, "marker_offset": 0.823, "pipe_radius": 0.057}
    assert cfg["drives"]["q3"]["gravity_preload"] is True
    assert cfg["arm"]["obstacles"][-1]["form"] == "zylinder"
    assert len(list((tmp_path / "bak").iterdir())) == 1
    try:
        save_station(d, "../boese", tmp_path)
    except ValueError:
        pass
    else:
        raise AssertionError("ungültiger Name angenommen")


def test_inbetriebnahmepruefung_ohne_speichern(tmp_path):
    d = load_station("heta_prototyp")
    d["commissioning"]["step"] = 0.5
    r = commissioning(d, "pruefung", tmp_path)
    assert r["ok"] and "Antriebe" in r["report"]
    assert not list(tmp_path.glob("*.yaml"))  # nichts liegen geblieben


def test_http_schnittstelle(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(tmp_path, tmp_path / "bak"))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        page = urllib.request.urlopen(base + "/").read().decode()
        assert "Verladearm Konfigurator" in page
        d = json.loads(urllib.request.urlopen(base + "/api/load?name=neu_2").read())
        assert not d["exists"]
        req = urllib.request.Request(base + "/api/save", json.dumps({"name": "neu_2", "data": d})
                                     .encode(), {"Content-Type": "application/json"})
        r = json.loads(urllib.request.urlopen(req).read())
        assert r["ok"] and "neu_2" in r["files"]
    finally:
        server.shutdown()
