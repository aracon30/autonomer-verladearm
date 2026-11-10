# Betriebsanleitung OMIM-4896: Änderungen für den autonomen Verladearm

Grundlage: `OMIM_Obenverladearm_elektrisch.docx` (Stand Oktober 2026). Die Anleitung beschreibt den
Arm mit **einer** elektrischen Achse (Heben/Senken), Tippbetrieb per Hängetaster, MOVITRAC
classic, Liquiphant + Ultraschall. Für den autonomen Arm (3 Achsen, Kamera, Vision-PC, SPS,
Leitstelle) sind folgende Änderungen nötig. Offene Werte sind mit **[folgt]** markiert.

## Deckblatt und Kapitel 1

- Titel: „Autonomer Obenverladearm mit elektrischen Antrieben (Drehen J1/J2, Heben/Senken J3)“.
- Geltungsbereich um **Kamera, Vision-PC mit Software, SPS und Schnittstelle zur Leitstelle**
  erweitern; Herstellerunterlagen: SEW (Servomotoren, Getriebe, MOVITRAC advanced), IMO
  (Schwenkantrieb), SICK (Kamera), Baumer/E+H (Füllstand, Überfüllsicherung), Beckhoff
  (Industrie-PC C6027 mit TwinCAT 3 und TwinSAFE).
- 1.2 Konformität: Maschinenrichtlinie 2006/42/EG gilt nur für Inverkehrbringen **bis 19.01.2027**,
  danach **Maschinenverordnung (EU) 2023/1230**. Risikobeurteilung und Sicherheitsfunktionen
  (EN ISO 13849, PL je Funktion) für den automatischen Betrieb neu. Keine Ex-Zone bleibt.
- Neu 1.5: Softwarestand (Version Vision-Software, SPS-Programm) und Anlagendatei angeben.

## Kapitel 2 – Technische Daten

| Zeile | alt | neu |
|---|---|---|
| Antriebe | RF47, 0,75 kW (nur Heben/Senken) | J1/J2: SEW CM3C71S + P5KG31 i = 4 + Zahnkranz (i ges. 10,6), Bremse BK1 16 Nm, Geber AZ2Z · J3: RF47 DRN80M4/BE05 + IMO WD-E 0223/3 (i ges. 1 457,6), Geber AK8Z |
| Bewegung | Heben/Senken ±45° | J1 −120…+120°, J2 −140…+140°, J3 −45…+45°, max. 6 °/s je Gelenk |
| Antriebsregelung | MOVITRAC | 3 × SEW MOVITRAC advanced MCX91A (2 × 4 A, 1 × 2,5 A), PROFINET oder EtherCAT [folgt SEW], STO, MOVIKIT Positioning Drive |
| Steuerung | – | Beckhoff C6027 (Windows 11 IoT) mit TwinCAT 3 (SPS, OPC UA) und TwinSAFE, zugleich Vision-PC [Aufstellort Vision folgt]; Schaltschrank NemaSoft |
| Kamera | – | SICK Visionary-T Mini CX (3D), Montage über der Verladestelle |
| Bedienung | Taster Heben/Senken/Reset, Hängetaster XAC-A2713 | Leuchttaster „Beladen starten“, Not-Halt, „Quittieren“, Schlüsselschalter Automatik/Hand, Leuchtmelder; steckbares **Handbediengerät** mit Zustimmtaster, Not-Halt, Achswahl, +/−; Auftrag, Produkt und Kalibrierung aus der **Leitstelle** |
| Sensorik Bewegung | 2 Endlagensensoren, induktiver Hindernissensor | Multiturn-Absolutgeber je Achse, Software-Endlagen, Endlagenschalter [folgt], Hindernissensor Lanze (beibehalten?) [folgt], Lichtschranke Stellplatz, Rückmeldung Klapptreppe |
| Sensorik Füllstand | Liquiphant + Ultraschall | **ein** Sensor fürs Nachziehen (Baumer LBFS am Auslassrohr oder Radar an der Dom-Abdeckung, Entscheidung BASF [folgt]), Maximalhöhe aus Armhöhe, **Überfüllsicherung Baumer LBFS** an der Dom-Abdeckung (keine WHG-/SIL-Anforderung), elektrische Absperrklappe am Anfang des Fallrohrs mit Stellungsrückmeldung. Menge, Pumpe und Füllende: Leitstelle |
| Elektrischer Anschluss / Schaltschrank | 16 A, Rittal AX 500 × 500 × 300 | Leistung und Schrankgröße neu (3 Umrichter, SPS, PC) [folgt Schaltschrankbauer] |
| Gewicht | 251/326 kg | neu mit Antrieben J1/J2 und Zahnkränzen [folgt] |
| Abtropfen | – | **mechanische Abtropfsicherung** (Pendelwanne, vom Rohrende geöffnet), ohne Antrieb und ohne Signale |
| Neu | – | Umgebungstemperatur −20…+40 °C (Getriebe J1/J2 −15 °C, zurückgestellt), Windgrenze für Automatik [folgt], Netzwerk/Schnittstellen (EtherCAT/PROFINET, OPC UA, PLS) |

## Kapitel 3 – Aufbau und Funktion

Neu schreiben:
- Drei Achsen, Arm faltet sich in die Parkstellung; Kamera, Vision-PC, SPS und ihre Aufgaben
  (PC misst und plant kollisionsfreie Bahnen, SPS fährt, prüft und überwacht).
- **Automatischer Ablauf:** Leitstelle gibt Auftrag/Produkt frei → Bediener drückt „Beladen
  starten“ → Dom messen → über den Dom fahren → nachmessen → senkrecht eintauchen → Klappe auf,
  „Arm bereit“ → Leitstelle befüllt, Arm zieht nach → Füllende der Leitstelle (oder Maximalhöhe)
  → Pumpe aus → Verdrängen/Spülen mit Klappe offen [Ablauf folgt BASF] → Klappe zu, Abtropfen →
  nächste Kammer oder Rückfahrt in die Parkstellung.
- Satz „Der Antrieb bewegt sich nur, solange ein Taster gedrückt ist“ gilt nur noch im
  Handbetrieb.
- Haltebremsen an allen Achsen; J1/J2 nicht selbsthemmend, J3 Selbsthemmung nicht zugesichert.

## Kapitel 4 – Sicherheit

- 4.4 Personal: neu **Leitstand-Personal** (Freigabe, Produkt, Kalibrierung anstoßen) und
  **Servicepersonal Software/Kalibrierung**.
- 4.6 Restrisiken neu:
  - Arm bewegt sich nach dem Start **selbsttätig** (kein Tippbetrieb) → Bereich frei, Start nur vor
    Ort mit Sicht, Klapptreppe und Lichtschranke verriegelt.
  - Kamera erkennt nicht alles (verdeckt, Spiegelung, Regen/Schnee/Gegenlicht, Personen auf dem
    Fahrzeug) → kein Personal auf dem Fahrzeug während der Automatik.
  - Wind beim Schwenken → Windgrenze.
  - Bremse lüften: J1/J2 kann durch Wind wegdrehen; **J3 nie lüften** (Arm sackt ab).
  - Überfüllung → unabhängige Überfüllsicherung wirkt direkt auf die Absperrklappe.
  - Fernstart/Fernhandbetrieb aus der Leitstelle **nicht zulässig**.
  - IT-Sicherheit: Vision-PC und Netzwerk nur im internen Netz, Zugänge geschützt.
- 4.7 Schutzeinrichtungen ergänzen: Zustimmtaster, STO je Umrichter, Software-Endlagen,
  Verriegelung Klapptreppe/Lichtschranke, Heartbeat-Überwachung PC↔SPS, Überfüllsicherung.

## Kapitel 5 – Warnhinweise

Neu: „Automatische Bewegung nach dem Start“, „Bremse J3 nie lüften“, „Bremse J1/J2 lüften nur im
Handbetrieb, Arm gegen Wegdrehen sichern“, Restspannung MOVITRAC advanced [Zeit laut SEW folgt],
Not-Halt und Quittieren nur vor Ort. Hindernissensor-Hinweis anpassen (im Automatikbetrieb
übernimmt die Kamera die Hinderniserkennung, nichtmetallische Hindernisse nur, wenn sichtbar).

## Kapitel 6 – Störungen

Ergänzen: Bedeutung der Leuchtmelder; Vision-Fehler (keine Öffnung erkannt, mehrere Öffnungen,
nicht erreichbar, Kollision, Auslass nicht gefunden, Kamera nicht verfügbar – Codes aus
`docs/schnittstelle.md`), Heartbeat-Ausfall, Lichtschranke frei, Klapptreppe nicht in Ruhelage,
Überfüllsicherung ausgelöst, Nachziehen am Ende (Maximalhöhe), Sensor Nachziehen meldet nach dem
Hub weiter „nass“ (Belag), Leitstelle beendet nicht, Kamera verschmutzt,
Rückfahrt nicht möglich → Handbetrieb mit Handbediengerät oder „Automatisch in Parkstellung“.
Stromausfall: Bremsen halten, Absolutgeber behalten die Lage, keine Referenzfahrt.

## Kapitel 7 – Montage

- Kamera über der Verladestelle montieren (Höhe, Ausrichtung, Netzwerk), Vision-PC im Schaltschrank.
- Ausrichten (90° rechts/links schwenken) jetzt mit Handbediengerät statt von Hand.
- Elektrischer Anschluss nach neuem Stromlaufplan [folgt]; SEW-Hybridkabel (SD1/KD1),
  Kabelführung am Arm (Verdrehung J1/J2).
- 7.4 Prüfung je Achse: Drehrichtung, Software- und Hardware-Endlagen, Not-Halt/STO, Bremsen
  (Bremsentest), Nullpunkt der Absolutgeber, Parkstellung, Verriegelungen.

## Kapitel 8 – Inbetriebnahme

Neu: Anlagendatei einrichten (Konfigurator), Kalibrierung Kamera↔Arm, Inbetriebnahmeprüfung
(Bericht), Probelauf ohne Produkt, Test Überfüllsicherung und Absperrklappe, Test Leitstelle,
Abnahme mit Protokoll (`docs/inbetriebnahme.md`).

## Kapitel 9 – Bedienung (neu schreiben)

- **Automatik:** Voraussetzungen (Fahrzeug steht, geerdet, Dom offen, Klapptreppe in Ruhelage,
  niemand auf dem Fahrzeug, Freigabe Leitstelle) → „Beladen starten“ → Ablauf überwachen →
  Ende automatisch; Fahrzeug erst bei grüner Anzeige wegfahren.
- **Handbetrieb** (Schlüsselschalter, Handbediengerät, Zustimmtaster, Tippen je Achse, Bremse
  J1/J2 lüften, J3 gesperrt); danach „Automatisch in Parkstellung“.
- **Not-Halt und Quittieren** vor Ort.
- **Kalibrierung** aus der Leitstelle anstoßen, vor Ort freigeben.
- Abschnitte zum Senken per Taste und zum Hängetaster entfallen.

## Kapitel 10 – Wartung

Ergänzen: Kamerafenster reinigen, Kalibrierung prüfen (Prüfstellung), Bremsentest, Getriebe
(SEW/IMO-Intervalle), Ritzel/Zahnkranz J1/J2 schmieren und Flankenspiel prüfen, Kabel am Arm,
Datensicherung Anlagendatei/Software, Software-Updates nur durch HETA. Füllrohr wöchentlich mit
Hochdruck reinigen (Vorgabe BASF; Ausführung am Arm [folgt Konstruktion]), Sensoren Füllstand und
Überfüllsicherung reinigen und prüfen, Abtropfsicherung (Gelenk, Feder, Gleitstück) prüfen.

## Kapitel 11 – Ersatzteile

Neu: Servomotor J1/J2 mit Getriebe, Getriebemotor J3, IMO-Schwenkantrieb, 3 Umrichter
(Speichermodul CMM11A), Kamera, Beckhoff-IPC und E/A-Klemmen, Handbediengerät, Ritzel/Zahnkranz,
Sensoren Füllstand/Überfüllsicherung, Absperrklappe. Ultraschallsensor, Hängetaster und
MOVITRAC classic entfallen. Teilenummern [folgt].

## Kapitel 13 und 14

- Außerbetriebnahme: Arm in die Parkstellung, Daten sichern.
- Mitgeltend: SEW-Unterlagen (CM3C, P5KG, RF47/DRN, MOVITRAC advanced, MOVIKIT Positioning Drive
  33350930), IMO WD-E, SICK-Kamera, Füllstandsensoren (Baumer/E+H), Beckhoff C6027 und TwinCAT,
  Risikobeurteilung, Stromlaufplan neu, Software-Dokumentation (Schnittstelle, Inbetriebnahme).
