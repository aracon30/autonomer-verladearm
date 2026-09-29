# Schnittstelle Vision-PC ↔ SPS

**Version:** 2 (`InterfaceVersion = 2`)
**Protokoll:** OPC UA. Die SPS ist Server (z. B. S7-1500, integrierter OPC-UA-Server), der Vision-PC ist Client.
**Datenbaustein:** `DB_Vision` (Quelle: `plc/DB_Vision.db`)

## Aufgabenteilung

| Ebene | Aufgabe |
|---|---|
| **Vision-PC** (nicht sicherheitsgerichtet) | Dom messen, Kinematik, Rückwärtsrechnung, Kollisionsprüfung gegen Sperrbereiche, Bahn als **Stützpunkte in Servo-Grad**, Nachmessen Auslass ↔ Dom |
| **SPS** | Ablauf, **Plausibilitätsprüfung jeder Vorgabe**, Referenzfahrt, Positionieren je Achse mit Technologieobjekten (Geschwindigkeit, Beschleunigung, Verzögerung, **Ruck** → sanftes Anfahren und Bremsen), synchrones Anfahren der Stützpunkte, Bremsen, Füllstand, Überfüllsicherung, PLS |
| **Servoregler** | Strom-, Drehzahl- und Lageregelung (PROFINET, deterministisch) |
| **Sicherheits-SPS** | Not-Halt, Schutzbereich, sicheres Abschalten (STO/SS1) |

Der PC regelt nichts in Echtzeit. Er liefert Vorgaben, die SPS entscheidet und fährt.
Begründung: [ADR 0002](adr/0002-gelenkwinkel-vom-pc.md).

## Variablen

### SPS → PC

| Name | Typ | Bedeutung |
|---|---|---|
| HeartbeatPLC | Int | Zählt alle ~100 ms hoch |
| Trigger | Bool | Auftrag starten |
| **Job** | Int | 1 = Dom messen, Bahn planen · 2 = Auslass nachmessen, Bahn korrigieren · 3 = Rückfahrt planen · 0 = nur messen |
| ProductId | Int | Produkt der aktuellen Verladung (Eintauchtiefe) |
| Reset | Bool | Fehler quittieren |
| **ActualJ1 / J2 / J3** | Real | Istwinkel der Servoachsen [Servo-Grad] |
| **AxesHomed** | Bool | Alle Achsen referenziert, Istwinkel gültig |
| **ArmState** | Int | 0 Park · 1 fährt · 2 über Dom · 3 eingetaucht · 9 Störung (Anzeige, Protokoll) |

### PC → SPS

| Name | Typ | Bedeutung |
|---|---|---|
| HeartbeatPC | Int | Zählt je Zyklus (~50 ms) hoch |
| Ready | Bool | Vision-Dienst bereit, SPS-Heartbeat OK |
| Busy | Bool | Auftrag läuft |
| Done | Bool | Ergebnis liegt vor (gültig oder Fehler) |
| Error | Bool | Auftrag fehlgeschlagen, siehe ErrorCode |
| ErrorCode | Int | siehe Tabelle unten |
| ResultId | DInt | Laufende Nummer des Ergebnisses |
| TargetX / TargetY / TargetZ | Real | Oberkante Domöffnung (Mitte), Armbasis [mm]; bei Job 2 aus Job 1 |
| NormalX / NormalY / NormalZ | Real | Normale der Öffnung (Einheitsvektor, Armbasis) |
| DiameterMm | Real | Erkannter Durchmesser [mm] |
| Confidence | Real | Qualität der Erkennung 0…1 |
| **WaypointCount** | Int | Anzahl gültiger Stützpunkte (0…16) |
| **WaypointsJ1 / J2 / J3** | Array[1..16] of Real | Zielwinkel je Stützpunkt [Servo-Grad] |
| **ApproachIndex** | Int | Nummer des Stützpunkts „über dem Dom“ (1-basiert, 0 = keiner). Danach folgt das Eintauchen |
| **CorrectionX / CorrectionY** | Real | Job 2: gemessene Abweichung Soll − Ist des Auslasses über dem Dom [mm] |
| InterfaceVersion | Int | Muss der SPS-seitig erwarteten Version entsprechen (2) |

## Aufträge

| Job | PC tut | Stützpunkte | ApproachIndex |
|---|---|---|---|
| 1 | Dom messen, Bahn ab **Istlage** planen | Anfahrt (Gelenkraum, synchron) + Eintauchen (senkrecht) | letzter Anfahrpunkt |
| 2 | Auslass über dem Dom nachmessen (Markierungsscheibe), Modellabweichung ausgleichen | korrigierter Anfahrpunkt + Eintauchen | 1 |
| 3 | Rückfahrt ab Istlage planen | senkrecht heraus + synchron in die Parkstellung | 0 |

Die Anfahrt zwischen zwei Stützpunkten ist als **synchrone Gelenkbewegung** geplant: Alle Achsen
starten und erreichen den Stützpunkt gleichzeitig. Nur so stimmt die gefahrene Bahn mit der
kollisionsgeprüften Bahn überein. Stützpunkte nach `ApproachIndex` mit reduzierter Dynamik fahren.

## Ablauf einer Verladung (SPS)

1. Start durch Fahrer, Freigabe PLS, Sicherheitsbedingungen erfüllt, `AxesHomed = TRUE`.
2. **Job 1** → Stützpunkte prüfen (Achsgrenzen, Sprünge) → bis `ApproachIndex` fahren.
3. Beruhigungszeit, der Auslass pendelt frei (J4).
4. **Job 2** → Korrektur prüfen (Betrag < Grenzwert, sonst Job 2 wiederholen oder Abbruch) →
   Stützpunkt 1 anfahren → restliche Stützpunkte langsam = Eintauchen.
5. Befüllung mit Füllstandsregelung und Überfüllsicherung, **ohne PC**.
6. **Job 3** → Stützpunkte fahren → Parkstellung.

Bei Fehler, fehlendem Ergebnis oder Heartbeat-Ausfall: Bewegung stoppen, sicherer Zustand.

## Handshake

1. SPS setzt `Job`, `ProductId`, Istwerte und dann `Trigger` (nur wenn `Ready = TRUE`).
2. PC setzt `Busy`, löscht `Error`.
3. PC schreibt alle Ergebniswerte und `ResultId` in **einem** Aufruf, danach `Done` (bei Fehler zusätzlich `Error` + `ErrorCode`), löscht `Busy`.
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
| 30 | Ziel außerhalb der Reichweite / Achsgrenzen |
| 31 | Bahn kollidiert mit Sperrbereich |
| 32 | Achsen nicht referenziert oder Istwinkel unplausibel |
| 33 | Auslass bzw. Markierungsscheibe beim Nachmessen nicht erkannt |
| 34 | Job 2 ohne vorheriges Ergebnis aus Job 1 |
| 90 | Interner Fehler Vision-Dienst |
| 91 | Unbekannter Auftrag (Job) |

## Koordinatensystem

Armbasis-Koordinaten in mm: Ursprung auf der Drehachse J1 am Haltepunkt, x nach vorne,
y nach links, z nach oben (siehe `docs/kinematik.md`). Servowinkel so, wie der Antrieb sie
anzeigt; Umrechnung über Nullstellung und Drehrichtung aus der Anlagendatei. Das
Kalibrierverfahren wird in `docs/kalibrierung.md` festgelegt (offen).

## Änderungen

Jede Änderung an dieser Schnittstelle erhöht `InterfaceVersion` und erfolgt per Pull Request
mit Freigabe durch den SPS-Programmierer.

| Version | Änderung |
|---|---|
| 1 | Zielkoordinate, Handshake, Heartbeat |
| 2 | Aufträge (Job), Istwinkel und Referenzierung von der SPS, Stützpunkte in Servo-Grad, Nachmessen mit Korrektur, Fehlercodes 30–34, 91 |
