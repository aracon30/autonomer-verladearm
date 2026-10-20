"""Inhalt der überarbeiteten Betriebsanleitung OMIM-4793 (autonomer Verladearm).

Blöcke: ("h1"|"h2"|"p"|"sub"|"li", text), ("note", text, …), ("warn", Stufe, Titel, Folge,
[Maßnahmen]), ("table", Spaltenbreiten, Zeilen, Kopfzeile), ("keep", Index aus der Vorlage).
**fett**, [offene Punkte] werden gelb markiert.
"""

W2 = [3600, 6038]
W2b = [2900, 6738]

BLOCKS = [
    # 1 ---------------------------------------------------------------------------------------
    ("h1", "1. ZWECK UND GELTUNGSBEREICH"),
    ("p", "Diese Betriebsanleitung beschreibt den sicheren Umgang mit dem autonomen Obenverladearm "
          "mit elektrischen Antrieben gemäß HETA-Zeichnung **00028433** einschließlich "
          "Schaltschrank, Steuerung, 3D-Kamera, Vision-PC mit Software und der Schnittstelle zur "
          "Leitstelle des Betreibers."),
    ("p", "Der Verladearm fährt nach Freigabe durch die Leitstelle und Start durch den Bediener "
          "selbstständig über die Domöffnung des Fahrzeugs, taucht ein, wird während der "
          "Befüllung nachgezogen und fährt danach in die Parkstellung zurück."),
    ("p", "Die Anleitung gilt für Transport, Montage, Inbetriebnahme, Betrieb, Inspektion, "
          "Wartung, Störungsbehandlung und Außerbetriebnahme des Verladearms. Sie ersetzt nicht "
          "die Betriebsanweisungen der Gesamt-Verladeanlage oder die Herstellerunterlagen der "
          "Zukaufteile (Servomotoren, Getriebe, Schwenkantrieb, Frequenzumrichter, Kamera, "
          "Industrie-PC, SPS, Sensorik)."),
    ("keep", 11), ("keep", 12), ("keep", 13), ("keep", 14),
    ("h2", "1.2. Konformität"),
    ("p", "Der Verladearm einschließlich Schaltschrank, Steuerung und Software ist als Maschine "
          "im Sinne der **Verordnung (EU) 2023/1230 (Maschinenverordnung)** ausgeführt und trägt "
          "die CE-Kennzeichnung. Die EU-Konformitätserklärung liegt der Lieferung bei."),
    ("p", "Angewandte Normen (Auswahl): EN ISO 12100 (Risikobeurteilung), EN ISO 13849-1/-2 "
          "(sicherheitsbezogene Teile der Steuerung), EN 60204-1 (elektrische Ausrüstung), "
          "EN 61800-5-2 (sichere Antriebsfunktionen, STO). [Liste und Performance Level je "
          "Sicherheitsfunktion folgen aus der Risikobeurteilung]"),
    ("p", "Die Software des Verladearms lernt im Betrieb nicht selbstständig; sie hat kein "
          "selbstentwickelndes Verhalten im Sinne von Anhang I Teil A der Maschinenverordnung. "
          "Sicherheitsfunktionen (Not-Halt, STO, Verriegelungen, Überfüllsicherung) liegen in der "
          "SPS bzw. in der Hardware, nicht im Vision-PC."),
    ("p", "Der Verladearm ist nicht für den Einsatz in explosionsgefährdeten Bereichen ausgelegt "
          "und darf nicht in Ex-Zonen aufgestellt oder betrieben werden."),
    ("h2", "1.3. Aufbewahrung der Anleitung"),
    ("p", "Diese Betriebsanleitung ist Bestandteil des Verladearms. Sie ist während der gesamten "
          "Lebensdauer in der Nähe des Verladearms aufzubewahren und muss dem Bedien-, Leitstand- "
          "und Wartungspersonal jederzeit zugänglich sein. Bei Weitergabe des Verladearms ist die "
          "Anleitung mitzugeben."),
    ("p", "Wird die Anleitung digital bereitgestellt, stellt HETA auf Anfrage beim Kauf oder "
          "innerhalb von sechs Monaten danach kostenlos eine Papierfassung zur Verfügung "
          "(Maschinenverordnung, Anhang III Nr. 1.7.4)."),
    ("keep", 20), ("keep", 21), ("keep", 22),
    ("h2", "1.5. Softwarestand"),
    ("p", "Diese Anleitung gilt für folgenden Stand. Nach jeder Änderung von Software oder "
          "Anlagendaten ist der Stand im Wartungsprotokoll festzuhalten."),
    ("table", W2, [
        ("Vision-Software", "[Version folgt]"),
        ("SPS-Programm", "[Version folgt]"),
        ("Anlagendatei (Achsdaten, Parkstellung, Hindernisse)", "[Name / Datum folgt]"),
        ("Kalibrierung Kamera ↔ Arm", "[Datum folgt]"),
    ]),

    # 2 ---------------------------------------------------------------------------------------
    ("h1", "2. TECHNISCHE DATEN"),
    ("sub", "Verladearm"),
    ("table", W2, [
        ("Bezeichnung", "Autonomer Obenverladearm mit elektrischen Antrieben"),
        ("Werksnummer / Zeichnung", "4793-01 / 00028433"),
        ("Nennweite", "DN 100"),
        ("Medium", "Polymerdispersion, flüssig"),
        ("Dichte", "ca. 1.100 kg/m³"),
        ("Betriebsdruck PS", "1 bis 4 bar"),
        ("Prüfdruck PT", "15 bar"),
        ("Auslegungstemperatur", "10 bis 180 °C"),
        ("Umgebungstemperatur", "−20 bis +40 °C [Getriebe J1/J2 laut Datenblatt ab −15 °C – "
                                "klären]"),
        ("Volumen", "68 l"),
        ("Gewicht leer / gefüllt", "[folgt – mit Antrieben J1/J2 und Zahnkränzen neu ermitteln]"),
        ("Gesamtausladung", "ca. 5,5 m"),
        ("Achsen", "J1 Drehen am Haltepunkt, J2 Drehen am Fallrohr, J3 Heben / Senken "
                   "Ausleger; Auslass hängt frei (Drehgelenk J4)"),
        ("Bewegungsbereich", "J1 −120 … +120°, J2 −140 … +140°, J3 −45 … +45° (Software-"
                             "Endlagen; J1/J2 durch die Öffnung im Zahnkranz begrenzt)"),
        ("Geschwindigkeit", "max. 6 °/s je Gelenk, Eintauchen und Herausfahren 30 %, "
                            "Handbetrieb ca. 20 %"),
        ("Geräuschemission", "A-bewerteter Emissionsschalldruckpegel am Bedienplatz < 70 dB(A) "
                             "[mit neuen Antrieben bestätigen]"),
        ("Windgrenze Automatikbetrieb", "[folgt]"),
        ("Einsatzbereich", "Nicht explosionsgefährdeter Bereich (keine Ex-Zone), im Freien"),
    ]),
    ("sub", "Antriebe"),
    ("table", [1700, 2646, 2646, 2646], [
        ("Motor", "SEW CM3C71S, Synchron-Servomotor, 400 V, M0 6,5 Nm",
         "wie J1", "SEW DRN80M4, 0,75 kW, 400 V"),
        ("Getriebe", "Planetengetriebe P5KG31 i = 4 + Ritzel z 48 / Zahnkranz z 127 "
                     "(gesamt i = 10,6)", "wie J1",
         "Stirnradgetriebe RF47 i = 42,87 + Schwenkantrieb IMO WD-E 0223/3 i = 34 "
         "(gesamt i = 1 457,6)"),
        ("Bremse", "BK1, 24 V DC, 16 Nm", "wie J1", "BE05, 230 V AC, 1,8 Nm"),
        ("Geber", "AZ2Z Multiturn-Absolutwertgeber, MOVILINK DDI", "wie J1",
         "AK8Z Multiturn-Absolutwertgeber, MOVILINK DDI"),
        ("Umrichter", "SEW MOVITRAC advanced MCX91A-0040, PROFINET, STO", "wie J1",
         "SEW MOVITRAC advanced MCX91A-0025, PROFINET, STO"),
        ("Selbsthemmung", "nein – Haltebremse erforderlich", "nein",
         "nicht zugesichert – Bremse nie lüften"),
    ], ("", "J1", "J2", "J3")),
    ("sub", "Schaltschrank, Steuerung und Sensorik"),
    ("table", W2, [
        ("Elektrischer Anschluss", "400 V AC, 3~ (3P + N + PE), 50 Hz"),
        ("Bemessungsstrom / Netzstecker", "[folgt – 3 Umrichter, SPS, PC]"),
        ("Bauseitige Absicherung", "[folgt]; FI-Schutzschalter falls vorhanden allstromsensitiv "
                                   "(Typ B)"),
        ("Schaltschrank", "[Typ und Abmessungen folgen]"),
        ("Steuerung", "Siemens SIMATIC S7-1500 [Typ / F-CPU folgt]"),
        ("Vision-PC", "Siemens Industrie-PC, Linux, Vision-Software HETA [Typ folgt]"),
        ("3D-Kamera", "SICK Visionary-T Mini CX, über der Verladestelle [Typ bestätigen]"),
        ("Antriebsregelung", "3 × SEW MOVITRAC advanced mit MOVIKIT Positioning Drive, "
                             "Einkabeltechnik MOVILINK DDI, Bremswiderstände [folgt]"),
        ("Bedienung vor Ort", "Leuchttaster „Beladen starten“, Not-Halt, Taster „Quittieren“, "
                              "Schlüsselschalter Automatik / Hand, Leuchtmelder (bereit / läuft / "
                              "Störung), Anschluss für Handbediengerät"),
        ("Handbediengerät", "steckbar, mit 3-stufigem Zustimmtaster, Not-Halt, Achswahl "
                            "J1 / J2 / J3 und Tasten + / − [Typ folgt]"),
        ("Leitstelle", "Freigabe, Produkt, Sollmenge, Kalibrierung, Meldungen über "
                       "[Schnittstelle zum PLS folgt]"),
        ("Sensorik Bewegung", "Multiturn-Absolutwertgeber je Achse, Software-Endlagen, "
                              "[Endlagenschalter folgen], [induktiver Hindernissensor an der "
                              "Lanze – beibehalten?], Lichtschranke Stellplatz, Rückmeldung "
                              "Klapptreppe „Ruhelage“"),
        ("Sensorik Füllstand", "Messstab (geführte Mikrowelle) an der Lanze, Durchflusssensor "
                               "[Typen folgen]"),
        ("Überfüllsicherung", "Grenzschalter an aufliegender Lanze mit fester Länge unter dem "
                              "Domrand, wirkt direkt auf die Absperrklappe [Typ und Zulassung "
                              "folgen, z. B. SICK LFV 200]"),
        ("Absperrklappe", "DN 100 mit Antrieb und Stellungsrückmeldung [Typ folgt]"),
        ("Stromlaufplan", "[Nummer folgt]"),
    ]),

    # 3 ---------------------------------------------------------------------------------------
    ("h1", "3. AUFBAU UND FUNKTION"),
    ("p", "Der Obenverladearm bildet eine bewegliche Verbindung zwischen der stationären "
          "Produktleitung und dem zu befüllenden Fahrzeug. Er hat drei angetriebene Achsen: "
          "**J1** dreht den inneren Ausleger am Haltepunkt, **J2** dreht den äußeren Ausleger am "
          "Fallrohr, **J3** hebt und senkt den äußeren Ausleger. Der Auslass hängt frei "
          "(Drehgelenk J4) und zeigt immer senkrecht nach unten. In der Parkstellung ist der Arm "
          "zusammengefaltet."),
    ("sub", "Mechanik"),
    ("li", "J1 und J2: Servomotor mit Planetengetriebe und Ritzel auf Zahnkranz, Haltebremse am "
           "Motor. Die Zahnradstufe ist nicht selbsthemmend."),
    ("li", "J3: Getriebemotor RF47 mit Schwenkantrieb (Schnecke), Haltebremse am Motor. Die "
           "Selbsthemmung der Schnecke ist nicht zugesichert."),
    ("li", "Bei Stromausfall, Not-Halt oder Abschalten über den Hauptschalter fallen alle "
           "Bremsen ein; der Arm bleibt in seiner Position stehen."),
    ("li", "Mehrere 4\"-Drehgelenke, Produktleitung DN 100 mit Einlass N1 und Auslass N2."),
    ("li", "Lanze am Auslass mit Messstab (Füllstand) und aufliegender Lanze für die "
           "Überfüllsicherung."),
    ("sub", "Steuerung und Sensorik"),
    ("li", "**SPS:** steuert den Ablauf, fährt die Achsen, prüft jede Vorgabe des Vision-PCs und "
           "überwacht Not-Halt, Verriegelungen, Füllstand und Überfüllsicherung."),
    ("li", "**Vision-PC mit 3D-Kamera:** misst Domöffnung, Deckel und Aufbauten des Fahrzeugs und "
           "berechnet eine kollisionsfreie Bahn. Er gibt nur Vorschläge; die SPS entscheidet."),
    ("li", "**Umrichter:** positionieren jede Achse; die SPS gibt Ziel, Geschwindigkeit und "
           "Beschleunigung so vor, dass alle Achsen gleichzeitig ankommen. Die Multiturngeber "
           "behalten die Lage auch ohne Spannung – eine Referenzfahrt ist nicht nötig."),
    ("li", "**Leitstelle:** gibt den Auftrag frei, wählt Produkt und Sollmenge, stößt die "
           "Kalibrierung an und erhält alle Meldungen. Aus der Leitstelle kann der Arm nicht "
           "von Hand verfahren werden."),
    ("li", "**Bedienung vor Ort:** Start-Taster, Not-Halt, Quittieren, Schlüsselschalter "
           "Automatik / Hand, Leuchtmelder und Handbediengerät."),
    ("sub", "Ablauf einer Verladung (Automatik)"),
    ("li", "Fahrzeug steht, ist geerdet, Dom ist geöffnet, Klapptreppe in Ruhelage, niemand auf "
           "dem Fahrzeug. Die Leitstelle gibt den Auftrag mit Produkt frei."),
    ("li", "Der Bediener drückt „Beladen starten“."),
    ("li", "Die Kamera misst den Dom, der Arm fährt über die Öffnung, misst die Lage des "
           "Auslasses nach und taucht senkrecht ein."),
    ("li", "Die Absperrklappe öffnet. Steigt der Füllstand, zieht die SPS den Arm senkrecht nach, "
           "sodass der Auslass knapp unter der Oberfläche bleibt."),
    ("li", "Ist die Sollmenge erreicht, schließt die Klappe. Nach einer Abtropfpause fährt der "
           "Arm senkrecht heraus und in die Parkstellung. Die grüne Leuchte zeigt: Fahrzeug darf "
           "wegfahren."),
    ("p", "Im **Handbetrieb** bewegt sich eine Achse nur, solange Zustimmtaster und +/− am "
          "Handbediengerät gedrückt sind (Tippbetrieb, reduzierte Geschwindigkeit)."),

    # 4 ---------------------------------------------------------------------------------------
    ("h1", "4. SICHERHEITSMASSNAHMEN"),
    ("keep", 45), ("keep", 46), ("keep", 47), ("keep", 48), ("keep", 49), ("keep", 50),
    ("h2", "4.2. Bestimmungsgemäße Verwendung"),
    ("p", "Die Verladeeinrichtung ist ein elektrisch angetriebenes, automatisch arbeitendes "
          "Verladesystem zur Befüllung von Tankwagen und Kesselwagen von oben durch die "
          "vorgesehene Domöffnung."),
    ("keep", 53), ("keep", 54), ("keep", 55), ("keep", 56),
    ("li", "der Betrieb nur mit wirksamer Überfüllsicherung, Lichtschranke und Verriegelung der "
           "Klapptreppe,"),
    ("li", "der Start jeder Verladung vor Ort mit Sicht auf den Arm."),
    ("keep", 57),
    ("h2", "4.3. Missbräuchliche Verwendung"),
    ("keep", 59),
    ("li", "Start einer Verladung oder Verfahren des Arms aus der Ferne ohne Sicht auf den "
           "Bewegungsbereich."),
    ("li", "Betrieb mit Personen auf dem Fahrzeug oder der Klapptreppe während der Automatik."),
    ("li", "Überbrücken von Verriegelungen, Überfüllsicherung oder Lichtschranke."),
    ("li", "Ändern von Software, Anlagendaten oder Kalibrierung ohne Freigabe durch HETA."),
    ("h2", "4.4. Personal und Qualifikation"),
    ("table", W2b, [
        ("Bedienung vor Ort", "Vom Betreiber unterwiesenes Bedienpersonal, das diese Anleitung "
                              "gelesen und verstanden hat."),
        ("Leitstand", "Unterwiesenes Leitstandpersonal (Freigabe, Produkt, Sollmenge, "
                      "Kalibrierung anstoßen, Meldungen)."),
        ("Handbetrieb", "Bedienpersonal mit Schlüsselberechtigung und Unterweisung im "
                        "Handbetrieb."),
        ("Montage, Inbetriebnahme, mechanische Arbeiten", "Fachpersonal mit Ausbildung in "
                                                          "Mechanik/Anlagenbau."),
        ("Elektrische Arbeiten", "Elektrofachkraft nach DGUV Vorschrift 3 / DIN VDE 1000-10."),
        ("Software, Kalibrierung, Anlagendaten", "Fachpersonal der HETA Verfahrenstechnik GmbH."),
        ("Wartung", "Fachpersonal der HETA Verfahrenstechnik GmbH (siehe Kapitel 10)."),
    ], ("Tätigkeit", "Qualifikation")),
    ("keep", 63),
    ("keep", 64), ("keep", 65), ("keep", 66), ("keep", 67), ("keep", 68), ("keep", 69),
    ("keep", 70),
    ("h2", "4.6. Restrisiken"),
    ("keep", 72),
    ("table", W2b, [
        ("Selbsttätige Bewegung des Arms nach dem Start", "Start nur vor Ort mit Sicht auf den "
         "Arm; Klapptreppe und Lichtschranke verriegelt; Not-Halt am Schaltschrank und am "
         "Handbediengerät; niemand im Bewegungsbereich und auf dem Fahrzeug."),
        ("Kamera erkennt ein Hindernis nicht (verdeckt, spiegelnd, Regen, Schnee, Gegenlicht)",
         "Vor dem Start Bereich und Domumgebung prüfen; Kamerafenster sauber halten; bei "
         "Störung der Messung bricht die SPS ab."),
        ("Quetschen, Scheren, Stoß im Handbetrieb", "Tippbetrieb mit Zustimmtaster, reduzierte "
         "Geschwindigkeit, Bediener mit Sicht auf den Arm."),
        ("Absacken des Auslegers (J3)", "Bremse J3 nie lüften; Arbeiten unter dem Ausleger nur "
         "mit mechanischer Sicherung."),
        ("Wegdrehen J1/J2 durch Wind bei gelüfteter Bremse", "Bremse nur im Handbetrieb lüften, "
         "Arm festhalten; Windgrenze beachten."),
        ("Überfüllung des Fahrzeugs", "Unabhängige Überfüllsicherung schließt die Absperrklappe "
         "direkt; Funktion regelmäßig prüfen."),
        ("Manipulation von Software oder Netzwerk", "Vision-PC und SPS nur im internen Netz, "
         "Zugänge passwortgeschützt, Änderungen nur durch HETA."),
        ("Elektrischer Schlag", "Arbeiten nur durch Elektrofachkraft, Freischalten, Restspannung "
         "an den Frequenzumrichtern abwarten [Zeit laut SEW folgt]."),
        ("Produktaustritt, Kontakt mit dem Medium", "Dichtheit prüfen, Schutzausrüstung tragen, "
         "Sicherheitsdatenblatt beachten."),
        ("Heiße Oberflächen an der Produktleitung (je nach Produkttemperatur)",
         "Schutzhandschuhe tragen, Leitungen nicht ohne Schutz berühren."),
        ("Stolpern über Kabel", "Leitungen außerhalb der Verkehrswege verlegen, "
         "Handbediengerät nach Gebrauch abziehen und verwahren."),
        ("Elektrostatische Aufladung", "Tankwagen vor dem Verladen nach Betreibervorschrift "
         "erden."),
    ], ("Gefährdung", "Maßnahme")),
    ("h2", "4.7. Schutzeinrichtungen und Kennzeichnung"),
    ("keep", 76),
    ("li", "Not-Halt am Schaltschrank und am Handbediengerät"),
    ("li", "Sicher abgeschaltetes Moment (STO) an allen drei Umrichtern"),
    ("li", "Haltebremsen an allen drei Antrieben"),
    ("li", "Zustimmtaster am Handbediengerät, Schlüsselschalter Automatik / Hand"),
    ("li", "Software-Endlagen je Achse [Endlagenschalter folgen]"),
    ("li", "Verriegelung Klapptreppe („Ruhelage“) und Lichtschranke Stellplatz"),
    ("li", "Überwachung der Verbindung Vision-PC ↔ SPS (Heartbeat), Plausibilitätsprüfung jeder "
           "Bahn in der SPS"),
    ("li", "Überfüllsicherung mit direkter Wirkung auf die Absperrklappe"),
    ("li", "[Induktiver Hindernissensor an der Lanze – falls beibehalten]"),
    ("keep", 83),

    # 5 ---------------------------------------------------------------------------------------
    ("h1", "5. ZUSÄTZLICHE SICHERHEITS- UND NOTFALLHINWEISE"),
    ("keep", 85),
    ("warn", "GEFAHR", "Gefährliche elektrische Spannung im Schaltschrank",
     "Tod oder schwere Verletzung durch elektrischen Schlag. An den Frequenzumrichtern liegt "
     "nach dem Abschalten noch gefährliche Spannung an [Zeit laut SEW folgt].",
     ["Arbeiten am Schaltschrank nur durch Elektrofachkraft.",
      "Hauptschalter auf „0“, gegen Wiedereinschalten sichern.",
      "Wartezeit einhalten und Spannungsfreiheit feststellen."]),
    ("warn", "WARNUNG", "Selbsttätige Bewegung des Verladearms",
     "Nach dem Start bewegt sich der Arm ohne weitere Betätigung über das Fahrzeug, taucht ein "
     "und fährt zurück. Schwere Verletzungen an Kopf, Händen und Körper.",
     ["Vor dem Start sicherstellen, dass sich niemand im Bewegungsbereich oder auf dem Fahrzeug "
      "befindet.", "Start nur vor Ort mit Sicht auf den Arm.",
      "Bei Gefahr sofort Not-Halt betätigen."]),
    ("warn", "WARNUNG", "Ausleger sackt ab (J3)",
     "Die Last hängt an der Schnecke, deren Selbsthemmung nicht zugesichert ist. Wird die Bremse "
     "J3 gelüftet, kann der Ausleger herabfallen.",
     ["Bremse J3 nie lüften – J3 im Handbetrieb nur tippen.",
      "Arbeiten unter dem Ausleger nur mit mechanischer Sicherung."]),
    ("warn", "WARNUNG", "Unbeabsichtigte Bewegung bei Wartungs-, Reparatur- oder "
     "Einstellarbeiten", "Schwere Verletzungen, Produktaustritt.",
     ["Verladearm drucklos setzen, entleeren und mechanisch sichern.",
      "Anlage elektrisch freischalten und gegen Wiedereinschalten sichern.",
      "Leitstelle informieren; Freigaben aus der Leitstelle sperren."]),
    ("warn", "WARNUNG", "Kamera erkennt nicht jedes Hindernis",
     "Verdeckte, sehr dünne oder spiegelnde Gegenstände und Personen werden unter Umständen "
     "nicht erkannt. Schwere Verletzungen und Sachschäden.",
     ["Bereich und Domumgebung vor jedem Start selbst einsehen.",
      "Kamera nicht als alleinige Schutzmaßnahme ansehen."]),
    ("warn", "VORSICHT", "Heiße Oberflächen und Kontakt mit dem Medium",
     "Verbrennungen, Haut- und Augenreizungen je nach Produkt und Produkttemperatur.",
     ["Schutzhandschuhe und Schutzbrille tragen.", "Sicherheitsdatenblatt des Mediums "
      "beachten."]),
    ("li", "Bei Gefahr den Not-Halt am Schaltschrank oder am Handbediengerät betätigen. Alle "
           "Antriebe werden stillgesetzt (STO), die Bremsen halten den Arm, die Absperrklappe "
           "schließt."),
    ("li", "Nach einem Not-Halt erst die Ursache beseitigen. Anschließend den Not-Halt "
           "entriegeln und vor Ort mit „Quittieren“ zurücksetzen. Ein Quittieren aus der "
           "Leitstelle ist nicht möglich."),
    ("keep", 115), ("keep", 116),
    ("li", "Not-Halt-, Verriegelungs-, Füllstands- und Überfüllsignale dürfen nicht überbrückt, "
           "verstellt oder entfernt werden."),
    ("li", "Änderungen an Arm, Antrieb, Sensorik, Steuerung, Software oder Anlagendaten sind nur "
           "nach dokumentierter Freigabe durch HETA zulässig."),

    # 6 ---------------------------------------------------------------------------------------
    ("h1", "6. STÖRUNGEN UND ABHILFEMASSNAHMEN"),
    ("sub", "Leuchtmelder am Schaltschrank"),
    ("table", W2b, [
        ("Grün", "Arm in Parkstellung, bereit; Fahrzeug darf fahren."),
        ("Gelb", "Automatik läuft (Arm bewegt sich oder befüllt)."),
        ("Rot", "Störung – Meldung in der Leitstelle beachten."),
    ], ("Anzeige", "Bedeutung [Farben mit Schaltschrankbauer festlegen]")),
    ("table", W2b, [
        ("Leckage", "Produktzufuhr stoppen, Anlage absperren und drucklos setzen. Nicht weiter "
                    "betreiben."),
        ("Start nicht möglich", "Voraussetzungen prüfen: Automatik gewählt, Arm in "
         "Parkstellung, Klapptreppe in Ruhelage, Lichtschranke belegt, Freigabe der Leitstelle, "
         "Vision-PC bereit, kein Not-Halt."),
        ("Domöffnung nicht erkannt / mehrere Öffnungen", "Fahrzeugstellung und Dom prüfen "
         "(geöffnet, frei), Kamerafenster reinigen, erneut starten."),
        ("Bahn nicht erreichbar oder Kollision gemeldet", "Fahrzeug anders stellen oder Hindernis "
         "beseitigen. Bleibt die Meldung, Verladung von Hand nach Betreiberverfahren."),
        ("Auslass beim Nachmessen nicht gefunden", "Arm fährt zurück. Markierung bzw. Flansch am "
         "Auslass und Kamerafenster prüfen."),
        ("Verbindung Vision-PC gestört / Kamera nicht verfügbar", "Bewegung stoppt. Arm im "
         "Handbetrieb in die Parkstellung fahren; HETA informieren."),
        ("Lichtschranke frei oder Klapptreppe nicht in Ruhelage während der Automatik",
         "Bewegung stoppt sofort. Ursache klären, dann „Automatisch in Parkstellung“ oder "
         "Handbetrieb."),
        ("Überfüllsicherung ausgelöst", "Absperrklappe ist zu. Füllstand prüfen, Ursache klären "
         "(z. B. Durchflusssensor). Arm erst danach zurückfahren."),
        ("Nachziehen am oberen Ende angekommen", "Absperrklappe ist zu. Sollmenge und "
         "Fahrzeugdaten prüfen."),
        ("Antrieb bewegt nicht", "Keine Gewalt anwenden. Hauptschalter, Not-Halt, Betriebsart, "
         "Meldung am Umrichter und Blockaden prüfen."),
        ("Fehleranzeige am Frequenzumrichter", "Fehlercode gemäß Betriebsanleitung SEW "
         "MOVITRAC advanced auswerten, nur durch Elektrofachkraft."),
        ("Arm steht nach Störung im Dom", "Wenn möglich „Automatisch in Parkstellung“ (Arm fährt "
         "erst senkrecht heraus). Sonst Handbetrieb: zuerst J3 heben, dann J1/J2 schwenken."),
        ("Geräusche oder ruckartige Bewegung", "Bewegung stoppen, Arm sichern und Getriebe, "
         "Zahnkränze, Befestigungen sowie Drehgelenke prüfen."),
        ("Füllstandssignal fehlerhaft", "Verladung nicht starten bzw. sofort stoppen. Sensorik "
         "und Signalkette prüfen."),
        ("Stromausfall", "Bremsen halten den Arm, Absperrklappe schließt. Die Geber behalten die "
         "Lage. Wiederanlauf erst nach kontrollierter Anlagenfreigabe und Quittieren."),
    ], ("Störung", "Maßnahme")),

    # 7 ---------------------------------------------------------------------------------------
    ("h1", "7. MONTAGE UND EINBAU"),
] + [("keep", i) for i in range(122, 136)] + [
    ("keep", 136), ("keep", 137), ("keep", 138), ("keep", 139), ("keep", 140), ("keep", 141),
    ("keep", 142), ("keep", 143), ("keep", 144), ("keep", 145), ("keep", 146), ("keep", 147),
    ("keep", 148), ("keep", 149), ("keep", 150), ("keep", 151),
    ("li", "Schwenken Sie J1 mit dem Handbediengerät aus der Mitte 90° nach rechts."),
    ("keep", 153), ("keep", 154),
    ("li", "Schwenken Sie J1 mit dem Handbediengerät aus der Mitte 90° nach links."),
    ("keep", 156), ("keep", 157),
    ("li", "Schwenken Sie J1 in die Mitte."),
    ("keep", 159), ("keep", 160),
    ("note", "Sollte die Mittenposition nicht senkrecht sein, bringen Sie den Verladearm durch "
             "Unterlegen von Scheiben zwischen Grundplatte und Tragsäule in eine senkrechte "
             "Lage. Eine schiefe Säule belastet die Antriebe J1/J2 dauerhaft und verfälscht die "
             "Kinematik."),
] + [("keep", i) for i in range(163, 177)] + [
    ("li", "Fahren Sie den Verladearm mit dem Handbediengerät in die Parkstellung."),
    ("h2", "7.3. Kamera montieren"),
    ("li", "Montieren Sie die 3D-Kamera über der Verladestelle gemäß Zeichnung "
           "[Höhe und Lage folgen]. Die Kamera muss den gesamten Bereich der Domlagen sehen."),
    ("li", "Ausrichtung nach der Montage nicht mehr verändern; jede Änderung erfordert eine neue "
           "Kalibrierung."),
    ("li", "Netzwerkkabel zum Vision-PC verlegen; Kamerafenster vor Verschmutzung schützen."),
    ("h2", "7.4. Schaltschrank aufstellen und elektrisch anschließen"),
    ("li", "Stellen Sie den Schaltschrank so auf, dass der Bediener vom Start-Taster aus den "
           "Arm und das Fahrzeug sieht [Abstand und Aufstellung folgen]."),
    ("li", "Verlegen Sie die Leitungen so, dass sie den Bewegungsbereich nicht kreuzen und keine "
           "Stolperstellen entstehen. Am Arm die Hybridkabel (SEW, Einkabeltechnik) so führen, "
           "dass sie die Drehung von J1/J2 mitmachen."),
    ("li", "Schließen Sie Antriebe, Sensorik, Kamera, Lichtschranke, Klapptreppe, "
           "Überfüllsicherung, Absperrklappe und die Leitstelle gemäß Stromlaufplan [Nummer "
           "folgt] an."),
    ("li", "Netzanschluss gemäß Kapitel 2 [folgt]."),
    ("note", "Im Schaltschrank sind Frequenzumrichter verbaut. Wird ein FI-Schutzschalter "
             "vorgeschaltet, muss dieser allstromsensitiv sein (Typ B). Die bauseitige "
             "Installation ist durch eine Elektrofachkraft des Betreibers zu prüfen."),
    ("h2", "7.5. Antriebe und Betriebsstellungen prüfen"),
    ("warn", "WARNUNG", "Unerwartete Bewegung bei der ersten Inbetriebnahme",
     "Quetsch- und Stoßverletzungen bei falscher Drehrichtung oder fehlerhafter Verdrahtung.",
     ["Bewegungsbereich absperren.",
      "Erste Bewegungen nur kurz im Handbetrieb ausführen, Hand am Not-Halt."]),
    ("p", "Vor der ersten Inbetriebnahme sind für jede Achse zu prüfen:"),
    ("li", "Drehrichtung im Handbetrieb (Taste + / −) entsprechend der Zeichnung."),
    ("li", "Software-Endlagen: Der Antrieb muss vor der Endlage selbsttätig anhalten "
           "[Hardware-Endlagen folgen]."),
    ("li", "Not-Halt und STO: Alle Antriebe müssen sofort stoppen und dürfen erst nach "
           "Entriegeln und „Quittieren“ wieder anlaufen."),
    ("li", "Bremsen: Bremsentest je Achse; Bremse J3 lässt sich nicht lüften."),
    ("li", "Nullpunkt der Absolutwertgeber: Gelenkwinkel 0° und Parkstellung einstellen und "
           "dokumentieren."),
    ("li", "Verriegelungen: Klapptreppe, Lichtschranke, Zustimmtaster, Schlüsselschalter."),
    ("li", "Der Verladearm muss sich ohne Kollision, ungewöhnliche Geräusche oder ruckartige "
           "Bewegung verfahren lassen."),
    ("keep", 202), ("keep", 203),

    # 8 ---------------------------------------------------------------------------------------
    ("h1", "8. INBETRIEBNAHME"),
    ("keep", 205), ("keep", 206), ("keep", 207),
    ("sub", "Vorbereitungen treffen"),
    ("keep", 209),
    ("li", "Prüfen Sie Antriebe, Not-Halt, Endlagen, Verriegelungen, Füllstands- und "
           "Überfüllsignale sowie die Absperrklappe auf ordnungsgemäße Funktion."),
    ("keep", 211),
    ("sub", "Einrichtung durch HETA"),
    ("li", "Anlagendaten einrichten (Abmessungen, Achsgrenzen, Parkstellung, feste Hindernisse "
           "wie Stützen, Bühne, Klapptreppe)."),
    ("li", "Kamera und Arm kalibrieren (Arm fährt mehrere Stellungen ab, Bereich frei halten)."),
    ("li", "Inbetriebnahmeprüfung mit Bericht: Erreichbarkeit aller Domlagen, Kollisionsfreiheit, "
           "Fahrzeiten."),
    ("li", "Probeläufe ohne Produkt mit stehendem Fahrzeug (verschiedene Fahrzeuge und Dome)."),
    ("li", "Test Überfüllsicherung und Absperrklappe, Test der Signale zur Leitstelle."),
    ("li", "Abnahme mit Protokoll; Softwarestand in Kapitel 1.5 eintragen."),
    ("keep", 212), ("keep", 213), ("keep", 214), ("keep", 215),

    # 9 ---------------------------------------------------------------------------------------
    ("h1", "9. BEDIENUNG"),
    ("keep", 217), ("keep", 218), ("keep", 219),
    ("h2", "9.2. Automatische Verladung"),
    ("warn", "WARNUNG", "Selbsttätige Bewegung nach dem Start",
     "Schwere Verletzungen an Händen und Kopf zwischen Arm, Lanze und Fahrzeug.",
     ["Niemand auf dem Fahrzeug, der Klapptreppe oder im Bewegungsbereich.",
      "Bei Gefahr sofort Not-Halt betätigen."]),
    ("li", "Fahrzeug abstellen, erden, Dom öffnen. Klapptreppe in Ruhelage fahren."),
    ("li", "Vergewissern Sie sich, dass sich niemand auf dem Fahrzeug und im Bewegungsbereich "
           "befindet."),
    ("li", "Die Leitstelle gibt den Auftrag mit Produkt und Sollmenge frei."),
    ("li", "Drücken Sie „Beladen starten“ (Leuchte grün = bereit)."),
    ("li", "Der Arm fährt über den Dom, misst nach, taucht ein und befüllt (Leuchte gelb). "
           "Beobachten Sie den Vorgang auf Leckagen und ungewöhnliche Bewegungen."),
    ("li", "Ist die Sollmenge erreicht, schließt die Absperrklappe, der Arm tropft ab und fährt "
           "in die Parkstellung."),
    ("li", "Das Fahrzeug darf erst wegfahren, wenn die Leuchte grün ist."),
    ("h2", "9.3. Verladung vorzeitig beenden"),
    ("li", "Die Leitstelle kann die Befüllung jederzeit beenden: Klappe zu, Abtropfen, "
           "Rückfahrt in die Parkstellung."),
    ("li", "Bei Gefahr Not-Halt betätigen. Danach quittieren und den Arm mit „Automatisch in "
           "Parkstellung“ oder im Handbetrieb zurückfahren."),
    ("h2", "9.4. Handbetrieb"),
    ("p", "Der Handbetrieb dient zum Freifahren nach einer Störung, für Wartung und "
          "Inbetriebnahme. Er ist nur vor Ort mit Sicht auf den Arm zulässig."),
    ("li", "Schlüsselschalter auf „Hand“ stellen, Handbediengerät anschließen."),
    ("li", "Achse wählen, Zustimmtaster in Mittelstellung halten und mit + / − tippen. Der Arm "
           "fährt mit reduzierter Geschwindigkeit, die Software-Endlagen bleiben aktiv."),
    ("li", "Aus dem Dom zuerst J3 heben, bis der Auslass frei ist, dann J1/J2 schwenken."),
    ("li", "Bei J1/J2 kann die Bremse zum Schieben von Hand gelüftet werden (nur solange gedrückt). "
           "Bei Wind Arm festhalten. J3 nie lüften."),
    ("li", "Danach Arm in die Parkstellung fahren oder „Automatisch in Parkstellung“ wählen, "
           "Schlüsselschalter auf „Automatik“, Handbediengerät abziehen."),
    ("h2", "9.5. Kalibrierung"),
    ("li", "Die Leitstelle stößt die Kalibrierung an; sie startet erst nach Freigabe vor Ort "
           "mit „Beladen starten“."),
    ("li", "Kein Fahrzeug auf dem Stellplatz, Bewegungsbereich frei. Der Arm fährt mehrere "
           "Stellungen ab und kehrt in die Parkstellung zurück."),
    ("keep", 240), ("keep", 241),

    # 10 --------------------------------------------------------------------------------------
    ("h1", "10. WARTUNG"),
    ("keep", 243), ("keep", 244), ("keep", 245), ("keep", 246), ("keep", 247),
    ("h2", "10.2. Regelmäßige Prüfungen durch den Betreiber"),
    ("li", "Kamerafenster reinigen [Intervall folgt]."),
    ("li", "Funktion Not-Halt, Lichtschranke, Klapptreppe und Überfüllsicherung prüfen "
           "[Intervall nach Vorgabe Betreiber / Zulassung]."),
    ("li", "Sichtprüfung Kabel am Arm, Zahnkränze, Befestigungen, Dichtheit."),
    ("h2", "10.3. Wartungszyklen"),
    ("p", "Um einen sicheren Betrieb und eine lange Lebensdauer des Verladearms zu ermöglichen, "
          "sind neben den Drehgelenken auch Antriebe, Getriebe, Zahnkränze, Befestigungen, "
          "Leitungen, Sensorik, Kamera, Not-Halt, Steuerung und Software regelmäßig zu prüfen. "
          "Es gelten die nachfolgenden HETA-Intervalle sowie die Herstellerunterlagen der "
          "Zukaufteile:"),
    ("keep", 250),
    ("p", "Zusätzlich bei jeder Inspektionswartung: Bremsentest je Achse, Ritzel/Zahnkranz J1/J2 "
          "schmieren und Flankenspiel prüfen, Getriebe nach SEW/IMO, Kalibrierung prüfen "
          "(Prüfstellung), Datensicherung von Anlagendatei und Software, Softwarestand "
          "dokumentieren."),
    ("keep", 252), ("keep", 253),

    # 11 --------------------------------------------------------------------------------------
    ("h1", "11. ERSATZTEILE"),
] + [("keep", i) for i in range(255, 262)] + [
    ("h2", "11.2. Ersatzteilliste"),
    ("table", [1100, 5400, 3138], [
        ("–", "Servomotor J1 mit Planetengetriebe P5KG31 MD071A CM3C71S/BK/AZ2Z", "SEW"),
        ("–", "Servomotor J2 (wie J1)", "SEW"),
        ("–", "Getriebemotor J3 RF47 DRN80M4/BE05/DI/KD1/TF/AK8Z", "SEW"),
        ("4", "Schwenkantrieb J3 IMO WD-E 0223/3 mit Adaption", "30000-041 [prüfen]"),
        ("–", "Ritzel / Zahnkranz J1 und J2", "[Zeichnungs-Nr. folgt]"),
        ("–", "Frequenzumrichter MOVITRAC advanced MCX91A-0040 (2×), MCX91A-0025 (1×) mit "
              "Speichermodul CMM11A", "SEW"),
        ("–", "3D-Kamera SICK Visionary-T Mini CX", "siehe Herstellerunterlagen"),
        ("–", "Vision-PC", "[folgt]"),
        ("–", "SPS-Baugruppen", "siehe Stromlaufplan"),
        ("–", "Handbediengerät mit Zustimmtaster und Not-Halt", "siehe Stromlaufplan"),
        ("–", "Messstab Füllstand, Überfüllsicherung, Durchflusssensor", "[folgt]"),
        ("–", "Absperrklappe DN 100 mit Antrieb", "[folgt]"),
        ("14", "Flachdichtung DN100 PN16, NBR", "10162-001"),
        ("25", "Drehgelenk 4\"", "00008424"),
        ("26", "Drehgelenk 4\"", "00028675"),
    ], ("Position", "Bezeichnung", "Zeichnungs-Nr.")),
] + [("keep", i) for i in range(264, 280)] + [
    # 13 / 14 ---------------------------------------------------------------------------------
    ("h1", "13. AUSSERBETRIEBNAHME UND ENTSORGUNG"),
    ("li", "Arm in die Parkstellung fahren."),
    ("keep", 281), ("keep", 282),
    ("li", "Datensicherung von Anlagendatei und Software an HETA übergeben."),
    ("li", "Hauptschalter auf „0“ stellen und gegen Wiedereinschalten sichern."),
    ("keep", 284), ("keep", 285),
    ("h1", "14. MITGELTENDE UNTERLAGEN UND FREIGABEPUNKTE"),
    ("li", "HETA-Zeichnung und Stückliste 00028433."),
    ("li", "Risikobeurteilung und EU-Konformitätserklärung nach Verordnung (EU) 2023/1230."),
    ("li", "Freigegebener Stromlauf- und Klemmenplan [Nummer folgt]."),
    ("li", "SEW: Servomotoren CM3C, Planetengetriebe P5KG, Getriebemotor RF47/DRN, MOVITRAC "
           "advanced, Handbuch MOVIKIT Positioning Drive (33350930)."),
    ("li", "IMO: Schwenkantrieb WD-E 0223/3."),
    ("li", "SICK: 3D-Kamera Visionary-T Mini; Herstellerunterlagen Füllstand und "
           "Überfüllsicherung."),
    ("li", "Industrie-PC, Siemens S7-1500."),
    ("li", "HETA-Softwaredokumentation: Schnittstelle SPS ↔ Vision-PC, Inbetriebnahme, "
           "Kalibrierung."),
]
