# BASF Verladestelle H517 – Stand der Aufnahme

Quelle: Projektdokumentation S. Kaestel (BASF E-EDE/OE), 22.10.2026, Mail vom 23.10.2026,
Gespräch vom 27.10.2026 und Mail vom 10.11.2026 (Sensortest).
Die Fotos sind **vertraulich** und werden nicht im Repository abgelegt; hier nur die für die
Auslegung nötigen Angaben.

## Angaben BASF

| Thema | Angabe |
|---|---|
| Produkte | hauptsächlich **Acronal**, außerdem Lhydran und Lurapret (Polymerdispersionen) |
| Eintauchtiefe | optimal 2–3 cm unter dem Füllspiegel; **ca. 5–15 cm sind zulässig** (10.11.). Gründe fürs Nachziehen: weniger Verschmutzung (Armaturen/Griffe), kein Produktverlust durch Abspülen, geringerer Pumpendruck |
| Mannloch | Innendurchmesser **0,5 m** bei allen gemessenen Fahrzeugen, Wandstärke 5 mm; Verschlussart und Aufbau unterschiedlich |
| Ex-Schutz | keine Ex-Zone; Maschinenrichtlinie 2006/42/EG bzw. ab Januar Verordnung (EU) 2023/1230 |
| Verladebrücke | Länge 1,75 m; Abstand Steg bis Mannloch ca. 2 m (je nach Stellung des Tankzugs) |
| Heutiger Arm | Aufhängung zur Decke, Abstand Aufhängung zum Boden 2,30 m [Bezug prüfen]; mittlerer schräger Teil 2,8–3 m; Füllrohr 2 m (1,5 m bis Flansch); Füllrohrverlängerung mit Kupplung 1,3 m – wird **wöchentlich abgekuppelt und mit Hochdruck gereinigt**, sonst setzt sich der Auslauf zu (10.11.) |
| Absperrung heute | manuelle Stellklappe am Arm DN 80, PN 10, −10 … +100 °C |
| Grundstellung heute | optischer Näherungsschalter mit Reflektor |
| Überfüllsicherung heute | Liquiphant (E+H FTL51-6K0D0/0, FEL54, Länge 220 mm, Schaltpunkt 207 mm) auf einem Halter, der auf dem Domkasten aufliegt und das Füllrohr mit einem Ring umfasst – von Hand gesetzt. Schutzkorb ragt 22 cm in den Tank |
| Überfüllsicherung neu | **keine WHG-/SIL-Anforderung**; BASF favorisiert **Baumer LBFS** (schaltet auch bei Schaum, im Betrieb bekannt); Alternative im nächsten Versuch: UWT Capanivo (10.11.) |
| Abschaltung heute | Überfüllsicherung über die **SPS**; Sicherheitsabschaltung könnte über eigenen Sicherheitskreis die **Pumpe** stoppen (27.10.) |
| Füllgrad | normal **95 %**; Produkt darf nicht überlaufen, Schaum ggf. schon – Reinigung dann ca. 30 min (27.10.) |
| Füllleistung | **20–25 t/h**, Dichte meist 1,01–1,04 g/cm³ → ca. **20–25 m³/h** (27.10.) |
| Fahrzeuge | **50–60 Tankwagen pro Tag** (27.10.) |
| Schäumen | Produkt **schäumt** beim Befüllen; Radar und Ultraschall können durch Schaum gestört werden |
| Spülwanne | an der Parkstellung **bestätigt**; Spülen kann verriegelt werden (Arm muss in Parkstellung stehen) (27.10.) |
| Verdrängen/Spülen der Leitung | nach dem Abfüllen drückt **Druckluft** den Leitungsinhalt in den Tank; die Absperrklappe muss beim Verdrängen und Spülen **offen** sein (10.11.); Ablauf und Signal angefragt |
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
- Der heutige Liquiphant-Halter entspricht dem HETA-Konzept der aufliegenden Lanze; neu sitzt die
  Überfüllsicherung an der **Dom-Abdeckung** am Arm (`docs/fuellstand_ueberfuellsicherung.md`).
- Der Arm wird nach der Verladung in eine Wanne **gespült**.

## Folgen für das Projekt

- Mannloch 0,5 m: tiefes Eintauchen möglich (Grenze dann Reichweite und Tankboden); Referenz für
  das Nachmessen wird die **Dom-Abdeckung** (statt Referenzflansch, Maße folgen Konstruktion).
- Nachziehen: Auslass **5–15 cm unter dem Spiegel** (10.11.), ein Sensor, Hub ca. 5 cm.
- Messstab und Koaxialrohr: Dispersionen trocknen an → Reinigung/Spülen berücksichtigen.
- Parkstellung über der vorhandenen Spülwanne (bestätigt 27.10.).
- Füllleistung 20–25 m³/h statt angenommen 60 m³/h: Spiegel steigt langsamer (bei ca. 5 m²
  Spiegelfläche ca. 7–8 cm/min) → Nachziehen ruhiger, Befüllung je Kammer länger.
- Überfüllsicherung kurz: heute ca. 20 cm Einhängetiefe.
- **Abtropfsicherung**: rein mechanisch (Pendelwanne, Rev6), Vorstellung beim nächsten Termin.
- Rohrisolierung über J1: von BASF zugesagt (geklärt).
- **Reinigung Füllrohr** (wöchentlich, Hochdruck): Umsetzung am Arm klärt die HETA-Mechanik.
- **Verdrängen/Spülen**: Klappe offen, Arm bleibt im Tank, Signal „beendet“ von der Leitstelle (SPS-Schritt folgt nach Antwort BASF).
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

## Sensortest BASF (Mail 10.11.2026)

- **Baumer LBFS** erkennt Schaum; bei AN6337 genügt schon leichter Schaumkontakt. Bei AN6281
  reagiert er schwächer → empfindlichere Schaltschwelle und Reinigung nötig.
- **Anhaftung:** nach dem Herausziehen kehrt das Signal nicht auf den Luftwert zurück. Minimum der
  Kennlinie: Luft ca. 95 %, Produktfilm ca. 45 %, eingetaucht ca. 20 % (Sweep range). Mit „Range
  max“ ca. 30 % ließe sich Film von Produkt trennen; BASF prüft im Wiederholversuch, wie stabil
  das über viele Zyklen bleibt. Ob „trocken“ trotz Film erkannt wird: nein, nur Schalten ja/nein.
- Je nach Schwelle schaltet er auf Schaum oder erst auf Flüssigkeit.
- HETA hat als Alternative fürs Nachziehen ein **Radar an der Dom-Abdeckung** vorgeschlagen (z. B.
  E+H Micropilot FMR20B); Entscheidung über den Sensor liegt bei BASF.
- Fragen zur Steuerung beantwortet ein BASF-Ansprechpartner (folgt); Termin Do 12.11. ab 15 Uhr
  vorgeschlagen.

## Offene Fragen an BASF

1. Tiefe Domrand bis Tankboden (Spanne) und Kammeraufteilung (Schwallwände oder Mehrkammer).
2. ~~Überfüllsicherung Fabrikat/Zulassung~~: Baumer LBFS, keine WHG/SIL (10.11.). Offen:
   Bestellcode, Länge, Prozessanschluss.
3. ~~Abschaltung~~: Überfüllsicherung schaltet die **Pumpe** ab (festgelegt). Offen: Signalweg (SPS oder eigener Sicherheitskreis).
4. Kammerwahl: am Bedienpult vor Ort oder aus der Leitstelle?
5. DN80-Reduzierung/Lanze (~~Rohrisolierung über J1~~: geklärt).
6. Sensor Nachziehen: LBFS (Wiederholversuch) oder Radar – Entscheidung BASF.
7. Verdrängen/Spülen: wann im Ablauf, wie lange, welches Signal „beendet“.
8. Ansprechpartner Steuerung/Leitstelle.
