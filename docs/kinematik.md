# Kinematik Verladearm

Modell: `vision/src/verladearm_vision/kinematics.py`. Maße, Servowerte, Parkstellung und
Hindernisse sind für jeden Verladearm verschieden und stehen in der Anlagendatei
(`vision/config/anlagen/<anlage>.yaml`, Ablauf siehe [Inbetriebnahme](inbetriebnahme.md)).
`default.yaml` enthält nur Platzhalter für Entwicklung und Simulation.

## Aufbau (vom Haltepunkt zum Auslass)

| Nr. | Element | Antrieb | Parameter |
|---|---|---|---|
| J1 | Drehgelenk am Haltepunkt (Schnittstelle Rohrleitung), senkrechte Achse, links/rechts | Servo | `joints.q1` |
| | innerer Ausleger nach vorne, **fest** fallend (z. B. 3°) | | `inner_length`, `incline_deg` |
| | 90°-Winkel nach unten, Fallrohr | | `drop` |
| J2 | Drehgelenk um die Achse des Fallrohrs, links/rechts | Servo | `joints.q2` |
| | 90°-Winkel nach rechts | | `offset_right` |
| J3 | Drehgelenk um diese Querachse, Ausleger heben/senken | Servo | `joints.q3` |
| | 90°-Winkel nach vorne, äußerer Ausleger (bei J3 = 0 ebenfalls fallend) | | `outer_length` |
| | 90°-Winkel nach links | | `offset_left` |
| J4 | freies Drehgelenk, Achse parallel zu J3 | ohne Motor | |
| | 90°-Winkel nach unten, Auslass | Schwerkraft | `outlet_length` |

J1 und J2 positionieren den Auslass in der Waagerechten (wie ein Scara-Roboter), J3 bestimmt die
Höhe. Weil J4 frei pendelt und parallel zu J3 liegt, hängt der Auslass unabhängig vom Hubwinkel
senkrecht. Nur der innere Ausleger hat ein festes Gefälle; der Winkel danach hat entsprechend
90° − Gefälle (z. B. 87° bei 3°), sodass das Fallrohr mit J2 senkrecht steht und J2 um die
Senkrechte dreht;
der äußere Ausleger wird über J3 eingestellt (J3 = 0: waagerecht). Ist das Fallrohr an einem
anderen Arm geneigt, wird das mit `drop_tilt_deg` eingetragen; dann hängt der Auslass je nach J2
leicht schräg, und das Modell rechnet die Schräglage mit.

## Koordinatensystem Armbasis

Ursprung auf der Achse J1 am Haltepunkt, **x** nach vorne (innerer Ausleger bei J1 = 0),
**y** nach links, **z** nach oben. `TargetX/Y/Z` im `DB_Vision` beziehen sich darauf (mm).
Modellwinkel J1 = J2 = J3 = 0: beide Ausleger zeigen gestreckt nach vorne.
Positive Modellwinkel: J1 und J2 drehen nach links (von oben gesehen gegen den Uhrzeigersinn),
J3 hebt. Die Servowerte der Anlage werden über `zero` (Servowert in Nullstellung) und
`direction` (±1) umgerechnet: Servo = zero + direction · Modellwinkel.

Die Kalibriermatrix (`calibration.matrix`) rechnet Sensorkoordinaten in dieses System um.
Der Platzhalter nimmt einen Sensor 3 m vor J1 und 2,1 m über J1 an, senkrecht nach unten blickend.

## Rechnung

- **Vorwärts:** Gelenkwinkel → Lage aller Rohrecken und des Auslassendes (Kette aus Drehungen).
  J4 wird nicht gemessen: Der Auslass hängt senkrecht zur Achse J4 so tief, wie es die Schwerkraft
  zulässt.
- **Rückwärts:** Zielpunkt des Auslassendes → J1, J2, J3, numerisch innerhalb der Achsgrenzen.
  Ohne Startwert wird die Lösung nahe der Parkstellung gewählt, beim Eintauchen die zur
  vorherigen Stellung nächstgelegene (stetige Bahn).
- **Bahn (Job 1):** Istlage → **Vorpunkt** `approach_height + approach_lift` über der Öffnung
  (Gelenkraum, synchron) → senkrecht auf den Anfahrpunkt `approach_height` → senkrecht auf
  `insertion_depth` unter die Öffnung (kartesisch, J3 senkt, J1/J2 gleichen aus).
  Durch das senkrechte Absenken streift der Arm weder Domkragen noch Deckel.

## Kollisionsfreie Bahnen

Jede geplante Stellung wird gegen alle Hindernisse geprüft: Rohrführung vom Haltepunkt bis zum
Auslassende, als Linienzug alle 5 cm abgetastet, Abstand mindestens `clearance`. Zwischen zwei
Stützpunkten fährt die SPS synchron im Gelenkraum; die Prüfung tastet diese Bewegung so fein ab,
dass sich kein Punkt des Arms zwischen zwei Prüfstellungen mehr als 3 cm bewegt.

**Hindernisse**

| Herkunft | Hindernis | Form |
|---|---|---|
| Anlagendatei `arm.obstacles` | Stützen, Geländer, Bühne … | `quader` (achsparallel), `quader_gedreht`, `zylinder` |
| jede Messung (Job 1) | Tankkörper | Zylinder entlang der gemessenen Tankachse (Radius aus der Messung); ebenes Dach: Quader |
| jede Messung | Domkragen | senkrechter Zylinder, Öffnung + Wandstärke |
| jede Messung | **offener Domdeckel** | gedrehter Quader aus den Deckelpunkten |

Tank und Domkragen lassen über der Öffnung einen senkrechten **Durchgang** frei
(Radius = Öffnung − max(Rohr, Markierungsscheibe) − `passage_margin`, bei 500 mm Öffnung ≈ 88 mm).
Nur dort darf der Auslass hinein. Die Hindernisse aus Job 1 gelten auch für Job 2 und Job 3.

**Deckelerkennung:** Punkte seitlich der Öffnung (bis `lid_search` außerhalb) und über der
Domoberkante (bis `lid_max_above`) werden auf ein 4-cm-Raster gelegt. Die größte zusammenhängende
Gruppe dicht belegter Zellen ist der Deckel; Geländer oder einzelne Störpunkte hängen nicht daran.
Daraus wird ein am Deckel ausgerichteter Quader (radial, entlang des Scharniers, senkrecht) mit
den 1-/99-%-Perzentilen plus `lid_margin`. Die Richtung des Deckels (Azimut) und seine Höhe
stehen im Protokoll (`szene.deckel`) und in der Live-Ansicht.

**Suche nach dem Weg** (Job 1), der Reihe nach:

1. beide Armstellungen am Dom (Ellenbogen links/rechts): Eintauchen muss frei sein. Der Rohrbogen
   an J4 darf dabei z. B. nicht über dem Deckel stehen.
2. Vorpunkthöhen `approach_lift`, 0,35, 0,2, 0,1 m: senkrechtes Absenken muss frei sein.
3. direkte synchrone Fahrt; wenn nicht frei: J3 anheben, schwenken, J3 senken.
4. erst wenn für keine Möglichkeit eine direkte Fahrt frei ist: **Suche im Gelenkraum**
   (RRT-Connect) zu allen möglichen Vorpunkten gleichzeitig. Der gefundene Weg wird auf wenige
   Stützpunkte geglättet und fein geprüft. Fester Zufallsstartwert: gleiche Messung, gleiche Bahn.
5. danach kartesische **Umwege**: senkrecht auf sichere Höhe, waagerecht über den Vorpunkt, oder
   seitlich in 8 Richtungen 1 m am Dom vorbei. Höchstens 8 Zwischenstützpunkte.
6. nichts frei → **Fehler 31**, der Arm fährt nicht. Die Meldung nennt das Hindernis.

Die Suche ist auf `planning.time_limit_s` (Standard 3,5 s) begrenzt, für Job 1 und Job 3. Auf dem
Entwicklungsrechner braucht Job 1 im Mittel 0,5 s und höchstens 3,1 s.

**Rückfahrt (Job 3):** senkrecht heraus (so hoch wie möglich), dann wie oben in die Parkstellung.
Gibt es keinen neuen Weg, fährt der Arm senkrecht bis auf den Vorpunkt und den **in Job 1
geprüften Anfahrweg rückwärts** (`rueckfahrt_rueckwaerts` im Protokoll).

**Grenzen:** Die Hindernisse kommen aus einer Aufnahme. Was der Sensor nicht sieht (verdeckte
Teile, Personen), ist nicht enthalten; dafür bleibt die Sicherheitstechnik der Anlage zuständig.
In der Simulation (Beispielanlage, Deckel zufällig ausgerichtet, 95–115° geöffnet) kamen alle
Lkw kollisionsfrei an den Dom, Kesselwagen in etwa 70–90 % der Fälle. Die übrigen meldeten
Fehler 31: Der Kesselwagen-Dom liegt so hoch, dass der Arm den Auslass nur knapp 0,5 m über den
Kragen heben kann, der offene Deckel ist aber ca. 0,6 m hoch. Steht der Deckel zwischen Arm und
Dom oder unter dem Rohrbogen an J4, gibt es keinen Weg; auch eine Suche ohne Zeitlimit findet
dann keinen. Abhilfe: Deckel in eine andere Richtung stellen, Fahrzeug versetzen, oder bei der
Anlagenplanung mehr Hub an J3 bzw. einen höheren Haltepunkt vorsehen.

Die Achsregelung liegt in der SPS. Das Python-Modell dient der Planung, der Live-Ansicht, der
Plausibilisierung und als Referenz für die SPS-Programmierung.

## Offene Punkte

- Rohrdurchmesser nur über `clearance` berücksichtigt (Rohrachse als Linie)
- Pendeln des Auslasses beim Anfahren (J4 frei): Beschleunigungen begrenzen, Beruhigungszeit
  vor dem Eintauchen
- Hand-Auge-Kalibrierung, siehe Schnittstelle (`docs/kalibrierung.md`, offen)
