# Antriebe Verladearm HETA (Stand Zeichnung / Datenblätter)

Je Achse: Motor, Getriebe, Geber, Bremse, Ansteuerung. Offene Punkte sind mit **offen** markiert.

## J3 – Ausleger heben/senken (Schwenkantrieb Pos. 4, Motor Pos. 11)

> Zuordnung zu J3 durch den Schwenkantrieb bestätigt (Schwenkwinkel 90° = ±45°).
> **Praxistest 30.09.2026:** Handbetrieb am Prototyp mit Getriebemotor, Schwenkantrieb und
> Bremse ohne Befund (Heben, Senken, Halten). Prototyp derzeit **ohne Drehgeber**; Gebertyp bei
> SEW angefragt.

| | Wert |
|---|---|
| Getriebemotor | SEW-Eurodrive **RF47 DRN80M4/BE05/TF** (Stirnrad-Getriebemotor, Flanschausführung) |
| Motor | Drehstrom-Asynchronmotor 4-polig, 0,75 kW, IE3, 230/400 V Δ/Y, 1,75 A (400 V), S1 |
| Drehzahl | 1440 → **34 1/min** am Getriebeabtrieb, i = 42,87 |
| Abtriebsmoment | 215 Nm (Ma max 300 Nm), Betriebsfaktor 1,40 |
| Bremse | BE05, 230 V AC, **1,8 Nm** (motorseitig), Gleichrichter BG1.5 |
| Temperaturschutz | TF (Kaltleiter) |
| Geber | **Motorgeber von SEW wird nachgerüstet** (Typ **offen**: Absolutwert multiturn empfohlen, z. B. AK0H; inkremental z. B. EI7C nur mit Referenzfahrt) |
| Schutzart | IP55, −20 … +40 °C, **kein Ex-Schutz** |
| Gewicht | 31,3 kg |
| Schwenkantrieb Pos. 4 | **IMO WD-E 0223/3** (Schneckengetriebe), IMO-Projekt 10000481356, Technical Notes 10.12.2025 |
| Md max (dynamisch, inkl. Stöße) | **9 500 Nm** |
| Mh max (statisch, Halten) | **11 000 Nm** |
| Auslegung (Lastfälle HETA) | Betriebs-/Haltemoment 3,52 kNm und 2,24 kNm, Kippmoment 0,657 kNm, Radiallast 2 kN, je 50 % ED |
| Abtriebsdrehzahl max | **1 1/min** (= 6 °/s) |
| Einschaltdauer | max. 58 % bzw. 69 % Schwenkzeit je Minute |
| Lebensdauer (Auslegung) | 480 h Schwenkzeit gesamt |
| Selbsthemmung | **nicht zugesichert** (theoretisch bei Wirkungsgrad < 50 %), am gelieferten Antrieb prüfen → Bremse nötig |
| Motoranbindung | Adapterwelle: max. 1 200 Nm (1 1/4"-Keilwelle) bzw. 600 Nm (Ø 25 Passfeder / 1"-Keilwelle) |
| Einbau | Antriebswelle **nicht oben**; Grundierung reicht außen nicht (Deckanstrich, Dichtungen nicht überstreichen); kein Hochdruckreiniger; −20 … +70 °C |
| Verzahnung | Modul 4,5 mm, Schnecke **2-gängig**, **i_S = 34**, 1 Antrieb |
| Lager | radial und Kippspiel 0 (vorgespannt) |
| Verzahnungsspiel | **offen** |
| Beschichtung / Fett | Einschichtlack RAL 9005; Fett DIN 51502 KPF 1 R-20 |

| Umrichter | SEW **MOVITRAC classic MCC91A-0032-5E3-4-…** (Typenschild), 3 × 200–500 V, 1,1 kW ASM, Ausgang 3,2 A (max. 4,8 A), 0–599 Hz, −10 … +40 °C; Gateway laut Typenschild vermutlich CFX11A (PROFINET) – **bestätigen** |

### Bewertung

- **Kein Servomotor**, sondern Asynchron-Getriebemotor mit Bremse. Sanftes Anfahren/Bremsen
  über einen **Frequenzumrichter** mit Rampen (z. B. SEW MOVITRAC/MOVIDRIVE oder Siemens
  SINAMICS G120, PROFINET). TF und Bremse am Umrichter anschließen.
- **Geber am Motor (SEW)** statt am Gelenk. Gelenkwinkel = Motorwinkel ÷ (42,87 × i_S);
  Auflösung am Gelenk sehr fein. Das Getriebespiel wird nicht gemessen – bei J3 unkritisch, weil
  das Gewicht des Auslegers die Zahnflanken immer in dieselbe Richtung andrückt (Spiel ist
  vorgespannt). Restfehler gleicht Job 2 (Nachmessen) aus. Ein Gelenkgeber an J3 entfällt.
- **Entscheidung 30.09.2026: Weg 1** – SEW-Umrichter mit Geberauswertung und Positionierung
  (z. B. MOVITRAC advanced oder MOVIDRIVE) + SEW-Motorgeber (Absolutwert multiturn). Anfrage an
  SEW läuft. Offen: Positionierung im Umrichter (SPS gibt Ziel und Geschwindigkeit je Stützpunkt
  vor) oder als Positionierachse in der S7-1500 (PROFIdrive) – mit SEW und SPS-Programmierer
  festlegen; für die synchrone Fahrt der drei Achsen muss die SPS je Stützpunkt die
  Geschwindigkeiten so skalieren, dass alle Achsen gleichzeitig ankommen.
- **Umrichter und Geber:** MOVITRAC classic ist laut SEW für Motoren **ohne Geber** gedacht
  (Drehzahlsteuerung mit Rampen). Einen Motorgeber wertet er nach unseren Unterlagen nicht aus
  → mit SEW klären. Wege:
  1. Umrichter mit Geberauswertung/Positionierung (z. B. MOVITRAC advanced oder MOVIDRIVE)
     und SEW-Motorgeber.
  2. MOVITRAC classic behalten (Drehzahl + Rampen über PROFINET) und einen **Absolutwertgeber,
     den die SPS direkt liest** (PROFINET-Geber am Gelenk oder SSI-Motorgeber an einer
     SPS-Zählerbaugruppe); S7-1500 Positionierachse mit Drehzahlsollwert + externem Geber.
- **Bremswiderstand** für das Senken am MOVITRAC prüfen (vorhanden/angeschlossen?).
- **Absolut oder inkremental:** Multiturn-Absolutwertgeber → Position sofort nach dem
  Einschalten. 90° am Gelenk ≈ 0,25 × 42,87 × i_S Motorumdrehungen (bei i_S = 60 ca. 640) –
  innerhalb von 4096 Umdrehungen üblicher Multiturngeber. Inkrementalgeber → nach jedem
  Einschalten Referenzfahrt auf Endschalter/Referenznocken.
- **Ansteuerung:** Geber an einen SEW-Umrichter mit Geberauswertung (z. B. MOVIDRIVE/MOVI-C,
  PROFINET), S7-1500 Positionierachse über PROFIdrive-Telegramm (z. B. 105) oder SEW-Positionier-
  baustein. Bei Umrichtern anderer Hersteller Geberschnittstelle (Hiperface/SSI …) prüfen.
- **Gesamtübersetzung** 42,87 × 34 = **1458**: eine Motorumdrehung = 0,25° am Gelenk,
  90° = 364 Motorumdrehungen (passt in Multiturngeber mit 4096 Umdrehungen).
- **Geschwindigkeit:** 34 1/min ÷ 34 = **1 1/min = 6 °/s** bei 50 Hz – genau die zulässige
  Höchstdrehzahl des Schwenkantriebs. 90° in 15 s. Umrichter auf max. 50 Hz begrenzen,
  Technologieobjekt J3 z. B. 5 °/s Anfahrt, 1–2 °/s beim Eintauchen.
- **Moment:** Last laut IMO-Auslegung 3,52 kNm, eigene Schätzung 1,6–2,0 kNm. Verfügbar
  215 Nm × 34 × Wirkungsgrad: bei η = 0,4/0,5/0,6 → 2,9/3,7/4,4 kNm (kurzzeitig mit 300 Nm
  4,1/5,1/6,1 kNm). Für die geschätzte Last reichlich, für 3,52 kNm **knapp** → Lastannahme
  3,52 kNm klären und Wirkungsgrad bei IMO erfragen. Momentbegrenzung im Umrichter auf
  ≤ 300 Nm Getriebeabtrieb (IMO-Hinweis, Adapterwelle ≥ 600 Nm).
- **Senken und Bremswiderstand:** 2-gängige Schnecken sind oft **nicht selbsthemmend**. Beim
  Senken treibt das Gewicht den Motor → Umrichter mit **Bremswiderstand** (bzw. Bremschopper).
- **Haltebremse:** 1,8 Nm × 1458 = 2,6 kNm ohne Reibung; mit Rückwärts-Wirkungsgrad 0,5
  genügen rechnerisch 1,2 Nm für 3,52 kNm. Ausreichend, aber mit wenig Reserve bei
  unbekanntem Wirkungsgrad → bei SEW höheres Bremsmoment der BE05 anfragen; Haltetest bei der
  Inbetriebnahme mit gefülltem Ausleger.
- **Lebensdauer:** 480 h Schwenkzeit; bei ca. 1 min J3-Bewegung je Verladung ≈ 29 000
  Verladungen. Mit der geplanten Verladezahl pro Jahr abgleichen.
- **Ex-Schutz:** IP55 ohne Ex-Kennzeichnung. Liegt der Arm in einer Ex-Zone, ist ein Motor in
  ATEX-Ausführung nötig (Zoneneinteilung klären, Lastenheft N-06).

## J1 – Drehen am Haltepunkt

**offen** (Datenblatt folgt)

## J2 – Drehen am Fallrohr

**offen** (Datenblatt folgt)
