# Anfrage Schaltschrankbau (Entwurf 30.09.2026)

**An:** Peter (Schaltschrankbau)

**Betreff:** Verladearm Prototyp – Schaltschrank und Verkabelung für Automatisierung

Hallo Peter,

wir automatisieren den Verladearm-Prototyp: Eine 3D-Kamera erkennt den Dom am Tankwagen, ein
Industrie-PC berechnet die Fahrt, eine neue S7-1500 fährt die drei Achsen. Für Schaltschrank und
Verkabelung brauchen wir dich. Bitte schau dir die Punkte an und gib uns eine erste Einschätzung
zu Aufwand, Platzbedarf und Termin.

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
    (Start, Stopp, Automatik/Hand, Meldeleuchten), Referenzschalter und Windmesser (optional)
  - Bedienpanel (optional, z. B. SIMATIC HMI 7″) für Handbetrieb und Meldungen

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

**5. Optional**
- Windmesser mit Eingang an der SPS (Automatikbetrieb bei starkem Wind sperren)
- Wartungssteckdose/LAN-Anschluss im Schrank für Laptop (Inbetriebnahme)

**Offene Punkte von unserer Seite:** Umrichtertyp (SEW), Ex-Zone, Aufstellort des Schranks.
Stückliste und Antriebsdaten schicke ich dir gerne mit.

Viele Grüße
