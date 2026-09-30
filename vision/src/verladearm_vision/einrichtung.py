"""Ersteinrichtung eines Verladearms: Anlagendatei im Dialog anlegen oder ändern.

    python -m verladearm_vision.einrichtung --name lich_station3
    python -m verladearm_vision.einrichtung --name lich_station3 --from-plc   # Servowerte lesen

Fragt Maße, Servoachsen, Hindernisse, Produkte und Arbeitsraum Schritt für Schritt ab, prüft jeden
Wert auf Plausibilität und schreibt `vision/config/anlagen/<name>.yaml`. Gibt es die Datei schon,
sind ihre Werte die Vorschläge (Enter übernimmt). Danach folgen Kalibrierung und
Inbetriebnahmeprüfung (docs/inbetriebnahme.md).
"""

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import yaml

from verladearm_vision.config import load_config
from verladearm_vision.kinematics import JOINTS, ArmGeometry, forward, validate

ANLAGEN = Path(__file__).resolve().parents[2] / "config" / "anlagen"

# (Schlüssel, Frage, kleinster, größter plausibler Wert) – Maße in m
DIMENSIONS = [
    ("base_height", "Höhe Rohrmitte innerer Ausleger an der Achse J1 über Fahrbahn "
                    "(Standfläche Tankwagen)", 2.0, 12.0),
    ("inner_length", "Innerer Ausleger: Achse J1 bis Mitte Winkel nach unten", 0.3, 10.0),
    ("incline_deg", "Festes Gefälle des inneren Auslegers [Grad, nach unten positiv]", -15.0, 15.0),
    ("drop", "Fallrohr: Winkel nach unten bis Mitte Winkel nach rechts (Achse J2)", 0.05, 3.0),
    ("offset_right", "Winkel nach rechts bis Mitte Winkel nach vorne (Achse J3)", 0.05, 2.0),
    ("outer_length", "Äußerer Ausleger: Winkel nach vorne bis Mitte Winkel nach links", 0.3, 10.0),
    ("offset_left", "Winkel nach links bis freies Drehgelenk J4", 0.05, 2.0),
    ("outlet_length", "Auslass: J4 bis Auslassende", 0.2, 4.0),
]
JOINT_TEXT = {"q1": "J1 (Drehen am Haltepunkt)", "q2": "J2 (Drehen am Fallrohr)",
              "q3": "J3 (Ausleger heben/senken)"}
DIRECTION_TEXT = {"q1": "nach links (von oben gesehen gegen den Uhrzeigersinn)",
                  "q2": "nach links (von oben gesehen gegen den Uhrzeigersinn)",
                  "q3": "nach oben (Ausleger heben)"}


def parse_float(text: str) -> float:
    return float(text.strip().replace(",", "."))


def larger_than(lo):
    return lambda v: (None if all(b > a for a, b in zip(lo, v, strict=True))
                      else "jeder Wert muss größer als MIN sein")


def parse_vec(text: str) -> list:
    parts = text.replace(";", " ").split()
    if len(parts) != 3:
        raise ValueError("drei Werte x y z erwartet")
    return [parse_float(p) for p in parts]


def fmt(v) -> str:
    if isinstance(v, (list, tuple)):
        return " ".join(fmt(x) for x in v)
    return f"{v:g}" if isinstance(v, float) else str(v)


class Dialog:
    """Fragen und Antworten über Konsole (austauschbar für Tests)."""

    def __init__(self, input_fn=input, print_fn=print):
        self.input, self.print = input_fn, print_fn

    def ask(self, question: str, default=None, parse=str, check=None):
        hint = f" [{fmt(default)}]" if default is not None else ""
        while True:
            text = self.input(f"  {question}{hint}: ").strip()
            if not text and default is not None:
                return default
            try:
                value = parse(text)
                if check and (msg := check(value)):
                    raise ValueError(msg)
                return value
            except ValueError as e:
                self.print(f"    ⚠️  {e or 'ungültige Eingabe'}")

    def number(self, question: str, default=None, lo=None, hi=None) -> float:
        def check(v):
            if (lo is not None and v < lo) or (hi is not None and v > hi):
                return f"unplausibel, erwartet {fmt(lo)} … {fmt(hi)}"
        return self.ask(question, default, parse_float, check)

    def yes(self, question: str, default=False) -> bool:
        ans = self.ask(question + " (j/n)", "j" if default else "n",
                       check=lambda v: None if v.lower() in ("j", "n") else "j oder n")
        return ans.lower() == "j"

    def step(self, title: str, text: str = ""):
        self.print(f"\n== {title} ==")
        if text:
            self.print(text)


def ask_arm(d: Dialog, cur: dict) -> dict:
    d.step("1. Maße des Arms [m]", "Immer Rohrmitte zu Rohrmitte bzw. Gelenkachse zu Gelenkachse "
           "messen, nie Außenkanten.\nBei 90°-Winkeln zählt der Schnittpunkt der beiden "
           "Rohrmittellinien (Skizze: docs/inbetriebnahme.md).")
    return {k: d.number(q, cur.get(k), lo, hi) for k, q, lo, hi in DIMENSIONS}


def ask_joints(d: Dialog, cur: dict, read_angles=None) -> dict:
    d.step("2. Servoachsen [Servo-Grad, wie am Antrieb angezeigt]")
    joints = {k: dict(cur.get(k, {})) for k in JOINTS}
    known = set()  # Drehrichtung aus der SPS ermittelt
    if read_angles:
        d.ask("Arm im Handbetrieb in NULLSTELLUNG fahren: beide Ausleger gestreckt nach vorne, "
              "äußerer Ausleger waagerecht. Dann Enter", "")
        for k, v in zip(JOINTS, read_angles(), strict=True):
            joints[k]["zero"] = round(v, 2)
        d.print("    Nullstellung gelesen: " + fmt([joints[k]["zero"] for k in JOINTS]))
        for i, k in enumerate(JOINTS):
            before = read_angles()[i]
            d.ask(f"{JOINT_TEXT[k]} ein Stück {DIRECTION_TEXT[k]} fahren, dann Enter", "")
            delta = read_angles()[i] - before
            if abs(delta) < 0.5:
                d.print("    ⚠️  kaum Bewegung erkannt, bitte Drehrichtung eingeben")
            else:
                joints[k]["direction"] = 1 if delta > 0 else -1
                known.add(k)
                d.print(f"    Drehrichtung {joints[k]['direction']:+d}")
    for k in JOINTS:
        j = joints[k]
        d.print(f"  {JOINT_TEXT[k]}")
        if not read_angles:
            j["zero"] = d.number("  Servowert in Nullstellung (Ausleger gestreckt nach vorne)",
                                 j.get("zero", 0.0), -720, 720)
        if k not in known:
            j["direction"] = int(d.ask(f"  Drehrichtung: +1, wenn steigender Servowert "
                                       f"{DIRECTION_TEXT[k]} dreht, sonst -1",
                                       j.get("direction", 1), int,
                                       lambda v: None if v in (1, -1) else "+1 oder -1"))
        j["min"] = d.number("  freigegebener Bereich MIN (nicht der mechanische Anschlag)",
                            j.get("min"), -720, 720)
        j["max"] = d.number("  freigegebener Bereich MAX", j.get("max"), j["min"] + 1, 720)
    if read_angles:
        d.ask("Arm in PARKSTELLUNG fahren, dann Enter", "")
        for k, v in zip(JOINTS, read_angles(), strict=True):
            joints[k]["park"] = round(v, 2)
        d.print("    Parkstellung gelesen: " + fmt([joints[k]["park"] for k in JOINTS]))
    for k in JOINTS:
        j = joints[k]
        j["park"] = d.number(f"  {JOINT_TEXT[k]}: Servowert in Parkstellung", j.get("park"),
                             j["min"], j["max"])
    return {k: {f: joints[k][f] for f in ("min", "max", "park", "zero", "direction")}
            for k in JOINTS}


def ask_obstacles(d: Dialog, cur: list, clearance: float,
                  base_height: float) -> tuple[list, float]:
    d.step("3. Hindernisse im Schwenkbereich", "Armbasis-Koordinaten in m: Ursprung auf Achse J1, "
           "x nach vorne, y nach links, z nach oben. Großzügig umschließen.")
    out = []
    for o in cur:
        if d.yes(f"Vorhandenes Hindernis „{o.get('name')}“ behalten?", True):
            out.append(o)
    while d.yes("Weiteres Hindernis erfassen?"):
        name = d.ask("Bezeichnung", check=lambda v: None if v else "Name angeben")
        if d.ask("Form: q = Quader, z = senkrechter Zylinder (Stütze, Mast)", "q",
                 check=lambda v: None if v in ("q", "z") else "q oder z") == "q":
            lo = d.ask("Ecke MIN x y z", parse=parse_vec)
            hi = d.ask("Ecke MAX x y z", parse=parse_vec, check=larger_than(lo))
            out.append({"name": name, "min": lo, "max": hi})
        else:
            x, y = d.ask("Mitte x y", parse=lambda t: parse_vec(t + " 0")[:2])
            z0 = d.number("Unterkante z (Fahrbahn = -Höhe J1)", -base_height)
            z1 = d.number("Oberkante z", 1.0, z0 + 0.01)
            r = d.number("Radius", 0.15, 0.01, 5)
            out.append({"name": name, "form": "zylinder", "p0": [x, y, (z0 + z1) / 2],
                        "axis": [0, 0, 1], "radius": r, "half_length": (z1 - z0) / 2})
    clearance = d.number("Mindestabstand Rohrachse zu Hindernissen [m]", clearance, 0.05, 1.0)
    return out, clearance


def ask_products(d: Dialog, cur: dict) -> dict:
    d.step("4. Produkte (Eintauchtiefe je ProductId der SPS) [m]")
    default = (cur.get("default") or {}).get("insertion_depth", 0.4)
    out = {"default": {"insertion_depth": d.number("Eintauchtiefe Standard", default, 0.05, 3)}}
    for key, entry in cur.items():
        if key != "default" and d.yes(f"Produkt {key} „{entry.get('name', '')}“ behalten?",
                                      True):
            out[key] = entry
    while d.yes("Weiteres Produkt erfassen?"):
        pid = d.ask("ProductId", parse=int, check=lambda v: None if v > 0 else "> 0")
        name = d.ask("Bezeichnung", "")
        out[pid] = {"name": name, "insertion_depth": d.number("Eintauchtiefe", default, 0.05, 3)}
    return out


def ask_outlet(d: Dialog, cur: dict) -> dict:
    d.step("5. Referenz am Auslass (Nachmessen und Kalibrierung)",
           "Von oben sichtbare runde Scheibe oder ein Flansch am Auslassrohr, rechtwinklig und "
           "mittig zum Rohr.")
    dia = d.number("Außendurchmesser Markierungsscheibe bzw. Flansch [m]",
                   round(2 * (cur.get("marker_radius") or 0.125), 3), 0.15, 0.45)
    off = d.number("Oberkante Referenz bis unterster Punkt Auslass [m]",
                   cur.get("marker_offset", 0.15), 0.03, 1.5)
    return {"marker_radius": round(dia / 2, 4), "marker_offset": off}


def ask_workspace(d: Dialog, cur: dict) -> dict:
    d.step("6. Arbeitsraum", "Bereich, in dem die Oberkante der Domöffnung bei dieser Station "
           "liegen kann (alle Fahrzeuge, Abstellpositionen), Armbasis-Koordinaten in m.")
    lo = d.ask("MIN x y z", cur.get("workspace_min"), parse_vec)
    hi = d.ask("MAX x y z", cur.get("workspace_max"), parse_vec, larger_than(lo))
    return {"workspace_min": lo, "workspace_max": hi, "step": cur.get("step", 0.2)}


def summary(arm: dict) -> list[str]:
    """Kennzahlen zur Kontrolle: Reichweite und Höhen des Auslassendes."""
    geom = ArmGeometry(**arm)
    lo, hi = geom.bounds
    grid = np.stack(np.meshgrid(*[np.linspace(a, b, 15) for a, b in zip(lo, hi, strict=True)],
                                indexing="ij"), -1).reshape(-1, 3)
    tips = np.array([forward(geom, q)[-1] for q in grid])
    r = np.hypot(tips[:, 0], tips[:, 1])
    park = forward(geom, geom.park)[-1]
    return [f"Reichweite Auslassende: {r.min():.2f} … {r.max():.2f} m von Achse J1",
            f"Höhe Auslassende über Fahrbahn: {tips[:, 2].min() + geom.base_height:.2f} … "
            f"{tips[:, 2].max() + geom.base_height:.2f} m",
            f"Auslassende in Parkstellung: x {park[0]:.2f}, y {park[1]:.2f}, "
            f"z {park[2]:.2f} m (Armbasis)"]


def _flow(v) -> str:
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {_flow(x)}" for k, x in v.items()) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_flow(x) for x in v) + "]"
    if isinstance(v, str):
        return v if v and all(c not in v for c in ":#{}[],'\"") else f'"{v}"'
    return fmt(round(v, 4) if isinstance(v, float) else v)


KNOWN = {"extends", "plc", "calibration", "arm", "products", "outlet", "commissioning"}
ARM_KNOWN = {k for k, *_ in DIMENSIONS} | {"joints", "obstacles", "clearance"}


def render(meta: dict, plc_url: str, calibration: list, arm: dict, products: dict,
           workspace: dict, extends: str = "../default.yaml", outlet: dict | None = None,
           keep: dict | None = None) -> str:
    """Anlagendatei als YAML mit Erläuterungen. `keep`: weitere Abschnitte der bisherigen Datei
    (z. B. drives, scene), die der Dialog nicht abfragt – sie bleiben unverändert erhalten."""
    keep = keep or {}
    extra_arm = {k: v for k, v in (keep.get("arm") or {}).items() if k not in ARM_KNOWN}
    others = {k: v for k, v in keep.items() if k not in KNOWN}
    """Anlagendatei als YAML mit Erläuterungen."""
    lines = [
        "# Anlagenparameter Verladearm (angelegt mit python -m verladearm_vision.einrichtung)",
        "# Ablauf und Bedeutung der Werte: docs/inbetriebnahme.md",
        "#",
        f"# Anlage:            {meta['anlage']}",
        f"# Inbetriebnahme:    {meta['datum']}, {meta['name']}",
        "# Freigabe:          offen",
        "",
        f"extends: {extends}",
        "",
        "plc:",
        f"  url: {plc_url}",
        "",
        "calibration:",
        "  # Sensor -> Armbasis (4x4, m); Ergebnis von python -m verladearm_vision.calibrate",
        "  matrix:",
        *[f"    - {_flow(row)}" for row in calibration],
        "",
        "arm:",
        "  # Maße von Gelenkachse zu Gelenkachse bzw. Rohrmitte [m]",
        *[f"  {k}: {fmt(float(arm[k]))}" for k, *_ in DIMENSIONS],
        "  # Servoachsen in Servo-Grad wie am Antrieb angezeigt (zero = Ausleger gestreckt nach",
        "  # vorne; direction +1 = steigender Servowert dreht nach links bzw. hebt)",
        "  joints:",
        *[f"    {k}: {_flow(arm['joints'][k])}" for k in JOINTS],
        "  # Sperrbereiche, Armbasis-Koordinaten [m] (Ursprung Achse J1, x vorne, y links, z oben)",
        "  obstacles:" + ("" if arm["obstacles"] else " []"),
        *[f"    - {_flow(o)}" for o in arm["obstacles"]],
        f"  clearance: {fmt(float(arm['clearance']))}",
        *[f"  {k}: {_flow(v)}" for k, v in extra_arm.items()],
        "",
        *(["# Referenz am Auslass (Markierungsscheibe oder Flansch) [m]",
           "outlet:",
           f"  marker_radius: {fmt(float(outlet['marker_radius']))}   # halber Außendurchmesser",
           f"  marker_offset: {fmt(float(outlet['marker_offset']))}   # Oberkante bis Auslassende",
           ""] if outlet else []),
        "# Eintauchtiefe je ProductId [m]",
        "products:",
        *[f"  {k}: {_flow(v)}" for k, v in products.items()],
        "",
        "commissioning:",
        "  # Bereich, in dem die Domöffnung bei dieser Station liegen kann (Armbasis, m)",
        f"  workspace_min: {_flow(workspace['workspace_min'])}",
        f"  workspace_max: {_flow(workspace['workspace_max'])}",
        f"  step: {fmt(float(workspace['step']))}",
        "",
    ]
    if others:  # unverändert übernommen
        lines += ["# Weitere Abschnitte (vom Dialog nicht abgefragt, unverändert übernommen)",
                  yaml.safe_dump(others, allow_unicode=True, sort_keys=False, width=100)]
    return "\n".join(lines)


def python_cmd() -> str:
    """So, wie der Befehl im Terminal einzugeben ist (z. B. .venv/bin/python)."""
    exe = Path(sys.executable)
    try:
        return exe.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return str(exe)


def run(d: Dialog, target: Path, reader=None) -> Path | None:
    """`reader(plc_cfg)` liefert die Servo-Istwinkel J1–J3 (z. B. calibrate.read_plc_angles);
    None = Werte werden eingegeben."""
    base = target if target.exists() else ANLAGEN / "beispiel.yaml"
    cur = load_config(base)
    d.print(f"Ersteinrichtung Verladearm → {target}")
    d.print("Vorschläge in [Klammern] stammen aus "
            + ("der vorhandenen Anlagendatei." if target.exists() else "der Vorlage beispiel.yaml "
               "und müssen vor Ort ersetzt werden."))
    d.print("Enter übernimmt den Vorschlag, Dezimalkomma ist erlaubt.")

    d.step("0. Anlage")
    meta = {"anlage": d.ask("Anlage / Station", target.stem),
            "name": d.ask("Name Inbetriebnehmer", "–"),
            "datum": f"{date.today():%d.%m.%Y}"}
    plc_url = d.ask("OPC-UA-Adresse der SPS", cur["plc"]["url"])
    read_angles = None
    if reader:
        plc_cfg = dict(cur["plc"], url=plc_url)
        read_angles = lambda: reader(plc_cfg)  # noqa: E731

    cur_arm = cur.get("arm", {})
    arm = ask_arm(d, cur_arm)
    arm["joints"] = ask_joints(d, cur_arm.get("joints", {}), read_angles)
    arm["obstacles"], arm["clearance"] = ask_obstacles(d, cur_arm.get("obstacles") or [],
                                                       cur_arm.get("clearance", 0.15),
                                                       arm["base_height"])
    products = ask_products(d, cur.get("products") or {})
    outlet = ask_outlet(d, cur.get("outlet", {}))
    workspace = ask_workspace(d, cur.get("commissioning", {}))

    d.step("7. Kontrolle")
    problems = validate(ArmGeometry(**arm))
    for p in problems:
        d.print(f"  ❌ {p}")
    if not problems:
        for line in summary(arm):
            d.print(f"  {line}")
        d.print("  Bitte mit der realen Anlage vergleichen.")
    if not d.yes("Anlagendatei schreiben?", not problems):
        d.print("Nicht gespeichert.")
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    extends = Path(os.path.relpath(ANLAGEN.parent / "default.yaml", target.parent)).as_posix()
    keep = {}
    if target.exists():  # eigene Abschnitte der Datei (ohne extends-Basis) erhalten
        keep = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    target.write_text(render(meta, plc_url, cur["calibration"]["matrix"], arm, products,
                             workspace, extends, outlet, keep), encoding="utf-8")
    py = python_cmd()
    d.print(f"\nGespeichert: {target}\nNächste Schritte (docs/inbetriebnahme.md):\n"
            f"  1. Prüfung:       {py} -m verladearm_vision.commissioning --config {target}\n"
            f"  2. Kalibrierung:  {py} -m verladearm_vision.calibrate --config {target} "
            "--from-plc\n"
            "                   (braucht SPS, Sensor und Arm; Probelauf ohne Hardware: --sim)\n"
            f"  3. Sichtprüfung:  {py} -m verladearm_vision.viewer --opcua --config {target}")
    return target


def main():
    p = argparse.ArgumentParser(description="Ersteinrichtung Verladearm (Anlagendatei)")
    p.add_argument("--name", required=True, help="Dateiname, z. B. lich_station3")
    p.add_argument("--dir", default=str(ANLAGEN), help="Ordner der Anlagendateien")
    p.add_argument("--from-plc", action="store_true",
                   help="Nullstellung, Drehrichtung und Parkstellung aus der SPS lesen")
    args = p.parse_args()
    target = Path(args.dir) / f"{args.name}.yaml"
    reader = None
    if args.from_plc:
        from verladearm_vision.calibrate import read_plc_angles as reader
    try:
        sys.exit(0 if run(Dialog(), target, reader) else 1)
    except (KeyboardInterrupt, EOFError):
        print("\nAbgebrochen, nichts gespeichert.")
        sys.exit(1)


if __name__ == "__main__":
    main()
