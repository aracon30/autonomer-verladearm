# Kinematik Verladearm

Modell: `vision/src/verladearm_vision/kinematics.py`. Maße, Servowerte, Parkstellung und
Hindernisse sind für jeden Verladearm verschieden und stehen in der Anlagendatei
(`vision/config/anlagen/<anlage>.yaml`, Ablauf siehe [Inbetriebnahme](inbetriebnahme.md)).
`default.yaml` enthält nur Platzhalter für Entwicklung und Simulation.

## Aufbau (vom Haltepunkt zum Auslass)

| Nr. | Element | Antrieb | Parameter |
|---|---|---|---|
| J1 | Drehgelenk am Haltepunkt (Schnittstelle Rohrleitung), senkrechte Achse, links/rechts | Servo | `joints.q1` |
| | innerer Ausleger nach vorne, fallend | | `inner_length`, `incline_deg` |
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
senkrecht. Die 3° Gefälle kippen das Fallrohr und damit die Achse J2 um 3°. Dadurch pendelt der
Auslass bei stark eingeschwenktem J2 um einige Zentimeter aus; das Modell berücksichtigt das.

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
- **Bahn:** Parkstellung → Anfahrpunkt `approach_height` über der Öffnung (Gelenkraum) →
  senkrecht auf `insertion_depth` unter die Öffnung (kartesisch, J3 senkt, J1/J2 gleichen aus).

Die Achsregelung liegt in der SPS. Das Python-Modell dient der Planung, der Live-Ansicht, der
Plausibilisierung und als Referenz für die SPS-Programmierung.

## Offene Punkte

- Sperrbereiche sind achsparallele Quader; schräge oder runde Hindernisse großzügig umschließen
- Kollision nur zwischen Rohrführung und Sperrbereichen, nicht mit dem Tankwagen selbst
- Pendeln des Auslasses beim Anfahren (J4 frei): Beschleunigungen begrenzen, Beruhigungszeit
  vor dem Eintauchen
- Hand-Auge-Kalibrierung, siehe Schnittstelle (`docs/kalibrierung.md`, offen)
