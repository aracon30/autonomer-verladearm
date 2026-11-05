# BSFZ-Antrag – Entwurf der Texte (Forschungszulage)

Stand 05.11.2026 · Entwurf. Texte zum Einfügen in das Antragsportal (Abschnitt „Inhaltliche/Fachliche
Angaben zum Vorhaben“). Zeichenzahl inkl. Leerzeichen in Klammern. **[prüfen]**: Zeiträume, Personenmonate (PM),
Beginn des Vorhabens. Kunde bewusst nicht genannt.

## Titel (167 von 200 Zeichen)

Autonomer Obenbefüllarm für Straßentankwagen mit 3D-kamerabasierter Domerkennung, kollisionsfreier Bahnplanung und sensorgeführtem Nachziehen beim Unterspiegelbefüllen

## Ziel (1256 von 1500 Zeichen)

Es soll ein Verladearm für die Obenbefüllung von Straßentankwagen entwickelt werden, der ohne Bediener am Arm die offene Domöffnung selbst findet, den Auslass bis ca. 20 cm über den Tankboden eintaucht und ihn beim Befüllen mit dem steigenden Spiegel nachzieht (Auslass 1–3 cm unter dem Spiegel). Heute führt ein Bediener auf dem Fahrzeugdach den Arm von Hand.
Der Arm hat zwei Drehachsen (Servo), eine Hubachse (Schneckenschwenktrieb) und einen frei pendelnden, 3,7 m langen Auslass. Eine über der Verladestelle montierte 3D-Time-of-Flight-Kamera erfasst Fahrzeugdach, Domkragen, offene Deckel und den Arm als Punktwolke. Zu entwickeln sind: (1) eine Erkennung von Domöffnungen (Ø 0,2–0,6 m) bei wechselnden Fahrzeugtypen, mehreren Kammern und Störobjekten mit ±20 mm Genauigkeit; (2) eine Bahnplanung der drei Achsen mit Kollisionsprüfung gegen die gemessene Szene, berechnet in unter 5 s; (3) das Nachmessen der tatsächlichen Auslasslage mit derselben Kamera über einen Referenzflansch, um Durchbiegung, Getriebespiel und Kalibrierfehler auszugleichen; (4) eine Nachziehregelung über zwei kapazitive Grenzschalter am Auslass für anhaftende, schäumende Polymerdispersionen. Ergebnis ist ein in der Werkstatt und an einer Verladestelle erprobter Prototyp.

## Stand der Technik (448 von 500 Zeichen)

Obenbefüllarme werden heute von Hand oder mit Servounterstützung durch einen Bediener positioniert. Automatische Lösungen setzen nach unserer Recherche feste Domlagen (z. B. Kesselwagen) oder Marker am Fahrzeug voraus. Straßentankwagen unterscheiden sich in Domzahl, -lage, -höhe und Deckelbauart. Eine markerlose 3D-Domerkennung mit Nachmessen des eigenen Auslasses und sensorgeführtem Nachziehen in anhaftenden Dispersionen ist uns nicht bekannt.

## Arbeiten (883 von 1000 Zeichen)

Nach Lastenheft und Kinematikmodell wird eine Simulation aufgebaut (synthetische Punktwolken von Tankwagen, simulierte Achsen und SPS), in der Erkennung, Planung und Ablauf vorab getestet werden. Die Domerkennung wird mit Ebenen- und Kreisanpassung (RANSAC) und Plausibilitätsprüfung entwickelt und an Aufnahmen realer Fahrzeuge validiert. Die Bahnplanung erzeugt synchrone Stützpunkte der drei Achsen mit Kollisionsprüfung gegen Szene und eigenen Arm. Für Hand-Auge-Kalibrierung und Nachmessen des Auslasses wird ein Verfahren mit Referenzflansch entwickelt. Parallel werden Arm, Antriebsanbau und Steuerung konstruiert und als Prototyp aufgebaut. Die Grenzschalter werden mit Produkt auf Anhaftung und Schaum getestet. Abschließend wird der Prototyp in der Werkstatt und an einer Verladestelle mit verschiedenen Fahrzeugen erprobt; Erkennung, Planung und Regelung werden angepasst.

## Risiken (870 von 1000 Zeichen)

Die Kamera misst aus 4–6 m Abstand; dunkle, glänzende oder nasse Domkragen und Deckel erzeugen Lücken und Ausreißer. Offen ist, ob kleine Füllöffnungen in Domdeckeln und teilweise verdeckte Öffnungen neben offenen Deckeln sicher und auf ±20 mm bestimmt werden. Am 3,7 m langen, frei pendelnden Auslass summieren sich Durchbiegung, Spiel des Schneckentriebs und Kalibrierfehler; ob das Nachmessen über einen teilweise verdeckten Referenzflansch dies ausreichend korrigiert, ist ungewiss. Die Bahnplanung muss im engen Raum zwischen Dach, Geländer und offenen Deckeln in unter 5 s eine kollisionsfreie Bahn finden. Beim Nachziehen können anhaftendes Produkt und Schaum die kapazitiven Grenzschalter fehlschalten; der Auslass würde auftauchen (Spritzen, Schaum) oder zu tief stehen. Ob eine Hubachse mit Schneckentrieb fein und schnell genug nachzieht, muss erprobt werden.

## Auftragnehmer NemaSoft (447 von 500 Zeichen)

NemaSoft GmbH entwickelt nach eigenem Konzept die Steuerungssoftware des Prototyps: synchrone Führung der drei Achsen entlang der vom Bildverarbeitungsrechner geplanten Stützpunkte, OPC-UA-Kopplung mit Plausibilitätsprüfung und Fehlerbehandlung, die Nachziehregelung über zwei Grenzschalter mit Maximalhöhenüberwachung sowie eine Sicherheitslogik für den Betrieb ohne Bediener am Arm. Schaltschrankbau und Montage sind nicht Teil der FuE-Leistung.

## Tabellarischer Arbeitsplan [prüfen: Zeiträume, PM]

| AP | Arbeitspaket (< 100 Zeichen) | Zeitraum | PM | Durchführung |
|---|---|---|---|---|
| AP-1 | Lastenheft, Kinematikmodell, Konzept Sensorik und Antriebe | 11.2025 – 02.2026 | 2 | HETA |
| AP-2 | Simulation: synthetische Punktwolken von Tankwagen, Achs- und SPS-Simulation | 02.2026 – 07.2026 | 2 | HETA |
| AP-3 | Domerkennung aus 3D-Punktwolken (Ebenen-/Kreismodell, mehrere Dome) | 03.2026 – 12.2026 | 4 | HETA |
| AP-4 | Bahnplanung mit Kollisionsprüfung und synchroner Führung der drei Achsen | 04.2026 – 12.2026 | 3 | HETA |
| AP-5 | Hand-Auge-Kalibrierung und Nachmessen des Auslasses über Referenzflansch | 06.2026 – 03.2027 | 2 | HETA |
| AP-6 | Konstruktion Arm, Antriebsanbau, Auslass mit Grenzschaltern | 06.2026 – 03.2027 | 4 | HETA |
| AP-7 | Steuerungssoftware: Achsführung, Ablauf, Nachziehregelung, Sicherheitslogik | 11.2026 – 04.2027 | 2 | HETA; Auftragnehmer NemaSoft GmbH |
| AP-8 | Aufbau Prototyp, Werkstatttests, Aufnahmen an stehenden Tankwagen | 01.2027 – 05.2027 | 3 | HETA; Auftragnehmer NemaSoft GmbH |
| AP-9 | Erprobung an einer Verladestelle mit Produkt, Anpassung Erkennung und Regelung | 05.2027 – 10.2027 | 3 | HETA; Auftragnehmer NemaSoft GmbH |

Summe 25 PM (Schätzung). Nicht aufnehmen: Projektmanagement, Vertrieb, Zertifizierung/CE, Serienbau, Montage und Inbetriebnahme beim Kunden.
## Wirtschaftsgüter (nur wenn sie bei HETA im Anlagevermögen bleiben)

Förderfähig sind abnutzbare, bewegliche Wirtschaftsgüter des **Anlagevermögens**, angeschafft nach dem
27.03.2024, über 800 € netto je Stück, je Typ eine eigene Position. **Wird der Prototyp samt Kamera und
Steuerung an den Kunden verkauft, ist er Umlaufvermögen und nicht förderfähig** – mit dem Steuerberater klären.

Beispiel, falls die Kamera als Entwicklungs- und Testgerät bei HETA bleibt:

| Feld | Eintrag |
|---|---|
| Bezeichnung | 3D-Time-of-Flight-Kamera inkl. Halter und Anschlusskabel |
| Menge | 1 |
| Modell | Visionary-T Mini CX |
| Hersteller | SICK AG |
| Anschaffung | 2026 |
| Preis je Stück (netto) | [laut Rechnung] |
| Beschreibung/Erfordernis | 3D-Kamera mit 70° × 60° Blickfeld, die Fahrzeugdach, Dome und Arm aus 4–6 m als Punktwolke erfasst. Erforderlich für Aufnahmen realer Tankwagen, Entwicklung und Validierung der Domerkennung, Hand-Auge-Kalibrierung, Nachmessen des Auslasses und die Erprobung des Prototyps. |
| Arbeitspakete | AP-3, AP-5, AP-8, AP-9 |

## Vorgehen

1. Zugang: Antragsportal www.bescheinigung-forschungszulage.de, Anmeldung mit dem ELSTER-Organisationszertifikat
   von HETA (Steuerberater/Buchhaltung).
2. Texte oben einfügen, Arbeitsplan in die Vorlage des Portals übertragen, Auftragnehmer NemaSoft erfassen.
3. Optional als Anlage: Prinzipskizze bzw. Systemübersicht (ohne Kundendaten).
4. Nach der Bescheinigung: Antrag auf Forschungszulage je Geschäftsjahr beim Finanzamt (ELSTER, Steuerberater).
5. Laufend: Stundenzettel je Person und Arbeitspaket, Rechnungen und Verträge (NemaSoft: Software getrennt von
   Schaltschrankbau) aufbewahren. Der BSFZ müssen sie nicht vorgelegt werden, dem Finanzamt ggf. schon.
