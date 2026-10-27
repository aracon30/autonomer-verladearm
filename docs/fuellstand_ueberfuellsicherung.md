# Konzept: Füllstand, Nachziehen und Überfüllsicherung

Stand 27.10.2026 – Entwurf zur Abstimmung mit dem Kunden (Anforderung BASF vom 15.10.2026,
Gespräch 27.10.2026: `docs/kunde_basf_h517.md`). Hintergrund und erste Idee: `docs/ideenspeicher.md`.

## Neu aus dem Gespräch mit BASF (27.10.2026)

| Thema | Angabe BASF | Folge |
|---|---|---|
| Füllleistung | 20–25 t/h ≈ **20–25 m³/h** | Spiegel steigt ca. 7–8 cm/min (bei ca. 5 m²), Nachziehen etwa alle 15–20 s um 2 cm |
| Füllgrad | normal **95 %** | = Maximalhöhe (Ebene 2), je Fahrzeug bzw. Kammer |
| Überfüllsicherung heute | Schutzkorb **22 cm** im Tank, Gabel 17 cm | Schaltpunkt nur ca. 20 cm unter dem Rand → Lanze kurz, nicht 800 mm |
| Abschaltung | heute über die SPS; Sicherheitskreis könnte die **Pumpe** stoppen | Ebene 3: Klappe und/oder Pumpe – mit Peter und BASF festlegen |
| Sensor | BASF favorisiert **kapazitiv (Baumer)**, testet selbst; Druckmessung als Idee | Vergleich unten; Baumer CleverLevel als Alternative zum SICK LFC |
| Halterung | Gleithülse könnte bei Verschmutzung klemmen; möglichst kein Produktkontakt, spritzwassergeschützt | Führung offen gestalten (z. B. Gabel statt Hülse), reinigbar; Skizze überarbeiten |
| Abtropfen | heute Eimer, 1 min reicht nicht | einfahrbare Abtropfschale/-klappe am Arm vorsehen |

## Sensorvergleich Nachziehen (27.10.2026)

| Prinzip | Beispiele | Messwert | Schaum | Anhaftung (Dispersion) | Bewertung |
|---|---|---|---|---|---|
| **Kapazitiver Grenzschalter**, 2 Stück | Baumer CleverLevel, SICK LFC, ifm LMT | 2 Schaltpunkte (1 und 3 cm) | ausblendbar (Einstellung) | ausblendbar, kleine glatte Spitze, gut abzuspülen | **Favorit**, einfach, günstig; Test mit Produkt |
| **Hydrostatischer Drucksensor**, frontbündig | z. B. Baumer, VEGA, E+H | durchgehend (Eintauchtiefe aus Druck) | unempfindlich (misst Flüssigkeitssäule) | frontbündig, wenig Verkleben | Option; nur wenige mbar bei 2–3 cm → Genauigkeit und Drift prüfen; nicht im Strahl des Auslasses montieren (Strömungsdruck) |
| Geführte Mikrowelle (Messstab) | SICK LFP, ifm LR | durchgehend | leichter Schaum meist unkritisch | Stab bzw. Koaxrohr kann verkleben | Reserve |
| Radar / Ultraschall | – | durchgehend | **gestört** | – | ungeeignet (Schaum, Rohr im Weg) |

## Festlegungen (Stand 26.10.2026)

| Thema | Lösung |
|---|---|
| **Nachziehen** | ja, gefordert. **Zwei kapazitive Grenzschalter** (z. B. SICK LFC) übereinander am Auslassrohr, ca. 1 cm (A) und 3 cm (B) über dem Auslassende; die SPS hält den Auslass **1–3 cm** unter dem Spiegel (Vorgabe BASF 2–3 cm, 23.10.2026). Messstab LFP nur noch Alternative, falls der LFC im Test nicht sicher schaltet (Abschnitt unten) |
| **Füllende** | 1. Sollmenge über Durchflusssensor; 2. zusätzlich **Maximalhöhe** aus Armhöhe + Grenzschaltern (Spiegel an jedem Schaltpunkt bekannt). **Nie über die Überfüllsicherung** (Abschnitt Schutzebenen) |
| **Füllstand aus der Armhöhe** | an jedem Schaltpunkt: Spiegel unter Domrand = Eintauchtiefe des Auslasses (Kamera + Kinematik) − Höhe des Schaltpunkts über dem Auslassende. Für Maximalhöhe, Anzeige und Plausibilität gegen den Durchflusssensor |
| **Überfüllsicherung** | wie heute **Liquiphant mit fester Länge ab Domrand** – künftig an der **aufliegenden Lanze** (Skizze `docs/skizzen/ueberfuell_lanze.png`): Auflage am Domrand, Lanze bleibt beim Nachziehen liegen, Schaltpunkt bleibt fest; wirkt direkt auf die Absperrklappe |

**Gerätewahl (Vorschlag HETA, 15.10.2026):**
- Überfüllsicherung: **SICK LFV 200** (Schwinggabel) mit **Rohrverlängerung** – die Verlängerung bildet
  die Lanze (Länge L). Voraussetzung: Ausführung mit Zulassung als Überfüllsicherung (WHG/SIL nach
  Vorgabe BASF) und Freigabe durch BASF; sonst Liquiphant wie heute.
- Nachziehen (Stand 26.10.2026): **2 × kapazitiver Grenzschalter** (SICK LFC, Alternativen ifm LMT,
  Baumer CleverLevel, VEGAPOINT, E+H Liquipoint – ähnlicher Preis; entscheidend ist das Ausblenden
  von Anhaftung und Schaum). Test mit Acronal vorab (Abschnitt unten).
- Alternative Messstab: geführte Mikrowelle **SICK LFP Cubic** oder **ifm LR** (IO-Link); Koaxrohr
  kann sich mit Dispersion zusetzen.

Heute wird der Liquiphant von Hand am oberen Rand des Tankwagens befestigt. Die Lanze übernimmt
genau diesen Bezug (Domrand + feste Länge) automatisch.

## Anforderung

- **Unterspiegelbeladung:** Der Arm taucht möglichst tief in die Tankkammer ein.
- Die **Füllstandssensorik** steuert das Fahren des Arms im Tank (Nachziehen bei steigendem Spiegel).
- Eine **Überfüllsicherung** ist heute Pflicht und wird von Hand aufgelegt. Sie muss auch
  automatisiert vorhanden sein oder gleichwertig ersetzt werden.
- An der Verladestelle liegt **keine Ex-Zone** vor.

## Grundsatz: zwei getrennte Funktionen

| Funktion | Aufgabe | Wirkt auf | Anforderung |
|---|---|---|---|
| **Füllstandsmessung** (Betrieb) | Spiegelhöhe laufend messen, Arm nachziehen, Füllende ankündigen | SPS → Arm, Füllventil | normale Betriebsmesstechnik |
| **Überfüllsicherung** (Sicherheit) | Grenzstand erkennen und Befüllung sicher beenden | direkt auf Absperrklappe/Pumpe, unabhängig von PC, Kamera und Betriebsmessung | zugelassene Einrichtung, sicherheitsgerichtet (SIL nach Vorgabe des Betreibers) |

Eine einzelne Messung darf nicht beides übernehmen: Fällt sie aus, versagen Regelung und Schutz
gleichzeitig. Die Kamera kommt für beides nicht in Frage (Rohr verdeckt die Öffnung, Flüssigkeit
spiegelt).

## Ablauf mit Unterspiegelbeladung

1. Klapptreppe eingefahren, Bediener bestätigt den Start.
2. Messen, Anfahren, Nachmessen wie bisher (Job 1 und 2).
3. **Eintauchen bis zur Tiefe „Unterspiegel“** – produktabhängig, mit Mindestabstand zum Tankboden
   (Bodenhöhe aus der Fahrzeugmessung bzw. Fahrzeugdaten).
4. **Befüllen:** Füllstandsmessung am Auslasskopf meldet den Spiegel. Der Auslass bleibt knapp
   unter der Oberfläche; die SPS zieht den Arm stufenweise senkrecht nach (Stützpunkte vom PC als
   Nachzieh-Tabelle, die SPS fährt sie selbstständig ab).
5. **Füllende:** Sollmenge (Durchfluss) oder Sollfüllstand erreicht → Absperrklappe zu.
   Überfüllsicherung greift unabhängig, falls die Betriebsmessung versagt.
6. Abtropfpause, Rückfahrt in die Parkstellung (Job 3).

## Überfüllsicherung – Varianten

| | Variante | Bewertung |
|---|---|---|
| A | Treppe erneut ausfahren, Mitarbeiter legt die Sicherung nach dem Eintauchen auf | einfach, bewährte Sonde; aber wieder Personal auf dem Fahrzeug, Treppe muss neben dem eingetauchten Arm Platz haben |
| B | **Grenzwertgeber am Verladearm** (Auslasskopf) | vollautomatisch. Der Schaltpunkt muss auf **fester Höhe im Tank** liegen: Da der Arm beim Nachziehen nach oben fährt, braucht der Geber eine eigene, mechanisch festgelegte Lage (z. B. Lanze mit Anschlag am Domrand) oder das Nachziehen endet unterhalb des Schaltpunkts. Zulassung als Überfüllsicherung klären |
| C | Mitarbeiter legt die Sicherung vor dem Start ein; die Kamera erkennt sie als Hindernis im Dom und der Arm fährt daran vorbei | mit der vorhandenen Software weitgehend machbar (Aufbauten im Dom werden schon erkannt). Kritisch: Kabel im Dom, Platz neben der Sonde für das Füllrohr bei kleinen Öffnungen |
| D | **Zugelassene Füllstandsmessung als Überfüllsicherung** (z. B. Radar mit SIL-Zulassung am Auslasskopf), zusätzlich zur Betriebsmessung | vollautomatisch, kein Personal; zwei unabhängige Sensoren am Auslasskopf. Akzeptanz durch Betreiber und Prüfstelle klären |

**Empfehlung zur Abstimmung:** Variante **D** bzw. **B+D** – am Auslasskopf ein Radar für die
Betriebsmessung (Nachziehen) und ein zweiter, zugelassener Grenzwertgeber als Überfüllsicherung,
der direkt auf die Absperrklappe wirkt. **Variante C** als Übergangslösung für den Prototyp, weil
sie die heutige Sonde weiterverwendet.

## Offene Fragen an den Betreiber

- Vorgaben für Überfüllsicherungen am Standort (Zulassung, SIL, Prüfintervalle)?
- Darf die Sicherung fest am Arm sitzen, oder muss sie fahrzeugseitig/separat sein?
- Unterspiegelbeladung für alle Produkte? Mindestabstand zum Tankboden?
- Füllende heute über Menge (Durchfluss) oder Füllstand?
- Anbindung an das PLS: welche Signale (Freigabe, Menge, Störungen)?

## Folgen für das Projekt

- **Hardware:** Radar und Grenzwertgeber am Auslasskopf (Kabelführung entlang des Arms), Absperrklappe
  mit Stellungsrückmeldung, ggf. Durchflussmesser.
- **SPS (Peter):** Nachziehregelung, Füllventil, Auswertung Überfüllsicherung (direkt, nicht über PC).
- **Vision-PC:** Bodenhöhe/Tankgeometrie für die maximale Eintauchtiefe, Nachzieh-Tabelle
  (Schnittstelle Version 3), Erkennung einer eingelegten Sonde (Variante C).
- **Simulation:** steigender Füllstand, Nachziehen, Abschaltung.

## Nachziehen mit zwei Grenzschaltern (26.10.2026)

```
        │ Auslassrohr
   [B]  ├─ ca. 3 cm über Auslassende  → „nass“ = zu tief → J3 hebt
   [A]  ├─ ca. 1 cm über Auslassende  → „nass“ = Auslass eingetaucht
        └─ Auslassende
```

| A | B | Bedeutung | SPS |
|---|---|---|---|
| trocken | trocken | Auslass über dem Spiegel (Füllbeginn) | warten, Spiegel steigt; war A schon nass → zu weit gehoben, Störung |
| nass | trocken | **richtig**: Auslass 1–3 cm unter dem Spiegel | Arm steht |
| nass | nass | zu tief | J3 hebt, bis B trocken |
| trocken | nass | unplausibel (Schaum, Belag, Defekt) | Störung, Klappe zu |

Die Schalter überwachen sich gegenseitig. Beide dienen **nur** dem Nachziehen und der
Maximalhöhe, nie als Überfüllsicherung.

## Schutzebenen Füllende (26.10.2026)

Die Überfüllsicherung darf **nicht betriebsmäßig** zum Beenden der Füllung genutzt werden
(Grundsatz WHG/AwSV): Sie ist die letzte, unabhängige Ebene; ihr Ansprechen ist eine Störung.

| Ebene | Einrichtung | Normalfall |
|---|---|---|
| 1 | **Sollmenge** über Durchflusssensor (Vorgabe Leitstelle) | beendet die Füllung |
| 2 | **Maximalhöhe** aus Armhöhe + Grenzschaltern (Einstellwert je Anlage/Fahrzeug) | greift, wenn die Menge nicht passt → Klappe zu, Meldung |
| 3 | **Überfüllsicherung** (Liquiphant bzw. aufliegende Lanze), direkt auf die Absperrklappe bzw. Pumpe (BASF 27.10.: Sicherheitskreis stoppt die Pumpe – festlegen) | greift nur, wenn 1 und 2 versagen → Klappe zu, Störung |

Die Maximalhöhe (Ebene 2) muss einige Zentimeter **unter** dem Schaltpunkt der Überfüllsicherung
liegen, damit Ebene 3 im Normalfall nie anspricht.

## Test Grenzschalter LFC für das Nachziehen (Entscheidung 26.10.2026)

Der **SICK LFC-XXSBTE** ist ein **kapazitiver Grenzschalter** (kompakt, G ½", PEEK-Spitze, IO-Link,
2 × PNP), **kein Messstab**: er meldet nur „Produkt an der Spitze ja/nein“. Laut SICK kann er Schaum
und Anhaftungen ausblenden; wasserbasierte Medien sind voreingestellt.

Einsatz: zwei Stück am Auslassrohr (Abschnitt „Nachziehen mit zwei Grenzschaltern“). Für den Test
reicht ein LFC – beide Schaltpunkte lassen sich nacheinander prüfen.

LFP Cubic (kontinuierlich) bleibt die Alternative, falls der LFC im Test nicht sicher schaltet.

Test mit echter Dispersion (Acronal), Auswertung über SiLink2 am Laptop (SOPAS):
1. Schaltpunkt: Spitze langsam eintauchen und herausziehen, Schaltpunkt gegen Maßstab notieren
   (Ziel ±5 mm, Wiederholbarkeit).
2. Anhaftung: nach dem Herausziehen mit Film an der Spitze – schaltet er wieder auf „trocken“?
   Nach 10 min / 1 h / angetrocknet wiederholen; Einstellungen zum Ausblenden von Anhaftungen testen.
3. Schaum: Produkt aufschäumen – schaltet er im Schaum oder erst an der Flüssigkeit?
4. Reinigung: mit Wasser abspülen, danach Schaltverhalten wie neu?
5. Ergebnis mit Fotos dokumentieren; Entscheidung LFC (Zweipunkt) oder LFP (kontinuierlich).
