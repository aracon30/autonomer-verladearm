"""Fasst Aufzeichnungen des Vision-Dienstes als CSV zusammen (eine Zeile je Auftrag).

    python tools/auswertung.py --dir data/aufzeichnung > auswertung.csv

Semikolon-getrennt mit Dezimalkomma, direkt in Excel öffnen.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

COLUMNS = ["zeit", "anlage", "job", "produkt", "ok", "fehler", "ziel_x", "ziel_y", "ziel_z",
           "durchmesser", "confidence", "korrektur_x", "korrektur_y", "stuetzpunkte",
           "aufnahme_ms", "gesamt_ms", "ordner"]


def rows(folder: Path):
    for f in sorted(folder.glob("**/ergebnis.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        a, e, i = d["auftrag"], d["ergebnis"], d.get("info", {})
        yield {
            "zeit": d["zeit"], "anlage": d.get("anlage", ""), "job": a.get("job"),
            "produkt": a.get("product_id"), "ok": e["ok"], "fehler": e["error_code"],
            "ziel_x": e["target_mm"][0], "ziel_y": e["target_mm"][1], "ziel_z": e["target_mm"][2],
            "durchmesser": e["diameter_mm"], "confidence": e["confidence"],
            "korrektur_x": e["correction_mm"][0], "korrektur_y": e["correction_mm"][1],
            "stuetzpunkte": len(e["waypoints"]), "aufnahme_ms": i.get("aufnahme_ms"),
            "gesamt_ms": i.get("gesamt_ms"), "ordner": str(f.parent),
        }


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dir", default="data/aufzeichnung")
    args = p.parse_args()
    w = csv.DictWriter(sys.stdout, COLUMNS, delimiter=";")
    w.writeheader()
    for r in rows(Path(args.dir)):
        w.writerow({k: str(v).replace(".", ",") if isinstance(v, float) else v
                    for k, v in r.items()})


if __name__ == "__main__":
    main()
