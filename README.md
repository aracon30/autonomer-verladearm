# Autonomer Verladearm

Autonomer Obenbefüllarm für Lkw-Tankwagen (Prototyp HETA, Erprobung an einer Verladestelle für
Polymerdispersionen): Eine 3D-Kamera erkennt die offenen Dome, der Vision-PC plant eine
kollisionsfreie Bahn, die SPS fährt den Arm ein, zieht beim Befüllen nach und fährt zurück in die
Parkstellung.

## Architektur

```
3D-Kamera (SICK Visionary-T Mini CX)
      │ Ethernet
      ▼
Vision-Software (dieses Repo) ──OPC UA──► SPS: Beckhoff-IPC, TwinCAT 3 ──PROFINET/EtherCAT──► 3 × SEW MOVITRAC
                                            │  TwinSAFE: Not-Halt, Zustimmung, STO (festverdrahtet)
Grenzschalter Nachziehen (IO-Link) ────────►┤
Absperrklappe (auf/zu, Endlagen) ◄─────────►┤
Leitstelle/Pumpe BASF ◄────────────────────►┘  „Befüllung Start/Ende“, „Arm bereit“, „Befüllung stoppen“
Überfüllsicherung (Liquiphant) ──────────────► schaltet die Pumpe direkt ab (Meldung an die SPS)
```

Der Vision-PC misst Domöffnung, Tank und offenen Deckel und liefert eine **kollisionsgeprüfte Bahn
als Stützpunkte in Servo-Grad**. Die SPS prüft sie und fährt; Ablauf und Sicherheit liegen in der
SPS (siehe [ADR 0001](docs/adr/0001-architektur.md), [ADR 0002](docs/adr/0002-gelenkwinkel-vom-pc.md),
[Schnittstelle](docs/schnittstelle.md), [Kinematik und Bahnplanung](docs/kinematik.md)).

**Aufgabenteilung bei der Befüllung:** Menge, Pumpe und Füllende steuert die Leitstelle. Der Arm
positioniert den Auslass, öffnet die Absperrklappe erst, wenn er im Tank steht, und zieht über
**einen Grenzschalter** (ca. 10–15 cm über dem Auslass, Hub ca. 5 cm) nach. Bei Störung oder
Maximalhöhe meldet er „Befüllung stoppen“: erst Pumpe aus, dann Klappe zu. Die Überfüllsicherung
sitzt auf einer Dom-Abdeckung, die mit dem Arm auf den Domkasten gesetzt wird; eine mechanische
Pendelwanne fängt das Nachtropfen ([Skizze Rev. 6](docs/skizzen/Prinzipskizze_Abtropfsicherung_Rev6.pdf)).

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

Die Simulation bildet den Stand vom 10.11.2026 ab (`hardware/antriebe.md`,
`docs/fuellstand_ueberfuellsicherung.md`). **Noch nicht nachgezogen** ist die Dom-Abdeckung mit
Pendelwanne (wartet auf die Konstruktion); nachgemessen wird bis dahin noch über den
Referenzflansch.
- **Arm** mit den Maßen aus dem Konfigurator (Flansch 7,34 m über Fahrbahn, Auslass 3,7 m) und
  den SEW-Antrieben.
- **Nur Lkw-Tankwagen** (Tank Ø 2,2 m, Domrand 3,4–3,9 m über Fahrbahn, Mannloch offen) mit
  1–3 Kammern, je ein Dom, Abstand 2,5 m (`source` in `simulation.yaml`).
- **Antriebe wie MOVIKIT Positioning Drive:** Die SPS gibt jeder Achse Ziel, Geschwindigkeit und
  Beschleunigung im Verhältnis zu ihrem Weg vor (gleiche Ruckzeit), alle kommen gleichzeitig an.
  `PROZESSDATEN=1 tools/simulation.sh` schreibt die Vorgaben je Fahrt ins SPS-Log.
- **Befüllen von unten mit Nachziehen:** Der Auslass taucht bis ca. 20 cm über den Tankboden ein
  (Eintauchtiefe 2,1 m). Die SPS öffnet die Absperrklappe und meldet „Arm bereit“; die Leitstelle
  startet die Pumpe (22 m³/h), der Spiegel steigt in der liegenden zylindrischen Kammer. **Ein**
  Grenzschalter sitzt 12 cm über dem Auslassende: nass → J3 hebt um 5 cm (ca. 35 Hübe je Kammer),
  danach muss er trocken sein, sonst Störung. Der Auslass bleibt ca. 7–12 cm unter dem Spiegel.
- **Füllende in drei Ebenen:** 1. Leitstelle meldet „Befüllung Ende“ (ihre Menge, hier 95 % der
  Kammer) → Klappe zu, Abtropfen, Rückfahrt; 2. Maximalhöhe bzw. Arm am Ende → „Befüllung
  stoppen“ (Test: Befehl `u`); 3. Überfüllsicherung schaltet die Pumpe direkt ab – immer
  Störung. Die SPS schließt die Klappe immer erst, wenn die Pumpe aus ist (Auslaufzeit 3 s).
- **Mehrkammer:** Der Dauertest wechselt ab zwischen „Kammern verbunden“ (ein Dom, automatisch der
  nächste, ganzer Tank) und „Mehrkammer“ (alle offenen Dome von vorn nacheinander, je Kammer
  eine Füllung, ohne Umweg über die Parkstellung). Schnittstelle: `DomeNo`, `DomeCount`,
  `DomeSelected` (`docs/schnittstelle.md`).

Selbst bedienen wie an der Anlage statt Dauertest: `tools/simulation.sh --netz --bedienen`.
Befehle im Terminal (`?` zeigt alle):

| Befehl | Bedeutung |
|---|---|
| `n` | neues Fahrzeug: fährt vor (Lichtschranke belegt), Klapptreppe aus, Dom öffnen, Treppe zurück |
| `p 1`, `f`, `s` | Produkt wählen, „Fahrzeug bereit“ bestätigen, „Automatisch beladen“ starten |
| `k 0`, `k 1 2 3` | Auftrag: Kammern verbunden (ein Dom, automatisch) bzw. Mehrkammer, Dome von vorn nacheinander |
| `e` | Leitstelle meldet „Befüllung Ende“ vorzeitig → Klappe zu, Rückfahrt in die Parkstellung |
| `u` | Leitstelle beendet nicht (Mengenfehler) → Füllende über die Maximalhöhe (Schutzebene 2, „Befüllung stoppen“) |
| `g` | Grenzschalter bleibt nass (Belag, Defekt) → Störung nach dem nächsten Hub, Pumpe aus, Klappe zu |
| `l`, `t` | Lichtschranke / Klapptreppe umschalten (Verriegelungen testen) |
| `x` | Stopp |
| `h` | Handbetrieb: `j 3 +5` tippen, `b 2 -20` Bremse lüften und von Hand schieben (nur J1/J2, J3 gesperrt), `d` Arm wie von Hand in einen Dom führen |
| `z` | „Automatisch in Parkstellung“ aus jeder Lage (Job 3, misst ohne Job 1 neu) |

Der Simulator setzt die Startbedingungen und Verriegelungen um, die das SPS-Programm haben
soll (`docs/schnittstelle.md`); der Bedienstatus erscheint auch in der Live-Ansicht.

Anlagendatei eines Arms im Browser bearbeiten (Konfigurator, http://<IP>:8090):

```bash
.venv/bin/python -m verladearm_vision.konfigurator --host 0.0.0.0 --port 8090
```

Die folgenden Befehle setzen eine aktivierte Umgebung voraus (`source .venv/bin/activate`);
sonst `.venv/bin/python` statt `python` schreiben.

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
| `docs/` | **[Projektstand](docs/projektstand.md)** (Entscheidungen, Anfragen, Bestellungen, offene Punkte), Lastenheft, Schnittstelle, Kinematik, Inbetriebnahme, Kalibrierung, Betrieb, Architekturentscheidungen, [Ideenspeicher](docs/ideenspeicher.md), [Füllstand und Überfüllsicherung](docs/fuellstand_ueberfuellsicherung.md), [Kunde](docs/kunde_basf_h517.md) |
| `docs/skizzen/` | Prinzipskizzen (Abtropfsicherung Rev. 6, Überfüll-Lanze) |
| `docs/entwicklung/` | Entwicklungsakte nach ISO 9001 Kap. 8.3 (Plan, Anforderungsnachweis, Reviews, Änderungen, Dokumentenliste) |
| `docs/foerderung/` | Entwurf BSFZ-Antrag Forschungszulage |
| `docs/extern/` | Unterlagen für Kunde und Lieferanten (Betriebsanleitung, Softwaredokumentation, Antriebsliste) |
| `hardware/` | [Antriebe](hardware/antriebe.md) (SEW, IMO), Stückliste, [Stückliste Prototyp-Steuerung](hardware/stueckliste_prototyp_steuerung.md), Anfragen; Kamera: [docs/sensor_sick.md](docs/sensor_sick.md) |
| `plc/` | Schnittstellen-DB, SPS-Programm-Entwurf in Strukturiertem Text (`plc/codesys/`, Basis für TwinCAT 3) |
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

## Status (10.11.2026)

Prototyp in Entwicklung.

- **Software:** Erkennung (auch mehrere Dome, Schnittstelle Version 3), Bahnplanung, Simulation und
  Konfigurator auf synthetischen Daten getestet. Treiber für die SICK-Kamera vorhanden, am echten
  Gerät noch nicht erprobt.
- **Bestellt:** SICK Visionary-T Mini CX, SEW-Servos J1/J2.
- **Entschieden:** Steuerung TwinCAT 3 auf Beckhoff-IPC (Schaltschrank und Grundsoftware über
  Automatisierungspartner), Befüllung über die Leitstelle, ein Grenzschalter, mechanische
  Abtropfsicherung.
- **Offen:** Feldbus der Umrichter (Antwort SEW), J3-Schwenktrieb (Lastfall mit langem Auslass,
  IMO), Sensoren und Überfüllsicherung (Antwort Kunde), Angebot Schaltschrank/Software.
- **Nächste Schritte:** Aufnahmen an echten Tankwagen mit der Kamera, Simulation und SPS-Entwurf
  auf den Stand vom 09.11. bringen, Konstruktion Dom-Abdeckung.

Details: [Projektstand](docs/projektstand.md).
