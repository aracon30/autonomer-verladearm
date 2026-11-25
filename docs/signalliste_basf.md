# Signalliste BASF (Steuerung/PLS) ↔ HETA-SPS – Entwurf

Stand 24.11.2026 · **Version 2, Entwurf zur Abstimmung mit BASF** (S. Kaestel, D. Bettag) nach der
Besprechung vom 24.11.2026. Grundlage: Aufgabenteilung vom 09.11. (Menge, Pumpe und Füllende
steuert die Leitstelle, Absperrklappe gehört zum Arm) und Mail BASF vom 11.11. (Signale über
freie E/A im IVK, Pumpenabschaltung durch die Überfüllsicherung übernimmt BASF). Vor Ort sind
BASF-Remote-E/A (Allen-Bradley) nahe den Verladearmen vorhanden; freie Kapazität prüft BASF.
Das normale Füllende kommt von BASF (Sollmenge); Pumpe und Füllventil stoppen BASF-seitig auch
bei Störung oder Druckgrenzen.

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
| E6 | Verdrängen beendet | DI | Nach Füllende: Verdränger 3,5–5 bar, Handventil langsam öffnen, Restprodukt in den Tank; Klappe offen, Arm bleibt im Tank. Bestätigung heute durch Schichtpersonal am Vor-Ort-Panel → dieses Signal | – | Bestätigung am Panel als Signal verfügbar? |
| E6a | Spülen aktiv | DI | Spülen erfolgt in der **Parkstellung** (2× Luft, ca. 500 l VE-Wasser); Arm darf sich währenddessen nicht bewegen | – | Signal vorhanden? sonst Freigabe über A3 |
| E7 | Überfüllsicherung in Ordnung | DI, Ruhestrom | 0 = ausgelöst. Not-Abschaltung (nicht das normale Füllende): LBFS schaltet die Pumpe über die BASF-Remote-E/A (Allen-Bradley) ab; Meldung an HETA | `xUeberfuellAus` (invertiert) | zweiter Kontakt/Koppelrelais oder Meldung aus der Remote-E/A? |
| E8 | Fahrzeug geerdet | DI | Start nur bei Erdung. Heute nur in der Checkliste des Bedieners | – | elektrische Erdungsüberwachung vorhanden? (BASF prüft) |
| E9 | Klapptreppe in Ruhelage | DI | Start und Bewegung nur bei Ruhelage; Treppe hat bereits eine Zustandsleuchte | `xKlapptreppeRuhe` | Signal der Zustandsleuchte abgreifbar? |
| E10 | Lichtschranke Stellplatz belegt | DI | **zurückgestellt** (24.11.): nur nötig, falls Dome falsch erkannt werden | `xLichtschranke` | – |
| E11 | Not-Halt / Sicherheitskreis BASF in Ordnung | DI, Ruhestrom, ggf. 2-kanalig | Not-Halt bzw. Stopp der Verladestelle stoppt auch den Arm | Sicherheitssteuerung | vorhandene Stopp-/Not-Halt-Kreise prüfen (BASF) |

## HETA → BASF (Ausgänge der HETA-SPS)

| Nr. | Signal | Art | Bedeutung | HETA-SPS (`GVL_IO`) | Offen |
|---|---|---|---|---|---|
| A1 | Freigabe Befüllung (Arm bereit) | DO, Ruhestrom | 1 = Arm im Tank, Klappe offen, Pumpe darf laufen; 0 = Pumpe aus (Füllende, Störung, Maximalhöhe, Not-Halt, Drahtbruch) | `xArmBereit` und `NOT xBefuellStoppen` | ein Signal statt zwei (fehlersicher)? |
| A2 | Befüllung stoppen | DO | Störung bzw. Maximalhöhe erreicht (Grund für das Abschalten, Meldung im PLS) | `xBefuellStoppen` | entfällt, wenn A1 Ruhestrom und A5 Störung |
| A3 | Arm in Parkstellung | DO | Fahrzeug darf wegfahren, Treppe darf ausfahren | `xMeldeGruen` | |
| A4 | Arm in Bewegung / im Tank | DO | Automatik läuft, Arm bewegt sich bzw. ist im Tank | `xMeldeGelb` |  |
| A5 | Sammelstörung + Störcode | DO (+ Code) | Störung am Arm; **Störcode** an BASF gewünscht (24.11.) – binär über mehrere DO oder Bus | `xMeldeRot` | Anzahl Codes / Übertragungsweg |
| A6 | Klapptreppe verriegeln | DO | Treppe darf nicht ausfahren, solange der Arm nicht in Park ist | – (neu) | Eingriff in die Treppensteuerung möglich? |
| A7 | Not-Halt Arm | potentialfreier Kontakt, 2-kanalig | Not-Halt am Arm schaltet die Pumpe festverdrahtet ab (über TwinSAFE) | Sicherheitssteuerung | Einbindung in den BASF-Pumpenkreis |

## Ablauf (Signale)

1. BASF: **E1** Freigabe, **E2** Produkt, **E3** Kammern → Bediener drückt „Beladen starten“.
2. HETA: Arm fährt ein, Klappe auf → **A1** Freigabe Befüllung = 1.
3. BASF: Pumpe an (**E4** = 1). HETA zieht nach.
4. BASF: Sollmenge erreicht → Pumpe aus, **E5** Befüllung Ende. HETA: **A1** = 0, Klappe bleibt offen.
5. BASF: **Verdrängen** (3,5–5 bar, Handventil langsam), Arm bleibt im Tank → **E6** beendet.
   HETA: Klappe zu, Abtropfen.
6. Nächste Kammer (ab 2.) oder Rückfahrt → **A3** Arm in Parkstellung.
7. BASF: **Spülen in der Parkstellung** (2× Luft, ca. 500 l VE-Wasser), **E6a** Spülen aktiv
   sperrt den Arm.

Abbruch durch HETA (Störung, Maximalhöhe): **A1** = 0 (+ **A2**/**A5**) → BASF schaltet die Pumpe
ab → HETA wartet auf **E4** = 0 und Auslaufzeit → Klappe zu. Überfüllsicherung: BASF schaltet die
Pumpe direkt ab, **E7** = 0 → HETA-SPS geht in Störung.

## Offene Punkte (nach Besprechung 24.11.)

1. Freie E/A in der Remote-E/A (Allen-Bradley); festverdrahtet bestätigen.
2. Produkt und Kammern aus dem PLS oder Auswahl vor Ort? Reihenfolge der Kammern festlegen.
3. Bestätigung „Verdrängen beendet“ und „Spülen aktiv“ als Signal verfügbar?
4. Erdungsüberwachung elektrisch vorhanden? Zustandsleuchte Klapptreppe abgreifbar?
5. Einbindung in vorhandene Stopp- und Not-Halt-Kreise.
6. Störcodes: Anzahl und Übertragungsweg.
7. Genauere Fahrzeug- und Tankdaten (Tanktiefe Domrand–Boden 2,10–2,30 m bestätigt).
