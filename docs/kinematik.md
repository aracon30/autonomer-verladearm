# Kinematik Verladearm

Modell: `vision/src/verladearm_vision/kinematics.py`, Maße in `vision/config/default.yaml` (`arm`).
**Die Maße dort sind Platzhalter** und müssen durch die Werte der realen Anlage ersetzt werden.

## Aufbau (vom Haltepunkt zum Auslass)

| Nr. | Element | Antrieb | Parameter |
|---|---|---|---|
| J1 | Drehgelenk am Haltepunkt (Schnittstelle Rohrleitung), senkrechte Achse, links/rechts | Servo | `limits_deg.q1` |
| | innerer Ausleger nach vorne, fallend | | `inner_length`, `incline_deg` |
| | 90°-Winkel nach unten, Fallrohr | | `drop` |
| J2 | Drehgelenk um die Achse des Fallrohrs, links/rechts | Servo | `limits_deg.q2` |
| | 90°-Winkel nach rechts | | `offset_right` |
| J3 | Drehgelenk um diese Querachse, Ausleger heben/senken | Servo | `limits_deg.q3` |
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
J1 = J2 = J3 = 0: beide Ausleger zeigen gestreckt nach vorne.
Positive Winkel: J1 und J2 drehen nach links (von oben gesehen gegen den Uhrzeigersinn), J3 hebt.

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

- Reale Maße, Achsgrenzen und Parkstellung eintragen (inkl. Lage J1 über Fahrbahn)
- Nullstellungen und Drehsinn der Servos mit dem Modell abgleichen
- Kollisionsbereiche (Stützen, Bühne, Geländer) als Sperrbereiche ergänzen
- Pendeln des Auslasses beim Anfahren (J4 frei): Beschleunigungen begrenzen, Beruhigungszeit
  vor dem Eintauchen
- Hand-Auge-Kalibrierung, siehe Schnittstelle (`docs/kalibrierung.md`, offen)
