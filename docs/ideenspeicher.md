# Ideenspeicher: Open-Source-Bausteine und zurückgestellte Erweiterungen

Stand 01.10.2026. Nichts davon ist beschlossen – Optionen für später, mit Einschätzung.

## Vergleichbare Projekte

Ein Open-Source-Projekt für **automatische Verladearme mit Domerkennung** gibt es nach Recherche
nicht; in diesem Bereich gibt es nur kommerzielle Lösungen (z. B. LuminWave „Filling Port
Position“) und Patente.

Am nächsten kommen **Laderoboter für Elektroautos** (Buchse finden → hinfahren → Stecker
einführen, also dieselbe Kette wie Dom finden → anfahren → eintauchen), meist Studien- oder
Forschungsprojekte:

- [EV_ChargingRobot](https://github.com/SpencerBall99/EV_ChargingRobot) – findet den Ladeanschluss
  und steckt selbst ein
- [Automatic-charging-system-for-EV-using-Robotic-Arm](https://github.com/PARTHIPRAJ/Automatic-charging-system-for-EV-using-Robotic-Arm)
  – Position per Kamera und Markern (OpenCV), vergleichbar mit unserer Markierungsscheibe
- Forschung mit 3D-Punktwolken bzw. Kamera + LiDAR:
  [Autonomous positioning and compliant plugging](https://www.sciencedirect.com/science/article/abs/pii/S0166361525000521),
  [Robotic Plug-in Charging](https://www.researchgate.net/publication/338439251_Robotic_Plug-in_Combined_Charging_System_with_Improved_Robustness)

## Open-Source-Bausteine mit denselben Techniken

| Aufgabe | Heute im Projekt | Etablierte Alternative |
|---|---|---|
| Tankoberfläche (RANSAC), Punktwolke filtern | eigener Code (NumPy/SciPy) | **Open3D** (Python), **PCL** (C++) |
| Kollisionsfreie Bahn | eigenes RRT-Connect | **OMPL** (Ursprung von RRT-Connect), genutzt von **MoveIt 2** / ROS 2 |
| Kollisionsprüfung | Quader/Zylinder, Rohr als Linie | **FCL** (beliebige Formen, Netze) |
| Höhenkarte der Hindernisse | eigenes Raster | **OctoMap** (3D-Belegungskarte) |
| Kinematik | eigene Vorwärts-/Rückwärtsrechnung | **Pinocchio**, **ikpy**, Robotics Toolbox (P. Corke) |
| Hand-Auge-Kalibrierung | eigener Ausgleich über Messpaare | **OpenCV** `calibrateHandEye`, **easy_handeye** (ROS) |
| Kamera | `sick_visionary_python_base` | `sick_visionary_ros` (SICK) |
| SPS-Anbindung | `asyncua` (OPC UA) | `open62541` (C) |
| Simulation | eigene Punktwolken-Simulation | **Gazebo**, PyBullet, Isaac Sim |
| 3D-Erkennung per KI | – (geometrisch) | [OpenPCDet](https://github.com/open-mmlab/OpenPCDet) |

**Einschätzung:**

- **Kein Umstieg auf ROS 2 / MoveIt 2.** Drei Achsen, die SPS fährt, der PC liefert nur
  Stützpunkte: Der Installations- und Pflegeaufwand auf dem Industrie-PC stünde in keinem
  Verhältnis zum Nutzen. Die eigenen Verfahren entsprechen dem Stand der Technik.
- **Sinnvolle Ergänzungen, sobald echte Daten da sind:**
  - **Open3D** zum Ansehen und Auswerten echter Aufnahmen am PC.
  - **OpenCV `calibrateHandEye`** als unabhängige Gegenprobe zur eigenen Kalibrierung.
- **KI-Erkennung** erst, wenn die geometrische Erkennung an vielen Dombauarten scheitert – dafür
  wären Hunderte beschriftete echte Aufnahmen nötig.

## Zurückgestellt: Füllstand messen und Arm nachziehen

Beschluss 01.10.2026: hinten angestellt. Idee: Auslass bleibt während der Befüllung knapp unter
der Flüssigkeitsoberfläche (Unterspiegelbefüllung, weniger Schaum und Aufladung – wichtig für
schäumende Produkte).

- **Überfüllsicherung bleibt unabhängig** (zugelassener Grenzwertgeber bzw. Fahrzeugstecker,
  wirkt direkt auf das Füllventil) – nie über Kamera/PC.
- **Füllstand:** Radarsensor am Auslasskopf (Ex-Ausführung, z. B. VEGAPULS, E+H Micropilot), Blick
  neben dem Rohr in den Dom. Die 3D-Kamera ist dafür ungeeignet (Rohr verdeckt die Öffnung,
  Flüssigkeit spiegelt). Durchflusszähler + Tanktabelle nur als Schätzung.
- **Nachziehen:** Der PC liefert nach dem Eintauchen eine Nachzieh-Tabelle (Stützpunkte auf der
  senkrechten Linie, z. B. alle 50 mm, mit Höhe des Auslassendes). Die SPS fährt allein danach,
  sobald der Radar zu tiefes Eintauchen meldet – der PC muss während der Befüllung nicht laufen.
- **Folgen:** Schnittstelle Version 3 (Höhe je Stützpunkt), Produktparameter (Eintauchtiefe unter
  der Oberfläche, Mindestabstand zum Boden), SPS-Umfang bei Peter (Füllventil, Radar,
  Nachziehregelung, Überfüllsicherung), Simulation mit steigendem Füllstand.
- **Offene Fragen:** Unterspiegelbefüllung gewünscht/vorgeschrieben? Vorhandene Füllsteuerung?
  Füllgeschwindigkeit (mm Spiegelanstieg pro Minute)?
