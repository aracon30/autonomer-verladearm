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

## J1 und J2 – Drehen am Haltepunkt / am Fallrohr

SEW-Angebot **426368452A** vom 18.09.2026 (Version A, Getriebe P5KG31), je Achse 1 Stück,
1.620,78 € netto, Lieferzeit ca. 4–6 Wochen.

| | Wert |
|---|---|
| Typ | **P5KG31-0004/N/S/0 MD071A CM3C71S-20A-D/PK/RH1M/SM1** |
| Planetengetriebe | P5KG31, **i = 4**, Ma_N 81 Nm, Ma_pk 132 Nm, **Verdrehspiel 5′**, IP65, Welle 22 × 36 mit Passfeder |
| Servomotor | CM3C71S (Synchron-Servo), nN 2000 1/min, **M0 6,5 Nm**, Mpk 19,5 Nm, I0 3,5 A, Imax 12,2 A, 400 V, IP65, S9 |
| Geber | **RH1M Resolver** (2-polig) – **kein Absolutwert** über mehrere Umdrehungen |
| Bremse | **keine** (kein /B.. in der Typenbezeichnung) |
| Temperatur | PK (PT1000) |
| Anschluss | SM1-Steckverbinder (SpeedTec) |
| Gewicht | 9,9 kg |

### Bewertung

- **Zahnradstufe (Angabe HETA):** Ritzel auf der Getriebeabtriebswelle, großer Zahnkranz um die
  Rohrleitung, **kein Schneckengetriebe**. Übersetzung i_Z = Zähne Zahnkranz ÷ Zähne Ritzel
  **offen**. Gesamtübersetzung = 4 × i_Z.
- **Nicht selbsthemmend** (Stirnradstufe) → **Haltebremse am Servo notwendig**.
- **Moment:** 6,5 Nm × 4 × i_Z × ~0,92 → bei i_Z = 5/8/10: ca. 120/190/240 Nm dauernd,
  Spitze (Getriebe 132 Nm) 640/1 020/1 280 Nm. Für ca. 1 kNm Dauerlast (Wind, Reibung der
  Drehgelenke) wäre eine Gesamtübersetzung von ca. 170 nötig → mit bekanntem i_Z prüfen, ggf.
  Planetengetriebe mit größerer Übersetzung bei SEW anfragen (dreht der Motor dann auch näher
  an seiner Nenndrehzahl statt bei wenigen 100 1/min).
- **Spiel:** Ritzel/Zahnkranz hat Flankenspiel; ohne Schwerkraft-Vorspannung wirkt es in beide
  Richtungen → Ziel immer aus derselben Richtung anfahren oder verspanntes Ritzel; Rest gleicht
  Job 2 aus. Gelenkgeber am Zahnkranz würde das Spiel mitmessen.
- **Moment am Gelenk** = 6,5 Nm × 4 × 0,95 × i_S × Wirkungsgrad Schnecke. Bei i_S = 34:
  ca. 340–420 Nm dauernd, 1,0–1,3 kNm Spitze. Last: Beschleunigen gering (Trägheit J1 grob
  1 700 kg·m² → ca. 90 Nm für 6 °/s in 2 s), aber **Wind** (ca. 0,9 kNm bei 20 m/s, 1 m²,
  3 m Hebel) und **Reibung der Rohrdrehgelenke** unter Druck. → Lastannahme J1/J2 festlegen
  (wie 3,52 kNm für J3 an IMO) und nachrechnen.
- **Servo braucht Servoumrichter** (z. B. MOVIDRIVE, MOVI-C) – MOVITRAC classic kann ihn nicht
  betreiben. Passt zu Weg 1 (alle Achsen SEW mit Geberauswertung).
- **Resolver = nur inkremental über Umdrehungen:** nach jedem Einschalten **Referenzfahrt**
  (Endschalter/Referenznocken). Besser: bei SEW **Multiturn-Absolutwertgeber** statt RH1M
  anfragen, oder Absolutwertgeber am Gelenk als zweiten Geber am Umrichter.
- **Keine Bremse:** J1/J2 drehen um (fast) senkrechte Achsen, Schwerkraft wirkt kaum. Ohne
  Bremse kann Wind den Arm aber bei abgeschaltetem Antrieb (Not-Halt/STO) verdrehen, und die
  Schnecke hält nicht sicher → **Haltebremse** empfohlen, sofern der Schwenkantrieb nicht
  sicher selbsthemmend ist.
- **Spiel:** Planetengetriebe 5′ (am Gelenk ÷ i_S vernachlässigbar); Spiel des Schwenkantriebs
  zählt. Anders als bei J3 drückt keine Schwerkraft das Spiel auf eine Seite → Job 2
  (Nachmessen) gleicht aus.
- **Ex-Schutz:** IP65, kein Ex – wie bei J3 klären.
