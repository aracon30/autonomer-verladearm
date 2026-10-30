# Anforderungsnachweis (ISO 9001, 8.3.4)

Stand 30.10.2026 · Entwurf · Freigabe: [Name, Datum]

Jede Anforderung aus dem [Lastenheft](../lastenheft.html) (Version 0.1, Entwurf) mit Lösung,
Nachweis und Stand. Nachweise:
- **T**: automatischer Test (`vision/tests/…`, läuft bei jeder Änderung)
- **S**: Simulation (`tools/simulation.sh`, SPS-Simulator)
- **I**: Inbetriebnahmeprüfung (`python -m verladearm_vision.commissioning`, Bericht)
- **P**: Prüfung am Prototyp (Phase 4/5)
- **A**: Abnahme an der Anlage BASF (Phase 6)

Stand:
- ✅ = in Software/Simulation nachgewiesen (Prototyp/Anlage noch offen)
- 🔶 = Lösung festgelegt, Nachweis offen
- ⬜ = offen
- ⚠️ = **Abweichung vom Lastenheft** → Lastenheft ändern bzw. mit dem Kunden abstimmen

## Funktionale Anforderungen

| ID | Anforderung (Kurzfassung) | Prio | Lösung | Nachweis | Stand |
|---|---|---|---|---|---|
| F-01 | Dom automatisch erkennen, Mitte und Ausrichtung | Muss | 3D-Kamera SICK Visionary-T Mini, Erkennung `detection/opening.py` | T `test_detection.py` (u. a. `test_findet_oeffnung`, `test_fuelloeffnung_im_domdeckel`); P Kameratest | ✅ |
| F-02 | verschiedene Tankwagen, Aufbauhöhen, Positionen | Muss | runde und ebene Dächer, Arbeitsraum je Anlage | T `test_runder_tank_*`, `test_ebenes_dach_*`; I Arbeitsraum; P | ✅ |
| F-03 | Edelstahl, Lack, Tag/Nacht, Nässe, Schmutz | Muss | aktive ToF-Kamera, Median über Bilder, Glasscheibe | P Kameratest am Tankwagen (Spiegelung, Nässe) | ⬜ |
| F-04 | Sensor zentral oberhalb, wenig Hardware an der Spitze | Soll | Kamera über der Verladestelle; an der Spitze nur Referenzflansch, Grenzschalter, Abtropfsicherung | Stückliste, Skizzen | 🔶 |
| F-05 | keine/mehrere Öffnungen erkennen und abbrechen | Muss | keine Öffnung → Fehler 20; **mehrere Dome werden nicht mehr abgebrochen**, sondern per `DomeNo` gewählt (Mehrkammer, Schnittstelle V3) | T `test_keine_oeffnung`, `test_mehrkammer_*`, `test_dom_nicht_vorhanden` | ⚠️ |
| F-06 | Plausibilität der Zielposition | Muss | Größe/Lage in der Erkennung, Nachmessen Job 2 mit Grenzwert, Prüfung der Stützpunkte in der SPS | T `test_korrektur_gleicht_modellfehler_aus`, `test_fehlercodes`; S | ✅ |
| F-07 | Feinpositionierung im Nahbereich (Kann) | Kann | Nachmessen des Auslasses mit der Kamera (Job 2) statt Ultraschall | T `test_messen_nachmessen_rueckfahrt` | ✅ |
| F-10 | produktspezifische Eintauchtiefe, Nachziehen | Muss | Eintauchtiefe je ProductId; Nachziehen durch die SPS | T `test_eintauchtiefe_je_produkt`; S `test_befuellen_mit_nachziehen_bis_sollmenge` | ✅ |
| F-11 | Auslass bleibt unter der Oberfläche | Muss | 2 kapazitive Grenzschalter, Auslass 1–3 cm unter dem Spiegel (BASF: 2–3 cm) | S (bisher mit durchgehendem Messwert); Sensortest BASF; P | 🔶 |
| F-12 | Füllstand **kontinuierlich**, zuverlässig bei Schaum | Muss | **Zwei Grenzschalter statt kontinuierlicher Messung**; Füllstand an jedem Schaltpunkt aus Armhöhe | Sensortest BASF; P | ⚠️ |
| F-13 | Überfüllsicherung erkennt Flüssigkeit und Schaum, unabhängig | Muss | eigener zugelassener Grenzschalter (Schaltpunkt ca. 20 cm unter Rand), schaltet die Pumpe ab; nie betriebsmäßig | Zulassung (WHG/SIL) nach BASF; P; A | 🔶 |
| F-14 | Sensorik beständig gegen klebrige Medien | Muss | glatte kapazitive Spitzen, Ausblenden von Anhaftung, Spülen | Sensortest BASF | 🔶 |
| F-20 | Nachtropfen beim Herausfahren auffangen | Muss | pendelnde Abtropfsicherung (`docs/skizzen/Prinzipskizze_Abtropfsicherung_Rev3.pdf`) | Konstruktion; P | 🔶 |
| F-21 | Auffang entleeren/reinigen ohne Betreten | Soll | Kippnase und Anschlag an der Spülwanne, Spülen in der Parkstellung | P | 🔶 |
| F-22 | selbstständig in die Parkstellung | Muss | Job 3 (Rückfahrt aus jeder Lage, auch ohne vorige Messung) | T `test_rueckfahrt_*`; S | ✅ |
| F-30 | Start am **Touchscreen** und über das PLS | Muss | **kein Display** (Entscheidung 19.10.): Leuchttaster „Beladen starten“, Freigabe aus dem PLS | S `test_start_nur_mit_allen_freigaben` | ⚠️ |
| F-31 | Parameter je Produkt | Muss | Eintauchtiefe je Produkt in der Anlagendatei (Konfigurator); Menge aus dem PLS; Grenzen der Positionierung je Anlage | T `test_eintauchtiefe_je_produkt`, `test_konfigurator.py` | 🔶 (Füllgeschwindigkeit, Mindestabstand offen) |
| F-32 | **HMI** zeigt Status, Schritt, Füllstand, Meldungen | Muss | **kein HMI vor Ort**: Leuchtmelder; Status, Menge und Störungen im PLS | Signalliste SPS↔PLS (offen) | ⚠️ |
| F-33 | Tippbetrieb für Einrichtung und Wartung | Muss | Handbetrieb nur vor Ort mit Handbediengerät (Zustimmtaster) | S `test_handbetrieb_und_verriegelungen` | ✅ |
| F-34 | Protokoll je Verladung an das PLS | Soll | Vision-PC zeichnet jeden Auftrag auf; Übergabe an das PLS über die SPS | T `test_aufzeichnung_und_wiedergabe`; PLS-Signale offen | 🔶 |
| F-35 | Punktwolken speichern | Kann | Aufzeichnung mit Aufbewahrungsdauer | T `test_aufzeichnung_und_wiedergabe`, `test_alte_aufzeichnungen_werden_geloescht` | ✅ |

## Nichtfunktionale Anforderungen

| ID | Anforderung | Prio | Lösung | Nachweis | Stand |
|---|---|---|---|---|---|
| N-01 | Genauigkeit ±20 mm | Muss | Nachmessen und Korrektur in Job 2 (< 5 mm in der Simulation) | T `test_messen_nachmessen_rueckfahrt`; P | ✅ (Simulation) |
| N-02 | Start bis Befüllung ≤ 2 min | Soll | synchrone Fahrt, Fahrzeiten aus den Antriebsdaten | I Abschnitt Antriebe (ca. 1–1,5 min Anfahrt); P | 🔶 |
| N-03 | Erfolgsquote ≥ 98 % | Muss | – | P Dauertest; A | ⬜ |
| N-04 | −20 … +40 °C, Witterung | Muss | Kamera bis −20 °C im Dauerbetrieb; Getriebe J1/J2 nur bis −15 °C (zurückgestellt; H517 überdacht) | Datenblätter; offen | ⬜ |
| N-05 | IP65 | Muss | Kamera IP65/67/69, Motoren J1/J2 IP65, J3 IP55 | Datenblätter; J3 klären | 🔶 |
| N-06 | Ex-Zone | Muss | **keine Ex-Zone** an H517 (BASF, 15.10.) | Angabe BASF | ✅ (entfällt) |
| N-07 | optische Flächen geschützt, leicht zu reinigen | Muss | Glasscheibe, Montage oben unter dem Dach | P | 🔶 |
| N-08 | übertragbar auf andere Stationen | Soll | Anlagendatei je Arm, Konfigurator, Inbetriebnahmeprüfung | T `test_einrichtung.py`, `test_konfigurator.py`; I | ✅ |
| N-09 | Ersatzteile und Support 10 Jahre | Soll | Standardkomponenten (SEW, SICK, Siemens) | Lieferantenangaben | ⬜ |
| N-10 | Fernwartung (Kann) | Kann | – | – | ⬜ |

## Sicherheitsanforderungen

| ID | Anforderung | Prio | Lösung | Nachweis | Stand |
|---|---|---|---|---|---|
| S-01 | keine Personen im Bewegungsbereich, **sicherheitsgerichtete Personenerkennung** | Muss | heute: Klapptreppe in Ruhelage, Lichtschranke Stellplatz, Start nur vor Ort mit Sicht; **keine Personenerkennung vorgesehen** | Risikobeurteilung | ⚠️ |
| S-02 | Bewegung nur bei Verladebühne in sicherer Endlage | Muss | Klapptreppe „Ruhelage“ als Startbedingung und Verriegelung | S `test_bewegung_stoppt_bei_verriegelung`; P | ✅ (Simulation) |
| S-03 | zertifizierte Komponenten, PL aus Risikobeurteilung | Muss | F-CPU vorgeschlagen, STO fest verdrahtet | Risikobeurteilung, Validierung nach EN ISO 13849-2 | ⬜ |
| S-04 | Not-Halt am Bedienplatz und an der Station | Muss | Not-Halt Schaltschrank und Handbediengerät | Stromlaufplan; P | 🔶 |
| S-05 | bei Energieausfall Position halten, Befüllung stoppen | Muss | Haltebremsen alle Achsen, Absolutgeber; Klappe/Pumpe stromlos zu bzw. aus | P | 🔶 |
| S-06 | Kollisionen verhindern (Arbeitsraum, Moment) | Muss | Kollisionsprüfung jeder Bahn (Tank, Kragen, Deckel, Fremdkörper, Selbstkollision), Software-Endlagen, Momentgrenze im Umrichter | T `test_scene.py`, `test_fremdkoerper_*`, `test_selbstkollision_*`; P | ✅ (Software) |
| S-07 | Wegfahren des Tankwagens erkennen | Soll | Lichtschranke Stellplatz → Stopp | S (Simulator: Lichtschranke frei bei eingetauchtem Arm) | ✅ (Simulation) |
| S-08 | wiederholtes Aufsetzen auf dem Domrand vermeiden | Soll | senkrechtes Eintauchen durch den freien Durchgang, Nachmessen vor dem Eintauchen | T `test_verdeckte_oeffnung_sperrt_eintauchen`; P | ✅ (Software) |

## Neue Anforderungen (noch nicht im Lastenheft)

| Quelle | Anforderung | Stand |
|---|---|---|
| BASF 23.10. | Auslass 2–3 cm unter dem Spiegel | in F-11 aufnehmen |
| BASF 27.10. | Füllleistung 20–25 t/h, Füllgrad 95 %, 50–60 Fahrzeuge/Tag | in Lastenheft Kap. 3/5 aufnehmen |
| BASF 27.10. | Überfüllsicherung schaltet die Pumpe ab; nie betriebsmäßig | in F-13 aufnehmen |
| HETA 27.10. | Mehrkammer-Fahrzeuge: mehrere Dome nacheinander | F-05 ändern |
| HETA 19.10. | Bedienkonzept ohne Display, Handbetrieb nur vor Ort | F-30, F-32 ändern |
| BASF 27.10. | Rohrisolierung über J1 beachten | Kap. 8 (mechanische Randbedingungen) |
