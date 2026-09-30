# Anfrage SEW: Absolutwertgeber, Bremse, Umrichter (Entwurf 30.09.2026)

**An:** fabian.lay@sew-eurodrive.de

**Betreff:** Angebots-Nr. 426368452A – Änderung Geber/Bremse, Umrichter für 3 Achsen

Guten Tag Fabian Lay,

vielen Dank für Ihr Angebot **Nr. 426368452A** für P5KG31-0004/N/S/0 MD071A
CM3C71S-20A-D/PK/RH1M/SM1. Wir bitten um ein geändertes Angebot (Punkte 1 und 2) und um ein
Angebot zu den Punkten 3 und 4.

**1. Servo J1 (Drehachse am Haltepunkt), 1 Stück**
- wie angeboten: CM3C71S, P5KG31 i = 4
- **Geber:** Multiturn-Absolutwertgeber statt Resolver RH1M, damit nach dem Einschalten keine
  Referenzfahrt nötig ist. Bitte nennen Sie den für den CM3C71S passenden Geber
  (digital/HIPERFACE, möglichst Einkabeltechnik) und ob dafür eine sicherheitsgerichtete
  Ausführung verfügbar ist.
- ohne Bremse

**2. Servo J2 (Drehachse am Fallrohr), 1 Stück**
- wie angeboten: CM3C71S, P5KG31 i = 4
- **Geber:** Multiturn-Absolutwertgeber wie J1
- **Haltebremse** 24 V DC. Die Achse ist über eine Stirnradstufe (Ritzel z48 / Zahnkranz z127)
  nicht selbsthemmend und muss bei STO/Not-Halt gegen Windlast halten.

**3. Vorhandener Getriebemotor J3 (Heben/Senken): RF47 DRN80M4/BE05/TF**
- Stirnrad-Getriebemotor R..DRN.. (IE3), mit Bremse BE05 und TF, bisher ohne Geber
- **Multiturn-Absolutwertgeber nachrüsten:** Ist das am vorhandenen Motor möglich (Anbausatz,
  Lüfterhaube)? Falls nicht, bitte einen gleichwertigen Getriebemotor mit Geber anbieten.

**4. Umrichter für alle drei Achsen**
- bisher MOVITRAC classic MCC91A-0032-5E3-4 (ohne Geberauswertung) an J3
- gesucht: Umrichter mit Auswertung der obigen Geber, **PROFINET** zur Siemens S7-1500
  (TIA Portal), **STO**, Bremsenansteuerung. Positionierung als Positionierachse in der S7-1500
  (PROFIdrive) oder im Umrichter – bitte Ihre Empfehlung.
- Schaltschrankeinbau, Netz 3 × 400 V (Kabel und Schaltschrank stellen wir selbst)

**Einsatzbedingungen**
- Verladearm im Freien, Umgebungstemperatur ca. −20 … +40 °C, Motoren IP65 oder besser
- Explosionsschutz: Zone ___ (wird noch geklärt, bitte Auswirkungen auf die Auswahl nennen)
- Betrieb: langsame Positionierfahrten, max. 6 °/s am Gelenk, wenige Fahrten pro Stunde
- Lastträgheit am Gelenk (Schätzung): J1 ca. 1 700 kg·m², J2 ca. 500 kg·m². Gesamtübersetzung
  Motor → Gelenk 10,58. Bitte prüfen Sie Regelbarkeit und Reglereinstellung für dieses
  Trägheitsverhältnis.

Bitte teilen Sie uns außerdem Lieferzeiten und die Datenblätter der Geber mit.

Mit freundlichen Grüßen
