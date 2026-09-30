# Sensor SICK Visionary-T Mini CX

3D-Time-of-Flight-Kamera (Station: **V3S105-1AAAAAD**, Frontscheibe Glas, Art.-Nr. 1132065;
Prüfstand auch V3S105-1AAAAAA mit PMMA-Scheibe, Art.-Nr. 1112649), 512 × 424 Pixel, ca. 70° × 60°, bis 30 Bilder/s,
IP65, 24 V DC, Gigabit Ethernet. Treiber: `vision/src/verladearm_vision/acquisition/sick_visionary.py`
auf Basis der offiziellen SICK-Bibliothek
[sick_visionary_python_base](https://github.com/SICKAG/sick_visionary_python_base)
(Firmware laut SICK getestet mit 2.1.0 und 4.0.1).

## Anschluss

| Anschluss | Gegenstück |
|---|---|
| Ethernet M12, 8-polig, X-kodiert | Kabel M12 X-kodiert → RJ45, Cat6a, passende Länge zur Traverse |
| Versorgung / E/A (Stecker laut Datenblatt) | 24 V DC, typ. 12 W, Spitzenstrom 2 A |

Der PC braucht einen Gigabit-Anschluss zum Sensor. Empfehlung: eigener Netzwerkanschluss nur für
den Sensor (zweiter LAN-Port oder USB-LAN-Adapter), getrennt vom SPS-Netz.

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
  (je näher, desto dichter die Punkte: bei 3,5 m ca. 1 cm Punktabstand).
- Blickfeld bei 3,5 m ca. 4,9 m × 4,0 m; der Arbeitsraum `detection.roi_min/roi_max`
  muss die Fahrbahn ausschließen.
- Direkte Sonneneinstrahlung und Spiegelungen (blanker Edelstahl, Pfützen) am Mock-up testen.
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
