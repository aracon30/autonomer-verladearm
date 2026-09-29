# Autonomer Verladearm

Erkennung der Domöffnung von Tankwagen per 3D-Sensorik und Übergabe der Zielkoordinate an die SPS
für einen autonomen Verladearm (Obenbefüllung).

## Architektur

```
3D-Sensor ──► Vision-PC (dieses Repo) ──OPC UA──► SPS ──► Antriebe Verladearm
                                                   │
Füllstand / Überfüllsicherung ────────────────────►┤
Sicherheitssensorik ──► Sicherheits-SPS ──────────►┘──► PLS
```

Der Vision-PC liefert **nur die Zielkoordinate**. Bewegung, Ablauf und Sicherheit liegen in der SPS
(siehe [ADR 0001](docs/adr/0001-architektur.md) und [Schnittstelle](docs/schnittstelle.md)).

## Schnellstart

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # mit Sensor SICK Visionary-T Mini: ".[dev,sick]"

python tools/make_synthetic.py      # Testdaten erzeugen
python -m verladearm_vision.service.main --once   # eine Messung ohne SPS
pytest                              # Tests
```

Kompletter Ablauf ohne Hardware (SPS-Simulator mit Achsen, simulierter Sensor mit Getriebespiel):

```bash
# Anlagendatei für die Simulation, z. B. sim.yaml:
#   extends: vision/config/anlagen/beispiel.yaml
#   source: {type: sim, joint_error_deg: [0.3, -0.25, 0.2]}
#   plc: {url: "opc.tcp://127.0.0.1:4840/"}
python tools/plc_simulator.py --config vision/config/anlagen/beispiel.yaml
python -m verladearm_vision.service.main --config sim.yaml
python -m verladearm_vision.viewer --opcua --config sim.yaml   # Arm live aus den Istwinkeln
```

Live-Ansicht im Browser (Punktwolke, Erkennung, schematische Armbewegung):

```bash
python -m verladearm_vision.viewer   # dann http://127.0.0.1:8000 öffnen
```

Mit `--host 0.0.0.0` ist die Ansicht im Netzwerk erreichbar, z. B. auf dem Tablet an der Verladestation.

Die Ansicht kann auch mitlesen, was der Vision-Dienst an die SPS liefert (drei Terminals):

```bash
python tools/plc_simulator.py                 # oder echte SPS, siehe plc.url
python -m verladearm_vision.service.main
python -m verladearm_vision.viewer --opcua
```

Mit `--opcua` liest die Ansicht `DB_Vision` per OPC UA (nur lesend) und zeigt Handshake-Signale,
Heartbeats und jedes neue Ergebnis. Die zugehörige Punktwolke legt der Vision-Dienst unter
`snapshot.path` ab (Standard `data/last_measurement.npy`).

Inbetriebnahme einer Anlage (Parameter je Verladearm, siehe [docs/inbetriebnahme.md](docs/inbetriebnahme.md)):

```bash
python -m verladearm_vision.commissioning --config vision/config/anlagen/beispiel.yaml
```

## Struktur

| Ordner | Inhalt |
|---|---|
| `docs/` | Lastenheft, Schnittstelle, Kinematik, Inbetriebnahme, Architekturentscheidungen |
| `hardware/` | Stückliste, Halterungen, Elektro (Sensor: [docs/sensor_sick.md](docs/sensor_sick.md)) |
| `plc/` | Schnittstellen-DB für TIA Portal |
| `vision/src/verladearm_vision/` | acquisition, detection, calibration, kinematics, plc, service, viewer |
| `vision/config/` | Konfiguration: `default.yaml`, Anlagendateien unter `anlagen/` |
| `vision/tests/` | Tests |
| `tools/` | SPS-Simulator, Testdatengenerator |

## Arbeitsweise

- `main` ist geschützt, Änderungen per Feature-Branch und Pull Request.
- Aufgaben als Issues, Planung im GitHub-Project, Bezug zu Lastenheft-IDs (z. B. F-01).
- Releases taggen (`v0.1.0` …); `InterfaceVersion` mit der SPS abstimmen.
- Messdaten nicht einchecken, siehe [data/README.md](data/README.md).

## Status

Prototyp. Erkennung für ebene und runde Tanks (Lkw, Kesselwagen) mit Domkragen auf synthetischen
Daten getestet. Treiber für den SICK Visionary-T Mini CX vorhanden, am echten Gerät noch nicht
erprobt; Kalibrierung und Messungen an echten Fahrzeugen folgen.
