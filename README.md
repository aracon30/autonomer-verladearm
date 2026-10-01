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

Der Vision-PC misst Domöffnung, Tank und offenen Deckel und liefert eine **kollisionsgeprüfte Bahn
als Stützpunkte in Servo-Grad**. Die SPS prüft sie und fährt; Ablauf und Sicherheit liegen in der
SPS (siehe [ADR 0001](docs/adr/0001-architektur.md), [ADR 0002](docs/adr/0002-gelenkwinkel-vom-pc.md),
[Schnittstelle](docs/schnittstelle.md), [Kinematik und Bahnplanung](docs/kinematik.md)).

## Schnellstart

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # mit Sensor SICK Visionary-T Mini: ".[dev,sick]"

python tools/make_synthetic.py      # Testdaten erzeugen
python -m verladearm_vision.service.main --once   # eine Messung ohne SPS
pytest                              # Tests
```

### Simulation auf einem Linux-Testserver

Braucht nur Python ab 3.10 (`sudo apt install python3-venv git` unter Debian/Ubuntu):

```bash
git clone <repo-url> && cd autonomer-verladearm
tools/simulation.sh          # beim ersten Start wird .venv angelegt und alles installiert
```

Startet SPS-Simulator, Vision-Dienst und Live-Ansicht mit
`vision/config/anlagen/simulation.yaml` (HETA-Prototyp mit seinen Antrieben: Geschwindigkeiten,
Rampen, Getriebespiel; Fahrten im Zeitraffer, `ZEITRAFFER=1` für Echtzeit). Live-Ansicht vom eigenen PC per SSH-Tunnel:
`ssh -L 8000:127.0.0.1:8000 <benutzer>@<server>`, dann http://127.0.0.1:8000 öffnen.
Logs unter `data/logs/`, Beenden mit Strg+C. Eine im Konfigurator angelegte Anlage simulieren:
`tools/simulation.sh --netz --anlage <name>` (Datei `vision/config/anlagen/<name>.yaml`).

Selbst bedienen wie an der Anlage statt Dauertest: `tools/simulation.sh --netz --bedienen`.
Befehle im Terminal (`?` zeigt alle):

| Befehl | Bedeutung |
|---|---|
| `n` | neues Fahrzeug: fährt vor (Lichtschranke belegt), Klapptreppe aus, Dom öffnen, Treppe zurück |
| `p 1`, `f`, `s` | Produkt wählen, „Fahrzeug bereit“ bestätigen, „Automatisch beladen“ starten |
| `e` | „Beladung beendet“ → Rückfahrt in die Parkstellung |
| `l`, `t` | Lichtschranke / Klapptreppe umschalten (Verriegelungen testen) |
| `x` | Stopp |
| `h` | Handbetrieb: `j 3 +5` tippen, `b 2 -20` Bremse lüften und von Hand schieben (nur J1/J2), `d` Arm wie von Hand in einen Dom führen |
| `z` | „Automatisch in Parkstellung“ aus jeder Lage (Job 3, misst ohne Job 1 neu) |

Der Simulator setzt die Startbedingungen und Verriegelungen um, die das SPS-Programm haben
soll (`docs/schnittstelle.md`); der Bedienstatus erscheint auch in der Live-Ansicht.

Anlagendatei eines Arms im Browser bearbeiten (Konfigurator, http://<IP>:8090):

```bash
.venv/bin/python -m verladearm_vision.konfigurator --host 0.0.0.0 --port 8090
```

Kompletter Ablauf ohne Hardware, einzeln gestartet (SPS-Simulator mit Achsen, simulierter Sensor mit Getriebespiel):

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

Kalibrierung, Aufzeichnung und Betrieb:

```bash
python -m verladearm_vision.calibrate --config <anlage>.yaml --sim     # Probelauf, sonst --from-plc
python tools/auswertung.py --dir data/aufzeichnung > auswertung.csv    # alle Aufträge als CSV
sudo deploy/install.sh vision/config/anlagen/<anlage>.yaml             # Autostart auf dem Edge-PC
```

Siehe [Kalibrierung](docs/kalibrierung.md) und [Betrieb](docs/betrieb.md).

## Struktur

| Ordner | Inhalt |
|---|---|
| `docs/` | Lastenheft, Schnittstelle, Kinematik, Inbetriebnahme, Kalibrierung, Betrieb, Architekturentscheidungen |
| `hardware/` | Stückliste, Halterungen, Elektro (Sensor: [docs/sensor_sick.md](docs/sensor_sick.md)) |
| `plc/` | Schnittstellen-DB für TIA Portal |
| `vision/src/verladearm_vision/` | acquisition, detection, calibration, kinematics, plc, service, viewer |
| `vision/config/` | Konfiguration: `default.yaml`, Anlagendateien unter `anlagen/` |
| `vision/tests/` | Tests |
| `tools/` | SPS-Simulator, Testdatengenerator, Auswertung der Aufzeichnungen |
| `deploy/` | Systemdienste und Installationsskript für den Edge-PC |

## Arbeitsweise

- `main` ist geschützt, Änderungen per Feature-Branch und Pull Request.
- Aufgaben als Issues, Planung im GitHub-Project, Bezug zu Lastenheft-IDs (z. B. F-01).
- Releases taggen (`v0.1.0` …); `InterfaceVersion` mit der SPS abstimmen.
- Messdaten nicht einchecken, siehe [data/README.md](data/README.md).

## Status

Prototyp. Erkennung für ebene und runde Tanks (Lkw, Kesselwagen) mit Domkragen auf synthetischen
Daten getestet. Treiber für den SICK Visionary-T Mini CX vorhanden, am echten Gerät noch nicht
erprobt; Kalibrierung und Messungen an echten Fahrzeugen folgen.
