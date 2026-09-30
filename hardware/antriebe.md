# Antriebe Verladearm HETA (Stand Zeichnung / Datenblätter)

Je Achse: Motor, Getriebe, Geber, Bremse, Ansteuerung. Offene Punkte sind mit **offen** markiert.

## J3 – Ausleger heben/senken (Schwenkantrieb Pos. 4, Motor Pos. 11)

> Zuordnung zu J3 durch den Schwenkantrieb bestätigt (Schwenkwinkel 90° = ±45°).

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
| Übersetzung, Spiel | **offen** (nicht in den Technical Notes) |

### Bewertung

- **Kein Servomotor**, sondern Asynchron-Getriebemotor mit Bremse. Sanftes Anfahren/Bremsen
  über einen **Frequenzumrichter** mit Rampen (z. B. SEW MOVITRAC/MOVIDRIVE oder Siemens
  SINAMICS G120, PROFINET). TF und Bremse am Umrichter anschließen.
- **Geber am Motor (SEW)** statt am Gelenk. Gelenkwinkel = Motorwinkel ÷ (42,87 × i_S);
  Auflösung am Gelenk sehr fein. Das Getriebespiel wird nicht gemessen – bei J3 unkritisch, weil
  das Gewicht des Auslegers die Zahnflanken immer in dieselbe Richtung andrückt (Spiel ist
  vorgespannt). Restfehler gleicht Job 2 (Nachmessen) aus. Ein Gelenkgeber an J3 entfällt.
- **Absolut oder inkremental:** Multiturn-Absolutwertgeber → Position sofort nach dem
  Einschalten. 90° am Gelenk ≈ 0,25 × 42,87 × i_S Motorumdrehungen (bei i_S = 60 ca. 640) –
  innerhalb von 4096 Umdrehungen üblicher Multiturngeber. Inkrementalgeber → nach jedem
  Einschalten Referenzfahrt auf Endschalter/Referenznocken.
- **Ansteuerung:** Geber an einen SEW-Umrichter mit Geberauswertung (z. B. MOVIDRIVE/MOVI-C,
  PROFINET), S7-1500 Positionierachse über PROFIdrive-Telegramm (z. B. 105) oder SEW-Positionier-
  baustein. Bei Umrichtern anderer Hersteller Geberschnittstelle (Hiperface/SSI …) prüfen.
- **Lastmoment J3:** Auslegung IMO mit 3,52 kNm (HETA-Vorgabe); eigene Schätzung (Rohr
  114,3 × 3,6, Ausleger waagerecht) 1,6 kNm leer, 2,0 kNm gefüllt. Reserve zu Md max 9,5 kNm
  und Mh max 11 kNm groß.
- **Motor ↔ Schwenkantrieb:** Getriebemotor max. 300 Nm < 600 Nm (kleinste Adapterwelle) – passt.
  IMO empfiehlt trotzdem eine **Momentbegrenzung im Umrichter**; zusammen mit der Übersetzung
  i_S des Schwenkantriebs muss 215 Nm × i_S × Wirkungsgrad (~0,3–0,5) über 3,52 kNm liegen,
  also i_S ≳ 35–55 – mit Übersetzung aus dem Datenblatt nachrechnen.
- **Drehzahl:** 34 1/min ÷ i_S darf 1 1/min nicht überschreiten → i_S ≥ 34, sonst im Umrichter
  begrenzen. **Technologieobjekt J3: v max 6 °/s**, beim Eintauchen deutlich weniger.
- **Haltebremse:** notwendig (Selbsthemmung nicht zugesichert). 1,8 Nm × 42,87 × i_S am Gelenk,
  bei i_S = 50 rechnerisch 3,9 kNm – knapp über 3,52 kNm. Bremsmoment der BE05 ggf. höher
  einstellen lassen (bis 5 Nm möglich), Selbsthemmung bei Inbetriebnahme prüfen.
- **Lebensdauer:** 480 h Schwenkzeit; bei ca. 1 min J3-Bewegung je Verladung ≈ 29 000
  Verladungen. Mit der geplanten Verladezahl pro Jahr abgleichen.
- **Ex-Schutz:** IP55 ohne Ex-Kennzeichnung. Liegt der Arm in einer Ex-Zone, ist ein Motor in
  ATEX-Ausführung nötig (Zoneneinteilung klären, Lastenheft N-06).

## J1 – Drehen am Haltepunkt

**offen** (Datenblatt folgt)

## J2 – Drehen am Fallrohr

**offen** (Datenblatt folgt)
