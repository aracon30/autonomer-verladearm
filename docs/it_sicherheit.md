# IT-Sicherheit – Prüfung der Software (Stand 25.11.2026)

Geprüft gegen eine übliche Liste typischer Web-Schwachstellen. Die Software hat **keine Anmeldung,
keine Datenbank und keine Datei-Uploads**; erreichbar sind zwei kleine Webserver (Konfigurator,
Live-Ansicht) und der OPC-UA-Client zur SPS.

| Nr. | Schwachstelle | Befund | Maßnahme |
|---|---|---|---|
| 1 | Script im Namen (XSS) | Namen und Texte werden als Text eingefügt, `innerHTML` nur mit Zahlen/festen Texten | – |
| 2 | ID in der URL ändern / Pfad | Anlagenname nur `A–Z a–z 0–9 _ -` (max. 60), kein Zugriff außerhalb des Anlagenordners | – |
| 3, 7 | /admin, selbst Admin werden | **keine Anmeldung**: wer den Konfigurator erreicht, kann Anlagendateien ändern | Standard nur `127.0.0.1`; `--host 0.0.0.0` nur im abgeschotteten Netz; an der Anlage nicht im Netz freigeben |
| – | Fremde Webseite schickt Befehle (CSRF/DNS-Rebinding) | war möglich | **behoben 25.11.**: nur JSON, Origin muss zum Host passen (Test) |
| 4, 9 | API-Key/Passwörter im Code bzw. auf GitHub | keine Schlüssel, keine `.env`; einzig das **SICK-Werks-Servicepasswort** `CUST_SERV` als Standardwert | an der Anlage in der Kamera ändern und nur lokal in die Anlagendatei schreiben |
| 5, 6, 8 | Datenbankrechte, KI-Regeln, Login-Codes | nicht vorhanden | – |
| 10 | Upload | keine Uploads; Aufnahmen werden mit `allow_pickle=False` geladen (kein Code aus Dateien) | – |
| – | OPC UA ohne Verschlüsselung | Prototyp: anonym, unverschlüsselt | Anlagennetz trennen; für BASF Security-Policy (Basic256Sha256, Zertifikate) mit Peter/BASF festlegen |
| – | Repository | enthält Kundennamen und Projektdaten | Repository **privat** halten; keine Fotos/vertraulichen BASF-Unterlagen einchecken |
