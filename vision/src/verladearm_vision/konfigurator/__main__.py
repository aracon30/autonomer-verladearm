"""Konfigurator im Browser: Anlagendatei eines Verladearms anlegen und bearbeiten.

    python -m verladearm_vision.konfigurator                 -> http://127.0.0.1:8090
    python -m verladearm_vision.konfigurator --host 0.0.0.0  (im Netzwerk, ohne Anmeldung!)

Bearbeitet dieselben Anlagendateien wie der Dialog (`python -m verladearm_vision.einrichtung`)
unter vision/config/anlagen/. Vor jedem Speichern wird die bisherige Datei gesichert
(data/sicherung_anlagen/). Abschnitte, die der Konfigurator nicht kennt, bleiben erhalten.
"""

import argparse
import io
import json
import logging
import os
import re
import threading
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path

import numpy as np
import yaml

from verladearm_vision.commissioning import check as commissioning_check
from verladearm_vision.config import load_config
from verladearm_vision.drives import Drives
from verladearm_vision.einrichtung import ANLAGEN, DIMENSIONS, render
from verladearm_vision.kinematics import JOINTS, ArmGeometry, forward, validate
from verladearm_vision.viewer.__main__ import obstacle_for_view

log = logging.getLogger("verladearm.konfigurator")
NAME = re.compile(r"^[A-Za-z0-9_\-]{1,60}$")
BACKUP = ANLAGEN.parents[2] / "data" / "sicherung_anlagen"
DRIVE_FIELDS = ("motor", "gear", "motor_speed", "ratio", "speed_limit", "accel_time", "backlash",
                "gravity_preload", "torque", "torque_peak", "brake", "encoder")


def list_files(folder: Path = ANLAGEN) -> list[str]:
    return sorted(p.stem for p in folder.glob("*.yaml") if not p.name.startswith("."))


def _meta(text: str) -> dict:
    meta = {}
    for key, label in (("anlage", "Anlage"), ("name", "Inbetriebnahme")):
        m = re.search(rf"^#\s*{label}:\s*(.+)$", text, re.M)
        if m:
            meta[key] = m.group(1).strip()
    if "name" in meta and "," in meta["name"]:  # "TT.MM.JJJJ, Name"
        meta["name"] = meta["name"].split(",", 1)[1].strip()
    return meta


def load_station(name: str, folder: Path = ANLAGEN) -> dict:
    """Anlagendatei (mit geerbten Standardwerten) für die Formularansicht."""
    path = folder / f"{name}.yaml"
    base = path if path.exists() else ANLAGEN / "beispiel.yaml"
    cfg = load_config(base)
    arm = cfg.get("arm", {})
    geom = ArmGeometry(**arm)
    outlet = cfg.get("outlet", {})
    return {
        "name": name,
        "exists": path.exists(),
        "meta": {"anlage": name, "name": ""} | (_meta(path.read_text(encoding="utf-8"))
                                                if path.exists() else {}),
        "plc_url": cfg.get("plc", {}).get("url", ""),
        "arm": {k: float(arm.get(k, getattr(geom, k))) for k, *_ in DIMENSIONS}
        | {"drop_tilt_deg": float(arm.get("drop_tilt_deg", 0.0)),
           "clearance": float(arm.get("clearance", 0.15)),
           "joints": {k: {f: arm["joints"][k][f] for f in ("min", "max", "park", "zero",
                                                           "direction")}
                      for k in JOINTS},
           "obstacles": arm.get("obstacles") or []},
        "products": {str(k): v for k, v in (cfg.get("products") or {}).items()},
        "outlet": {"marker_radius": outlet.get("marker_radius", 0.125),
                   "marker_offset": outlet.get("marker_offset", 0.15),
                   "pipe_radius": outlet.get("pipe_radius", 0.06)},
        "commissioning": {k: cfg.get("commissioning", {}).get(k)
                          for k in ("workspace_min", "workspace_max", "step")},
        "drives": {k: (cfg.get("drives") or {}).get(k) or {} for k in JOINTS},
        "dimensions": [{"key": k, "text": t, "min": lo, "max": hi} for k, t, lo, hi in DIMENSIONS],
    }


def _arm(data: dict) -> dict:
    a = data["arm"]
    arm = {k: float(a[k]) for k, *_ in DIMENSIONS}
    arm["drop_tilt_deg"] = float(a.get("drop_tilt_deg") or 0.0)
    arm["clearance"] = float(a["clearance"])
    arm["joints"] = {k: {"min": float(j["min"]), "max": float(j["max"]), "park": float(j["park"]),
                         "zero": float(j["zero"]), "direction": int(j["direction"])}
                     for k, j in a["joints"].items()}
    arm["obstacles"] = list(a.get("obstacles") or [])
    return arm


def preview(data: dict) -> dict:
    """Plausibilitätsprüfung, Kennzahlen und Geometrie für die Ansichten."""
    try:
        arm = _arm(data)
        geom = ArmGeometry(**arm)
    except (KeyError, TypeError, ValueError) as e:
        return {"ok": False, "problems": [f"Eingabe unvollständig oder ungültig: {e}"]}
    problems = validate(geom)
    out = {"ok": not problems, "problems": problems,
           "obstacles": [obstacle_for_view(o) for o in geom.obstacles],
           "ground_z": -geom.base_height}
    lo, hi = geom.bounds
    if np.all(hi > lo):
        grid = np.stack(np.meshgrid(*[np.linspace(a, b, 13) for a, b in zip(lo, hi, strict=True)],
                                    indexing="ij"), -1).reshape(-1, 3)
        tips = np.array([forward(geom, q)[-1] for q in grid])
        r = np.hypot(tips[:, 0], tips[:, 1])
        out["reach"] = [round(float(r.min()), 3), round(float(r.max()), 3)]
        out["height"] = [round(float(tips[:, 2].min() + geom.base_height), 2),
                         round(float(tips[:, 2].max() + geom.base_height), 2)]
        out["tips"] = tips[:: max(1, len(tips) // 400)].round(3).tolist()
    out["zero"] = forward(geom, np.zeros(3)).round(4).tolist()
    out["park"] = forward(geom, geom.park).round(4).tolist()
    ws = data.get("commissioning") or {}
    if ws.get("workspace_min") and ws.get("workspace_max"):
        out["workspace"] = [ws["workspace_min"], ws["workspace_max"]]
    drives = Drives.from_config(data.get("drives"))
    if drives.configured:
        out["drive_speed"] = {k: round(d.speed_max, 2) for k, d in drives.axes.items()}
    return out


def _clean_drives(drives: dict | None) -> dict:
    out = {}
    for k, d in (drives or {}).items():
        entry = {f: d[f] for f in DRIVE_FIELDS if f in d and d[f] not in ("", None)}
        if entry:
            out[k] = entry
    return out


def station_yaml(data: dict, folder: Path, name: str) -> str:
    path = folder / f"{name}.yaml"
    keep = {}
    if path.exists():  # eigene Abschnitte der Datei (ohne extends-Basis) erhalten
        keep = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    base = load_config(path if path.exists() else ANLAGEN / "beispiel.yaml")
    arm = _arm(data)
    extra_arm = dict(keep.get("arm") or {})
    extra_arm["drop_tilt_deg"] = arm.pop("drop_tilt_deg")
    if not extra_arm["drop_tilt_deg"]:
        extra_arm.pop("drop_tilt_deg")
    keep["arm"] = extra_arm
    drives = _clean_drives(data.get("drives"))
    if drives:
        keep["drives"] = drives
    else:
        keep.pop("drives", None)
    meta = {"anlage": data["meta"].get("anlage") or name, "name": data["meta"].get("name") or "–",
            "datum": f"{date.today():%d.%m.%Y}"}
    ws = dict(data["commissioning"])
    ws["step"] = ws.get("step") or 0.2
    extends = Path(os.path.relpath(ANLAGEN.parent / "default.yaml", folder)).as_posix()
    return render(meta, data["plc_url"], base["calibration"]["matrix"], arm,
                  {k if not str(k).isdigit() else int(k): v for k, v in data["products"].items()},
                  ws, extends, data["outlet"], keep)


def save_station(data: dict, name: str, folder: Path = ANLAGEN,
                 backup: Path = BACKUP) -> Path:
    if not NAME.match(name):
        raise ValueError("Name nur aus Buchstaben, Ziffern, _ und - (max. 60 Zeichen)")
    text = station_yaml(data, folder, name)
    path = folder / f"{name}.yaml"
    if path.exists():
        backup.mkdir(parents=True, exist_ok=True)
        (backup / f"{name}_{datetime.now():%Y%m%d_%H%M%S}.yaml").write_text(
            path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(text, encoding="utf-8")
    load_config(path)  # muss wieder lesbar sein
    return path


def commissioning(data: dict, name: str, folder: Path = ANLAGEN) -> dict:
    """Inbetriebnahmeprüfung mit den Formularwerten (ohne zu speichern)."""
    tmp = folder / f".pruefung_{threading.get_ident()}.yaml"
    try:
        tmp.write_text(station_yaml(data, folder, name if NAME.match(name) else "neu"),
                       encoding="utf-8")
        buf = io.StringIO()
        ok = commissioning_check(load_config(tmp), f"{name}.yaml (nicht gespeichert)", out=buf)
        return {"ok": ok, "report": buf.getvalue()}
    finally:
        tmp.unlink(missing_ok=True)


def read_plc(url: str) -> list[float]:
    from verladearm_vision.calibrate import read_plc_angles

    plc = dict(load_config(ANLAGEN / "beispiel.yaml")["plc"], url=url)
    return [round(v, 2) for v in read_plc_angles(plc)]


def make_handler(folder: Path = ANLAGEN, backup: Path = BACKUP):
    page = resources.files("verladearm_vision.konfigurator").joinpath("index.html").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body, status: int = 200, ctype: str = "application/json"):
            if not isinstance(body, bytes):
                body = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(page, ctype="text/html; charset=utf-8")
            elif self.path == "/api/files":
                self._send({"files": list_files(folder)})
            elif self.path.startswith("/api/load?name="):
                name = self.path.split("=", 1)[1]
                if not NAME.match(name):
                    return self._send({"error": "ungültiger Name"}, 400)
                self._send(load_station(name, folder))
            else:
                self._send(b"Nicht gefunden", 404, "text/plain; charset=utf-8")

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                if self.path == "/api/check":
                    self._send(preview(body["data"]))
                elif self.path == "/api/save":
                    path = save_station(body["data"], body["name"], folder, backup)
                    self._send({"ok": True, "path": str(path), "files": list_files(folder)})
                elif self.path == "/api/commissioning":
                    self._send(commissioning(body["data"], body.get("name", "neu"), folder))
                elif self.path == "/api/plc":
                    self._send({"angles": read_plc(body["url"])})
                else:
                    self._send({"error": "unbekannt"}, 404)
            except Exception as e:  # Fehlermeldung im Browser anzeigen
                log.warning("%s: %s", self.path, e)
                self._send({"error": str(e)}, 400)

        def log_message(self, fmt, *args):
            log.debug(fmt, *args)

    return Handler


def main():
    p = argparse.ArgumentParser(description="Konfigurator Verladearm (Browser)")
    p.add_argument("--host", default="127.0.0.1", help="0.0.0.0 = im Netzwerk (ohne Anmeldung!)")
    p.add_argument("--port", type=int, default=8090)
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
    try:
        server = ThreadingHTTPServer((args.host, args.port), make_handler())
    except OSError as e:
        raise SystemExit(f"Port {args.port} ist nicht verfügbar ({e.strerror}). "
                         f"Anderen Port wählen, z. B. --port 8091") from None
    shown = args.host if args.host != "0.0.0.0" else "<IP dieses Rechners>"
    log.info("Konfigurator: http://%s:%d  (Anlagendateien: %s)", shown, args.port, ANLAGEN)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Beendet")


if __name__ == "__main__":
    main()
