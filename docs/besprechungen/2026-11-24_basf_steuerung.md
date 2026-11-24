# Besprechung BASF 24.11.2026 – Signale, Spülen, Sensorik, Kamera

Teilnehmer: S. Kaestel, D. Bettag (BASF), P. Schreiber (HETA). Quelle: automatisches Protokoll,
von P. Schreiber übermittelt.

## Ergebnisse

**Steuerung / Signale**
- Überfüllsicherung heute über **Allen-Bradley Remote-E/A** nahe den Verladearmen; freie E/A
  prüft BASF. Überfüllsicherung = Not-Abschaltung, **nicht** das normale Füllende.
- Normales Ende über die **Sollmenge**; Pumpe und Füllventil stoppen auch bei Störung oder
  Druckgrenzen (BASF-seitig).
- Vorschlag HETA (festverdrahtet 24 V, Koppelrelais, Ruhestrom) angenommen zur Prüfung.
  Eingänge: Freigabe, Produkt, Kammer/Füllschritt, Rückmeldung Pumpe/Ventil, Füllschritt fertig.
  Ausgänge: Freigabe/Stopp Befüllung, Arm in Park / in Bewegung, **Störcodes**.
- Ablauf, Signale und freie E/A gemeinsam prüfen, bevor umgesetzt wird.

**Ablauf / Sicherheit vor Ort**
- Kammern werden über die **offenen Dome** erkannt; Reihenfolge der Kammern noch festlegen.
- **Tankhöhen 2,10–2,30 m, Domrand bis Tankboden** (bestätigt) – BASF liefert genauere
  Fahrzeug- und Tankdaten. **Wichtig für die Eintauchtiefe** (heute 2,1 m unter Domrand angenommen).
- Klapptreppe hat bereits eine Zustandsleuchte; Treppenstellung kann die Armbewegung sperren.
- Erdung steht in der Checkliste des Bedieners; elektrische Überwachung unklar.
- **Lichtschranke Stellplatz zurückgestellt**, solange es keine Fehlerkennung von Domen gibt.
- Vorhandene Stopp- und Not-Halt-Kreise auf Einbindung des Arms prüfen.

**Verdrängen, Spülen, Abtropfen (Ablauf heute)**
1. Nach dem Füllen: Verdrängerbehälter auf **3,5–5 bar**, Arm bleibt im Tank.
2. Handventil **langsam** öffnen (gegen Spritzer und Schaum) → Restprodukt wird in den Tank
   gedrückt, Arm läuft leer.
3. Arm fährt in die **Parkstellung**, erst dann Spülen.
4. Füllrohrverlängerung abnehmen, Arm **zweimal mit Luft** verdrängen.
5. Spülen mit ca. **500 l VE-Wasser**; außen wird beim Verdrängen mit abgespült.
6. Schichtpersonal bestätigt am **Vor-Ort-Panel**.

**Arm / Reinigung**
- Pendelwanne (mechanische Klappe) vorgestellt; ggf. Parkstellung anpassen für Platte/Klappe.
- Sensorreinigung evtl. mit Wasserschlauch in einer Reinigungsstellung.
- Wöchentlich Hochdruckreinigung nach Abnehmen der Füllrohrverlängerung; Eignung Sensor und Kabel
  mit Baumer klären. Kunststoff-Verlängerungen ausgeschlossen (Hochdruck).
- **Abgelenkter bzw. geteilter Auslass** (Strömung zur Seite) könnte Schaum mindern; BASF klärt,
  warum ein gebogenes Füllrohr früher nicht übernommen wurde.

**Sensorik**
- Überfüllsicherung **Baumer LBFS-43L21.0**, auf 207 mm einstellbar; **Schutzkorb** vorgesehen
  (Spitze evtl. bruchempfindlich). Befestigung direkt oder Schelle am Füllrohr.
- HETA schlägt **80-GHz-Radar** fürs Nachziehen vor; Verhalten bei Schaum produktabhängig →
  BASF testet (Radar/Ultraschall) mit Produkt und Schaum, mit internem Fachmann.

**Kamera**
- Prototyp gezeigt (3D-Punktwolke, Abstandsmessung, Wand 4,95 m).
- Werkstatttest: Domerkennung, Licht, Spiegelungen.
- Kamera dient der Domerkennung über Tiefe, **nicht der Personenüberwachung**; Datenschutz und
  Information der Mitarbeiter vor dem Einsatz klären (beide Seiten).

**Sonstiges**
- Halbautomatischer Verladearm wird nächste Woche geliefert; Besuch P. Schreiber möglich.
- Filtertest an H517 beendet; Ergebnis/Grund unbekannt, BASF fragt nach.

## Aufgaben

| Wer | Was |
|---|---|
| HETA (P. Schreiber) | Signalliste und repräsentatives Kamerabild schicken; Radar-Daten (80 GHz) schicken; Kameratest in der Werkstatt (Domerkennung, spiegelnde Flächen) diese Woche |
| BASF | freie Remote-E/A prüfen, Signalliste prüfen; Radar/Ultraschall mit Produkt und Schaum testen; Tank- und Aufliegerhöhen, Füllablauf, Erdungsüberwachung, Stopp/Not-Halt klären; Grund gegen gebogenes Füllrohr klären |
| beide | Datenschutz Kamera klären |

## Folgen für HETA

- **Eintauchtiefe auf 1,90 m gesenkt** (flachster Tank 2,10 m − 20 cm): Simulation, Anlagendatei
  `simulation.yaml`, SPS-Entwurf `GVL_Param`. Bei tieferen Tanks bleibt mehr Abstand; besser später
  Tiefe je Fahrzeug aus dem PLS oder über das Radar.
- **SPS-Ablauf:** Verdrängen mit Arm im Tank (Klappe offen, Handventil heute von Hand – künftig
  Signal „Verdrängen beendet“), danach Parkstellung; Spülen erst in Park (Spülwanne). Störcodes
  als Ausgang an BASF.
- Signalliste V2 nach Rückmeldung BASF (Remote-E/A Allen-Bradley, Treppenleuchte, Erdung,
  Lichtschranke zurückgestellt).
- Schutzkorb LBFS und ggf. Reinigungsstellung in der Konstruktion.
