# Schnittstelle Vision-PC ↔ SPS

**Version:** 1 (`InterfaceVersion = 1`)
**Protokoll:** OPC UA. Die SPS ist Server (z. B. S7-1500, integrierter OPC-UA-Server), der Vision-PC ist Client.
**Datenbaustein:** `DB_Vision` (Quelle: `plc/DB_Vision.db`)

## Grundsatz

Der Vision-PC liefert ausschließlich eine **Zielkoordinate**. Ablaufsteuerung, Bewegung, Verriegelungen,
Füllstand, Überfüllsicherung und alle Sicherheitsfunktionen liegen in der SPS bzw. Sicherheits-SPS.
Die SPS prüft jedes Ergebnis selbst auf Plausibilität (Arbeitsraumgrenzen, Mindest-Confidence,
produktspezifische Grenzen).

## Variablen

| Name | Typ | Richtung | Bedeutung |
|---|---|---|---|
| HeartbeatPLC | Int | SPS → PC | Zählt alle ~100 ms hoch |
| Trigger | Bool | SPS → PC | Messung anfordern |
| ProductId | Int | SPS → PC | Produkt der aktuellen Verladung |
| Reset | Bool | SPS → PC | Fehler quittieren |
| HeartbeatPC | Int | PC → SPS | Zählt je Zyklus (~50 ms) hoch |
| Ready | Bool | PC → SPS | Vision-Dienst bereit, SPS-Heartbeat OK |
| Busy | Bool | PC → SPS | Messung läuft |
| Done | Bool | PC → SPS | Ergebnis liegt vor (gültig oder Fehler) |
| Error | Bool | PC → SPS | Messung fehlgeschlagen, siehe ErrorCode |
| ErrorCode | Int | PC → SPS | siehe Tabelle unten |
| ResultId | DInt | PC → SPS | Laufende Nummer des Ergebnisses |
| TargetX / TargetY / TargetZ | Real | PC → SPS | Mittelpunkt Domöffnung, Armbasis-Koordinaten [mm] |
| NormalX / NormalY / NormalZ | Real | PC → SPS | Normale der Öffnung (Einheitsvektor, Armbasis) |
| DiameterMm | Real | PC → SPS | Erkannter Durchmesser [mm] |
| Confidence | Real | PC → SPS | Qualität der Erkennung 0…1 |
| InterfaceVersion | Int | PC → SPS | Muss der SPS-seitig erwarteten Version entsprechen |

## Handshake

1. SPS setzt `Trigger` (nur wenn `Ready = TRUE`).
2. PC setzt `Busy`, löscht `Error`.
3. PC schreibt Ergebnis, erhöht `ResultId`, setzt `Done` (bei Fehler zusätzlich `Error` + `ErrorCode`), löscht `Busy`.
4. SPS übernimmt die Werte und löscht `Trigger`.
5. PC löscht `Done`.

Zeitüberwachung in der SPS: `Done` muss innerhalb von **5 s** nach `Trigger` kommen, sonst Abbruch.

## Heartbeat

Beide Seiten prüfen, ob sich der Heartbeat der Gegenseite ändert. Ausfall > **1 s**:
- PC setzt `Ready = FALSE` und nimmt keine Aufträge an.
- SPS stoppt die automatische Bewegung und geht in den sicheren Zustand.

## Fehlercodes

| Code | Bedeutung |
|---|---|
| 0 | kein Fehler |
| 11 | Zu wenige Messpunkte im Arbeitsraum (Sensor verschmutzt/verdeckt?) |
| 12 | Tankoberfläche nicht erkannt |
| 20 | Keine Domöffnung gefunden (Deckel geschlossen?) |
| 21 | Mehrere Domöffnungen gefunden |
| 90 | Interner Fehler Vision-Dienst |

## Koordinatensystem

Armbasis-Koordinaten in mm; Ursprung, Achsrichtungen und Kalibrierverfahren werden in
`docs/kalibrierung.md` festgelegt (offen).

## Änderungen

Jede Änderung an dieser Schnittstelle erhöht `InterfaceVersion` und erfolgt per Pull Request
mit Freigabe durch den SPS-Programmierer.
