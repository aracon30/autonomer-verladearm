# Projektstand Verladearm (Stand 15.10.2026)

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
| 26.10. | Übersetzung J1/J2 | i = 10,6 wird **ohne Rückfrage bei SEW** angenommen; Regelung bei der Inbetriebnahme mit flachen Rampen einstellen | `hardware/antriebe.md` |
| 26.10. | Füllende | Schutzebenen: 1. Sollmenge (Durchfluss), 2. Maximalhöhe aus Armhöhe + Grenzschaltern, 3. Überfüllsicherung **nur als letzte Ebene, nie betriebsmäßig** | `docs/fuellstand_ueberfuellsicherung.md` |
| 26.10. | Nachziehen | **zwei kapazitive Grenzschalter** (A 1 cm, B 3 cm über Auslassende) statt Messstab; zuerst **SICK LFC mit Acronal testen** (Anhaftung, Schaum); LFP Cubic zurückgestellt | `docs/fuellstand_ueberfuellsicherung.md` |
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
| **IMO** (Herr Krasnici) | weiterer Schwenkantrieb WD-E 0223/3 + Adaption 07975 020, SEW-Motor mit Multiturngeber; Geber am Schwenkantrieb nur als Option (Anforderungsbogen ausgefüllt: `hardware/IMO_Anforderungsbogen_Drehgeber_J3.pdf`) | angefragt (Ref. 20022371). Hinweis: Motor ggf. doppelt angeboten (IMO und SEW) – nur bei einem bestellen |
| **SICK** (Herr Müller) | **Angebot 33503320 (09.10., gültig bis 31.01.2027)**: Visionary-T Mini CX V3S105-1AAAAAD + Halter 2124497 + Leitungen 15 m (M12 A 8-pol. offen 2095599, M12 X → RJ45 2124208), **1.501,19 €**; alternativ Visionary-B Two V3S146-1AAAAAA (Stereo) mit Halter und 5-m-Leitungen 2.217,05 € | Empfehlung T Mini CX (Treiber vorhanden, Halle überdacht); ab Lager, kann bestellt werden. SICK-Betriebsruhe 24.12.–06.01. |
| SICK (Herr Müller) | **Angebot 33503391, ergänzt 22.10.**: LFC-XXSBTE + SiLink2 + Leitung (Test), **LFV230-XASGBTPM0800** (Überfüllsicherung, 800 mm), **LFP0800-A4NMB** LFP Cubic + Koaxialrohr LFPCT-0800G1 (Messstab), 1.384,88 € netto, gültig bis 09.01.2027 | erhalten; offen: Zulassung Überfüllsicherung (WHG/SIL), Länge LFV (800 mm vermutlich zu lang, Einhängelänge Liquiphant von BASF), Koaxrohr bei Dispersion, 5-polige Leitung LFP, Produkttemperatur |
| **Automatisierungspartner (Peter)** | Schaltschrank, Grundsoftware, Sicherheit, Siemens/Beckhoff-Vergleich | Angebot ausstehend; Antriebsliste: `hardware/antriebsliste.md` |

## Kunde BASF (Silas Kaestel, Werkstudent / Bachelorarbeit)

- Technische Zusammenfassung gesendet (`docs/extern/`), Feedback: Konzept „sehr gelungen“.
- BASF prüft intern Machbarkeit und **PLS-Anbindung**.
- **Fotos und Maße H517 erhalten (22./23.10.)**: Mannloch Ø 0,5 m, Eintauchtiefe 2–3 cm unter Spiegel, Produkte Acronal/Lhydran/Lurapret, überdachte Halle mit mehreren Spuren – Auswertung `docs/kunde_basf_h517.md` (Fotos vertraulich, nicht im Repository).
- Fahrzeugstatistik folgt (erbeten: Spanne Tiefe Domrand–Tankboden, Füllleistung).
- **Termin 27.10.2026**, Themen vorab gesendet: Überfüllsicherung (von Hand weiter oder automatisch mit dem Arm andocken), Tanktiefen, Spülwanne an der Parkstellung.

### Fragen für den nächsten Termin

1. Liquiphant heute: **Typ** (Typenschild/Foto), **Einhängelänge unter Domrand**, für alle Fahrzeuge gleich?
2. Welches **Auswertegerät** bzw. welche Abschaltung (Relais, PLS)?
3. Werden andere Hersteller (z. B. SICK LFV 200) als Überfüllsicherung akzeptiert? Bevorzugte Hersteller?
4. ~~Eintauchtiefe~~ (2–3 cm, beantwortet); Mindestabstand zum Tankboden, Tiefe Domrand–Boden?
5. Anbindung an das PLS: welche Signale?

## Nächste Schritte

- [ ] Angebote SEW (J3-Motor, Umrichter), IMO, SICK (Kamera, LFV 200, LFP) einholen
- [ ] Termin mit BASF, Fragen oben klären, Länge L der Überfüll-Lanze festlegen
- [ ] Konstruktion: aufliegende Lanze mit Führung am Auslassrohr (Skizze), Platz für Messstab
- [ ] Kameratest an einem stehenden Tankwagen (Aufnahmen für die Software)
- [ ] Software: Nachziehen (Schnittstelle Version 3), Füllstand aus Armhöhe, Simulation mit steigendem Füllstand
- [ ] Branch nach `main` übernehmen (Pull Request), damit Server und Prüfstand den aktuellen Stand haben
