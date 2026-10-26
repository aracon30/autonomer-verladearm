"""HETA-Softwaredokumentation SWD-4793: Schnittstelle SPS ↔ Vision-PC, Inbetriebnahme,
Kalibrierung. Mitgeltende Unterlage zur Betriebsanleitung OMIM-4793."""

FRONT = [
    (1, ">BETRIEBS-, WARTUNGS- UND INSTALLATIONSHANDBUCH<", ">SOFTWAREDOKUMENTATION<"),
    (2, "Obenverladearm mit elektrischem Antrieb (Heben / Senken)",
     "Autonomer Obenverladearm – Schnittstelle SPS ↔ Vision-PC, Inbetriebnahme, Kalibrierung"),
    (3, ">Obenverladearm, elektrisch<", ">Autonomer Obenverladearm, Software<"),
    (3, ">OMIM-4793<", ">SWD-4793<"),
]
HEADER = [("Betriebs-, Wartungs- und Installationshandbuch – Obenverladearm elektrisch",
           "Softwaredokumentation – autonomer Obenverladearm")]
FOOTER = [("OMIM-4793", "SWD-4793")]

W2 = [3600, 6038]
W2b = [2900, 6738]
W3 = [2600, 1300, 5738]

BLOCKS = [
    # 1 ---------------------------------------------------------------------------------------
    ("h1", "1. ZWECK UND GELTUNGSBEREICH"),
    ("p", "Diese Dokumentation beschreibt die Software des autonomen Obenverladearms "
          "(Auftrag K-04793/26, Fabrik-Nr. 4793-01): die Aufgabenteilung zwischen SPS und "
          "Vision-PC, die Schnittstelle zwischen beiden, Installation und Betrieb des Vision-PCs, "
          "die Inbetriebnahme mit der Anlagendatei und die Kalibrierung von Kamera und Arm."),
    ("p", "Sie ist mitgeltende Unterlage zur Betriebsanleitung **OMIM-4793** und richtet sich an "
          "den Programmierer der SPS, das Inbetriebnahmepersonal von HETA und die "
          "Instandhaltung des Betreibers. Bedienung und Sicherheitshinweise stehen in der "
          "Betriebsanleitung."),
    ("note", "Die Software des Vision-PCs ist nicht sicherheitsgerichtet. Not-Halt, sicheres "
             "Abschalten (STO), Verriegelungen, Endlagen und Überfüllsicherung liegen in der SPS "
             "bzw. in der Hardware und wirken unabhängig vom Vision-PC."),
    ("h2", "1.1. Softwarestand"),
    ("table", W2, [
        ("Vision-Software", "[Version folgt]"),
        ("Schnittstelle", "InterfaceVersion 2 (Version 3 mit Nachziehen in Vorbereitung)"),
        ("SPS-Programm", "[Version folgt]"),
        ("Betriebssystem Vision-PC", "Ubuntu Linux 22.04 / 24.04 [Stand bei Auslieferung folgt]"),
    ]),

    # 2 ---------------------------------------------------------------------------------------
    ("h1", "2. SYSTEMÜBERSICHT"),
    ("p", "Eine 3D-Kamera über der Verladestelle nimmt das Fahrzeug von oben auf. Der Vision-PC "
          "erkennt daraus Domöffnung, offenen Deckel und Aufbauten und berechnet eine "
          "kollisionsfreie Bahn als Folge von Gelenkwinkeln (Stützpunkte). Die SPS prüft jede "
          "Vorgabe, fährt die Achsen über die Umrichter und überwacht den Ablauf."),
    ("table", W2b, [
        ("Vision-PC (nicht sicherheitsgerichtet)", "Dom messen, offenen Deckel erkennen, "
         "Kinematik, Rückwärtsrechnung, Kollisionsprüfung (feste Hindernisse, Tankkörper, "
         "Domkragen, Deckel, eigener Arm), Bahn als Stützpunkte in Servo-Grad, Nachmessen des "
         "Auslasses über dem Dom, Aufzeichnung, Live-Ansicht."),
        ("SPS", "Ablauf, Plausibilitätsprüfung jeder Vorgabe, synchrones Fahren der Stützpunkte, "
         "Bremsen, Befüllen mit Nachziehen, Absperrklappe, Verriegelung Klapptreppe und "
         "Lichtschranke, Bedienung vor Ort, Schnittstelle zur Leitstelle."),
        ("Umrichter (SEW MOVITRAC advanced)", "Positionierung je Achse mit MOVIKIT Positioning "
         "Drive, Strom-, Drehzahl- und Lageregelung, Bremsenansteuerung, STO."),
        ("Sicherheitstechnik", "Not-Halt, Zustimmtaster, STO, sichere Verriegelungen "
         "[Ausführung und PL folgen aus der Risikobeurteilung]."),
        ("Leitstelle (PLS)", "Freigabe, Produkt, Sollmenge, Kalibrierung anstoßen, Meldungen."),
    ], ("Ebene", "Aufgabe")),
    ("p", "Der Vision-PC regelt nichts in Echtzeit. Er liefert Vorschläge; die SPS entscheidet "
          "und fährt. Fällt der Vision-PC aus, stoppt die SPS die automatische Bewegung; der Arm "
          "kann im Handbetrieb weiter verfahren werden."),
    ("sub", "Komponenten"),
    ("table", W2, [
        ("3D-Kamera", "SICK Visionary-T Mini CX, Ethernet zum Vision-PC [Typ bestätigen]"),
        ("Vision-PC", "Siemens Industrie-PC mit Linux, Dienste „verladearm-vision“ und "
                      "„verladearm-viewer“ [Typ folgt]"),
        ("SPS", "Siemens S7-1500 mit integriertem OPC-UA-Server [Typ folgt]"),
        ("Verbindung Vision-PC ↔ SPS", "OPC UA über Ethernet, SPS = Server, Vision-PC = Client"),
        ("Verbindung SPS ↔ Umrichter", "PROFINET, MOVIKIT Positioning Drive (8 Prozessdaten)"),
    ]),

    # 3 ---------------------------------------------------------------------------------------
    ("h1", "3. SCHNITTSTELLE SPS ↔ VISION-PC"),
    ("p", "Protokoll **OPC UA**. Die SPS stellt den Datenbaustein **DB_Vision** als Server "
          "bereit, der Vision-PC liest und schreibt als Client. Aktuelle Version: "
          "**InterfaceVersion = 2**."),
    ("h2", "3.1. Variablen SPS → Vision-PC"),
    ("table", W3, [
        ("HeartbeatPLC", "Int", "Zählt alle ca. 100 ms hoch"),
        ("Trigger", "Bool", "Auftrag starten"),
        ("Job", "Int", "1 = Dom messen, Bahn planen · 2 = Auslass nachmessen, Bahn korrigieren · "
                       "3 = Rückfahrt planen · 0 = nur messen"),
        ("ProductId", "Int", "Produkt der aktuellen Verladung (bestimmt die Eintauchtiefe)"),
        ("Reset", "Bool", "Fehler quittieren"),
        ("ActualJ1 / J2 / J3", "Real", "Istwinkel der Achsen [Servo-Grad]"),
        ("AxesHomed", "Bool", "Istwinkel gültig (Multiturngeber, keine Referenzfahrt nötig)"),
        ("ArmState", "Int", "0 Park · 1 fährt · 2 über Dom · 3 eingetaucht · 9 Störung"),
    ], ("Name", "Typ", "Bedeutung")),
    ("h2", "3.2. Variablen Vision-PC → SPS"),
    ("table", W3, [
        ("HeartbeatPC", "Int", "Zählt je Zyklus (ca. 50 ms) hoch"),
        ("Ready", "Bool", "Vision-Dienst bereit: SPS-Heartbeat in Ordnung und Kamera verbunden "
                          "(nach dem Einschalten ca. 20 s)"),
        ("Busy", "Bool", "Auftrag läuft"),
        ("Done", "Bool", "Ergebnis liegt vor (gültig oder Fehler)"),
        ("Error / ErrorCode", "Bool / Int", "Auftrag fehlgeschlagen, Fehlercode (Kapitel 3.6)"),
        ("ResultId", "DInt", "Laufende Nummer des Ergebnisses"),
        ("TargetX / Y / Z", "Real", "Oberkante Domöffnung (Mitte), Armbasis [mm]"),
        ("NormalX / Y / Z", "Real", "Normale der Öffnung (Einheitsvektor)"),
        ("DiameterMm", "Real", "Erkannter Durchmesser der Öffnung [mm]"),
        ("Confidence", "Real", "Qualität der Erkennung 0 … 1"),
        ("WaypointCount", "Int", "Anzahl gültiger Stützpunkte (0 … 16)"),
        ("WaypointsJ1 / J2 / J3", "Array[1..16] of Real", "Zielwinkel je Stützpunkt "
                                                          "[Servo-Grad]"),
        ("ApproachIndex", "Int", "Nummer des Stützpunkts „über dem Dom“ (ab 1, 0 = keiner); "
                                 "danach folgt das Eintauchen"),
        ("CorrectionX / Y", "Real", "Job 2: gemessene Abweichung Soll − Ist des Auslasses "
                                    "[mm]"),
        ("InterfaceVersion", "Int", "Muss der in der SPS erwarteten Version entsprechen"),
    ], ("Name", "Typ", "Bedeutung")),
    ("h2", "3.3. Aufträge"),
    ("table", [1000, 4300, 4338], [
        ("1", "Dom und Deckel messen, Bahn ab Istlage planen", "Anfahrt (ggf. mit Umweg), "
         "senkrechtes Absenken, Eintauchen; ApproachIndex = Anfahrpunkt über dem Dom"),
        ("2", "Auslass über dem Dom nachmessen (Referenzflansch), Modellabweichung ausgleichen",
         "korrigierter Anfahrpunkt und Eintauchen; ApproachIndex = 1"),
        ("3", "Rückfahrt ab Istlage planen (aus jeder Lage, auch nach Handbetrieb)",
         "senkrecht heraus, dann kollisionsfrei in die Parkstellung; ApproachIndex = 0"),
        ("0", "nur messen (Test, Anzeige)", "keine"),
    ], ("Job", "Vision-PC", "Stützpunkte")),
    ("p", "Tankkörper, Domkragen und offener Deckel werden in Job 1 gemessen und gelten bis zur "
          "Rückfahrt. Liegt bei Job 3 keine passende Messung vor (z. B. Arm von Hand in einen Dom "
          "gefahren), nimmt der Vision-PC neu auf und behandelt alles außer dem Arm als "
          "Hindernis. Ist die Kamera nicht verfügbar, meldet Job 3 Fehler 90 – Rückfahrt im "
          "Handbetrieb."),
    ("h2", "3.4. Handshake und Zeitüberwachung"),
    ("li", "SPS setzt Job, ProductId und Istwerte, danach Trigger (nur wenn Ready = TRUE)."),
    ("li", "Vision-PC setzt Busy und löscht Error."),
    ("li", "Vision-PC schreibt alle Ergebniswerte und ResultId in einem Aufruf, danach Done (bei "
           "Fehler zusätzlich Error und ErrorCode) und löscht Busy."),
    ("li", "SPS übernimmt die Werte und löscht Trigger."),
    ("li", "Vision-PC löscht Done."),
    ("p", "Done muss innerhalb von **5 s** nach Trigger kommen, sonst bricht die SPS ab. Job 1 "
          "braucht mit Umwegsuche bis ca. 3 s."),
    ("p", "**Heartbeat:** Beide Seiten prüfen, ob sich der Heartbeat der Gegenseite ändert. "
          "Ausfall länger als **1 s**: Der Vision-PC setzt Ready = FALSE und nimmt keine Aufträge "
          "an; die SPS stoppt die automatische Bewegung und geht in den sicheren Zustand."),
    ("h2", "3.5. Prüfung und Ausführung in der SPS"),
    ("li", "Jeden Stützpunkt gegen die Achsgrenzen prüfen und große Sprünge zwischen "
           "Stützpunkten ablehnen."),
    ("li", "Job 2: Betrag der Korrektur gegen einen Grenzwert prüfen, sonst wiederholen oder "
           "abbrechen."),
    ("li", "**Synchron fahren:** Je Stützpunkt die Fahrzeit der langsamsten Achse bestimmen. "
           "Jede Achse bekommt Geschwindigkeit, Beschleunigung und Verzögerung im Verhältnis zu "
           "ihrem Weg (MOVIKIT Positioning Drive, PA 2–4) und die Zielposition (PA 7/8, "
           "Betriebsart 400). Alle Achsen im selben SPS-Zyklus starten."),
    ("li", "Die Ruckzeit ist auf allen Achsen gleich (nur im Stillstand ändern). Dann haben alle "
           "Achsen dasselbe Fahrprofil und der Arm fährt genau die geprüfte Bahn."),
    ("li", "Am Stützpunkt auf „Position erreicht“ aller Achsen warten. Stützpunkte nach dem "
           "ApproachIndex mit reduzierter Geschwindigkeit (30 %) fahren."),
    ("li", "**Nachziehen beim Befüllen:** Die Eintauch-Stützpunkte aus Job 2 bilden die "
           "Nachzieh-Tabelle. Die SPS fährt sie rückwärts ab und interpoliert dazwischen "
           "linear im Gelenkraum [Höhe je Stützpunkt mit InterfaceVersion 3 vom Vision-PC]."),
    ("h2", "3.6. Fehlercodes"),
    ("table", [1000, 8638], [
        ("0", "kein Fehler"),
        ("11", "Zu wenige Messpunkte im Arbeitsraum (Kamera verschmutzt oder verdeckt?)"),
        ("12", "Tankoberfläche nicht erkannt"),
        ("20", "Keine Domöffnung gefunden (Deckel geschlossen?)"),
        ("21", "Mehrere Domöffnungen gefunden"),
        ("30", "Ziel außerhalb der Reichweite oder der Achsgrenzen, bzw. Eintauchtiefe zu groß "
               "für die Öffnung"),
        ("31", "Kein kollisionsfreier Weg (festes Hindernis, Tankkörper, Domkragen, Deckel oder "
               "eigener Arm im Weg)"),
        ("32", "Istwinkel ungültig oder unplausibel"),
        ("33", "Auslass bzw. Referenzflansch beim Nachmessen nicht erkannt"),
        ("34", "Job 2 ohne vorheriges Ergebnis aus Job 1"),
        ("90", "Interner Fehler Vision-Dienst bzw. Kamera nicht verfügbar"),
        ("91", "Unbekannter Auftrag"),
    ], ("Code", "Bedeutung")),
    ("h2", "3.7. Koordinaten und Winkel"),
    ("p", "Armbasis-Koordinaten in mm: Ursprung auf der Drehachse J1 in Höhe der Rohrmitte des "
          "inneren Auslegers, x nach vorne, y nach links, z nach oben. Winkel in Servo-Grad, so "
          "wie der Antrieb sie meldet; die Umrechnung auf Gelenkwinkel erfolgt im Vision-PC über "
          "Nullstellung und Drehrichtung aus der Anlagendatei."),
    ("h2", "3.8. Versionen der Schnittstelle"),
    ("p", "Jede Änderung erhöht InterfaceVersion und wird mit dem SPS-Programmierer abgestimmt. "
          "Weicht die Version ab, nimmt die SPS keine Ergebnisse an."),
    ("table", [1000, 8638], [
        ("1", "Zielkoordinate, Handshake, Heartbeat"),
        ("2", "Aufträge (Job), Istwinkel von der SPS, Stützpunkte in Servo-Grad, Nachmessen mit "
              "Korrektur, Fehlercodes 30–34 und 91"),
        ("3", "[in Vorbereitung: Nachzieh-Tabelle mit Höhen, Kontrollwerte für die Prüfung in "
              "der SPS]"),
    ], ("Version", "Änderung")),

    # 4 ---------------------------------------------------------------------------------------
    ("h1", "4. SCHNITTSTELLE SPS ↔ LEITSTELLE"),
    ("p", "Am Schaltschrank gibt es kein Display. Auftrag, Produkt und Kalibrierung kommen aus "
          "der Leitstelle; vor Ort wird nur gestartet, quittiert und im Handbetrieb gefahren. "
          "Vorschlag für die Signale [Abstimmung mit dem Betreiber folgt]:"),
    ("table", [4300, 1300, 4038], [
        ("Freigabe Verladung", "PLS → SPS", "Auftrag freigegeben, Start vor Ort möglich"),
        ("Produkt (ProductId), Sollmenge", "PLS → SPS", "bestimmt Eintauchtiefe und Füllende"),
        ("Verladung beenden", "PLS → SPS", "Klappe zu, Abtropfen, Rückfahrt"),
        ("Kalibrierung anstoßen", "PLS → SPS", "startet erst nach Freigabe vor Ort"),
        ("Automatisch in Parkstellung", "PLS → SPS", "nur nach Freigabe vor Ort"),
        ("Zustand (bereit, läuft, Störung, Park)", "SPS → PLS", "entspricht den Leuchtmeldern"),
        ("Menge, Füllstand, Klappe", "SPS → PLS", "laufende Werte"),
        ("Störmeldung mit Code und Text", "SPS → PLS", "Fehlercodes Kapitel 3.6 und SPS-Meldungen"),
        ("Überfüllsicherung ausgelöst", "SPS → PLS", "sofort, unabhängig vom Ablauf"),
    ], ("Signal", "Richtung", "Bedeutung")),
    ("note", "Handbetrieb, Quittieren nach Not-Halt und der Start einer Bewegung sind aus der "
             "Leitstelle nicht möglich."),

    # 5 ---------------------------------------------------------------------------------------
    ("h1", "5. INSTALLATION UND BETRIEB DES VISION-PCS"),
    ("h2", "5.1. Installation"),
    ("p", "Die Software wird von HETA installiert. Das Installationsskript legt Benutzer, "
          "Programm, Konfiguration und Systemdienste an und kann für Updates erneut ausgeführt "
          "werden:"),
    ("code", "sudo deploy/install.sh vision/config/anlagen/<anlage>.yaml"),
    ("table", W2, [
        ("Programm", "/opt/verladearm/venv"),
        ("Konfiguration (Standardwerte + Anlagendatei)", "/etc/verladearm/"),
        ("Aufzeichnungen, Arbeitsdaten", "/var/lib/verladearm/data/"),
        ("Systemdienste", "verladearm-vision (OPC UA zur SPS), verladearm-viewer (Live-Ansicht, "
                          "Port 8000)"),
    ], ("Was", "Wo")),
    ("p", "Beide Dienste starten mit dem PC und nach einem Absturz automatisch neu. Während des "
          "Neustarts fehlt der Heartbeat; die SPS geht in den sicheren Zustand."),
    ("h2", "5.2. Bedienung durch die Instandhaltung"),
    ("table", W2, [
        ("Status", "systemctl status verladearm-vision"),
        ("Protokoll live", "journalctl -u verladearm-vision -f"),
        ("Neu starten", "sudo systemctl restart verladearm-vision verladearm-viewer"),
        ("Live-Ansicht", "Browser: http://<IP des PCs>:8000"),
    ], ("Aufgabe", "Befehl")),
    ("p", "Die **Live-Ansicht** zeigt Punktwolke, erkannten Dom, Arm, Hindernisse und geplante "
          "Bahn. Sie dient der Kontrolle und Fehlersuche, nicht der Bedienung."),
    ("p", "Jeder Auftrag wird mit Punktwolke und Ergebnis **aufgezeichnet** (Nachweis und "
          "Fehlersuche). Die Aufzeichnungen lassen sich auswerten und bei Störungen an HETA "
          "senden."),
    ("h2", "5.3. Update und Datensicherung"),
    ("li", "Updates nur durch HETA. Bei geänderter InterfaceVersion zuerst das SPS-Programm "
           "anpassen."),
    ("li", "Nach jeder Änderung Anlagendatei und Kalibrierung sichern und den Softwarestand im "
           "Wartungsprotokoll eintragen."),
    ("h2", "5.4. IT-Sicherheit"),
    ("li", "Vision-PC, Kamera und SPS nur im internen Anlagennetz betreiben, kein direkter "
           "Zugang aus dem Internet."),
    ("li", "Live-Ansicht und Konfigurator haben keine Anmeldung – nur im internen Netz "
           "freigeben; Konfigurator nur während der Inbetriebnahme starten."),
    ("li", "Benutzerkonten mit eigenen Passwörtern, Fernzugang nur nach Absprache mit dem "
           "Betreiber [Konzept folgt]."),

    # 6 ---------------------------------------------------------------------------------------
    ("h1", "6. INBETRIEBNAHME"),
    ("p", "Jeder Arm hat eigene Maße, Nullstellungen, Verfahrbereiche, Hindernisse und Produkte. "
          "Diese Werte stehen in der **Anlagendatei** und werden vor Ort eingestellt. Erkennung, "
          "Schnittstelle und Standardwerte sind für alle Anlagen gleich."),
    ("h2", "6.1. Werkzeuge"),
    ("table", W2b, [
        ("Konfigurator (Browser)", "alle Abschnitte der Anlagendatei auf einer Seite mit "
         "Plausibilitätsprüfung, Draufsicht und Seitenansicht, Hindernisse in der Vorschau "
         "verschieben, Servowerte per Knopf aus der SPS übernehmen, Inbetriebnahmeprüfung auf "
         "Knopfdruck."),
        ("Einrichtungsdialog (Kommandozeile)", "führt Schritt für Schritt durch die Werte und "
         "liest Nullstellung, Drehrichtung und Parkstellung aus der SPS."),
        ("Inbetriebnahmeprüfung", "rechnet alle Domlagen im Arbeitsraum durch und erstellt ein "
         "Protokoll."),
        ("Simulation", "SPS, Kamera und Arm ohne Hardware, zum Test von Ablauf und Bahnen."),
    ], ("Werkzeug", "Zweck")),
    ("code", "python -m verladearm_vision.konfigurator --host 0.0.0.0 --port 8090",
     "python -m verladearm_vision.einrichtung --name <anlage> --from-plc"),
    ("h2", "6.2. Maße aufnehmen"),
    ("p", "Von Gelenkachse zu Gelenkachse bzw. Rohrmitte zu Rohrmitte messen, in Metern, nie "
          "Außenkanten. Bei 90°-Winkeln zählt der Schnittpunkt der Rohrmittellinien."),
    ("table", W2b, [
        ("flange_height", "Fahrbahn bis Oberkante Schnittstellenflansch am Eintritt J1"),
        ("flange_offset", "Oberkante Flansch bis Rohrmitte innerer Ausleger auf Achse J1"),
        ("inner_length", "Achse J1 bis Mitte Winkel nach unten"),
        ("drop", "Winkel nach unten bis Mitte Winkel nach rechts"),
        ("offset_right", "Winkel nach rechts bis Mitte Winkel nach vorne"),
        ("outer_length", "Winkel nach vorne bis Mitte Winkel nach links"),
        ("offset_left", "Winkel nach links bis Mitte Winkel nach unten (Gelenk J4)"),
        ("outlet_length", "Winkel nach unten bis Auslassende"),
        ("incline_deg", "festes Gefälle des inneren Auslegers"),
        ("feed_length", "sichtbare Fallleitung über dem Flansch (festes Hindernis)"),
        ("pipe_diameter", "Außendurchmesser der Auslegerrohre"),
    ], ("Parameter", "Strecke")),
    ("h2", "6.3. Achsen einstellen"),
    ("li", "**Nullstellung:** Beide Ausleger gestreckt nach vorne, äußerer Ausleger waagerecht "
           "(Wasserwaage). Servowerte J1, J2, J3 übernehmen."),
    ("li", "**Drehrichtung:** Jede Achse ein Stück positiv fahren. Dreht J1/J2 von oben gesehen "
           "gegen den Uhrzeigersinn bzw. hebt J3 den Ausleger: +1, sonst −1."),
    ("li", "**Verfahrbereich:** freigegebener Bereich je Achse (nicht die mechanischen "
           "Anschläge); J1/J2 innerhalb des verzahnten Bereichs."),
    ("li", "**Parkstellung:** Servowerte der zusammengefalteten Stellung."),
    ("h2", "6.4. Hindernisse, Produkte, Referenz, Arbeitsraum"),
    ("li", "**Feste Hindernisse** (Stützen, Bühne, Geländer, Klapptreppe) als Quader oder "
           "Zylinder großzügig erfassen. Fahrzeug und offener Deckel werden bei jeder Messung "
           "erkannt. Mindestabstand zur Rohrachse standardmäßig 0,15 m; der Arm wird zusätzlich "
           "gegen sich selbst geprüft."),
    ("li", "**Produkte:** Eintauchtiefe je ProductId. Grenze: Der Referenzflansch am Auslass "
           "(Ø 220 mm, 0,82 m über dem Auslassende) muss durch die Öffnung passen."),
    ("li", "**Referenz am Auslass:** vorhandener Flansch Ø 220 mm, Oberkante 823 mm über dem "
           "untersten Punkt des Auslasses; rund, mittig und rechtwinklig zum Rohr."),
    ("li", "**Arbeitsraum:** Bereich, in dem Dome vorkommen (Fahrspur, Haltemarke, "
           "Haltetoleranz, Domhöhe niedrigstes/höchstes Fahrzeug). Nur für Prüfung und "
           "Kalibrierung."),
    ("h2", "6.5. Prüfen und abschließen"),
    ("li", "Kalibrierung durchführen (Kapitel 7)."),
    ("li", "Inbetriebnahmeprüfung ausführen und Protokoll ablegen: Parameter, Parkstellung und "
           "für jede Domlage Anfahrt und Eintauchen mit der größten Eintauchtiefe."),
    ("code", "python -m verladearm_vision.commissioning --config <anlage>.yaml > protokoll.md"),
    ("li", "In der Live-Ansicht Rohrführung, Hindernisse und Servowerte mit der realen Anlage "
           "vergleichen."),
    ("li", "Abgleich mit der SPS: Achsgrenzen, Nullstellungen, Drehrichtungen und Parkstellung "
           "müssen im SPS-Programm denselben Werten entsprechen."),
    ("li", "Probeläufe ohne Produkt an stehenden Fahrzeugen, danach Autostart einrichten "
           "(Kapitel 5.1)."),
    ("note", "Die Inbetriebnahmeprüfung ersetzt keine Sicherheitsfunktion. Verfahrbereiche, "
             "Endlagen und Schutzbereiche werden zusätzlich in der SPS überwacht."),

    # 7 ---------------------------------------------------------------------------------------
    ("h1", "7. KALIBRIERUNG KAMERA ↔ ARM"),
    ("p", "Die Kalibrierung bestimmt die Lage der Kamera relativ zur Armbasis. Sie ist nötig bei "
          "der Inbetriebnahme und immer, wenn die Kamera versetzt, getauscht oder ihre Halterung "
          "verändert wurde."),
    ("h2", "7.1. Prinzip"),
    ("p", "Der Arm fährt den Referenzflansch am Auslass an 10 Stellen im Arbeitsraum. Je "
          "Stellung gibt es zwei Angaben für denselben Punkt: aus den Istwinkeln über die "
          "Kinematik und aus der Punktwolke der Kamera. Aus den Punktpaaren folgt die beste "
          "Drehung und Verschiebung; die Restfehler zeigen, wie gut Kinematik und Messung "
          "zusammenpassen."),
    ("h2", "7.2. Voraussetzungen"),
    ("li", "Anlagendatei mit Maßen, Nullstellungen und Drehrichtungen (Kapitel 6)."),
    ("li", "Grobe Anfangsschätzung der Kameralage, mit Maßband oder Laser auf ca. 10 cm und 5° "
           "genau."),
    ("li", "Stellplatz leer (kein Fahrzeug), Bewegungsbereich frei."),
    ("h2", "7.3. Ablauf"),
    ("code", "python -m verladearm_vision.calibrate --config <anlage>.yaml --from-plc"),
    ("li", "Das Werkzeug schlägt 10 Stellungen vor (Ecken und Mitte des Arbeitsraums, zwei "
           "Höhen)."),
    ("li", "Arm in die Stellung fahren, Auslass auspendeln lassen, bestätigen. Die Istwinkel "
           "werden aus der SPS gelesen (nur lesend)."),
    ("li", "Nach allen Stellungen werden Ergebnis, Restfehler je Stellung und Hinweise "
           "ausgegeben und als Protokoll gespeichert."),
    ("li", "Ergebnis in die Anlagendatei übernehmen, Dienste neu starten, Inbetriebnahmeprüfung "
           "wiederholen."),
    ("p", "[Ausbaustufe: Die Leitstelle stößt die Kalibrierung an, nach Freigabe vor Ort fährt "
          "der Arm die Stellungen automatisch an – Umsetzung in SPS und Software folgt.]"),
    ("h2", "7.4. Bewertung"),
    ("table", W2b, [
        ("unter 5 mm", "gut"),
        ("5 bis 10 mm", "brauchbar; das Nachmessen vor dem Eintauchen gleicht den Rest aus"),
        ("über 10 mm", "Maße, Nullstellungen, Drehrichtungen oder Pendeln prüfen"),
    ], ("Restfehler (Mittel)", "Bewertung")),
    ("p", "Einzelne Ausreißer deuten auf einen nicht ausgependelten Auslass oder eine Verdeckung "
          "hin: Stellung wiederholen. Ein großer gleichmäßiger Restfehler deutet auf falsche "
          "Armmaße hin."),
    ("p", "Getriebespiel und Durchbiegung wechseln mit der Stellung und lassen sich nicht "
          "wegkalibrieren. Dafür misst der Vision-PC vor jedem Eintauchen die Lage des Auslasses "
          "über dem Dom nach (Job 2)."),

    # 8 ---------------------------------------------------------------------------------------
    ("h1", "8. MITGELTENDE UNTERLAGEN"),
    ("li", "Betriebsanleitung OMIM-4793."),
    ("li", "SPS-Datenbaustein DB_Vision (Quelle zur Schnittstelle)."),
    ("li", "Stromlauf- und Klemmenplan [Nummer folgt]."),
    ("li", "SEW: Handbuch MOVIKIT Positioning Drive (33350930), MOVITRAC advanced."),
    ("li", "SICK: 3D-Kamera Visionary-T Mini."),
    ("li", "Protokolle der Inbetriebnahmeprüfung und der Kalibrierung."),
]
