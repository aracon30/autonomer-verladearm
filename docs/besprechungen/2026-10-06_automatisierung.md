# Besprechung Automatisierungspartner (Peter) – Oktober 2026

Protokoll nach den Besprechungsnotizen, danach Einschätzung und Folgen für das Projekt.

## Aufgaben (Action Items)

| Wer | Aufgabe | Stand |
|---|---|---|
| Philipp | Antriebsliste mit genauen Motor- und Umrichterdaten erneut senden | Vorlage: `hardware/antriebsliste.md` |
| Automatisierungspartner | Preise und Eignung Siemens ↔ Beckhoff vergleichen | offen |
| Automatisierungspartner | F-CPU nötig oder reicht ein kleines Sicherheitsrelais / Auswertegerät? | offen (hängt an der Risikobeurteilung) |
| Automatisierungspartner | Angebot Schaltschrank, Grundsoftware, Antriebe, Sicherheitstechnik | offen, ggf. nach einer Woche Urlaub (ab Freitag) |
| Team | Prototyp-Aufbau: Kamera, Punkterkennung, Bahnplanung, Antriebsverhalten testen | offen |

## Bewegungssteuerung und Sicherheit

- Grundsatzfrage: Kinematik auf dem IPC oder in der SPS rechnen.
- SPS-seitige Kinematik könnte koordinierte Achsbewegung, kartesischen Handbetrieb und
  definierte Kollisions-/Sicherheitszonen unterstützen.
- Einfacher Prototyp: PC übergibt Achspositionen an die SPS, mit geschätzten Achsgeschwindigkeiten
  und Grundgrenzen; weniger genaue Koordination.
- Bahnplanung und Bildverarbeitung bleiben auf dem PC; kartesische Koordinaten könnten zur SPS
  gehen (Bewegung, Sicherheit).
- Sicherheit: Not-Halt, Sensor „Klapptreppe eingefahren“, Grenzen wie maximaler Achsweg;
  vollständige Risikobeurteilung steht noch aus.
- Handbetrieb im Normalbetrieb eingeschränkt; Service und Bergung nach Störung noch durchdenken.

## Prototyp und Schnittstellen

- Erster Aufbau: Schaltschrank, drei Antriebe, Grundsoftware, Sicherheitstechnik, IPC; die SPS
  als einfache Schnittstelle zu den Antrieben.
- OPC UA machbar; Lizenz ca. 150–250 € je nach Variablenanzahl, plus Software.
- Schnittstelle bis 16 Positionen sowie Signale wie Bereit, Füllen Start, Füllen Stopp.
- Vor der endgültigen Architektur testen, ob die Kamera die Domöffnung erkennt und brauchbare
  Daten liefert.
- Test nahe beim Partner mit Tankwagen und Platz möglich; Esserot eventuell interessiert.

## Ausrüstung und Bedienung

- Antriebe SEW: zwei Servo-Getriebemotoren (J1, J2), ein Drehstrommotor mit Schneckengetriebe (J3).
- Siemens-Antriebe vermutlich mindestens 30 % teurer als SEW – vergleichen.
- Beckhoff-IPC mit Windows und TwinCAT (Soft-SPS): IPC und SPS in einem, offene Schnittstellen,
  Kamerasoftware darauf möglich; Linux-Kenntnisse besprochen.
- Siemens bleibt Option; dem Kunden ggf. als abgeschlossene Komplettlösung („Black Box“).
- Bedienpanel 11": Automatik, Produktwahl, Betriebsparameter; normales Handverfahren nicht für
  Bediener.
- Kamerakalibrierung: 16 bekannte Punkte von Hand anfahren, Koordinaten in einer
  Konfigurationsdatei speichern.

## Ablauf und Mechanik

- Demo-Ablauf: Bereich scannen, Ziel anfahren, absenken, Lage am Referenzflansch prüfen, durch
  die Öffnung eintauchen, beladen, Rückweg planen.
- Kurze **Abtropfpause** nach dem Herausfahren (heute: Eimer).
- **Absperrarmatur in der Fallleitung**: Absperrklappe statt schwerem Kugelhahn bevorzugt.
- Termin: fertig bis April; eine Bachelorarbeit soll eingebunden werden.

---

## Einschätzung und Folgen (Software-Seite)

**Kinematik IPC oder SPS – Empfehlung: Mischform, wie im Prototyp vorgesehen.**
Der PC plant die Bahn (Hindernisse aus der Punktwolke, Kollisionsprüfung inkl. eigenem Arm) und
liefert **Gelenkwinkel-Stützpunkte** (eindeutig, genau so geprüft) **plus kartesisches Ziel**.
Die SPS rechnet nur die **Vorwärtskinematik** (einfache Formel, eindeutig) und prüft damit
unabhängig: Sperrzonen der Station, Absenkkorridor um den Dom, Grenzen. Kartesische Vorgaben mit
Rückwärtsrechnung in der SPS hätten mehrere Armstellungen je Punkt – die SPS könnte eine nicht
geprüfte wählen (Begründung: `docs/adr/0002-gelenkwinkel-vom-pc.md`).
Kartesischer Handbetrieb ist nur für den Service nötig; Achs-Tippen reicht dafür.

**Synchronfahrt** ist auch im „einfachen Prototyp“ genau machbar: Geschwindigkeit je Achse aus der
gemeinsamen Fahrzeit skalieren, gleichzeitig starten (`MC_MoveAbsolute`). Das ist nicht ungenauer
als SPS-Kinematik, weil zwischen den Stützpunkten ohnehin im Gelenkraum gefahren wird.

**Schnittstelle:** 16 Stützpunkte sind vorhanden (`DB_Vision`, InterfaceVersion 2). Füllen
Start/Stopp und Absperrklappe gehören in die SPS (nicht über den PC). Vorschlag für Version 3:
`SafeZ` und `CorridorRadius` für die SPS-Gegenprüfung, Abtropfzeit je Produkt.

**Kalibrierung:** Das Werkzeug ist vorhanden (`calibrate --from-plc`, schlägt ca. 10 Stellungen
vor; 16 sind besser abgesichert). Die Punkte werden nicht von Hand vermessen: Die Kamera misst den
Referenzflansch, die SPS liefert die Istwinkel, das Programm rechnet die Lage der Kamera.

**Abtropfpause:** Nach dem senkrechten Herausfahren den Auslass knapp über der Öffnung für eine
Abtropfzeit (je Produkt, Panel) halten, dann weiter in die Parkstellung. Umsetzung: PC markiert den
Stützpunkt „über der Öffnung“ in Job 3, SPS wartet dort.

**Kameratest vor der Architekturentscheidung:** sinnvoll. Kamera mit Stativ/Ausleger über einen
stehenden Tankwagen, Aufnahmen mit dem Vision-Dienst ohne Arm aufzeichnen und auswerten
(Domerkennung, Deckel, Armaturen, Spiegelungen). Die Aufnahmen dienen später auch als Testdaten.

**Sicherheit:** F-CPU oder Sicherheitsrelais entscheidet die Risikobeurteilung (Not-Halt, Treppe
eingefahren, STO der drei Umrichter, Bremsen, ggf. Schutzfeld). Bei mehreren Sicherheitsfunktionen
mit Logik (Treppe, Zonen, Bremsenansteuerung) ist eine kleine F-CPU bzw. TwinSAFE meist
übersichtlicher als verdrahtete Relais.
