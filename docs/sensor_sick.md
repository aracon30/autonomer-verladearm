# Sensor SICK Visionary-T Mini CX

3D-Time-of-Flight-Kamera (Station: **V3S105-1AAAAAD**, Frontscheibe Glas, Art.-Nr. 1132065;
Prüfstand auch V3S105-1AAAAAA mit PMMA-Scheibe, Art.-Nr. 1112649), 512 × 424 Pixel, ca. 70° × 60°, bis 30 Bilder/s,
IP65/67/69, 24 V DC, Gigabit Ethernet. Treiber: `vision/src/verladearm_vision/acquisition/sick_visionary.py`
auf Basis der offiziellen SICK-Bibliothek
[sick_visionary_python_base](https://github.com/SICKAG/sick_visionary_python_base)
(Firmware laut SICK getestet mit 2.1.0 und 4.0.1).

## Anschluss

| Anschluss | Gegenstück |
|---|---|
| Ethernet M12, 8-polig, X-kodiert | Kabel M12 X-kodiert → RJ45, Cat6a, passende Länge zur Traverse |
| Versorgung / E/A: M12, 8-polig, A-kodiert (Stecker am Gerät) | Leitung M12 A-kodiert Buchse, 8-polig; 24 V DC (−30 % … +25 %), typ. 12 W, Spitzenstrom 2 A |

Der PC braucht einen Gigabit-Anschluss zum Sensor. Empfehlung: eigener Netzwerkanschluss nur für
den Sensor (zweiter LAN-Port oder USB-LAN-Adapter), getrennt vom SPS-Netz.

## Kenndaten V3S105-1AAAAAD (Datenblatt)

| Größe | Wert | Bedeutung für uns |
|---|---|---|
| Arbeitsbereich | bis 16 m (sicher bis 9 m) | Montage 2,5–4 m über den Domen unkritisch |
| Blickfeld | 70° × 60°, 0,14°/Pixel | bei 3 m ca. 4,2 × 3,5 m, bei 4 m ca. 5,6 × 4,6 m; Punktabstand bei 3 m ca. 7 mm |
| Genauigkeit (90 % Remission) | ±3 mm @ 2 m, ±7 mm @ 4 m | weit unter der Vorgabe ±20 mm |
| Genauigkeit (10 % Remission) | ±10 mm @ 4 m | dunkle/matte Dome: Median über `frames` hilft |
| Wiederholgenauigkeit | 1 / 2 mm @ 2 / 4 m (90 %), 4 / 12 mm (10 %) | Simulation rechnet mit 3 mm Rauschen (konservativ) |
| Temperaturdrift | bis ±10 mm über den Temperaturbereich | Kalibrierung bei typischer Betriebstemperatur, Nachmessen per Job 2 fängt Drift ab |
| Umgebungslicht | ≤ 50 klx bei 2 m | direkte Sonne ≈ 100 klx: **Sonnenschutzdach nötig** |
| Betriebstemperatur | −10 … +50 °C (ab −20 °C nach 45 min Aufwärmen bei > 25 Bilder/s); Gehäuse max. 65 °C | Winter: Sensor dauernd eingeschaltet lassen; Sommer: Schatten, ggf. Kühlkörper (Zubehör) |
| Schutzart | IP65 / IP67 / IP69 | Außenmontage möglich |
| Startzeit | ca. 20 s (unter 0 °C länger) | Dienst verbindet sich selbst neu, Ablauf wartet |
| Laser | Klasse 1, 855 nm | keine Schutzmaßnahmen nötig |
| Befestigung | 4 × M5 (7,5 mm tief) + 2 × Passung Ø 5 H7 | Halter mit Passstiften, damit die Lage reproduzierbar bleibt |
| Abmessungen / Gewicht | 80 × 70 × 77 mm, 520 g | |

## Inbetriebnahme

1. **Netzwerk:** Sensor ab Werk `192.168.1.10`. PC-Anschluss z. B. auf `192.168.1.2/24` stellen.
   IP-Adresse, Firmware und Passwörter mit SICK SOPAS ET prüfen bzw. ändern.
2. **Software:** `pip install -e ".[sick]"`
3. **Konfiguration** (Anlagendatei):
   ```yaml
   source:
     type: sick
     ip: 192.168.1.10
     frames: 3            # Bilder je Messung, pixelweiser Median gegen Rauschen
     password: CUST_SERV  # Service-Passwort; nach Änderung in SOPAS hier anpassen
   ```
   Das Passwort gehört nicht ins Repository, wenn es geändert wurde (Anlagendatei lokal halten).
4. **Test ohne SPS:** `python -m verladearm_vision.viewer --config <anlage>.yaml` und im Browser
   die Punktwolke prüfen.

## Montage

- Senkrecht nach unten über dem Bereich der Domöffnungen, so tief wie möglich
  (je näher, desto dichter die Punkte: bei 3 m ca. 7 mm, bei 4 m ca. 1 cm Punktabstand).
- Blickfeld bei 3,5 m ca. 4,9 m × 4,0 m; der Arbeitsraum `detection.roi_min/roi_max`
  muss die Fahrbahn ausschließen.
- Sonnenschutzdach über dem Sensor (Fremdlicht max. 50 klx, Gehäuse max. 65 °C); Spiegelungen
  (blanker Edelstahl, Pfützen) am Mock-up testen.
- Im Winter nicht abschalten: Betrieb ab −10 °C, bis −20 °C nur nach Aufwärmen im Dauerbetrieb.
- Stabile Befestigung: jede Bewegung des Sensors verfälscht die Kalibrierung.

## Arbeitsweise des Treibers

- Kamera im Snapshot-Betrieb (FrontendMode `Stopped`): Jede Messung löst `frames` Einzelbilder aus,
  so kommt nie ein veraltetes Bild aus dem Netzwerkpuffer. Beim Beenden wird wieder auf
  `Continuous` geschaltet.
- Ungültige Pixel (Zustandswert ≠ 0) werden verworfen, danach Median über die Bilder und
  Umrechnung in Punkte mit den Kameraparametern aus dem Datenstrom (gleiche Formel wie SICK,
  per Test gegen die Bibliothek abgesichert). Die in SOPAS eingestellte Montage wird nicht
  verwendet, die Lage zum Arm bestimmt allein die Hand-Auge-Kalibrierung.
- Bei Verbindungsabbruch einmal Neuverbindung, sonst Fehler 90 an die SPS.
