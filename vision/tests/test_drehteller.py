"""Drehteller-Scan (tools/drehteller.py) mit simulierten Aufnahmen: Objekt dreht sich vor fester
Kamera, Hintergrund steht – zusammengesetzte Wolke hat die richtigen Maße."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[2] / "tools"))
import drehteller  # noqa: E402


def _objekt(rng):
    """Zylinder Ø 0,6 m × 1,0 m mit seitlichem Kasten (unsymmetrisch), Achse = y (Kamera: unten)."""
    n = 40000
    a, h = rng.uniform(0, 2 * np.pi, n), rng.uniform(-0.5, 0.5, n)
    zyl = np.column_stack([0.3 * np.cos(a), h, 0.3 * np.sin(a)])
    nz = np.column_stack([np.cos(a), np.zeros(n), np.sin(a)])
    m = 8000
    kasten = np.column_stack([np.full(m, 0.45), rng.uniform(-0.2, 0.2, m),
                              rng.uniform(-0.1, 0.1, m)])
    nk = np.tile([1.0, 0, 0], (m, 1))
    seite = np.column_stack([rng.uniform(0.3, 0.45, m), rng.uniform(-0.2, 0.2, m), np.full(m, 0.1)])
    ns = np.tile([0, 0, 1.0], (m, 1))
    return np.vstack([zyl, kasten, seite]), np.vstack([nz, nk, ns])


def _aufnahmen(schritt=15, anzahl=24, seed=0, kasten=True, wand_n=15000):
    rng = np.random.default_rng(seed)
    p, nrm = _objekt(rng)
    if not kasten:  # rein drehsymmetrisch (Filtergehäuse ohne Stutzen)
        p, nrm = p[:40000], nrm[:40000]
    mitte = np.array([0.1, 0.2, 2.2])  # Drehachse 2,2 m vor der Kamera
    n = 15000
    wand = np.column_stack([rng.uniform(-2, 2, wand_n), rng.uniform(-1.5, 1, wand_n),
                            np.full(wand_n, 4.0)])
    boden = np.column_stack([rng.uniform(-2, 2, n), np.full(n, 0.75), rng.uniform(1, 4, n)])
    bilder = []
    for k in range(anzahl):
        w = np.radians(k * schritt)
        r = np.array([[np.cos(w), 0, np.sin(w)], [0, 1, 0], [-np.sin(w), 0, np.cos(w)]])
        q, nq = p @ r.T + mitte, nrm @ r.T
        sichtbar = (nq * -q).sum(axis=1) > 0  # Fläche zeigt zur Kamera
        bild = np.vstack([q[sichtbar], wand, boden])
        bilder.append(bild + rng.normal(0, 0.003, bild.shape))
    return bilder


def _speichern(tmp_path, bilder, schritt=15):
    dateien = []
    for k, b in enumerate(bilder):
        f = tmp_path / (f"{k * schritt:05.1f}".replace(".", ",") + ".npy")
        np.save(f, b.astype(np.float32))
        dateien.append(f)
    return sorted(dateien, key=drehteller.winkel_aus_name)


def test_drehteller_setzt_objekt_zusammen(tmp_path):
    wolke, info = drehteller.zusammensetzen(_speichern(tmp_path, _aufnahmen()))
    assert info["rest"] < 0.01
    assert abs(info["hoehe"] - 1.0) < 0.05  # Höhe 1,0 m
    assert abs(info["durchmesser"] - 0.9) < 0.06  # bis Außenkante Kasten (0,45 m Radius)
    # Hintergrund ist weg: nichts in Wand- oder Bodennähe
    assert (wolke[:, 2] > 3.5).mean() < 0.01


def test_drehsymmetrisches_filtergehaeuse(tmp_path):
    """Reiner Zylinder: Bewegung ist nicht sichtbar, Maße kommen über Winkel und Drehachse."""
    wolke, info = drehteller.zusammensetzen(_speichern(tmp_path, _aufnahmen(kasten=False)))
    assert abs(info["hoehe"] - 1.0) < 0.05
    assert abs(info["durchmesser"] - 0.6) < 0.04
    # Rundum erfasst: Punkte auf allen Seiten der Achse
    rel = wolke[:, :3] - info["achspunkt"]
    rel -= np.outer(rel @ info["achse"], info["achse"])
    w = np.degrees(np.arctan2(rel[:, 2], rel[:, 0]))
    assert np.histogram(w, bins=12, range=(-180, 180))[0].min() > 50


def test_grosse_wand_wird_nicht_fuer_den_boden_gehalten(tmp_path):
    """Die Wand hat mehr Punkte als der Boden: trotzdem richtige Achse und Maße."""
    bilder = _aufnahmen(wand_n=60000, anzahl=12, schritt=30)
    wolke, info = drehteller.zusammensetzen(_speichern(tmp_path, bilder, schritt=30))
    assert abs(abs(info["boden"][1]) - 1) < 0.05  # Boden erkannt (Normale = Kamera-y), nicht Wand
    assert abs(abs(info["achse"][1]) - 1) < 0.05  # Achse senkrecht, nicht in Blickrichtung
    assert abs(info["hoehe"] - 1.0) < 0.06
