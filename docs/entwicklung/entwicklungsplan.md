# Entwicklungsplan (ISO 9001, 8.3.2)

Stand 30.10.2026 · Entwurf · Freigabe: [Name, Datum]

## Gegenstand

Autonomer Obenverladearm (HETA): Kamera erkennt Dom und Hindernisse, Vision-PC plant
kollisionsfreie Bahnen, SPS fährt drei Achsen (J1/J2 SEW-Servo, J3 SEW-Getriebemotor mit
IMO-Schwenkantrieb), befüllt mit Nachziehen und Überfüllsicherung, fängt Nachtropfen auf.
Erster Einsatz: BASF Ludwigshafen, Verladestelle H517 (Polymerdispersionen).

## Beteiligte und Verantwortung

| Rolle | Wer | Verantwortung |
|---|---|---|
| Projektleitung, Vertrieb | P. Schreiber (HETA) | Planung, Anforderungen, Lieferanten, Kunde, Freigabe der Entwicklungsergebnisse [bzw. nach HETA-Vorgabe] |
| Konstruktion | HETA Konstruktion [Name] | Arm, Antriebsanbau, Halterungen, Abtropfsicherung, Zeichnungen |
| Software Vision-PC | HETA (mit Claude Code) | Erkennung, Bahnplanung, Schnittstelle, Simulation, Konfigurator |
| Automatisierung | Peter [Firma] | Schaltschrank, SPS-Programm, Sicherheitstechnik, Stromlaufplan |
| Kunde | S. Kaestel (BASF) | Anforderungen, Anlagendaten, Sensortests mit Produkt, Abnahme |
| Freigabe Gesamt | [Geschäftsführung / QM nach HETA-Vorgabe] | Phasenfreigaben |

## Phasen und Meilensteine

| Phase | Inhalt | Ergebnis / Meilenstein | Review | Stand |
|---|---|---|---|---|
| 1 Konzept | Lastenheft, Architektur, Antriebsauslegung, Kamera, Füllstandskonzept | Lastenheft, ADR 0001/0002, Antriebs- und Stückliste | R1 Konzept | **weitgehend erledigt** (offen: Lastenheft-Update) |
| 2 Software und Simulation | Erkennung, Bahnplanung, Schnittstelle, Simulation, Konfigurator | Software mit Tests, Schnittstelle V3, Simulation | R2 Software | **erledigt für Prototyp** (Nachziehen mit Grenzschaltern in der Simulation offen) |
| 3 Detailentwicklung | Konstruktion, Schaltschrank, SPS, Sicherheit, Risikobeurteilung | Zeichnungen, Stromlaufplan, SPS-Programm, Risikobeurteilung | R3 Design (vor Bestellung/Fertigung) | **läuft** |
| 4 Prototyp | Bestellung, Bau, Inbetriebnahme in der HETA-Werkstatt | Prototyp, Inbetriebnahmeprotokoll | R4 Prototyp | offen |
| 5 Erprobung | Kameratest am Tankwagen, Sensortest BASF, Funktions- und Dauertests | Testberichte, Nachweise je Anforderung | R5 Verifizierung | offen |
| 6 Anlage BASF | Anpassung H517, Montage, Inbetriebnahme, Abnahme | Abnahmeprotokoll, CE-Konformität (VO (EU) 2023/1230), Betriebsanleitung | R6 Validierung / Abnahme | offen |

Termine: [nach Lieferzeiten SEW, IMO, Schaltschrank festlegen]

## Vorgaben

- Normen und Richtlinien: Verordnung (EU) 2023/1230 (ab 20.01.2027), EN ISO 12100
  (Risikobeurteilung), EN ISO 13849 (Sicherheitsfunktionen, PL), EN 60204-1 (Elektrik);
  Überfüllsicherung nach WHG/AwSV bzw. Vorgabe Betreiber. Keine Ex-Zone an H517 (BASF, 15.10.).
- Software: Versionsverwaltung Git, automatische Tests vor jeder Übernahme, Änderungen über
  Pull Request; Schnittstelle nur mit neuer `InterfaceVersion` und Abstimmung mit der SPS.

## Risiken des Vorhabens

| Risiko | Maßnahme |
|---|---|
| Regelbarkeit J1/J2 (Gesamtübersetzung 10,6, großes Trägheitsverhältnis) | bewusst angenommen (26.10.); Inbetriebnahme mit flachen Rampen, Prüfung auf Schwingen |
| Sensorik bei Schaum und klebriger Dispersion | Sensortest durch BASF mit Produkt; Alternativen (Drucksensor, Messstab) dokumentiert |
| Kollision Rohrisolierung über J1 | vor SEW-Bestellung mit Zeichnung prüfen |
| Kamera bei Spiegelung, Nachbarspur | Kameratest am Tankwagen; Domsuche nur in der eigenen Spur |
| Zulassung Überfüllsicherung | Vorgabe BASF abwarten (WHG/SIL, Fabrikat) |
