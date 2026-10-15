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
| 15.10. | Ex-Schutz | BASF: **keine Ex-Zone** an der Verladestelle | `docs/ideenspeicher.md` |
| 15.10. | Füllstand | Nachziehen gefordert; Messstab (geführte Mikrowelle) an der Lanze; Füllende über Durchflusssensor; Füllstand zusätzlich aus Armhöhe + Messstab | `docs/fuellstand_ueberfuellsicherung.md` |
| 15.10. | Überfüllsicherung | Grenzschalter mit fester Länge ab Domrand an **aufliegender Lanze** (wie heute der Liquiphant, nur automatisch); Vorschlag **SICK LFV 200** mit Rohrverlängerung | `docs/fuellstand_ueberfuellsicherung.md`, `docs/skizzen/ueberfuell_lanze.png` |

## Lieferanten und Anfragen

| Lieferant | Gegenstand | Stand |
|---|---|---|
| **SEW** (Herr Lay, Drive Office Rhein-Main) | J1/J2 Servo mit Geber und Bremse | Angebot **426368452B** vom 12.10.: J1 AK0Z (Sicherheitsgeber, Adapter HN14.01), J2 AZ2Z (MD071A), Bremse BK1 16 Nm, Einkabeltechnik MOVILINK DDI |
| SEW | J3: **neuer Getriebemotor** gleichwertig RF47 DRN80M4/BE05/TF (Referenz-Seriennr. 01.8693812401.0001.26), Geber passend zu J1/J2 | angefragt (alter Motor steht nicht mehr zur Verfügung) |
| SEW | Umrichter MOVI-C für J1–J3 (PROFINET, STO, Bremse) | angefragt |
| SEW | offen: J1/J2 gleiche Geberausführung, Getriebe nur bis −15 °C (Anlage −20 °C), Motordatenblatt mit Rotorträgheit | nachfragen |
| **IMO** (Herr Krasnici) | weiterer Schwenkantrieb WD-E 0223/3 + Adaption 07975 020, SEW-Motor mit Multiturngeber; Geber am Schwenkantrieb nur als Option (Anforderungsbogen ausgefüllt: `hardware/IMO_Anforderungsbogen_Drehgeber_J3.pdf`) | angefragt (Ref. 20022371). Hinweis: Motor ggf. doppelt angeboten (IMO und SEW) – nur bei einem bestellen |
| **SICK** (Herr Hebben) | Kamera Visionary-T Mini CX V3S105-1AAAAAD | Angebot angekündigt, nachgefragt |
| SICK | LFV 200 (Überfüllsicherung, Zulassung klären) + LFP Cubic (Messstab) | Anfrage vorbereitet |
| **Automatisierungspartner (Peter)** | Schaltschrank, Grundsoftware, Sicherheit, Siemens/Beckhoff-Vergleich | Angebot ausstehend; Antriebsliste: `hardware/antriebsliste.md` |

## Kunde BASF (Silas Kaestel, Werkstudent / Bachelorarbeit)

- Technische Zusammenfassung gesendet (`docs/extern/`), Feedback: Konzept „sehr gelungen“.
- BASF prüft intern Machbarkeit und **PLS-Anbindung**.
- Fotos, Maße und Unterschiede der Tankfahrzeuge folgen.
- Termin vorgeschlagen: Mittwoch bzw. Donnerstagvormittag.

### Fragen für den nächsten Termin

1. Liquiphant heute: **Typ** (Typenschild/Foto), **Einhängelänge unter Domrand**, für alle Fahrzeuge gleich?
2. Welches **Auswertegerät** bzw. welche Abschaltung (Relais, PLS)?
3. Werden andere Hersteller (z. B. SICK LFV 200) als Überfüllsicherung akzeptiert? Bevorzugte Hersteller?
4. Nachziehen: gewünschte Eintauchtiefe unter Spiegel, Mindestabstand zum Tankboden?
5. Anbindung an das PLS: welche Signale?

## Nächste Schritte

- [ ] Angebote SEW (J3-Motor, Umrichter), IMO, SICK (Kamera, LFV 200, LFP) einholen
- [ ] Termin mit BASF, Fragen oben klären, Länge L der Überfüll-Lanze festlegen
- [ ] Konstruktion: aufliegende Lanze mit Führung am Auslassrohr (Skizze), Platz für Messstab
- [ ] Kameratest an einem stehenden Tankwagen (Aufnahmen für die Software)
- [ ] Software: Nachziehen (Schnittstelle Version 3), Füllstand aus Armhöhe, Simulation mit steigendem Füllstand
- [ ] Branch nach `main` übernehmen (Pull Request), damit Server und Prüfstand den aktuellen Stand haben
