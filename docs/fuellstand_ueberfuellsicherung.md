# Konzept: Füllstand, Nachziehen und Überfüllsicherung

Stand 15.10.2026 – Entwurf zur Abstimmung mit dem Kunden (Anforderung BASF vom 15.10.2026).
Hintergrund und erste Idee: `docs/ideenspeicher.md`.

## Festlegungen (Stand 15.10.2026)

| Thema | Lösung |
|---|---|
| **Nachziehen** | ja, gefordert. Messstab (SICK LFC bzw. LFP) fest an der Lanze misst, wie tief der Auslass im Produkt steckt; die SPS hält ihn z. B. 100–200 mm eingetaucht und zieht den Arm nach |
| **Füllende** | Durchflusssensor mit Sollmenge (wie im ersten Termin mit BASF besprochen) |
| **Füllstand aus der Armhöhe** | Spiegel unter Domrand = Eintauchtiefe des Auslasses (Kamera + Kinematik) − benetzte Länge am Messstab. Für Anzeige, Nachziehen und als Plausibilitätsprüfung gegen den Durchflusssensor |
| **Überfüllsicherung** | wie heute **Liquiphant mit fester Länge ab Domrand** – künftig an der **aufliegenden Lanze** (Skizze `docs/skizzen/ueberfuell_lanze.png`): Auflage am Domrand, Lanze bleibt beim Nachziehen liegen, Schaltpunkt bleibt fest; wirkt direkt auf die Absperrklappe |

**Gerätewahl (Vorschlag HETA, 15.10.2026):**
- Überfüllsicherung: **SICK LFV 200** (Schwinggabel) mit **Rohrverlängerung** – die Verlängerung bildet
  die Lanze (Länge L). Voraussetzung: Ausführung mit Zulassung als Überfüllsicherung (WHG/SIL nach
  Vorgabe BASF) und Freigabe durch BASF; sonst Liquiphant wie heute.
- Messstab Nachziehen: geführte Mikrowelle, günstig **SICK LFP Cubic** oder **ifm LR** (IO-Link);
  Abstand zum Auslassrohr bzw. Koaxrohr beachten (Fehlechos, Anhaftung bei Kleber).

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
