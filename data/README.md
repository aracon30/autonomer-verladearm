# Messdaten

Punktwolken werden **nicht** im Repository versioniert. Ablage auf dem Netzlaufwerk bzw. SharePoint,
Ordnerstruktur: `JJJJ-MM-TT_ort_beschreibung/`.

Für lokale Tests synthetische Daten erzeugen:

```bash
python tools/make_synthetic.py --out data/samples --count 5
```

Dateiformat: `.npy` (N×3, Meter, Sensorkoordinaten) oder `.ply` (benötigt `pip install -e ".[viz]"`).
