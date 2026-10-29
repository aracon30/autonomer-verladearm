# BASF Verladestelle H517 – Stand der Aufnahme

Quelle: Projektdokumentation S. Kaestel (BASF E-EDE/OE), 22.10.2026, Mail vom 23.10.2026 und
Gespräch vom 27.10.2026.
Die Fotos sind **vertraulich** und werden nicht im Repository abgelegt; hier nur die für die
Auslegung nötigen Angaben.

## Angaben BASF

| Thema | Angabe |
|---|---|
| Produkte | hauptsächlich **Acronal**, außerdem Lhydran und Lurapret (Polymerdispersionen) |
| Eintauchtiefe | optimal **2–3 cm unter dem Füllspiegel**; heute wegen paralleler Bedienung mehrerer Tankzüge in der Praxis nicht eingehalten |
| Mannloch | Innendurchmesser **0,5 m** bei allen gemessenen Fahrzeugen, Wandstärke 5 mm; Verschlussart und Aufbau unterschiedlich |
| Ex-Schutz | keine Ex-Zone; Maschinenrichtlinie 2006/42/EG bzw. ab Januar Verordnung (EU) 2023/1230 |
| Verladebrücke | Länge 1,75 m; Abstand Steg bis Mannloch ca. 2 m (je nach Stellung des Tankzugs) |
| Heutiger Arm | Aufhängung zur Decke, Abstand Aufhängung zum Boden 2,30 m [Bezug prüfen]; mittlerer schräger Teil 2,8–3 m; Füllrohr 2 m (1,5 m bis Flansch); Füllrohrverlängerung mit Kupplung 1,3 m |
| Absperrung heute | manuelle Stellklappe am Arm DN 80, PN 10, −10 … +100 °C |
| Grundstellung heute | optischer Näherungsschalter mit Reflektor |
| Überfüllsicherung heute | Liquiphant auf einem Halter, der auf dem Domkasten aufliegt und das Füllrohr mit einem Ring umfasst – von Hand gesetzt. **Schutzkorb ragt 22 cm in den Tank, Schwinggabel 17 cm lang** (27.10.) |
| Abschaltung heute | Überfüllsicherung über die **SPS**; Sicherheitsabschaltung könnte über eigenen Sicherheitskreis die **Pumpe** stoppen (27.10.) |
| Füllgrad | normal **95 %**; Produkt darf nicht überlaufen, Schaum ggf. schon – Reinigung dann ca. 30 min (27.10.) |
| Füllleistung | **20–25 t/h**, Dichte meist 1,01–1,04 g/cm³ → ca. **20–25 m³/h** (27.10.) |
| Fahrzeuge | **50–60 Tankwagen pro Tag** (27.10.) |
| Schäumen | Produkt **schäumt** beim Befüllen; Radar und Ultraschall können durch Schaum gestört werden |
| Spülwanne | an der Parkstellung **bestätigt**; Spülen kann verriegelt werden (Arm muss in Parkstellung stehen) (27.10.) |
| Abtropfen heute | **Eimer** unter dem Arm; 1 min Abtropfzeit reicht nicht, es tropft auch nach dem Spülen nach. Automatische Lösung (einfahrbare Schale/Klappe) gewünscht (27.10.) |
| Bedienung | Leitstelle wählt Produkt und Menge, Bediener vor Ort bestätigt das Fahrzeug und startet; Kammeraufteilung **am Bedienpult vor Ort** wählbar (so in der Gesprächsnotiz – mit dem Konzept „ohne Display“ abgleichen) |
| AdBlue (anderer Platz) | weniger automatisiert: Fahrer setzt den Arm von Hand, Anschluss am Dom mit Entlüftungsrohr |
| Fahrzeugstatistik | in Arbeit |

## Beobachtungen aus den Fotos

- Verladung in einer **überdachten Halle** mit mehreren Spuren nebeneinander (Arme 1, 2, 6, 8, 10):
  wenig Wind, Licht gleichmäßiger; Nachbarspur und Nachbararme liegen im Blickfeld der Kamera →
  Auswertebereich auf die eigene Spur begrenzen.
- Der Dom sitzt in einem **Domkasten** (Edelstahlwanne mit Rand) mit Armaturen (Belüftung,
  Anschlüsse, Bügel); der Deckel ist aufgeklappt (stehend oder auf den Laufsteg gelegt), Verschluss
  mit Knebeln. Kastenrand, Armaturen und Deckel sind Hindernisse – werden von der Kamera erfasst.
- Laufstege mit Gitterrosten entlang des Tanks; rote Klapptreppe/Bühne neben dem Fahrzeug.
- Der heutige Liquiphant-Halter entspricht dem HETA-Konzept der **aufliegenden Lanze**
  (`docs/fuellstand_ueberfuellsicherung.md`).
- Der Arm wird nach der Verladung in eine Wanne **gespült**.

## Folgen für das Projekt

- Mannloch 0,5 m: Referenzflansch Ø 220 mm passt, tiefes Eintauchen möglich (Grenze dann Reichweite
  und Tankboden).
- Nachziehen auf **2–3 cm** auslegen statt 10–20 cm: kleine, häufige Schritte → besser
  kontinuierlich nachziehen (Geschwindigkeit an den Spiegelanstieg angepasst, siehe Stützpunkte
  nachschieben). Simulation umgestellt auf 2–5 cm.
- Messstab und Koaxialrohr: Dispersionen trocknen an → Reinigung/Spülen berücksichtigen.
- Parkstellung über der vorhandenen Spülwanne (bestätigt 27.10.).
- Füllleistung 20–25 m³/h statt angenommen 60 m³/h: Spiegel steigt langsamer (bei ca. 5 m²
  Spiegelfläche ca. 7–8 cm/min) → Nachziehen ruhiger, Befüllung je Kammer länger.
- Überfüllsicherung kurz: heute ca. 20 cm Einhängetiefe – das SICK LFV mit 800 mm ist zu lang.
- **Abtropfschale/-klappe** wird eigenes Konstruktionsthema (50–60 Fahrzeuge/Tag, Eimer heute).
- Rohrisolierung über J1 vor der Motorbestellung prüfen.
- Schaum: Messstab (geführte Mikrowelle) misst durch leichten Schaum meist den Flüssigkeitsspiegel, dichter Schaum kann stören; Schwinggabel kann bei dichtem Schaum früher schalten (sichere Seite). Mit SICK klären, am Versuch prüfen.
- Schnittstelle DN 80 (heute) ↔ DN 100 (HETA-Arm) klären.

## Gespräch 27.10.2026 (S. Kaestel)

**Sensorik**
- BASF favorisiert derzeit einen **kapazitiven Sensor von Baumer** gegenüber der Schwinggabel;
  BASF testet selbst mit Produktproben und Schaum und bezieht den Füllstand-Spezialisten und den
  Betrieb ein.
- Als weitere Option fürs Nachziehen genannt: **hydrostatische Druckmessung**, frontbündig (wenig
  Verkleben); BASF fragt nach Erfahrungen aus Filteranlagen.
- HETA hat das Nachziehen mit Messstab und mit zwei Grenzschaltern simuliert: Messstab kann
  verkleben, Grenzschalter liefern nur zwei Punkte.

**Halterung Überfüllsicherung**
- Vorschlag HETA (aufliegend auf dem Dom, Arm bewegt sich daneben). P. Schreiber selbst hat
  angemerkt, dass eine **Gleithülse bei Verschmutzung klemmen** kann → Führung offen gestalten.
- Sensor und Halterung sollen möglichst wenig Produktkontakt haben; der heutige Sensor bekommt
  beim Reinigen Spritzer ab.

**Weitere Ideen (verworfen bzw. offen)**
- Teleskop-Füllrohr bis zum Tankboden: erleichtert das Nachziehen, mit klebrigem Produkt aber
  schwer dicht und sauber zu halten.
- Arm eingetaucht lassen: vereinfacht das Nachziehen, erschwert die Reinigung; automatisches
  Spülen besprochen.

**Anlage**
- Wozu die **DN80-Reduzierung** und die separate Lanze dienen, ist unklar; BASF prüft, ob eine
  Standardlänge ohne Reduzierung geht.
- **Rohrisolierung über dem Arm** könnte mit dem Servomotor **J1** kollidieren → Zeichnung prüfen,
  ggf. Isolierung ändern.
- Armmaße aus dem ursprünglichen MCO-Aufmaß; vorerst keine Geometrieänderung.

**Aufgaben**
- HETA: Sensoroptionen und gewählte Typen (Nachziehen, Überfüllsicherung) schicken; Skizze der
  Halterung mit Blick auf Reinigung und Abtropfschale.
- BASF: Sensortest mit Produkt und Schaum; Tankgeometrie, Kammeraufteilung, DN80/Lanze, Abstand
  Isolierung – Antwort per Mail. Nächster Termin in ca. 2 Wochen (bei Bedarf früher).

## Offene Fragen an BASF

1. Tiefe Domrand bis Tankboden (Spanne) und Kammeraufteilung (Schwallwände oder Mehrkammer).
2. Überfüllsicherung: von Hand weiter oder andocken? Bezug der 22 cm (ab Domrand/Auflage?),
   zulässiges Fabrikat, Zulassung (WHG/SIL).
3. ~~Abschaltung~~: Überfüllsicherung schaltet die **Pumpe** ab (festgelegt). Offen: Signalweg (SPS oder eigener Sicherheitskreis).
4. Kammerwahl: am Bedienpult vor Ort oder aus der Leitstelle?
5. DN80-Reduzierung/Lanze, Abstand Rohrisolierung über J1.
6. Ergebnisse der Sensortests (Baumer kapazitiv, ggf. Drucksensor).
