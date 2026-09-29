# ADR 0002: Gelenkwinkel vom Vision-PC, Bewegung durch die SPS

**Status:** angenommen · **Datum:** 2026-09-29 · Ergänzt [ADR 0001](0001-architektur.md)

## Kontext
- Die Kinematik des Verladearms ist nicht standardmäßig (3° Gefälle, Winkelversatz, frei
  pendelnder Auslass J4). Rückwärtsrechnung und Kollisionsprüfung liegen in Python fertig vor.
- Ein Winkelfehler von 0,1° an einem Gelenk verschiebt den Auslass um 4–5 mm; gefordert sind
  ±20 mm (N-01). Getriebespiel und Durchbiegung des langen Auslegers liegen in dieser Größe.
- Die Servos haben keine Winkelgeber am Gelenk, nur Endlagenschalter (Stand der Klärung).

## Entscheidung
- Der PC liefert neben der Zielkoordinate **Stützpunkte als Servo-Sollwinkel** (`InterfaceVersion 2`).
- Die **SPS prüft** jede Vorgabe und **fährt** mit Technologieobjekten (Rampen, Ruckbegrenzung,
  synchrone Stützpunkte). Echtzeit-Regelung und Sicherheit bleiben in SPS, Antrieb und
  Sicherheits-SPS.
- **Nachmessen vor dem Eintauchen (Job 2):** Der Sensor misst Auslass (Markierungsscheibe) und Dom
  im selben Bild und korrigiert die Restbahn. Getriebespiel, Durchbiegung und Kalibrierfehler
  werden so ausgeglichen.

## Konsequenzen
- Maße und Achsparameter werden nur an einer Stelle gepflegt (Anlagendatei).
- Die SPS braucht Istwinkel (Referenzfahrt, Motorgeber oder Gelenkgeber) und meldet sie an den PC.
- Ein Ausfall des PCs führt weiterhin zum sicheren Stopp (Heartbeat, Zeitüberwachung).
- Die Markierungsscheibe am Auslass ist Teil der Mechanik.
