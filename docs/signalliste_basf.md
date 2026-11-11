# Signalliste BASF (Steuerung/PLS) ↔ HETA-SPS – Entwurf

Stand 11.11.2026 · **Entwurf zur Abstimmung mit BASF** (S. Kaestel, D. Bettag), Termin
vorgeschlagen Di 24.11.2026. Grundlage: Aufgabenteilung vom 09.11. (Menge, Pumpe und Füllende
steuert die Leitstelle, Absperrklappe gehört zum Arm) und Mail BASF vom 11.11. (Signale über
freie E/A im IVK, Pumpenabschaltung durch die Überfüllsicherung übernimmt BASF).

**Vorschlag Ausführung:** festverdrahtet, 24 V DC, Übergabe über Koppelrelais mit
potentialfreien Kontakten (galvanische Trennung, Klemmleiste im HETA-Schaltschrank).
Sicherheitsrelevante Signale **im Ruhestromprinzip** (1 = in Ordnung / freigegeben), damit
Drahtbruch oder Spannungsausfall sicher abschaltet. Alternativ für die Datenwerte (Produkt,
Kammern, Störcode) eine Busverbindung bzw. OPC UA – mit BASF klären.

## BASF → HETA (Eingänge der HETA-SPS)

| Nr. | Signal | Art | Bedeutung | HETA-SPS (`GVL_IO`) | Offen |
|---|---|---|---|---|---|
| E1 | Verladung freigegeben | DI | Auftrag liegt vor, Start vor Ort möglich | `xPlsFreigabe` | |
| E2 | Produkt | 4 × DI binär (0–15) oder Bus | bestimmt die Eintauchtiefe | `iPlsProdukt` | Anzahl Produkte/Eintauchtiefen? reicht eine Tiefe für alle? |
| E3 | Kammern / Füllschritte | 2 × DI binär (1–3) oder Bus | Anzahl Kammern; Dom je Schritt von vorn gezählt | `iPlsSchritte`, `aPlsDome` | Kammerwahl im PLS oder vor Ort? |
| E4 | Pumpe läuft | DI | Rückmeldung der Pumpe; Klappe schließt erst bei „Pumpe aus“ + Auslaufzeit | `xPlsPumpeLaeuft` | Auslaufzeit der Pumpe? |
| E5 | Befüllung Ende | DI | Menge des aktuellen Füllschritts erreicht oder vorzeitig beendet, Pumpe aus | `xPlsBefuellEnde` | |
| E6 | Verdrängen/Spülen beendet | DI | Klappe bleibt bis dahin offen, Arm bleibt im Tank | – (neu) | Ablauf erklärt BASF im Termin |
| E7 | Überfüllsicherung in Ordnung | DI, Ruhestrom | 0 = ausgelöst (Sensor LBFS schaltet die Pumpe über die BASF-Steuerung ab) | `xUeberfuellAus` (invertiert) | Signal von BASF oder zweiter Kontakt/Koppelrelais am Sensor? |
| E8 | Fahrzeug geerdet | DI | Erdungsüberwachung; Start nur bei Erdung | – (neu) | vorhanden? |
| E9 | Klapptreppe in Ruhelage | DI | Start und Bewegung nur bei Ruhelage | `xKlapptreppeRuhe` | Signal aus der vorhandenen Treppensteuerung? |
| E10 | Lichtschranke Stellplatz belegt | DI | Fahrzeug steht | `xLichtschranke` | vorhanden oder neu (HETA)? |
| E11 | Not-Halt / Sicherheitskreis BASF in Ordnung | DI, Ruhestrom, ggf. 2-kanalig | Not-Halt der Verladestelle stoppt auch den Arm | Sicherheitssteuerung | gemeinsamer Not-Halt-Kreis gewünscht? |

## HETA → BASF (Ausgänge der HETA-SPS)

| Nr. | Signal | Art | Bedeutung | HETA-SPS (`GVL_IO`) | Offen |
|---|---|---|---|---|---|
| A1 | Freigabe Befüllung (Arm bereit) | DO, Ruhestrom | 1 = Arm im Tank, Klappe offen, Pumpe darf laufen; 0 = Pumpe aus (Füllende, Störung, Maximalhöhe, Not-Halt, Drahtbruch) | `xArmBereit` und `NOT xBefuellStoppen` | ein Signal statt zwei (fehlersicher)? |
| A2 | Befüllung stoppen | DO | Störung bzw. Maximalhöhe erreicht (Grund für das Abschalten, Meldung im PLS) | `xBefuellStoppen` | entfällt, wenn A1 Ruhestrom und A5 Störung |
| A3 | Arm in Parkstellung | DO | Fahrzeug darf wegfahren, Treppe darf ausfahren | `xMeldeGruen` | |
| A4 | Automatik läuft | DO | Arm bewegt sich bzw. ist im Tank | `xMeldeGelb` | |
| A5 | Sammelstörung | DO | Störung am Arm, Details vor Ort bzw. über Störcode | `xMeldeRot` | Störcode über Bus gewünscht? |
| A6 | Klapptreppe verriegeln | DO | Treppe darf nicht ausfahren, solange der Arm nicht in Park ist | – (neu) | Eingriff in die Treppensteuerung möglich? |
| A7 | Not-Halt Arm | potentialfreier Kontakt, 2-kanalig | Not-Halt am Arm schaltet die Pumpe festverdrahtet ab (über TwinSAFE) | Sicherheitssteuerung | Einbindung in den BASF-Pumpenkreis |

## Ablauf (Signale)

1. BASF: **E1** Freigabe, **E2** Produkt, **E3** Kammern → Bediener drückt „Beladen starten“.
2. HETA: Arm fährt ein, Klappe auf → **A1** Freigabe Befüllung = 1.
3. BASF: Pumpe an (**E4** = 1). HETA zieht nach.
4. BASF: Menge erreicht → Pumpe aus, **E5** Befüllung Ende. HETA: **A1** = 0.
5. BASF: Verdrängen/Spülen (Klappe offen) → **E6** beendet. HETA: Klappe zu, Abtropfen.
6. Nächste Kammer (ab 2.) oder Rückfahrt → **A3** Arm in Parkstellung.

Abbruch durch HETA (Störung, Maximalhöhe): **A1** = 0 (+ **A2**/**A5**) → BASF schaltet die Pumpe
ab → HETA wartet auf **E4** = 0 und Auslaufzeit → Klappe zu. Überfüllsicherung: BASF schaltet die
Pumpe direkt ab, **E7** = 0 → HETA-SPS geht in Störung.

## Fragen an BASF (Termin)

1. Festverdrahtet über das IVK oder Busverbindung/OPC UA zum PLS? Wie viele freie E/A?
2. Produkt und Kammern aus dem PLS oder Auswahl vor Ort?
3. Erdungsüberwachung, Klapptreppe, Lichtschranke: vorhandene Signale nutzbar?
4. Gemeinsamer Not-Halt-Kreis Verladestelle ↔ Arm?
5. Ablauf und Dauer Verdrängen/Spülen, Auslaufzeit der Pumpe.
6. Tanktiefe bzw. Fahrzeugtyp aus dem PLS (für die Eintauchtiefe)?
