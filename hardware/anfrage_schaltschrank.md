# Anfrage Schaltschrankbau (Entwurf 30.09.2026)

> **Gesendet 01.10.2026** mit eigenen Anpassungen (HMI 11″, F-CPU „wenn sinnig“, ohne Windmesser,
> Termin Endkunde April 2027). Abweichung: In der gesendeten Fassung steht „Von Hand bewegen
> (J1/J2/J3)“ – J3 darf **nicht** gelüftet werden, Korrektur an Peter nachgereicht (siehe unten).

**An:** Peter (Schaltschrankbau)

**Betreff:** Verladearm Prototyp – Schaltschrank, Verkabelung und SPS-Programm

Hallo Peter,

wir automatisieren den Verladearm-Prototyp: Eine 3D-Kamera erkennt den Dom am Tankwagen, ein
Industrie-PC berechnet die Fahrt, eine neue S7-1500 fährt die drei Achsen. Für Schaltschrank,
Verkabelung und SPS-Programm brauchen wir dich. Bitte schau dir die Punkte an und gib uns ein Angebot bzw. eine erste
Einschätzung zu Aufwand, Platzbedarf und Termin – für Schaltschrank, Verkabelung und SPS-Programm.

**1. Komponenten im Schaltschrank**
- **Umrichter SEW für 3 Achsen** mit Geberauswertung, PROFINET, STO und Bremsenansteuerung;
  3 × 400 V. Typ kommt mit dem SEW-Angebot (angefragt), wir leiten es dir weiter.
- **SIMATIC IPC BX-32A** (Hutschiene, 24 V DC, lüfterlos), 2 Netzwerke:
  PROFINET/SPS-Netz und ein eigenes Netz nur für die Kamera
- **Netzwerk:** PROFINET als Linie SPS → Umrichter J1 → J2 → J3, der IPC an einem freien Port der
  SPS (X1 Port 2 oder X2). Die Kamera hängt direkt am IPC. Ein Switch nur, falls die Ports nicht reichen.
- **24-V-Netzteil** für IPC, Kamera (typ. 12 W, Spitze 2 A) und die Haltebremsen J1 und J2 –
  bitte selbst auslegen
- **SPS neu (bisher keine vorhanden):** S7-1500 als **F-CPU** (Standard- und Sicherheitsprogramm
  in einer CPU), z. B. **CPU 1512SP F-1 PN** (ET 200SP, kompakt) oder **CPU 1513F-1 PN**. Anforderungen:
  - PROFINET für 3 SEW-Umrichter (Positionierachsen über PROFIdrive, STO/SS1 über PROFIsafe
    oder verdrahtet) und OPC UA zum IPC
  - **Lizenz „SIMATIC OPC UA S7-1500“** passend zur CPU-Größe (für den OPC-UA-Server)
  - Peripherie: **F-DI** für Not-Halt, Endschalter und Quittierung; **DI/DQ** für Bedienelemente
    (Produktwahl, Fahrzeug bereit, Start Automatik, Beladung beendet, Stopp, Automatik/Hand,
    Meldeleuchten), **Endschalter Klapptreppe Ruhelage**, **Lichtschranke Fahrzeug**, Ampel und
    Windmesser (optional)
  - Bedienpanel für Produktwahl und Meldungen (z. B. SIMATIC HMI 7″) – bei der Produktwahl
    wahrscheinlich sinnvoller als Taster

**2. Antriebe im Feld**

| Achse | Motor | Bremse | Geber | Temperatur |
|---|---|---|---|---|
| J1 Drehen am Haltepunkt | SEW Servo CM3C71S, Steckverbinder SM1 | ja, 24 V | Multiturn absolut (angefragt) | PT1000 |
| J2 Drehen am Fallrohr | SEW Servo CM3C71S, Steckverbinder SM1 | ja, 24 V | Multiturn absolut (angefragt) | PT1000 |
| J3 Heben/Senken | SEW DRN80M4 (Drehstrom, vorhanden) | BE05 | Multiturn absolut (angefragt) | TF |

- J3 hängt heute am MOVITRAC classic MCC91A-0032-5E3-4. Der wird durch den neuen Umrichter ersetzt.
- J1 und J2 drehen je ca. 280°. Die Leitungen müssen die Drehung mitmachen
  (Leitungsführung, schleppkettentaugliche Motor- und Geberleitungen).

**3. 3D-Kamera SICK Visionary-T Mini (angefragt)**
- Montage auf einer Traverse über dem Tankwagen, im Freien, ca. 4–6 m hoch
- Ethernet: M12 8-polig X-kodiert auf RJ45 (Cat6a) direkt zum IPC, **nicht** über das SPS-Netz
- Versorgung: M12 8-polig A-kodiert, 24 V DC
- Bitte Leitungslängen von der Traverse zum Schrank aufnehmen.

**4. Sicherheit**
- Not-Halt wirkt auf STO aller drei Umrichter (J3 mit Bremse: SS1, damit der Arm nicht absackt)
- Endschalter bzw. Endlagen je Achse als Hardwaregrenze, Auswertung in der Sicherheitstechnik
- Explosionsschutz: Zone wird noch geklärt. Das kann die Auswahl von Kamera, Gebern und
  Leitungen beeinflussen.

**5. SPS-Programm (bitte mit kalkulieren)**
- Hardwarekonfiguration im TIA Portal: CPU, Peripherie, SEW-Umrichter, OPC-UA-Server
- Technologieobjekte: 3 Positionierachsen mit Absolutgebern, Grenzen, Rampen, Ruck (mit SEW)
- **Bedienablauf:**
  1. Arm steht in Parkstellung. LKW/Kesselwagen fährt vor, Klapptreppe fährt auf das Fahrzeug,
     Fahrer öffnet den Dom, Klapptreppe fährt zurück.
  2. Bediener wählt an der SPS das **Produkt** (bestimmt, wie tief der Arm eintaucht) und
     bestätigt „Fahrzeug bereit“.
  3. Bediener startet **„Automatisch beladen“**: Arm fährt selbstständig über den Dom und taucht ein.
  4. Beladung läuft (nicht Teil dieser Steuerung).
  5. Bediener meldet **„Beladung beendet“**: Arm fährt zurück in die Parkstellung.
- **Verriegelungen:** Start nur, wenn Arm in Parkstellung, **Klapptreppe in Ruhelage**
  (Endschalter) und – optional – **Lichtschranke** Stellplatz belegt. Während der Automatik darf
  die Klapptreppe nicht ausfahren. Fällt die Lichtschranke ab oder verlässt die Treppe die
  Ruhelage: Bewegung stoppen, Meldung. Optional Ampel für den Fahrer (rot = nicht wegfahren,
  Arm im Dom). Steuert ihr die Klapptreppe mit dieser SPS oder mit einer anderen?
- **Parkstellung:** „Arm in Parkstellung“ prüft die SPS selbst: Servowinkel J1–J3 innerhalb einer
  Toleranz (z. B. ±0,5°) um die Parkwerte. Die Parkwerte bitte als Parameter (am HMI änderbar),
  sie müssen mit unserer Anlagendatei übereinstimmen (heute J1 70°, J2 −135°, J3 10°, wird vor
  Ort festgelegt).
- **Ablauf der Verladung** nach unserer Schnittstellenbeschreibung (`docs/schnittstelle.md`,
  Datenbaustein `plc/DB_Vision.db` als SCL-Quelle liegt vor): Aufträge an den PC (Job 1–3),
  Handshake und Heartbeat, Prüfung der Stützpunkte, **synchrones Fahren** der drei Achsen
  (alle kommen gleichzeitig am Stützpunkt an), langsames Eintauchen, Zeitüberwachung,
  Fehlerbehandlung
- **Handbetrieb** (Betriebsartenwahl Automatik/Hand mit Schlüsselschalter):
  - **Verfahren am Touchscreen:** Achsen J1/J2/J3 einzeln tippen (+/−), nur solange gedrückt
    (Tippbetrieb), reduzierte Geschwindigkeit, Endlagen aktiv. Am besten **Mobile Panel mit
    Zustimmtaster und Not-Halt**, damit der Bediener dort steht, wo er Dom und Auslass sieht.
  - **Von Hand bewegen (J1/J2):** Taster „Bremse lüften“ in Hand, Antrieb dabei in STO, Bremse
    nur offen, solange der Taster gedrückt ist. Arm am Auslass von Hand führen, wie bisher.
    **J3 nie Bremse lüften** (Last hängt an der Schnecke, Selbsthemmung nicht zugesichert,
    Arm könnte absacken) → J3 immer über Tippen.
  - Die Absolutgeber zählen dabei weiter, keine Referenzfahrt nötig.
  - **„Automatisch in Parkstellung“** aus jeder Lage (PC plant die Rückfahrt: erst senkrecht
    heraus, dann kollisionsfrei in die Parkstellung = Job 3).
  - Handbetrieb dient auch als **Rückfallebene**, wenn die Kamera/Automatik ausfällt.
- **Sicherheitsprogramm** (F-CPU): Not-Halt, STO/SS1, Endlagen, Quittierung, inkl. Validierung
- HMI: Produktwahl, Bedienung, Meldungen, Fehlertexte
- Test: Unsere PC-Software läuft auch als Simulation und kann gegen PLCSIM Advanced getestet
  werden, bevor ihr an den Arm geht.
- Inbetriebnahme vor Ort (bitte Tage schätzen)

**6. Optional**
- Windmesser mit Eingang an der SPS (Automatikbetrieb bei starkem Wind sperren)
- Wartungssteckdose/LAN-Anschluss im Schrank für Laptop (Inbetriebnahme)

**Offene Punkte von unserer Seite:** Umrichtertyp (SEW), Ex-Zone, Aufstellort des Schranks.
Stückliste und Antriebsdaten schicke ich dir gerne mit.

Viele Grüße

---

## Nachtrag an Peter (Korrektur Handbetrieb J3)

Hallo Peter,

eine Korrektur zu meiner Mail, Punkt 5 Handbetrieb: „Bremse lüften“ bitte **nur für J1 und J2**.
Bei J3 (Heben/Senken) hängt das Gewicht des Arms am Schneckengetriebe, dessen Selbsthemmung nicht
zugesichert ist – mit gelüfteter Bremse könnte der Arm absacken. J3 im Handbetrieb nur tippen,
„Bremse lüften“ für J3 bitte in der Steuerung sperren.

Viele Grüße
