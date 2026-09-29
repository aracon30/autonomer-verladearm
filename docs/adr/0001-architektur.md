# ADR 0001: Aufgabenteilung Vision-PC und SPS

**Status:** angenommen · **Datum:** 2026-09-29

## Kontext
Der autonome Verladearm benötigt 3D-Erkennung der Domöffnung. Punktwolkenverarbeitung ist auf
einer SPS nicht sinnvoll umsetzbar.

## Entscheidung
- Ein Edge-PC übernimmt Sensorik und Erkennung und liefert nur die Zielkoordinate.
- Die SPS steuert Ablauf und Bewegung, führt Plausibilitätsprüfungen durch und bindet das PLS an.
- Füllstand und Überfüllsicherung werden direkt an der SPS angeschlossen, nicht am PC.
- Sicherheitsfunktionen ausschließlich über zertifizierte Komponenten und Sicherheits-SPS.
- Kommunikation per OPC UA, SPS als Server.

## Konsequenzen
Ein Ausfall oder Fehlverhalten des PCs kann keinen unsicheren Zustand erzeugen. Die Software auf
dem PC ist nicht sicherheitsgerichtet und kann agil weiterentwickelt werden.
