# Stückliste Prototyp-Steuerung (Werkstatt Lich, Soft-SPS)

Stand 02.11.2026 · Entwurf zur Anfrage bei Schaltschrankbauer bzw. Elektriker.
Konzept: Ein Linux-Industrie-PC führt die Vision-Software **und** die SPS (CODESYS Control for
Linux SL) aus; eine separate Sicherheitssteuerung übernimmt alle Sicherheitsfunktionen
(Programm: `plc/codesys/`). Typen sind **Beispiele**, Preise grobe Richtwerte ohne Angebot.

Status: **B** = Beistellung HETA (bereits angeboten/festgelegt) · **N** = neu anzufragen ·
**O** = optional in der Werkstatt (kann mit Schalter/Simulation ersetzt werden)

## 1. Rechner

| Pos | Teil | Anforderung / Beispiel | Menge | ca. € | Status |
|---|---|---|---|---|---|
| 1.1 | Industrie-PC (Vision + Soft-SPS) | x86-64, 4 Kerne (Core i5/i7), 16 GB RAM, Industrie-SSD ≥ 128 GB, **≥ 3 × LAN** (Intel), lüfterlos, 24 V DC, 0–50 °C. Linux (Debian/Ubuntu) mit Echtzeit-Kernel PREEMPT_RT. Beispiele: Beckhoff C6027 (mit Linux, ohne Windows/TwinCAT), Siemens IPC BX-32A, OnLogic/Advantech/Kontron | 1 | 1.500–3.300 | N |
| 1.2 | CODESYS-Lizenzen | Control for Linux SL, PROFINET Controller SL, OPC UA Server (falls nicht enthalten) | 1 | 1.000–1.500 | N |
| 1.3 | Programmier-Laptop | Windows 10/11, CODESYS Development System (kostenlos) | 1 | – | vorhanden |

## 2. Schaltschrank

| Pos | Teil | Anforderung / Beispiel | Menge | ca. € | Status |
|---|---|---|---|---|---|
| 2.1 | Sicherheitssteuerung | konfigurierbar, z. B. Pilz PNOZmulti 2 (Grundgerät + E/A-Erweiterung, optional PROFINET-Meldemodul); Funktionen siehe Abschnitt 5 | 1 | 1.500–2.500 | N |
| 2.2 | E/A-Modul PROFINET | z. B. Siemens ET 200SP: Buskoppler, DI 16 × 24 V, DQ 16 × 24 V/0,5 A | 1 | 600–1.000 | N |
| 2.3 | IO-Link-Master PROFINET | ≥ 4 Ports (Grenzschalter A/B, Durchfluss, Reserve), z. B. ifm AL1102 oder Siemens ET 200eco 6ES7148-6JE00 | 1 | 400–900 | N |
| 2.4 | Switch | unmanaged, Gigabit, 5–8 Ports, z. B. Phoenix FL SWITCH 1008N | 1 | 150–300 | N |
| 2.5 | Netzteil | 24 V DC, 20 A | 1 | 200–400 | N |
| 2.6 | Einspeisung | Hauptschalter, Leitungsschutz/Sicherungen für 3 × MOVITRAC nach SEW-Vorgabe, Klemmen, Kabelkanal | 1 | 500–1.000 | N |
| 2.7 | Schrank | ca. 1000 × 800 × 300 mm, IP54 (Werkstatt), Montageplatte | 1 | 500–1.000 | N |
| 2.8 | Umrichter | 3 × SEW MOVITRAC advanced MCX91A (PROFINET, STO, DDI, Positioning Drive) | 3 | – | B (SEW) |
| 2.9 | Bremswiderstände | Auslegung durch SEW | 3 | – | B (SEW, nachfordern) |

## 3. Bedienung und Sicherheit vor Ort

| Pos | Teil | Anforderung / Beispiel | Menge | ca. € | Status |
|---|---|---|---|---|---|
| 3.1 | Not-Halt Schaltschrank | 2-kanalig | 1 | 50–100 | N |
| 3.2 | Leuchttaster „Beladen starten“ | 24 V | 1 | 50 | N |
| 3.3 | Taster „Quittieren“ | | 1 | 30 | N |
| 3.4 | Schlüsselschalter Automatik / Hand | 2-kanalig, auf Sicherheitssteuerung | 1 | 80–150 | N |
| 3.5 | Meldeleuchten grün / gelb / rot | oder Signalsäule | 3 | 100–200 | N |
| 3.6 | Handbediengerät | 3-stufiger Zustimmtaster, Not-Halt, Achswahl J1/J2/J3, + / −, steckbar mit Anschlussbuchse und Not-Halt-Überbrückung im gezogenen Zustand (z. B. Euchner, Pilz, KEBA) | 1 | 800–1.500 | N |
| 3.7 | Lichtschranke Stellplatz | Reflexionslichtschranke | 1 | 100–300 | O |
| 3.8 | Rückmeldung Klapptreppe | in der Werkstatt Schalter, an der Anlage vorhandene Steuerung | 1 | – | O |

## 4. Prozess am Arm

| Pos | Teil | Anforderung / Beispiel | Menge | ca. € | Status |
|---|---|---|---|---|---|
| 4.1 | Grenzschalter Nachziehen A/B | kapazitiv, IO-Link, z. B. Baumer CleverLevel oder SICK LFC; Typ nach Sensortest BASF | 2 | 400–600 | N |
| 4.2 | Überfüllsicherung | zugelassen nach BASF-Vorgabe, Schaltpunkt ca. 20 cm unter Rand, wirkt direkt auf Pumpe/Klappe; Meldung an SPS | 1 | 500–1.500 | N (nach BASF) |
| 4.3 | Absperrklappe DN 100 | mit Antrieb (pneumatisch oder elektrisch) und Endlagen auf/zu | 1 | 800–2.000 | N |
| 4.4 | Durchflussmesser | IO-Link oder Impuls; in der Werkstatt Menge simuliert | 1 | 0–1.500 | O |
| 4.5 | Abtropfsicherung | **rein mechanisch** (Entscheidung 04.11.2026), kein Antrieb, keine Signale an die Steuerung | – | – | – |
| 4.6 | 3D-Kamera | SICK Visionary-T Mini CX mit Halter und Kabeln (Angebot 33503320) | 1 | – | B (SICK) |
| 4.7 | Motoren J1–J3 | SEW, mit Hybridkabeln und Kabelschlepps | 3 | – | B (SEW) |

## 5. Sicherheitsfunktionen (Sicherheitssteuerung, PL nach Risikobeurteilung)

| Funktion | Eingänge | Wirkung |
|---|---|---|
| Not-Halt | Not-Halt Schrank, Not-Halt Handbediengerät | STO an alle 3 Umrichter (2-kanalig), Klappe zu |
| Betriebsart | Schlüsselschalter Automatik / Hand | Automatik nur ohne Handbediengerät-Betrieb, Hand nur mit Zustimmung |
| Zustimmung | Zustimmtaster (Mittelstellung) | Bewegung im Handbetrieb nur bei Zustimmung, sonst STO |
| Verriegelung Fahrzeug | Klapptreppe in Ruhelage, Lichtschranke Stellplatz | Automatik nur bei Ruhelage, sonst Stopp |
| Bremse lüften J1/J2 | Taster Handbediengerät | nur Hand + Zustimmung + STO; J3 nie |
| Meldung an SPS | – | „Sicherheit OK“, „Zustimmung“, Zustände (nur lesen) |

## 6. Netzwerk am PC

| Anschluss | Teilnehmer |
|---|---|
| LAN 1 | Kamera (eigenes Netz) |
| LAN 2 | PROFINET: 3 × MOVITRAC, E/A-Modul, IO-Link-Master, ggf. Sicherheitssteuerung (Switch) |
| LAN 3 | Büro / Fernwartung, später PLS |

## Summe (grob, ohne SEW und Kamera)

| Block | ca. € |
|---|---|
| Rechner (1.1–1.2) | 2.500–4.800 |
| Schaltschrank (2.1–2.7) | 3.850–7.100 |
| Bedienung und Sicherheit (3.1–3.7) | 1.210–2.330 |
| Prozess (4.1–4.4) | 1.700–5.600 |
| **Gesamt Material** | **ca. 9.200–19.800** |

Zusätzlich: EPLAN, Aufbau und Verdrahtung des Schranks, Konfiguration und Validierung der
Sicherheitssteuerung (Schaltschrankbauer/Elektriker), Inbetriebnahme. SPS-Programm: HETA
(`plc/codesys/`).
