# Hand-Auge-Kalibrierung (Sensor → Armbasis)

Bestimmt `calibration.matrix` in der Anlagendatei: die Lage des Sensors relativ zur Armbasis
(Ursprung Achse J1, x vorne, y links, z oben). Nötig bei der Inbetriebnahme und immer, wenn der
Sensor versetzt, getauscht oder die Traverse verändert wurde.

## Prinzip

Der Sensor ist fest über der Station montiert („eye-to-hand“). Der Arm fährt die
**Markierungsscheibe am Auslass** (oder den Referenzflansch, siehe `outlet` in der
Anlagendatei) an 10 Stellen im Arbeitsraum. Je Stellung gibt es zwei Angaben
für denselben Punkt:

- **Armbasis:** Auslassende aus den Servo-Istwinkeln (Vorwärtsrechnung, `docs/kinematik.md`)
- **Sensor:** Mittelpunkt der Markierungsscheibe in der Punktwolke

Aus den Punktpaaren folgt die beste Drehung und Verschiebung (Kabsch-Verfahren). Die
Restfehler zeigen, wie gut Kinematik und Messung zusammenpassen.

## Voraussetzungen

- Anlagendatei mit Maßen, Servo-Nullstellungen und Drehrichtungen (docs/inbetriebnahme.md)
- **Grobe Anfangsschätzung** in `calibration.matrix`: Sensorlage mit Maßband/Laser gemessen,
  auf ca. 10 cm und 5° genau. Die Scheibe wird damit gesucht.
- Station **leer** (kein Tankwagen), Markierungsscheibe am Auslass montiert
- Achsen referenziert, SPS im Handbetrieb

## Ablauf

```bash
python -m verladearm_vision.calibrate --config vision/config/anlagen/<anlage>.yaml --from-plc
```

1. Das Werkzeug schlägt 10 Stellungen vor (Ecken und Mitte des Arbeitsraums, in zwei Höhen).
2. Arm im Handbetrieb in die Stellung fahren, **Auslass auspendeln lassen**, Enter.
   Die Istwinkel liest das Werkzeug aus dem DB_Vision (`--from-plc`, nur lesend) oder fragt sie ab.
3. Nach allen Stellungen: Matrix, Restfehler je Stellung und Hinweise werden ausgegeben und als
   Protokoll gespeichert (`kalibrierung_<datum>.md`).
4. Matrix in die Anlagendatei übernehmen, Dienste neu starten, Inbetriebnahmeprüfung wiederholen.

Probelauf ohne Hardware: `--sim` (Sensor absichtlich 4 cm und 1,5° neben der Schätzung).

## Bewertung

| Restfehler (Mittel) | Bewertung |
|---|---|
| < 5 mm | gut |
| 5–10 mm | brauchbar; Nachmessen in Job 2 gleicht den Rest aus |
| > 10 mm | Maße, Nullstellungen, Drehrichtungen oder Pendeln prüfen |

Einzelne Ausreißer deuten auf eine nicht ausgependelte Scheibe oder Verdeckung hin: Stellung
wiederholen. Ein großer gleichmäßiger Restfehler deutet auf falsche Armmaße hin.

## Hinweise

- Die Kalibrierung gleicht auch konstante Fehler der Kinematik teilweise aus. Getriebespiel und
  Durchbiegung wechseln aber mit der Stellung; dafür gibt es das Nachmessen vor dem Eintauchen.
- Nach dem Eintragen: Probeverladung am Mock-up, Aufzeichnung prüfen (`tools/auswertung.py`).
