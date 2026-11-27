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
from scipy.ndimage import minimum_filter
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
    p = hauptgruppe(p, abstand)
    if leer is None:
        p = teller_weg(p, boden_n, boden_d)
    return p


def hauptgruppe(p: np.ndarray, abstand: float = 0.03) -> np.ndarray:
    """Die zusammenhängende Punktgruppe, die am ehesten in Bildmitte und nah an der Kamera liegt
    (flache Gruppen wie Wände ausgenommen), samt Gruppen in ihrer Nähe."""
    if len(p) < 50:
        return p
    paare = cKDTree(p[:, :3]).query_pairs(abstand, output_type="ndarray")
    g = coo_matrix((np.ones(len(paare)), (paare[:, 0], paare[:, 1])), shape=(len(p), len(p)))
    n, lab = connected_components(g, directed=False)
    gruppen = []
    for k in range(n):
        m = lab == k
        if m.sum() < 30:
            continue
        # flache Gruppen (Wand, Tischplatte, Schrankfront) sind nicht das Objekt
        if m.sum() >= 50 and np.sqrt(np.linalg.eigvalsh(np.cov(p[m, :3].T))[0]) < 0.012:
            continue
        gruppen.append(m)
    if not gruppen:
        return p[:0]

    def wert(m):
        c = p[m, :3].mean(axis=0)
        return m.sum() / (1 + np.hypot(c[0], c[1]) / max(c[2], 0.1)) / max(c[2], 0.3) ** 2

    gruppen.sort(key=wert, reverse=True)
    # Steile Flächen sind aus der Ferne nur lückenhaft erfasst: das Objekt zerfällt dann in
    # mehrere Gruppen. Gruppen in der Nähe (< 8 cm) der gewählten gehören mit dazu.
    auswahl, rest = gruppen[0].copy(), gruppen[1:]
    while rest:
        baum = cKDTree(p[auswahl, :3])
        nah = [m for m in rest
               if np.isfinite(baum.query(p[m, :3], distance_upper_bound=0.08)[0]).any()]
        if not nah:
            break
        for m in nah:
            auswahl |= m
        rest = [m for m in rest if not any(m is x for x in nah)]
    return p[auswahl]


def teller_weg(p: np.ndarray, boden_n: np.ndarray, boden_d: float) -> np.ndarray:
    """Ohne Referenz bleibt die Telleroberfläche am Objekt hängen (sie ist mit ihm verbunden).
    Sie ist die unterste waagerechte Schicht: wenn diese einen großen Teil der Punkte hat, weg."""
    h = p[:, :3] @ boden_n - boden_d
    h = h * np.sign(np.median(h))  # nach oben (vom Boden weg) positiv
    unten = h[h < np.percentile(h, 1) + 0.03]
    schicht = np.abs(h - np.median(unten)) < 0.012
    return p[~schicht] if schicht.mean() > 0.1 else p


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
    # Grundriss (senkrecht zur Achse): kleinstes umschließendes Rechteck → Länge × Breite,
    # sinnvoll für nicht runde Teile (Kastenfilter, Gehäuse mit Stutzen)
    e1 = np.cross(achse, [1.0, 0, 0] if abs(achse[0]) < 0.9 else [0, 1.0, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(achse, e1)
    xy = np.column_stack([rel @ e1, rel @ e2])
    m = np.ones(len(xy), bool)
    for v in (xy[:, 0], xy[:, 1]):  # vereinzelte Ausreißer am Rand ignorieren
        a, b = np.percentile(v, [0.2, 99.8])
        m &= (v >= a) & (v <= b)
    xy = xy[m]
    best = (np.inf, 0.0, 0.0)
    for w in np.radians(np.arange(0, 90, 0.5)):
        c, s_ = np.cos(w), np.sin(w)
        u, v = xy @ [c, s_], xy @ [-s_, c]
        lu, lv = u.max() - u.min(), v.max() - v.min()
        if lu * lv < best[0]:
            best = (lu * lv, max(lu, lv), min(lu, lv))
    return {"hoehe": float(hi - lo), "durchmesser": float(2 * np.percentile(radial, 99.5)),
            "laenge": float(best[1]), "breite": float(best[2])}


# --- Zusammensetzen -------------------------------------------------------------------------
def achse_finden(objekte, winkel, n0, faktor_frei: bool = False):
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
        # Richtung: n0 um u und v gekippt (jede Richtung erreichbar); Achspunkt in der Ebene
        # senkrecht zur aktuellen Achse durch die Objektmitte
        achse = drehung(u, x[2]) @ drehung(v, x[3]) @ n0
        a1 = np.cross(achse, v)
        a1 /= np.linalg.norm(a1)
        a2 = np.cross(achse, a1)
        return mitte + x[0] * a1 + x[1] * a2, achse

    def kosten(x, sinn, paare):
        punkt, achse = teile(x)
        k = x[4] if len(x) > 4 else 1.0  # Faktor auf die Winkel (Drehzahl nur ungefähr bekannt)
        if abs(k - 1) > 0.15:  # Umlaufzeit ist auf ±15 % bekannt; sonst „dreht“ sich nichts mehr
            return 1.0 + abs(k - 1)
        e = []
        for i in paare:
            q = zurueckdrehen(proben[i + 1], punkt, achse, sinn * k * (winkel[i + 1] - winkel[i]))
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
    if faktor_frei:
        x0 = np.append(x0, 1.0)
        schritt = np.diag([0.05, 0.05, 0.03, 0.03, 0.05])
    erg = minimize(kosten, x0, args=(sinn, fein), method="Nelder-Mead",
                   options={"xatol": 2e-4, "fatol": 1e-6, "maxiter": 400,
                            "initial_simplex": x0 + np.vstack([np.zeros(len(x0)), schritt])})
    punkt, achse = teile(erg.x)
    k = float(erg.x[4]) if faktor_frei else 1.0
    return punkt, achse, sinn * k, erg.fun


def ebenen(p: np.ndarray, anzahl: int = 3, min_anteil: float = 0.05) -> list:
    """Die größten Ebenen nacheinander (Normale, d): Kandidaten für den Boden."""
    out, rest = [], p
    for k in range(anzahl):
        if len(rest) < 100:
            break
        n, d, m = ebene(rest, seed=k)
        if n is None or m.sum() < min_anteil * len(p):
            break
        out.append((n, d))
        rest = rest[~m]
    return out


def stillstehend(bilder, winkel, tol: float = 0.03, anteil: float = 0.7,
                 zelle: float = 0.005) -> list:
    """Je Bild: welche Punkte stehen still? Die Kamera steht fest, also wird je Blickrichtung
    (Zelle `zelle` rad) verglichen: Ein Punkt bewegt sich, wenn deutlich weitergedrehte Bilder
    (60–300°) an dieser Stelle dahinter freie Sicht haben (Hintergrund weiter weg). Liegt dort
    dieselbe Fläche oder etwas davor (Verdeckung), passt er zu „still“. Still sind Hintergrund,
    Gehäuse des Drehtischs und Teile, die um die Achse rund sind (Rohr, Teller)."""
    uv = [np.floor(b[:, :2] / b[:, 2:3] / zelle).astype(np.int64) for b in bilder]
    lo = np.min([u.min(axis=0) for u in uv], axis=0)
    hi = np.max([u.max(axis=0) for u in uv], axis=0)
    breite = int(hi[0] - lo[0] + 1)
    groesse = breite * int(hi[1] - lo[1] + 1)
    idx = [(u[:, 1] - lo[1]) * breite + (u[:, 0] - lo[0]) for u in uv]
    tiefe = []
    for b, i in zip(bilder, idx, strict=True):
        t = np.full(groesse, np.inf)
        np.minimum.at(t, i, b[:, 2])
        # Nachbarzellen mitnehmen: kleine Lücken im Bild sind keine „freie Sicht“
        t = minimum_filter(t.reshape(-1, breite), size=3, mode="nearest").ravel()
        tiefe.append(t)
    masken = []
    for k, (b, i) in enumerate(zip(bilder, idx, strict=True)):
        dw = np.degrees(np.abs(np.asarray(winkel) - winkel[k])) % 360
        andere = [j for j in range(len(bilder)) if 60 <= dw[j] <= 300]
        if len(andere) < 3:
            masken.append(np.ones(len(b), bool))
            continue
        andere = andere[:: max(1, len(andere) // 10)]
        frei = np.zeros(len(b))
        gesehen = np.zeros(len(b))
        for j in andere:
            t = tiefe[j][i]
            ok = np.isfinite(t)
            gesehen += ok
            frei += ok & (t > b[:, 2] + tol)
        masken.append(frei < (1 - anteil) * np.maximum(gesehen, 1))
    return masken


def drehsymmetrisch(p: np.ndarray, punkt, achse, baum, tol: float = 0.015) -> np.ndarray:
    """Liegt der Punkt auf einer Fläche, die um die Drehachse rund ist (um ±10/20/30° gedreht
    wieder auf Punkten)? Rohr und Teller ja, Gehäuse des Drehtischs nein. Streng, weil ein Rohr
    ohnehin aus allen Bildern zusammen rundum entsteht; Ränder dürfen ruhig wegfallen."""
    treffer = sum(np.isfinite(baum.query(zurueckdrehen(p, punkt, achse, np.radians(w))[:, :3],
                                         distance_upper_bound=tol)[0])
                  for w in (-30, -20, -10, 10, 20, 30))
    return treffer >= 5


def _ueber_bewegung(roh, winkel, dauerdrehung: bool, radius: float | None):
    """Ohne leeren Teller (Werkstatt, Drehtisch mit Gehäuse): Kamera steht, also ist alles, was
    in weitergedrehten Bildern an derselben Stelle bleibt, Hintergrund, Gehäuse oder rund um die
    Achse. Was sich bewegt (Abzweig, Stutzen), legt die Achse fest – Richtung aus der Kreisbahn
    seines Schwerpunkts, dann fein über das Zurückdrehen. Danach: Teller-Ebene und alles
    darunter weg, Stillstehendes nur, wenn es um die Achse rund ist (Rohr, Flansch).
    None, wenn sich zu wenig bewegt (rein drehsymmetrisches Teil)."""
    winkel = np.asarray(winkel)
    still = stillstehend(roh, winkel)
    bew = [hauptgruppe(r[~m]) for r, m in zip(roh, still, strict=True)]
    idx = [i for i, b in enumerate(bew) if len(b) >= 150]
    if len(idx) < 3:
        return None
    bew, w_b = [bew[i] for i in idx], winkel[idx]
    # Startrichtungen: Lot auf die Kreisbahn des Schwerpunkts und die größten Ebenen (Boden);
    # genommen wird die, mit der die bewegten Teile am besten zurückgedreht übereinanderliegen
    c = np.array([b[:, :3].mean(axis=0) for b in bew])
    _, sv, vt = np.linalg.svd(c - c.mean(axis=0))
    starts = ([vt[2]] if sv[1] > 0.02 else []) + [n for n, _ in ebenen(roh[0][:, :3])]
    if not starts:
        return None
    punkt, achse, sinn, rest = min((achse_finden(bew, w_b, n0, dauerdrehung) for n0 in starts),
                                   key=lambda e: e[3])
    hb = np.concatenate([(b[:, :3] - punkt) @ achse for b in bew])
    rb = np.concatenate([np.linalg.norm(np.cross(b[:, :3] - punkt, achse), axis=1) for b in bew])
    r_max = radius or float(np.percentile(rb, 99.5)) + 0.1

    def lage(r):
        rel = r[:, :3] - punkt
        h = rel @ achse
        return h, np.linalg.norm(rel - np.outer(h, achse), axis=1)

    # Teller: dichteste Schicht senkrecht zur Achse (nahe dem Bewegten). Oben ist die Seite, auf
    # der sich das Bewegte befindet; der Teller und alles darunter (Gehäuse, Boden) fliegt raus.
    hs, rs = zip(*(lage(r) for r in roh), strict=True)
    h_alle = np.concatenate([h[r <= r_max] for h, r in zip(hs, rs, strict=True)])
    lo, hi = np.percentile(hb, [1, 99])
    kand = h_alle[(h_alle > lo - 1.0) & (h_alle < hi + 1.0)]
    grenze = None
    if len(kand) > 100:
        z, k = np.histogram(kand, bins=np.arange(kand.min(), kand.max() + 0.01, 0.01))
        if z.max() > 0.02 * len(h_alle):
            mitte = k[:-1] + 0.005
            oben = 1.0 if np.median(hb) > mitte[z.argmax()] else -1.0
            # unter dem Teller liegt oft eine noch größere Platte (Gehäuse): die oberste dichte
            # Schicht unterhalb des Bewegten ist der Teller
            dicht = (z >= 0.3 * z.max()) & ((mitte - np.median(hb)) * oben < 0)
            teller = float(mitte[dicht][np.argmax(mitte[dicht] * oben)])
            if oben < 0:
                achse, sinn, hs = -achse, -sinn, tuple(-h for h in hs)
                teller = -teller
            grenze = teller + 0.015
    nah = [(r <= r_max) & (h > grenze if grenze is not None else True)
           for h, r in zip(hs, rs, strict=True)]
    baum = cKDTree(np.vstack([r[m & n, :3] for r, m, n in zip(roh, still, nah, strict=True)]))
    objekte = []
    for r, m, n in zip(roh, still, nah, strict=True):
        s = r[m & n]
        s = s[drehsymmetrisch(s, punkt, achse, baum, tol=0.02)]
        objekte.append(ausreisser_weg(np.vstack([r[~m & n], s])))
    if grenze is not None:
        # Telleroberfläche je Bild als Ebene nachmessen (der Teller taumelt etwas) und alles bis
        # 2 cm darüber und darunter weg
        neu = []
        for o in objekte:
            h, r = lage(o)
            m = (np.abs(h - grenze) < 0.06) & (r > 0.5 * r_max)
            if m.sum() > 200:
                n, d, _ = ebene(o[m, :3], tol=0.01)
                if n is not None and abs(n @ achse) > 0.98:
                    if n @ achse < 0:
                        n, d = -n, -d
                    o = o[o[:, :3] @ n - d > 0.02]
            neu.append(o)
        objekte = neu
    return objekte, punkt, achse, sinn, rest, (None if grenze is None else grenze - 0.015)


def zusammensetzen(dateien: list[Path], leer: Path | None = None, voxel_m: float = 0.01,
                   normale=None, alle_pruefen: bool = False, umlaufzeit: float | None = None,
                   radius: float | None = None):
    """`normale`: Bodennormale (Drehachsrichtung) in Kamerakoordinaten vorgeben, falls die
    automatische Wahl danebenliegt; mit `alle_pruefen` wird sie nur als zusätzlicher Kandidat
    genommen."""
    roh = [np.load(f, allow_pickle=False).astype(float) for f in dateien]
    roh = [voxel(r[np.isfinite(r[:, :3]).all(axis=1)], voxel_m) for r in roh]
    zeiten = [zeit_aus_name(f) for f in dateien]
    dauerdrehung = all(t is not None for t in zeiten)
    if dauerdrehung:  # Teller dreht gleichmäßig: Winkel = 360° × t / Umlaufzeit (Faktor angepasst)
        if not umlaufzeit:
            raise SystemExit("Bei Dauerdrehung --umlaufzeit angeben (Sekunden für 360°, Stoppuhr).")
        winkel = 2 * np.pi * np.asarray(zeiten) / umlaufzeit
    else:
        winkel = np.radians([winkel_aus_name(f) for f in dateien])
    ref = voxel(np.load(leer, allow_pickle=False).astype(float), voxel_m) if leer else None
    # Welche Ebene der Boden ist, steht nicht fest (eine große Wand oder Tischplatte kann mehr
    # Punkte haben). Daher die größten Ebenen bzw. eine vorgegebene Normale als Kandidaten
    # durchprobieren und die nehmen, mit der die zurückgedrehten Bilder am besten passen.
    kandidaten = ebenen(ref[:, :3] if ref is not None else roh[0][:, :3])
    if normale is not None:
        n = np.asarray(normale, float) / np.linalg.norm(normale)
        basis = ref if ref is not None else roh[0]
        kandidaten = [(n, float(np.median(basis[:, :3] @ n)))] + kandidaten
        kandidaten = kandidaten[:1] if not alle_pruefen else kandidaten
    if ref is None and normale is None:  # ohne leeren Teller: Achse aus dem, was sich dreht
        erg = _ueber_bewegung(roh, winkel, dauerdrehung, radius)
        if erg is not None:
            objekte, punkt, achse, sinn, rest, teller = erg
            teile = [zurueckdrehen(o, punkt, achse, sinn * (w - winkel[0]))
                     for o, w in zip(objekte, winkel, strict=True)]
            wolke = ausreisser_weg(voxel(np.vstack(teile), voxel_m / 2))
            info = masse(wolke, punkt, achse) | {"rest": rest, "punkte": len(wolke),
                                                 "achse": achse, "achspunkt": punkt,
                                                 "boden": achse}
            if teller is not None:  # Objekt steht auf dem Teller: Höhe ab Telleroberfläche
                h = (wolke[:, :3] - punkt) @ achse
                info["hoehe"] = float(np.percentile(h, 99.5) - teller)
            return wolke, info
    ergebnisse = []
    for n0, d0 in kandidaten:
        objekte = [ausreisser_weg(objekt_freistellen(r, ref, n0, d0)) for r in roh]
        if min(len(o) for o in objekte) < 100:
            continue
        ergebnisse.append((objekte, achse_finden(objekte, winkel, n0, dauerdrehung), n0))
    if not ergebnisse:
        raise SystemExit("Objekt nicht gefunden: Boden im Bild? Objekt in Bildmitte?")
    # Unter den gut passenden Lösungen die, deren Ebene senkrecht zur gefundenen Achse steht
    # (der Boden liegt senkrecht zur Drehachse, eine Wand dagegen parallel)
    bester_rest = min(e[1][3] for e in ergebnisse)
    gut = [e for e in ergebnisse if e[1][3] <= 1.3 * bester_rest + 0.002]
    objekte, (punkt, achse, sinn, rest), boden = max(gut, key=lambda e: abs(e[2] @ e[1][1]))
    if radius:  # nur Punkte nahe der Drehachse (Hintergrund neben dem Teller weg), dann nachrechnen
        objekte = [o[np.linalg.norm(np.cross(o[:, :3] - punkt, achse), axis=1) <= radius]
                   for o in objekte]
        if min(len(o) for o in objekte) < 100:
            raise SystemExit(f"Innerhalb von {radius} m um die Drehachse kaum Punkte.")
        punkt, achse, sinn, rest = achse_finden(objekte, winkel, achse, dauerdrehung)
    teile = [zurueckdrehen(o, punkt, achse, sinn * (w - winkel[0]))
             for o, w in zip(objekte, winkel, strict=True)]
    wolke = ausreisser_weg(voxel(np.vstack(teile), voxel_m / 2))
    info = masse(wolke, punkt, achse) | {"rest": rest, "punkte": len(wolke), "achse": achse,
                                         "achspunkt": punkt, "boden": boden}
    return wolke, info


def zeit_aus_name(f: Path) -> float | None:
    """Dauerdrehung: Dateiname t<Sekunden>, z. B. t012,35.npy → 12,35 s; sonst None."""
    m = re.match(r"t(\d+(?:[.,]\d+)?)$", f.stem)
    return float(m.group(1).replace(",", ".")) if m else None


def winkel_aus_name(f: Path) -> float:
    m = re.match(r"t?(\d+(?:[.,]\d+)?)", f.stem)
    return float(m.group(1).replace(",", ".")) if m else 0.0


# --- Aufnahme -------------------------------------------------------------------------------
def aufnahme(args):
    from verladearm_vision.config import load_config
    from verladearm_vision.konsole import quickedit_aus
    from verladearm_vision.service.main import build_source

    quickedit_aus()
    cfg = load_config(args.config)
    if args.dauer:  # bei drehendem Objekt ein Bild je Aufnahme (kein Mitteln, keine Unschärfe)
        cfg["source"]["frames"] = 1
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
    if args.dauer:  # Dauerdrehung: in festen Zeitabständen aufnehmen
        input(f"Teller gleichmäßig drehen lassen, Enter = Start ({args.dauer:g} s, "
              f"alle {args.intervall:g} s, Strg+C = Abbruch): ")
        t0 = time.monotonic()
        try:
            while (t := time.monotonic() - t0) < args.dauer:
                speichern(f"t{t:06.2f}".replace(".", ",") + ".npy")
                time.sleep(max(0.0, args.intervall - (time.monotonic() - t0 - t)))
        except KeyboardInterrupt:
            pass
        if hasattr(source, "close"):
            source.close()
        print(f"Fertig. Umlaufzeit stoppen, dann: python tools/drehteller.py zusammensetzen "
              f"{ordner} --umlaufzeit <Sekunden>")
        return
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
    a.add_argument("--dauer", type=float, default=0.0,
                   help="Dauerdrehung: so viele Sekunden aufnehmen (etwas mehr als eine Umdrehung)")
    a.add_argument("--intervall", type=float, default=1.0, help="Dauerdrehung: Abstand [s]")
    z = sub.add_parser("zusammensetzen")
    z.add_argument("ordner")
    z.add_argument("--stl", action="store_true", help="zusätzlich ein STL-Netz (grob)")
    z.add_argument("--voxel", type=float, default=0.01, help="Rasterweite [m] (Standard 1 cm)")
    z.add_argument("--radius", type=float,
                   help="nur Punkte bis zu diesem Abstand [m] von der Drehachse (Hintergrund weg), "
                   "z. B. Tellerradius + Überstand des Objekts")
    z.add_argument("--umlaufzeit", type=float,
                   help="Dauerdrehung: Sekunden für eine Umdrehung (Stoppuhr, ±5 %% genügt)")
    z.add_argument("--normale", help="Drehachse/Bodennormale vorgeben, z. B. 0,-1,0 "
                   "(Kamerakoordinaten; nur nötig, wenn die automatische Wahl danebenliegt)")
    args = p.parse_args()
    if args.befehl == "aufnahme":
        return aufnahme(args)
    ordner = Path(args.ordner)
    dateien = sorted((f for f in ordner.glob("*.npy")
                      if re.match(r"t?\d", f.name) and "_gesamt" not in f.name),
                     key=winkel_aus_name)
    if len(dateien) < 3:
        sys.exit(f"Mindestens 3 Aufnahmen in {ordner} nötig.")
    leer = ordner / "leer.npy"
    normale = [float(x) for x in args.normale.split(",")] if args.normale else None
    wolke, info = zusammensetzen(dateien, leer if leer.exists() else None, args.voxel, normale,
                                 umlaufzeit=args.umlaufzeit, radius=args.radius)
    basis = ordner / f"{ordner.name}_gesamt"
    np.save(basis.with_suffix(".npy"), wolke.astype(np.float32))
    schreibe_ply(wolke[:, :3], basis.with_suffix(".ply"))
    schreibe_pts(wolke, basis.with_suffix(".pts"))
    if args.stl:
        schreibe_stl(wolke, basis.with_suffix(".stl"))
    print(f"{len(dateien)} Aufnahmen → {info['punkte']:,} Punkte: {basis}.npy/.ply/.pts")
    print(f"Passgenauigkeit: {info['rest'] * 1000:.0f} mm mittlerer Abstand (gut: < 10 mm)")
    print(f"Grundriss (kleinstes Rechteck): {info['laenge'] * 1000:.0f} × "
          f"{info['breite'] * 1000:.0f} mm")
    if info["durchmesser"] > 2.5 and not args.radius:
        print("Achtung: sehr groß – vermutlich ist Hintergrund dabei. Leeren Teller als Referenz "
              "aufnehmen (leer.npy) oder --radius angeben, z. B. --radius 0.8.")
    print(f"Höhe entlang der Drehachse: {info['hoehe'] * 1000:.0f} mm, "
          f"größter Durchmesser: {info['durchmesser'] * 1000:.0f} mm")


if __name__ == "__main__":
    main()
