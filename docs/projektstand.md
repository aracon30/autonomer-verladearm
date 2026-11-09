# Projektstand Verladearm (Stand 09.11.2026)

**Auftragsnummer HETA: K-04896/26** (interner Entwicklungsauftrag, ersetzt K-04793/26; Fabrik-Nr. 4896-01, Unterlagen OMIM-4896 / SWD-4896). Nicht in Unterlagen für Lieferanten bzw. Peter.

Überblick über Entscheidungen, Lieferantenanfragen und offene Punkte. Details stehen in den
verlinkten Dokumenten.

## Entscheidungen

| Datum | Thema | Entscheidung | Details |
|---|---|---|---|
| 30.09. | Antriebe J1/J2 | Servo CM3C71S + P5KG31 i = 4 + Zahnkranz (Konstruktion), Multiturn-Absolutgeber, Haltebremse | `hardware/antriebe.md` |
| 30.09. | J3 | IMO-Schwenkantrieb WD-E 0223/3 mit SEW-Getriebemotor, Geber **am Motor** (nicht am Schwenkantrieb) | `hardware/antriebe.md` |
| 06.10. | Architektur | PC plant (Gelenkwinkel-Stützpunkte), SPS fährt und prüft; Vergleich Siemens/Beckhoff beim Automatisierungspartner | `docs/besprechungen/2026-10-06_automatisierung.md` |
| 12.10. | Selbstkollision | Bahnplanung prüft den Arm gegen sich selbst (Mindestspalt 0,10 m) | `docs/kinematik.md` |
| 15.10. | Geber J1/J2 | **kein Sicherheitsgeber**: J1 wie J2 mit AZ2Z und Direktanbau MD071A (Änderung bei SEW angefragt) | `hardware/antriebe.md` |
| 16.10. | Umrichter | MOVITRAC advanced mit **MOVIKIT Positioning Drive (Level 1)**; Synchronfahrt koordiniert die SPS (v/a je Achse skaliert, gleiche Ruckzeit) | `hardware/antriebe.md`, `docs/schnittstelle.md` |
| 27.10. | Mehrere Dome | **Schnittstelle Version 3**: Auftrag als Füllschritte (Dom, Menge); `DomeNo` 0 = automatisch (Kammern verbunden, Schwallwände), n = n-ter offener Dom von vorn (Mehrkammer); zwischen den Kammern senkrecht heraus und Job 1 vom vorigen Dom aus. Plausibilität (erwartete Zahl offener Dome) noch nicht | `docs/schnittstelle.md` |
| 09.11. | Befüllung | **Menge, Pumpe und Füllende steuert die Leitstelle (BASF)**, kein eigener Durchflussmesser. **Absperrklappe gehört zum Arm** (HETA-SPS): Leitstelle meldet „Befüllung Start“/„Ende“; die SPS öffnet die Klappe nur, wenn der Arm „bereit/in Position“ meldet, und schließt sie bei „Ende“, bei Störung/Not-Halt oder wenn der Arm nicht weiter nachziehen kann (Maximalhöhe). An die Leitstelle: „Arm bereit“, „Störung/Befüllung stoppen“. Nachziehen über **einen** Grenzschalter (ca. 100 mm über Auslass, Hub 50 mm). Offen: Pumpe darf nicht gegen die geschlossene Klappe fördern (Reihenfolge/Signal mit BASF klären) | `docs/fuellstand_ueberfuellsicherung.md` |
| 04.11. | Abtropfsicherung | **rein mechanische Lösung** (in Arbeit, Konstruktion); kein Motor, keine Endschalter, keine Signale an die SPS – ersetzt den Antrieb aus Skizze Rev. 3 | `docs/skizzen/` |
| 26.10. | Übersetzung J1/J2 | i = 10,6 wird **ohne Rückfrage bei SEW** angenommen; Regelung bei der Inbetriebnahme mit flachen Rampen einstellen | `hardware/antriebe.md` |
| 26.10. | Füllende | Schutzebenen: 1. Sollmenge (Durchfluss), 2. Maximalhöhe aus Armhöhe + Grenzschaltern, 3. Überfüllsicherung **nur als letzte Ebene, nie betriebsmäßig** | `docs/fuellstand_ueberfuellsicherung.md` |
| 26.10. | Nachziehen | **zwei kapazitive Grenzschalter** (A 1 cm, B 3 cm über Auslassende) statt Messstab; Test mit Produkt (Anhaftung, Schaum) macht **BASF** (27.10.), HETA testet nicht selbst; LFP Cubic zurückgestellt | `docs/fuellstand_ueberfuellsicherung.md` |
| 19.10. | Bedienung | Schaltschrank **ohne Display**: Leuchttaster „Beladen starten“, Not-Halt, Quittieren, Schlüsselschalter Automatik/Hand, Leuchtmelder; Produkt, Freigabe und Kalibrierung aus der **Leitstelle**; **Handbetrieb nur vor Ort** mit Handbediengerät (Zustimmtaster) | `docs/schnittstelle.md` |
| 15.10. | Ex-Schutz | BASF: **keine Ex-Zone** an der Verladestelle | `docs/ideenspeicher.md` |
| 15.10. | Füllstand | Nachziehen gefordert; Messstab (geführte Mikrowelle) an der Lanze; Füllende über Durchflusssensor; Füllstand zusätzlich aus Armhöhe + Messstab | `docs/fuellstand_ueberfuellsicherung.md` |
| 15.10. | Überfüllsicherung | Grenzschalter mit fester Länge ab Domrand an **aufliegender Lanze** (wie heute der Liquiphant, nur automatisch); Vorschlag **SICK LFV 200** mit Rohrverlängerung | `docs/fuellstand_ueberfuellsicherung.md`, `docs/skizzen/ueberfuell_lanze.png` |

## Lieferanten und Anfragen

| Lieferant | Gegenstand | Stand |
|---|---|---|
| **SEW** (Herr Lay, Drive Office Rhein-Main) | J1/J2 Servo mit Geber und Bremse | Angebot **426368452B** vom 12.10.: J1 AK0Z (Sicherheitsgeber, Adapter HN14.01), J2 AZ2Z (MD071A), Bremse BK1 16 Nm, Einkabeltechnik MOVILINK DDI |
| SEW | **Freigabe elektrisch (Peter, 16.10.)**: Servomotoren J1/J2 und alle Umrichter aus 426368452D können bestellt werden; J3-Motor (Pos. 3): Preisvergleich SEW ↔ IMO offen | freigegeben |
| SEW | **Angebot 426368452D (16.10.)**: J1/J2 AZ2Z + MD071A, J3 AK8Z, 3 Umrichter mit Positioning Drive – **8.380,64 €**, entspricht der Anfrage | aktuell; Übersetzung J1/J2 ohne Rückfrage angenommen (26.10.); Temperatur zurückgestellt; Bremswiderstände und Kabel mit Peter |
| SEW | **Angebot 426368452C (16.10.)**: alles in einem Angebot, Umrichter mit Positioning Drive (Level 1), 7.650,31 € – Korrektur nötig: J1 noch mit Sicherheitsgeber, nur 1 Umrichter für J1+J2 (`hardware/antriebe.md`) | erhalten, Rückfrage |
| SEW | **Angebot 426533683 (16.10.)**: J3-Motor RF47 DRN80M4/BE05/DI/KD1/TF/AK8Z + 3 Umrichter MOVITRAC advanced (PROFINET, STO, DDI), nur Velocity Drive (Level 0) | erhalten; Level 1/Positioning Drive, Bremswiderstände, BE05-Ansteuerung nachgefordert |
| SEW | J3: **neuer Getriebemotor** gleichwertig RF47 DRN80M4/BE05/TF (Referenz-Seriennr. 01.8693812401.0001.26), Geber passend zu J1/J2 | angefragt (alter Motor steht nicht mehr zur Verfügung) |
| SEW | Umrichter MOVI-C für J1–J3 (PROFINET, STO, Bremse) | angefragt |
| SEW | offen: J1/J2 gleiche Geberausführung, Getriebe nur bis −15 °C (Anlage −20 °C), Motordatenblatt mit Rotorträgheit | nachfragen |
| **IMO** (Herr Krasnici) | **Angebot 20023835 vom 04.11.2026** (bindend bis 13.11.): Kit WD-E 0223/3-14904 mit Adaption RF47 **und** Getriebemotor RF47 DRN80M4/BE05/DI/KD1/TF/AK8Z (Geber AK8Z, DDI), 5.329 € netto, frachtfrei Lich, 6–7 Wochen nach Auftrag und Zeichnungsfreigabe (+2 Wochen Weihnachten). Motor wahlweise 400 V Stern (1,75 A) oder 230 V Dreieck 87 Hz (3,05 A) → **400 V Stern** (passt zu MCX91A-0025). Offen: Lastfall mit Auslass 3,7 m, Lebensdauer (480 h), Preis ohne Motor (SEW-Pos. J3 nur einmal bestellen), TechSpec ausfüllen | Angebot liegt vor |
| **SICK** (Herr Müller) | **Angebot 33503320 (09.10., gültig bis 31.01.2027)**: Visionary-T Mini CX V3S105-1AAAAAD + Halter 2124497 + Leitungen 15 m (M12 A 8-pol. offen 2095599, M12 X → RJ45 2124208), **1.501,19 €**; alternativ Visionary-B Two V3S146-1AAAAAA (Stereo) mit Halter und 5-m-Leitungen 2.217,05 € | **Bestellung über Einkauf (Udo) am 09.11.2026 angestoßen**: Pos. 800–1100 zur Laboraktion **900 € netto**, Kommission K-04896/26. Sensorangebot 33503391 (LFC, LFV230, LFP) vorerst nicht bestellen – wartet auf BASF. SICK-Betriebsruhe 24.12.–06.01. |
| SICK (Herr Müller) | **Angebot 33503391, ergänzt 22.10.**: LFC-XXSBTE + SiLink2 + Leitung (Test), **LFV230-XASGBTPM0800** (Überfüllsicherung, 800 mm), **LFP0800-A4NMB** LFP Cubic + Koaxialrohr LFPCT-0800G1 (Messstab), 1.384,88 € netto, gültig bis 09.01.2027 | erhalten; offen: Zulassung Überfüllsicherung (WHG/SIL), Länge LFV (800 mm vermutlich zu lang, Einhängelänge Liquiphant von BASF), Koaxrohr bei Dispersion, 5-polige Leitung LFP, Produkttemperatur |
| **Automatisierungspartner (Peter Rektorschek, NemaSoft GmbH)** | Schaltschrank, Grundsoftware, Sicherheit | **Angebot 2604515 vom 30.10.2026**, gültig 30 Tage: Software pauschal 22.800 €, IBN 60 h + 15 h, Schaltschrank 10.500 €, EPLAN 6.175 €, Beckhoff C6027 (Vision-IPC) 3.250 €, Lieferung/Montage Lich 2.485 € – **52.803,25 € netto**. Beistellung HETA: SEW inkl. Bremswiderstände (Auslegung SEW), Sensoren/Aktoren, Kabelschlepps, Kabel. Klären: S7-1200 statt F-CPU, Sicherheitstechnik/Handbediengerät/Schlüsselschalter Auto-Hand fehlen, HMI 4" trotz „ohne Display“, Überfüllsicherung über IO-Link, Abtropfsicherung, PLS-Anbindung, IBN BASF. **V2 (04.11.2026): 42.891,25 € netto** – Software pauschal 15.200 € (TwinCAT inkl. TwinSAFE, ohne HMI, Doku durch HETA), IBN 60 h + 15 h (7.481 €), Schaltschrank 8.100 €, EPLAN 6.175 €, Beckhoff C6027 als SPS + Vision-IPC (Windows 11 IoT, TwinCAT PLC/OPC UA, EtherCAT-E/A, TwinSAFE EL1918/EL2904, IO-Link ED6224) 4.450 €, Montage Lich 1.485 € (Kabel verlegt HETA). Offen: Schrank weiterhin 2000×1200×600, Umrichter PROFINET (CFN) ↔ EtherCAT, Hand/Automatik + Zustimmung fehlen, E/A knapp (Klappe; Abtropfsicherung entfällt, rein mechanisch), Vision unter Windows prüfen, HMI für Prototyp |

## Kunde BASF (Silas Kaestel, Werkstudent / Bachelorarbeit)

- Technische Zusammenfassung gesendet (`docs/extern/`), Feedback: Konzept „sehr gelungen“.
- BASF prüft intern Machbarkeit und **PLS-Anbindung**.
- **Fotos und Maße H517 erhalten (22./23.10.)**: Mannloch Ø 0,5 m, Eintauchtiefe 2–3 cm unter Spiegel, Produkte Acronal/Lhydran/Lurapret, überdachte Halle mit mehreren Spuren – Auswertung `docs/kunde_basf_h517.md` (Fotos vertraulich, nicht im Repository).
- Fahrzeugstatistik folgt (erbeten: Spanne Tiefe Domrand–Tankboden, Füllleistung).
- **Gespräch 27.10.2026** (Details `docs/kunde_basf_h517.md`):
  - Füllleistung 20–25 t/h (≈ 20–25 m³/h), Füllgrad normal 95 %, 50–60 Tankwagen pro Tag.
  - Liquiphant heute: Schutzkorb 22 cm im Tank, Gabel 17 cm → Überfüll-Lanze kurz.
  - Abschaltung heute über die SPS; Sicherheitskreis könnte die Pumpe stoppen.
  - BASF favorisiert kapazitive Sensorik (Baumer) und testet selbst; Druckmessung als Idee.
  - Halterung: Gleithülse könnte klemmen (Hinweis HETA) → offene Führung; möglichst kein Produktkontakt.
  - Spülwanne an der Parkstellung bestätigt; Abtropfen heute mit Eimer, automatische Lösung gewünscht.
  - Kammeraufteilung laut Notiz am Bedienpult vor Ort wählbar (mit „ohne Display“ abgleichen).
  - Rohrisolierung über dem Arm könnte mit Servo J1 kollidieren – prüfen.
  - HETA schickt Sensoroptionen und Skizze; BASF antwortet per Mail, nächster Termin in ca. 2 Wochen.

### Offene Fragen an BASF

1. Tiefe Domrand–Tankboden (Spanne), Kammeraufteilung (Schwallwände/Mehrkammer).
2. Überfüllsicherung: von Hand oder andocken; Bezug der 22 cm; zulässiges Fabrikat, Zulassung.
3. Überfüllsicherung schaltet die **Pumpe** ab (festgelegt); offen: Signalweg (SPS oder Sicherheitskreis).
4. Kammerwahl vor Ort oder aus der Leitstelle; Signale PLS.
5. DN80-Reduzierung/Lanze; Abstand Rohrisolierung über J1.

## Nächste Schritte

- [ ] Entwicklungsakte (`docs/entwicklung/`) an HETA-Vorlage anpassen, Reviews R0-1…R0-6 freigeben, Lastenheft V1.0 (Abweichungen im Anforderungsnachweis)

- [x] Mail an BASF: Sensorvergleich, Füllende nie über die Überfüllsicherung, Fragen zur Zulassung (gesendet 27.10.)
- [ ] Rohrisolierung über J1 gegen Motorlage prüfen – vor der SEW-Bestellung
- [x] SICK-Kamera bestellt (Einkauf, 09.11., Laboraktion 900 €)
- [ ] SEW-Motoren J1/J2 bestellen (vorher Isolierung über J1 prüfen); Umrichter erst nach Feldbus-Entscheidung (Peter); IMO-Antwort J3 abwarten
- [ ] Mit Peter: Überfüll-Abschaltung (Klappe/Pumpe, F-SPS), Kammerwahl vor Ort oder Leitstelle
- [ ] Konstruktion: aufliegende Lanze kurz (ca. 20 cm), Führung ohne klemmende Hülse; Halter
  Grenzschalter; **Abtropfsicherung rein mechanisch** nach `docs/skizzen/Prinzipskizze_Abtropfsicherung_Rev6.pdf` (Dom-Abdeckung mit Überfüllsicherung, Pendelwanne vom Rohrende aufgedrückt, Feder schließt; Alternative Rev. 5)
- [x] Simulation: nur Lkw (1–3 Kammern), Arm aus Konfigurator 03.11. (Auslass 3,7 m), 22 m³/h,
  zwei Grenzschalter, Sollmenge 95 %, Maximalhöhe, Überfüllsicherung als letzte Ebene
- [ ] Kameratest an einem stehenden Tankwagen (Aufnahmen für die Software)
- [x] Software: mehrere Dome (Schnittstelle Version 3), Konfigurator mit Verladestelle
- [ ] Branch nach `main` übernehmen (Pull Request), damit Server und Prüfstand den aktuellen Stand haben
