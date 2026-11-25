"""Drehteller-Scan: Kamera steht fest, das Objekt (z. B. ein Filter) dreht sich auf einem
Drehteller.
In regelmäßigen Winkelschritten wird aufgenommen; am Ende entsteht eine 3D-Punktwolke des ganzen
Objekts zum Nachmessen (Betrachter, ReCap/Inventor, STL).

Aufnehmen (Kamera wie beim Kameratest angeschlossen):

    .venv\\Scripts\\python tools\\drehteller.py aufnahme --name Filter1 --schritt 15

    Optional zuerst den leeren Teller aufnehmen (verbessert das Freistellen). Dann je Schritt den
    Teller um den Winkel weiterdrehen und Enter drücken (q = Ende). Die Bilder landen in
    data\\drehteller\\Filter1\\000,0.npy, 015,0.npy, … (Dateiname = Winkel).

Zusammensetzen:

    .venv\\Scripts\\python tools\\drehteller.py zusammensetzen data\\drehteller\\Filter1 [--stl]

    → Filter1_gesamt.npy/.ply/.pts (+ .stl) im selben Ordner und die Maße (Höhe entlang der
    Drehachse, größter Durchmesser).

Verfahren: Hintergrund entfernen (Vergleich mit dem leeren Teller, sonst Boden-Ebene weg und die
Punktgruppe in Bildmitte behalten). Die Drehachse wird aus den Bildern bestimmt (Lot auf den Boden,
Lage so, dass die um die bekannten Winkel zurückgedrehten Bilder am besten übereinanderliegen) –
das klappt auch bei drehsymmetrischen Teilen wie Filtergehäusen. Dann alle Bilder um ihren Winkel
zurückdrehen und vereinen.
Tipps: Schritte 10–20°, Winkel am Teller genau einstellen (Skala), Kamera 30–45° schräg von oben
(sonst fehlt die Oberseite), 1–3 m Abstand, Boden im Bild, niemand im Bild, Objekt fest auf dem
Teller. Genauigkeit der Kamera ca. 1–2 cm.
"""

import argparse
import re
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).parent))
from npy_zu_ply import schreibe_ply, schreibe_pts, schreibe_stl  # noqa: E402


# --- Hilfen ---------------------------------------------------------------------------------
def voxel(p: np.ndarray, groesse: float) -> np.ndarray:
    """Ausdünnen: je Würfel der Kantenlänge `groesse` ein Punkt (Mittelwert aller Spalten)."""
    if len(p) == 0:
        return p
    _, inv = np.unique(np.floor(p[:, :3] / groesse).astype(np.int64), axis=0, return_inverse=True)
    inv = inv.ravel()
    out = np.zeros((inv.max() + 1, p.shape[1]))
    np.add.at(out, inv, p)
    return out / np.bincount(inv)[:, None]


def ebene(p: np.ndarray, tol: float = 0.015, versuche: int = 300, seed: int = 0):
    """Größte Ebene (RANSAC): (Normale, Abstand d mit n·x = d, Maske der Ebenenpunkte)."""
    rng = np.random.default_rng(seed)
    best = (None, 0.0, np.zeros(len(p), bool))
    for _ in range(versuche):
        a, b, c = p[rng.choice(len(p), 3, replace=False)]
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-9:
            continue
        n /= np.linalg.norm(n)
        m = np.abs(p @ n - n @ a) < tol
        if m.sum() > best[2].sum():
            best = (n, float(n @ a), m)
    return best


def ausreisser_weg(p: np.ndarray, k: int = 8, faktor: float = 2.5) -> np.ndarray:
    """Einzelne Streupunkte (fliegende Pixel an Kanten) entfernen."""
    if len(p) <= k:
        return p
    d, _ = cKDTree(p[:, :3]).query(p[:, :3], k=k + 1)
    m = d[:, 1:].mean(axis=1)
    return p[m < m.mean() + faktor * m.std()]


def objekt_freistellen(bild: np.ndarray, leer: np.ndarray | None, boden_n: np.ndarray,
                       boden_d: float, abstand: float = 0.03) -> np.ndarray:
    """Objekt aus einem Bild holen: ohne Hintergrund (leerer Teller) bzw. ohne Boden-Ebene, dann die
    zusammenhängende Punktgruppe, die am ehesten in Bildmitte und nah an der Kamera liegt."""
    p = bild
    if leer is not None:
        d, _ = cKDTree(leer[:, :3]).query(p[:, :3], distance_upper_bound=0.015)
        p = p[~np.isfinite(d)]
    p = p[np.abs(p[:, :3] @ boden_n - boden_d) > 0.015]  # Boden weg
    if len(p) < 50:
        return p
    paare = cKDTree(p[:, :3]).query_pairs(abstand, output_type="ndarray")
    g = coo_matrix((np.ones(len(paare)), (paare[:, 0], paare[:, 1])), shape=(len(p), len(p)))
    n, lab = connected_components(g, directed=False)
    best, wert = 0, -1.0
    for k in range(n):
        m = lab == k
        if m.sum() < 50:
            continue
        c = p[m, :3].mean(axis=0)
        w = m.sum() / (1 + np.hypot(c[0], c[1]) / max(c[2], 0.1)) / max(c[2], 0.3) ** 2
        if w > wert:
            best, wert = k, w
    return p[lab == best]


def drehung(achse: np.ndarray, winkel: float) -> np.ndarray:
    a = achse / np.linalg.norm(achse)
    k = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(winkel) * k + (1 - np.cos(winkel)) * k @ k


def zurueckdrehen(p: np.ndarray, punkt, achse, winkel: float) -> np.ndarray:
    q = p.copy()
    q[:, :3] = (p[:, :3] - punkt) @ drehung(achse, -winkel).T + punkt
    return q


def masse(p: np.ndarray, punkt: np.ndarray, achse: np.ndarray) -> dict:
    """Höhe entlang der Drehachse und größter Durchmesser um die Achse [m]."""
    rel = p[:, :3] - punkt
    h = rel @ achse
    radial = np.linalg.norm(rel - np.outer(h, achse), axis=1)
    lo, hi = np.percentile(h, [0.5, 99.5])
    return {"hoehe": float(hi - lo), "durchmesser": float(2 * np.percentile(radial, 99.5))}


# --- Zusammensetzen -------------------------------------------------------------------------
def achse_finden(objekte, winkel, n0):
    """Drehachse (Punkt, Richtung) und Drehsinn so, dass die um ihre Winkel zurückgedrehten Bilder
    am besten auf dem jeweils nächsten liegen. Start: Achse senkrecht zum Boden durch die
    Objektmitte."""
    rng = np.random.default_rng(0)
    proben = [o[rng.choice(len(o), min(len(o), 800), replace=False), :3] for o in objekte]
    baeume = [cKDTree(o[:, :3]) for o in objekte]
    u = np.cross(n0, [1.0, 0, 0] if abs(n0[0]) < 0.9 else [0, 1.0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(n0, u)
    mitte = np.vstack(proben).mean(axis=0)

    def teile(x):
        achse = n0 + x[2] * u + x[3] * v
        return mitte + x[0] * u + x[1] * v, achse / np.linalg.norm(achse)

    def kosten(x, sinn, paare):
        punkt, achse = teile(x)
        e = []
        for i in paare:
            q = zurueckdrehen(proben[i + 1], punkt, achse, sinn * (winkel[i + 1] - winkel[i]))
            d, _ = baeume[i].query(q[:, :3], distance_upper_bound=0.1)
            d = np.where(np.isfinite(d), d, 0.1)
            e.append(np.sort(d)[: int(0.8 * len(d))].mean())  # 80 %: Teilverdeckung erlaubt
        return float(np.mean(e))

    paare = list(range(len(objekte) - 1))
    grob = paare[:: max(1, len(paare) // 6)]
    best = (np.inf, None, 1)
    raster = np.linspace(-0.6, 0.6, 13)  # Achslage ±0,6 m um die Mitte, 10-cm-Raster
    for sinn in (1, -1):
        for a in raster:
            for b in raster:
                k = kosten([a, b, 0, 0], sinn, grob)
                if k < best[0]:
                    best = (k, np.array([a, b, 0.0, 0.0]), sinn)
    _, x0, sinn = best
    fein = paare[:: max(1, len(paare) // 12)]
    schritt = np.diag([0.05, 0.05, 0.03, 0.03])
    erg = minimize(kosten, x0, args=(sinn, fein), method="Nelder-Mead",
                   options={"xatol": 2e-4, "fatol": 1e-6, "maxiter": 400,
                            "initial_simplex": x0 + np.vstack([np.zeros(4), schritt])})
    punkt, achse = teile(erg.x)
    return punkt, achse, sinn, erg.fun


def zusammensetzen(dateien: list[Path], leer: Path | None = None, voxel_m: float = 0.01):
    roh = [np.load(f, allow_pickle=False).astype(float) for f in dateien]
    roh = [voxel(r[np.isfinite(r[:, :3]).all(axis=1)], voxel_m) for r in roh]
    winkel = np.radians([winkel_aus_name(f) for f in dateien])
    ref = voxel(np.load(leer, allow_pickle=False).astype(float), voxel_m) if leer else None
    n0, d0, _ = ebene(ref[:, :3] if ref is not None else roh[0][:, :3])  # Boden
    objekte = [ausreisser_weg(objekt_freistellen(r, ref, n0, d0)) for r in roh]
    if min(len(o) for o in objekte) < 100:
        raise SystemExit("Objekt nicht gefunden: Boden im Bild? Objekt in Bildmitte?")
    punkt, achse, sinn, rest = achse_finden(objekte, winkel, n0)
    teile = [zurueckdrehen(o, punkt, achse, sinn * (w - winkel[0]))
             for o, w in zip(objekte, winkel, strict=True)]
    wolke = ausreisser_weg(voxel(np.vstack(teile), voxel_m / 2))
    info = masse(wolke, punkt, achse) | {"rest": rest, "punkte": len(wolke), "achse": achse,
                                         "achspunkt": punkt}
    return wolke, info


def winkel_aus_name(f: Path) -> float:
    m = re.match(r"(\d+(?:[.,]\d+)?)", f.stem)
    return float(m.group(1).replace(",", ".")) if m else 0.0


# --- Aufnahme -------------------------------------------------------------------------------
def aufnahme(args):
    from verladearm_vision.config import load_config
    from verladearm_vision.konsole import quickedit_aus
    from verladearm_vision.service.main import build_source

    quickedit_aus()
    cfg = load_config(args.config)
    source = build_source(cfg["source"], cfg)
    print("Warte auf die Kamera …")
    for _ in range(60):
        if getattr(source, "ready", True):
            break
        time.sleep(1)
    else:
        sys.exit("Kamera nicht erreichbar: IP, Netzwerkeinstellung und 24 V prüfen.")
    ordner = Path(args.ordner) / args.name
    ordner.mkdir(parents=True, exist_ok=True)

    def speichern(name):
        p = source.grab()
        ir = getattr(source, "last_point_intensity", None)
        if ir is not None and len(ir) == len(p):
            p = np.column_stack([p[:, :3], ir])
        np.save(ordner / name, p.astype(np.float32))
        print(f"  {ordner / name}  ({len(p):,} Punkte)")

    if input("Leeren Teller zuerst aufnehmen? (j = ja, Enter = überspringen): ").strip() == "j":
        speichern("leer.npy")
    winkel = 0.0
    while winkel < 360 - 1e-6:
        e = input(f"Teller auf {winkel:g}° stellen, Enter = Aufnahme, q = Ende: ").strip().lower()
        if e == "q":
            break
        speichern(f"{winkel:05.1f}".replace(".", ",") + ".npy")  # z. B. 015,0.npy
        winkel += args.schritt
    if hasattr(source, "close"):
        source.close()
    print(f"Fertig. Zusammensetzen: python tools/drehteller.py zusammensetzen {ordner}")


def main():
    p = argparse.ArgumentParser(description="Drehteller-Scan aufnehmen bzw. zusammensetzen")
    sub = p.add_subparsers(dest="befehl", required=True)
    a = sub.add_parser("aufnahme")
    a.add_argument("--config", default="vision/config/anlagen/kameratest.yaml")
    a.add_argument("--name", required=True, help="Name des Objekts, z. B. Filter1")
    a.add_argument("--schritt", type=float, default=15.0, help="Winkelschritt in Grad (10–20)")
    a.add_argument("--ordner", default="data/drehteller")
    z = sub.add_parser("zusammensetzen")
    z.add_argument("ordner")
    z.add_argument("--stl", action="store_true", help="zusätzlich ein STL-Netz (grob)")
    z.add_argument("--voxel", type=float, default=0.01, help="Rasterweite [m] (Standard 1 cm)")
    args = p.parse_args()
    if args.befehl == "aufnahme":
        return aufnahme(args)
    ordner = Path(args.ordner)
    dateien = sorted((f for f in ordner.glob("*.npy")
                      if re.match(r"\d", f.name) and "_gesamt" not in f.name),
                     key=winkel_aus_name)
    if len(dateien) < 3:
        sys.exit(f"Mindestens 3 Aufnahmen in {ordner} nötig.")
    leer = ordner / "leer.npy"
    wolke, info = zusammensetzen(dateien, leer if leer.exists() else None, args.voxel)
    basis = ordner / f"{ordner.name}_gesamt"
    np.save(basis.with_suffix(".npy"), wolke.astype(np.float32))
    schreibe_ply(wolke[:, :3], basis.with_suffix(".ply"))
    schreibe_pts(wolke, basis.with_suffix(".pts"))
    if args.stl:
        schreibe_stl(wolke, basis.with_suffix(".stl"))
    print(f"{len(dateien)} Aufnahmen → {info['punkte']:,} Punkte: {basis}.npy/.ply/.pts")
    print(f"Passgenauigkeit: {info['rest'] * 1000:.0f} mm mittlerer Abstand (gut: < 10 mm)")
    print(f"Höhe entlang der Drehachse: {info['hoehe'] * 1000:.0f} mm, "
          f"größter Durchmesser: {info['durchmesser'] * 1000:.0f} mm")


if __name__ == "__main__":
    main()
