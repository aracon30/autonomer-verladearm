# Inbetriebnahme Verladearm

Jeder Verladearm hat eigene Maße, Servo-Nullstellungen, Verfahrbereiche, Hindernisse und
Produkte. Diese Werte stehen in einer **Anlagendatei** und werden vor Ort eingestellt.
Alles andere (Erkennung, Schnittstelle, Standardwerte) kommt aus `vision/config/default.yaml`.

Die Software ist für diese **Bauart** ausgelegt: J1 dreht am Haltepunkt, innerer Ausleger mit
festem Gefälle, Fallrohr mit J2, Winkel nach rechts mit J3 (heben/senken), äußerer Ausleger, Winkel nach
links, freies Gelenk J4, Auslass hängt durch die Schwerkraft (docs/kinematik.md). Alle Maße,
Winkel, Achsbereiche, Hindernisse und Produkte werden je Arm bei der Ersteinrichtung festgelegt.

## Konfigurator im Browser (empfohlen)

```bash
.venv/bin/python -m verladearm_vision.konfigurator --host 0.0.0.0 --port 8090
```

Im Browser `http://<IP des Rechners>:8090` öffnen. Alle Abschnitte der Anlagendatei auf einer
Seite, oben eine Leiste zum Springen (rot = ungültige Eingabe im Abschnitt): Anlage, Maße mit
Skizze, Servoachsen (Istwerte per Knopf aus der SPS übernehmen), Hindernisse (auch Vorlage
„Klapptreppe“), Produkte, Referenz am Auslass, Arbeitsraum (mit Höhe über Fahrbahn), Antriebe
(Kurzfassung je Achse) und Sensor/Kalibrierung (Quelle, IP der Kamera, Hinweis, ob noch
Beispielwerte der Kalibrierung gelten). Rechts laufend Plausibilitätsprüfung, Draufsicht und
Seitenansicht (Null- und Parkstellung, Hindernisse, Arbeitsraum, Kamera, erreichbare
Auslasslagen), die **nächsten Schritte** als kopierbare Befehle (Simulation, Prüfung,
Kalibrierung, Vision-Dienst für genau diese Anlage) und auf Knopfdruck die vollständige
Inbetriebnahmeprüfung.

Speichern schreibt `vision/config/anlagen/<name>.yaml`; die bisherige Fassung wird vorher unter
`data/sicherung_anlagen/` gesichert. **Vorlagen** aus dem Repository (`beispiel`,
`heta_prototyp`, `simulation`) sind markiert und werden nur unter neuem Namen gespeichert
(„Speichern unter …“, übernimmt alle Abschnitte der Vorlage) – so blockieren eigene Werte nie
ein `git pull`. Ohne `--host` nur auf dem Rechner selbst erreichbar
(SSH-Tunnel); mit `--host 0.0.0.0` für alle im Netz **ohne Anmeldung** – nur im internen Netz.

## Ersteinrichtung im Dialog (Kommandozeile)

```bash
python -m verladearm_vision.einrichtung --name lich_station3 --from-plc
```

Der Dialog führt durch die Schritte 1–6 unten, prüft jeden Wert auf Plausibilität und schreibt
`vision/config/anlagen/lich_station3.yaml`. Mit `--from-plc` liest er Nullstellung,
Drehrichtung und Parkstellung direkt aus der SPS: Arm im Handbetrieb in die angesagte Stellung
fahren, Enter drücken. Ohne `--from-plc` werden die Servowerte eingegeben. Zum Schluss zeigt er
Reichweite und Höhen des Auslassendes zum Vergleich mit der realen Anlage. Erneuter Aufruf mit
demselben Namen = Anlagendatei ändern (bisherige Werte sind die Vorschläge).

Danach weiter mit Schritt 7 (Kalibrierung).

## Ablauf

1. **Anlagendatei anlegen** (oder Dialog oben)
   `vision/config/anlagen/beispiel.yaml` kopieren, z. B. als `lich_station3.yaml`.
   Kopf ausfüllen (Anlage, Datum, Name). SPS-Adresse unter `plc.url` eintragen.

2. **Maße aufnehmen** (`arm`)
   Von Gelenkachse zu Gelenkachse bzw. Rohrmitte zu Rohrmitte messen, in Metern, nie Außenkanten.
   Bei 90°-Winkeln zählt der Schnittpunkt der beiden Rohrmittellinien (gedachter Eckpunkt).

   ```
                Fallleitung (von oben, Achse = Drehachse J1)
                      ║
                   ═══╩═══  Oberkante Schnittstellenflansch ──┐
                      │                                       │ flange_offset (HETA: 404 mm)
                      ●──── innerer Ausleger 3° ──(inner_length)──┐ Winkel nach unten
                      │  (Rohrmitte auf Achse J1)               │ drop
       flange_height  │                              J2 ────────┘── Winkel nach rechts ...
                      │
   ═══════════════════╧══════ Fahrbahn
   ```

   | Parameter | Strecke |
   |---|---|
   | `flange_height` | senkrecht: Fahrbahn (Standfläche Tankwagen) bis **Oberkante Schnittstellenflansch** am Eintritt J1 (Fallleitung von oben) |
   | `flange_offset` | senkrecht auf Achse J1: Oberkante Schnittstellenflansch bis Rohrmitte des 3°-Rohrs (innerer Ausleger) |
   | `base_height` | wird berechnet: `flange_height − flange_offset` = Rohrmitte innerer Ausleger auf J1 = Ursprung der Armbasis-Koordinaten (z = 0). Ältere Anlagendateien ohne Flanschmaße geben `base_height` direkt an |
   | `inner_length` | Achse J1 bis Mitte Winkel nach unten |
   | `drop` | Winkel nach unten bis Mitte Winkel nach rechts |
   | `offset_right` | Winkel nach rechts bis Mitte Winkel nach vorne |
   | `outer_length` | Winkel nach vorne bis Mitte Winkel nach links |
   | `offset_left` | Winkel nach links bis Mitte Winkel nach unten (freies Gelenk J4) |
   | `outlet_length` | Winkel nach unten bis Auslassende |
   | `incline_deg` | festes Gefälle des inneren Auslegers (Fallrohr senkrecht; sonst `drop_tilt_deg`) |
   | `support` | Bauform am Haltepunkt: `oben` = Zulauf als Fallleitung von oben durch J1 (HETA), `unten` = Säule |
   | `feed_length` | sichtbare Länge der Fallleitung über dem Flansch; wird als festes Hindernis berücksichtigt |
   | `pipe_diameter` | Außendurchmesser der Ausleger-Rohre (Darstellung, Simulation) |

3. **Servoachsen einstellen** (`arm.joints`, alle Werte in Servo-Grad wie am Antrieb angezeigt)
   - `zero`: Arm im Handbetrieb so stellen, dass beide Ausleger gestreckt nach vorne zeigen und
     der äußere Ausleger **waagerecht** liegt (Wasserwaage). Servowerte J1, J2, J3 ablesen.
   - `direction`: Jede Achse ein Stück im positiven Sinn verfahren. Dreht J1 bzw. J2 nach links
     (von oben gesehen gegen den Uhrzeigersinn) bzw. hebt J3 den Ausleger: `1`, sonst `-1`.
   - `min` / `max`: freigegebener Verfahrbereich (nicht die mechanischen Endanschläge).
   - `park`: Servowerte der Parkstellung.

4. **Hindernisse erfassen** (`arm.obstacles`)
   Stützen, Bühne, Geländer, Leitungen im Schwenkbereich als Quader, gedrehter Quader oder
   Zylinder in Armbasis-Koordinaten (Ursprung Achse J1, x vorne, y links, z oben; Meter).
   Großzügig umschließen. Tankwagen und offener Domdeckel werden bei jeder Messung erfasst und
   müssen hier nicht eingetragen werden.
   `clearance` ist der zusätzliche Mindestabstand zur Rohrachse.

5. **Produkte** (`products`): Eintauchtiefe je `ProductId`, `default` für alle übrigen.

   **Referenz am Auslass** (`outlet`): Markierungsscheibe (Standard Ø 250 mm, 150 mm über dem
   Auslassende) oder ein vorhandener, von oben sichtbarer Flansch am Auslassrohr, z. B. beim
   HETA-Prototyp Flansch Ø 220 mm, Oberkante 823 mm über dem untersten Punkt des Auslasses:
   `marker_radius: 0.11`, `marker_offset: 0.823`, `pipe_radius: 0.057`. Die Referenz muss rund,
   mittig und rechtwinklig zum Auslassrohr sein; keine Laschen o. ä. über den Außenrand.
   Eine teilweise Verdeckung durch die Rohrleitung darüber ist zulässig: Die Erkennung sucht
   den Rand mit bekanntem Durchmesser nahe der vom Armmodell erwarteten Lage und nutzt bei
   stark verdecktem Rand zusätzlich die Achse des Auslassrohrs über der Referenz.

6. **Arbeitsraum** (`commissioning`): wo Dome bei dieser Station vorkommen. Nur für die
   Inbetriebnahmeprüfung (welche Domlagen werden durchgerechnet) und die Kalibrierstellungen –
   im Betrieb findet die Kamera den Dom selbst. Eingabe in Konfigurator und Dialog anschaulich:
   Abstand Mitte Fahrspur bis J1, Haltemarke längs, Haltetoleranz quer/längs (±) und
   Domoberkante des niedrigsten/höchsten Fahrzeugs über der Fahrbahn (Lkw ca. 3,2 m, Kesselwagen
   ca. 4,6 m). Daraus wird `workspace_min/max` (Armbasis) berechnet.

7. **Hand-Auge-Kalibrierung** → `calibration.matrix`, siehe [Kalibrierung](kalibrierung.md):
   `python -m verladearm_vision.calibrate --config vision/config/anlagen/<anlage>.yaml --from-plc`

8. **Prüfen**
   ```bash
   python -m verladearm_vision.commissioning --config vision/config/anlagen/lich_station3.yaml > protokoll.md
   ```
   Prüft die Parameter, die Parkstellung und für jede Lage im Arbeitsraum, ob der Arm
   kollisionsfrei anfahren und mit der größten Eintauchtiefe eintauchen kann. Mängel werden mit
   Grund und Lage aufgeführt. Das Protokoll zur Inbetriebnahme ablegen.

9. **Sichtprüfung in der Live-Ansicht**
   ```bash
   python -m verladearm_vision.viewer --opcua --config vision/config/anlagen/lich_station3.yaml
   ```
   Rohrführung, Sperrbereiche und Servowerte mit der realen Anlage vergleichen.

10. **Autostart einrichten**: `sudo deploy/install.sh vision/config/anlagen/<anlage>.yaml`,
    siehe [Betrieb](betrieb.md).

11. **Abgleich mit der SPS**: Maße, Nullstellungen, Drehrichtungen und Grenzen im SPS-Programm
    müssen denselben Werten entsprechen. Anlagendatei per Pull Request einchecken.

## Grundsatz

Die Prüfung ersetzt keine Sicherheitsfunktion. Verfahrbereiche, Endlagen und Schutzbereiche
werden zusätzlich in der SPS bzw. Sicherheits-SPS überwacht (ADR 0001).
