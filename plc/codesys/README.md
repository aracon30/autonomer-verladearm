# SPS-Programm Prototyp in CODESYS (Entwurf)

Stand 02.11.2026 · **Entwurf, nicht übersetzt und nicht getestet.** Strukturierter Text
(IEC 61131-3) nach bestem Wissen. Beim Anlegen in CODESYS zeigt der Compiler Tippfehler und
fehlende Typumwandlungen an.

Aufbau und Ablauf entsprechen dem SPS-Simulator (`tools/plc_simulator.py`). Die Schnittstelle zum
Vision-PC ist die gleiche wie für die S7 (`docs/schnittstelle.md`, Version 3). Für die Anlage
BASF lässt sich der Code weitgehend nach TIA Portal (SCL) übertragen.

## Aufbau

| Datei | CODESYS-Objekt | Aufgabe |
|---|---|---|
| `GVL_Vision.st` | Globale Variablenliste | Schnittstelle zum Vision-PC (wie `DB_Vision`), per OPC UA freigeben |
| `GVL_IO.st` | Globale Variablenliste | Taster, Leuchten, Sensoren, Klappe, Abtropfsicherung, Leitstelle |
| `GVL_Achsen.st` | Globale Variablenliste | Prozessdaten der 3 MOVITRAC, Fahrbefehle, Istwerte |
| `GVL_Param.st` | Globale Variablenliste | Achsgrenzen, Geschwindigkeiten, Park, Eintauchtiefen, Zeiten |
| `DUT_Pd.st` | Datentyp (DUT) | Prozessdaten MOVIKIT Positioning Drive (8 PA / 8 PE) |
| `FB_PdAxis.st` | Funktionsbaustein | eine Achse: Ziel, v, a an den Umrichter; Istposition, Status |
| `FB_SyncMove.st` | Funktionsbaustein | synchrone Fahrt aller Achsen zu einem Stützpunkt (wie `Drives.sync`) |
| `FB_VisionJob.st` | Funktionsbaustein | Auftrag an den Vision-PC mit Handshake, Zeitüberwachung, Plausibilität |
| `F_Hilfen.st` | 4 Funktionen | Parkstellung, Höhe ↔ Lage in der Nachzieh-Tabelle, Interpolation |
| `PRG_Heartbeat.st` | Programm | Heartbeat zum PC und Überwachung |
| `PRG_Achsen.st` | Programm | Achsen jeden Zyklus bedienen, Istwerte an den PC |
| `PRG_Main.st` | Programm | Automatikablauf: Kammern, Job 1/2/3, Eintauchen, Befüllen mit Nachziehen, Störung |
| `PRG_Hand.st` | Programm | Tippbetrieb mit dem Handbediengerät |

**Task:** MainTask zyklisch 10 ms, Aufrufreihenfolge `PRG_Heartbeat`, `PRG_Achsen`, `PRG_Main`,
`PRG_Hand`.

## Anlegen in CODESYS

1. Neues Standardprojekt, Gerät **CODESYS Control for Linux SL** (zum Ausprobieren ohne Hardware:
   CODESYS Control Win aus dem Setup).
2. Objekte wie in der Tabelle anlegen. In jedem Objekt: der Teil bis zum letzten `END_VAR` kommt
   in den **Deklarationsteil** (oben), der Rest in den **Implementierungsteil** (unten). Die
   Zeilen `END_FUNCTION` in `F_Hilfen.st` trennen nur die Funktionen und werden nicht eingefügt.
3. **Gerätebaum:**
   - Ethernet-Adapter mit dem PROFINET-Netz (z. B. LAN 2) → PROFINET IO Controller.
   - Gerätebeschreibungen (GSDML) installieren: SEW MOVITRAC advanced, IO-Link-Master,
     E/A-Modul, ggf. PROFINET-Modul der Sicherheitssteuerung.
   - Geräte anhängen, PROFINET-Gerätenamen vergeben (wie an den Geräten eingestellt).
   - **E/A-Abbild:** Prozessdaten der MOVITRAC auf `GVL_Achsen.aPd[1..3].aPA/aPE` legen,
     Ein- und Ausgänge auf die Variablen in `GVL_IO`.
4. **OPC UA:** Symbolkonfiguration hinzufügen, `GVL_Vision` freigeben (Lesen/Schreiben),
   „Unterstützung für OPC UA-Features“ aktivieren. OPC-UA-Server-Lizenz bzw. -Funktion der
   Laufzeit prüfen.
5. Übersetzen, einloggen, starten.

## Vision-PC auf CODESYS umstellen

Nur die Anlagendatei, kein Programmcode. Namensraum und Knoten-ID mit einem OPC-UA-Client
(z. B. UaExpert) an der laufenden Steuerung ablesen und eintragen:

```yaml
plc:
  url: opc.tcp://<IP des PCs bzw. 127.0.0.1>:4840/
  namespace_uri: <Namensraum der CODESYS-Symbole, aus UaExpert>
  node_template: 'ns={ns};s=|var|<Gerätename>.Application.GVL_Vision.{name}'
```

Läuft die Soft-SPS auf demselben PC wie die Vision-Software, ist die Adresse `127.0.0.1`.

## Vor der Inbetriebnahme zu prüfen (Platzhalter im Code)

| Was | Wo | Quelle |
|---|---|---|
| Bitbelegung **Steuerwort PA1 / Statuswort PE1** | `FB_PdAxis` (Konstanten `CW_…`, `SW_…`) | SEW-Handbuch MOVIKIT Positioning Drive 33350930, Kap. 8 |
| **Anwendereinheiten** Position, Geschwindigkeit, Beschleunigung | `FB_PdAxis` (`EINHEIT_…`) und MOVISUITE | Inbetriebnahme SEW |
| Ruckzeit (Zusatz-PD oder Parameter, alle Achsen gleich) | MOVISUITE | Handbuch Kap. 7.2.1 |
| Nullpunkt (Offset, einmalig) | MOVISUITE bzw. Betriebsart 301 | `hardware/antriebe.md` |
| Park, Grenzen, Geschwindigkeiten, Eintauchtiefen | `GVL_Param` | Anlagendatei `heta_prototyp.yaml` |
| Bremse lüften J1/J2 im Handbetrieb | `PRG_Hand` (nur Kommentar) | SEW, Sicherheitskonzept |
| Signale Leitstelle | `GVL_IO` (`xPls…`) | Abstimmung BASF |

## Grenzen dieses Entwurfs

- **Sicherheit** ist nicht Teil der SPS: Not-Halt, Zustimmung, STO und Klapptreppe wertet die
  Sicherheitssteuerung aus. Die SPS liest nur Meldungen (`xSicherheitOk` usw.).
- Die **Höhe des Auslasses** beim Befüllen wird aus den Eintauch-Stützpunkten berechnet (gleichmäßig
  zwischen Anfahrpunkt und Eintauchtiefe). Das gilt für die Standardplanung
  (`planning.insert_waypoints: 5`). Mit Schnittstelle V4 soll der PC die Höhen mitliefern.
- Am Stützpunkt wird angehalten (kein Nachschieben des nächsten Ziels).
