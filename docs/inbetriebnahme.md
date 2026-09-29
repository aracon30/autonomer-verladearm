# Inbetriebnahme Verladearm

Jeder Verladearm hat eigene Maße, Servo-Nullstellungen, Verfahrbereiche, Hindernisse und
Produkte. Diese Werte stehen in einer **Anlagendatei** und werden vor Ort eingestellt.
Alles andere (Erkennung, Schnittstelle, Standardwerte) kommt aus `vision/config/default.yaml`.

## Ablauf

1. **Anlagendatei anlegen**
   `vision/config/anlagen/beispiel.yaml` kopieren, z. B. als `lich_station3.yaml`.
   Kopf ausfüllen (Anlage, Datum, Name). SPS-Adresse unter `plc.url` eintragen.

2. **Maße aufnehmen** (`arm`)
   Von Gelenkachse zu Gelenkachse bzw. Rohrmitte zu Rohrmitte messen, in Metern:

   | Parameter | Strecke |
   |---|---|
   | `base_height` | Achse J1 bis Fahrbahn |
   | `inner_length` | Achse J1 bis Mitte Winkel nach unten |
   | `drop` | Winkel nach unten bis Mitte Winkel nach rechts |
   | `offset_right` | Winkel nach rechts bis Mitte Winkel nach vorne |
   | `outer_length` | Winkel nach vorne bis Mitte Winkel nach links |
   | `offset_left` | Winkel nach links bis Mitte Winkel nach unten (freies Gelenk J4) |
   | `outlet_length` | Winkel nach unten bis Auslassende |
   | `incline_deg` | Gefälle der Ausleger |

3. **Servoachsen einstellen** (`arm.joints`, alle Werte in Servo-Grad wie am Antrieb angezeigt)
   - `zero`: Arm im Handbetrieb so stellen, dass beide Ausleger gestreckt nach vorne zeigen und
     der äußere Ausleger im Gefälle liegt. Servowerte J1, J2, J3 ablesen.
   - `direction`: Jede Achse ein Stück im positiven Sinn verfahren. Dreht J1 bzw. J2 nach links
     (von oben gesehen gegen den Uhrzeigersinn) bzw. hebt J3 den Ausleger: `1`, sonst `-1`.
   - `min` / `max`: freigegebener Verfahrbereich (nicht die mechanischen Endanschläge).
   - `park`: Servowerte der Parkstellung.

4. **Hindernisse erfassen** (`arm.obstacles`)
   Stützen, Bühne, Geländer, Leitungen im Schwenkbereich als Quader in Armbasis-Koordinaten
   (Ursprung Achse J1, x vorne, y links, z oben; Meter). Großzügig umschließen.
   `clearance` ist der zusätzliche Mindestabstand zur Rohrachse.

5. **Produkte** (`products`): Eintauchtiefe je `ProductId`, `default` für alle übrigen.

6. **Arbeitsraum** (`commissioning`): Bereich, in dem die Domöffnung bei dieser Station liegen
   kann (unterschiedliche Tankwagen, Aufbauhöhen, Abstellpositionen).

7. **Hand-Auge-Kalibrierung** → `calibration.matrix`, siehe [Kalibrierung](kalibrierung.md):
   `python -m verladearm_vision.calibrate --config vision/config/anlagen/<anlage>.yaml --from-plc`

8. **Prüfen**
   ```bash
   python -m verladearm_vision.commissioning --config vision/config/anlagen/lich_station3.yaml > protokoll.md
   ```
   Prüft die Parameter, die Parkstellung und für jede Lage im Arbeitsraum, ob der Arm
   kollisionsfrei anfahren und mit der größten Eintauchtiefe eintauchen kann. Mängel werden mit
   Grund und Lage aufgeführt. Das Protokoll zur Inbetriebnahme ablegen.

9. **Sichtprüfung in der Live-Ansicht**
   ```bash
   python -m verladearm_vision.viewer --opcua --config vision/config/anlagen/lich_station3.yaml
   ```
   Rohrführung, Sperrbereiche und Servowerte mit der realen Anlage vergleichen.

10. **Autostart einrichten**: `sudo deploy/install.sh vision/config/anlagen/<anlage>.yaml`,
    siehe [Betrieb](betrieb.md).

11. **Abgleich mit der SPS**: Maße, Nullstellungen, Drehrichtungen und Grenzen im SPS-Programm
    müssen denselben Werten entsprechen. Anlagendatei per Pull Request einchecken.

## Grundsatz

Die Prüfung ersetzt keine Sicherheitsfunktion. Verfahrbereiche, Endlagen und Schutzbereiche
werden zusätzlich in der SPS bzw. Sicherheits-SPS überwacht (ADR 0001).
