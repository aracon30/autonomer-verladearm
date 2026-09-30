# Antriebe Verladearm HETA (Stand Zeichnung / Datenblätter)

Je Achse: Motor, Getriebe, Geber, Bremse, Ansteuerung. Offene Punkte sind mit **offen** markiert.

## J3 – Ausleger heben/senken (Schwenkantrieb Pos. 4, Motor Pos. 11)

> Zuordnung zu J3 angenommen (Datenblatt ohne Achsangabe übergeben) – **bestätigen**.

| | Wert |
|---|---|
| Getriebemotor | SEW-Eurodrive **RF47 DRN80M4/BE05/TF** (Stirnrad-Getriebemotor, Flanschausführung) |
| Motor | Drehstrom-Asynchronmotor 4-polig, 0,75 kW, IE3, 230/400 V Δ/Y, 1,75 A (400 V), S1 |
| Drehzahl | 1440 → **34 1/min** am Getriebeabtrieb, i = 42,87 |
| Abtriebsmoment | 215 Nm (Ma max 300 Nm), Betriebsfaktor 1,40 |
| Bremse | BE05, 230 V AC, **1,8 Nm** (motorseitig), Gleichrichter BG1.5 |
| Temperaturschutz | TF (Kaltleiter) |
| Geber | **keiner** (kein /EI.. oder /AK.. in der Typenbezeichnung) |
| Schutzart | IP55, −20 … +40 °C, **kein Ex-Schutz** |
| Gewicht | 31,3 kg |
| Schwenkantrieb Pos. 4 | **offen**: Hersteller/Typ, Übersetzung, Abtriebs- und Haltemoment, Spiel, selbsthemmend? |

### Bewertung

- **Kein Servomotor**, sondern Asynchron-Getriebemotor mit Bremse. Sanftes Anfahren/Bremsen
  über einen **Frequenzumrichter** mit Rampen (z. B. SEW MOVITRAC/MOVIDRIVE oder Siemens
  SINAMICS G120, PROFINET). TF und Bremse am Umrichter anschließen.
- **Positionieren nur mit Geber.** Empfehlung: Absolutwertgeber am Gelenk (Stückliste Pos. 16),
  S7-1500 Positionierachse mit Drehzahlsollwert an den Umrichter und Gelenkgeber als Istwert.
  Alternativ Motorgeber nachrüsten (SEW-Option), dann bleibt das Getriebespiel ungemessen.
- **Lastmoment J3** (Schätzung, Rohr 114,3 × 3,6, Ausleger waagerecht): ca. 1,6 kNm leer,
  ca. 2,0 kNm mit gefülltem äußeren Ausleger; zzgl. Flansche/J4 grob mit 30 kg angesetzt.
  Mit 215 Nm am Getriebeabtrieb reicht das nur mit einer Übersetzung im Schwenkantrieb von
  **mindestens ca. 20–30** (bei Schnecke Wirkungsgrad ~0,5). Nachrechnen, sobald Pos. 4 bekannt.
- **Haltebremse:** 1,8 Nm am Motor ergeben mit i = 42,87 und Schwenkantrieb i = 50 rechnerisch
  ca. 3,9 kNm – ausreichend, falls der Schwenkantrieb nicht ohnehin selbsthemmend ist.
- **Geschwindigkeit am Gelenk:** 34 1/min ÷ Übersetzung Schwenkantrieb, z. B. i = 50 → 4 °/s,
  90° in ca. 22 s. Für die Anfahrt ausreichend, beim Eintauchen reduzieren.
- **Ex-Schutz:** IP55 ohne Ex-Kennzeichnung. Liegt der Arm in einer Ex-Zone, ist ein Motor in
  ATEX-Ausführung nötig (Zoneneinteilung klären, Lastenheft N-06).

## J1 – Drehen am Haltepunkt

**offen** (Datenblatt folgt)

## J2 – Drehen am Fallrohr

**offen** (Datenblatt folgt)
