# Antriebsliste Verladearm HETA (für Angebot Schaltschrank/Software)

Stand Oktober 2026. Details und Herleitung: `hardware/antriebe.md`. Geber, Bremse J1/J2 und
Umrichter sind bei SEW angefragt (`hardware/anfrage_sew_geber_bremse.md`) – Typen nach Angebot
ergänzen.

| | J1 – Drehen am Haltepunkt | J2 – Drehen am Fallrohr | J3 – Ausleger heben/senken |
|---|---|---|---|
| Motor | SEW **CM3C71S** Synchron-Servo, 400 V, M0 6,5 Nm, Mpk 19,5 Nm, I0 3,5 A, Imax 12,2 A, nN 2000 1/min, nN 2000 1/min, Nennstrom 3,32 A, S9, PK (PT1000), Stecker SM1 SpeedTec (passende SEW-Kabel nötig) | wie J1 | SEW **DRN80M4** Drehstrom-Asynchronmotor (Bestand), 0,75 kW, 400 V Y, 1,75 A, 1440 1/min, IE3, TF |
| Getriebe | Planetengetriebe **P5KG31 i = 4** (Verdrehspiel 5′) + Ritzel z 48 / Zahnkranz z 127, Modul 2 → **i = 10,58** | wie J1 | Stirnradgetriebe **RF47 i = 42,87** + Schwenkantrieb **IMO WD-E 0223/3**, Schnecke i = 34 → **i = 1457,6** |
| Bremse | Haltebremse 24 V DC – **angefragt** | Haltebremse 24 V DC – **angefragt** | **BE05**, 230 V AC, 1,8 Nm, Gleichrichter BG1.5 (vorhanden) |
| Geber | Multiturn-Absolutwertgeber am Motor – **angefragt** (statt Resolver RH1M) | wie J1 | Multiturn-Absolutwertgeber nachrüsten – **angefragt** |
| Umrichter | SEW mit Geberauswertung, **PROFINET** (bzw. EtherCAT bei Beckhoff), **STO**, Bremsenansteuerung – **angefragt** | wie J1 | wie J1; bisher MOVITRAC classic MCC91A-0032-5E3-4 (ohne Geberauswertung, entfällt bzw. Ersatz) |
| Ansteuerung | Positionierachse (Technologieobjekt), synchron mit J2/J3 | wie J1 | wie J1 |
| Drehbereich am Gelenk | −120 … +120° (verzahnt ca. 296°) | −140 … +140° | −45 … +45° |
| Geschwindigkeit am Gelenk | max. 6 °/s, Rampe ca. 4 s | max. 6 °/s, Rampe ca. 2 s | max. 6 °/s (IMO: 1 1/min), Rampe ca. 1,5 s |
| Moment am Gelenk | ca. 63 Nm dauernd / 190 Nm Spitze | wie J1 | ca. 3,3 kNm dauernd (IMO Md max 9,5 kNm) |
| Last (Schätzung) | Trägheit ca. 1 700 kg·m², Wind | ca. 500 kg·m² | Gewicht Ausleger; Spiel durch Schwerkraft vorgespannt |
| Besonderheit | nicht selbsthemmend → Bremse gegen Wind | nicht selbsthemmend → Bremse | Selbsthemmung **nicht zugesichert** → Bremse nie im Handbetrieb lüften |

**Umgebung:** im Freien, −20 … +40 °C, Motoren IP65 bzw. IP55 (J3). Explosionsschutz: Zone noch
offen (Lastenheft N-06) – Auswirkung auf Motoren und Geber klären.

**Weitere Antriebe / Aktoren im Schaltschrankumfang:**
- Absperrklappe in der Fallleitung (DN 100) mit Antrieb und Stellungsrückmeldung – Typ offen
- Klapptreppe: vorhandene Steuerung; Rückmeldung „eingefahren“ als Sicherheitssignal
