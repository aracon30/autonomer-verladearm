# Kameratest mit der SICK Visionary-T Mini CX am Laptop

Ziel: Kamera in Betrieb nehmen, Punktwolke live ansehen und **Aufnahmen von echten Tankwagen**
speichern, mit denen die Domerkennung entwickelt und geprüft wird. Kein Arm, keine SPS nötig.

## Material

| Teil | Hinweis |
|---|---|
| Kamera V3S105-1AAAAAD mit Halter | Lieferung SICK (Laboraktion) |
| Leitung M12 8-polig A → offenes Ende, 15 m | Versorgung 24 V |
| Leitung M12 X → RJ45, 15 m | Ethernet zum Laptop |
| **24-V-Netzteil**, mind. 1 A (Spitze 2 A) | z. B. Hutschienen-Netzteil mit Klemmen; Laborpersonal bzw. Elektrofachkraft anschließen lassen |
| Laptop mit LAN-Anschluss (oder USB-LAN-Adapter, Gigabit) | Windows, Projekt wie für die Simulation eingerichtet |
| Stativ oder Halter | Kamera **senkrecht nach unten**, 3–5 m über dem Objekt (Tankwagen: Brücke, Bühne, Hubsteiger) |

## Anschluss Versorgung (Leitung YF2A28, 8 Adern)

Welche Ader +24 V und welche 0 V ist, steht in der **Betriebsanleitung der Kamera** (Anschluss
Versorgung/E/A) und im Datenblatt der Leitung (spezieller Farbcode). Nur diese beiden Adern an das
Netzteil, die übrigen einzeln isolieren. Anschließen lassen von einer Elektrofachkraft; erst
anschließen, dann Netzteil einschalten. Die Kamera braucht ca. 20 s zum Hochfahren.

## Netzwerk am Laptop (einmalig)

Die Kamera hat ab Werk **192.168.1.10**. Der Laptop braucht eine feste Adresse im selben Netz:

1. Windows-Einstellungen → Netzwerk und Internet → Ethernet (der Anschluss mit der Kamera) →
   IP-Zuweisung **Bearbeiten → Manuell → IPv4 ein**
2. IP-Adresse **192.168.1.2**, Subnetzmaske **255.255.255.0**, Gateway leer lassen → Speichern
3. Test in der Eingabeaufforderung: `ping 192.168.1.10` – Antworten kommen, wenn die Kamera läuft.

Firmen-WLAN kann parallel aktiv bleiben. Nach dem Test die Einstellung wieder auf **Automatisch
(DHCP)** stellen, wenn der Anschluss sonst im Firmennetz genutzt wird.

## Live-Ansicht

```bat
tools\kameratest.bat
```

Beim ersten Mal wird die SICK-Bibliothek installiert (Internet nötig). Danach öffnet sich die
Live-Ansicht im Browser (http://127.0.0.1:8000) mit der Punktwolke der Kamera. Liegt ein Dom im
Bild, versucht die Software ihn zu erkennen.

## Aufnahmen speichern

```bat
tools\kameratest.bat aufnahme
```

Je **Enter** eine Aufnahme (3 Bilder gemittelt), **q** beendet. Gespeichert wird unter
`data\aufnahmen\<Datum>_<Zeit>.npy`. Mit Notiz im Dateinamen:

```bat
.venv\Scripts\python tools\aufnahme.py --config vision\config\anlagen\kameratest.yaml --notiz "Lkw 3 Kammern Dom 2 offen"
```

**Was aufnehmen** (je Fahrzeug mehrere Aufnahmen):
- Dom geschlossen, Dom offen (Deckel in verschiedenen Stellungen), mehrere Dome offen
- verschiedene Fahrzeuge (Tankform, Domkragen, Laufstege, Geländer), auch das Führerhaus im Bild
- unterschiedliche Höhe der Kamera über dem Dom (3 m, 4 m, 5 m), leicht schräg versetzt
- Licht: Halle, Tageslicht, nasse oder glänzende Oberflächen

Die Dateien bitte an HETA (Projektordner) geben, **nicht ins Repository einchecken**. Auf
**Werksgeländen (BASF)** nur mit Foto- bzw. Aufnahmegenehmigung aufnehmen; Punktwolken zeigen
keine Gesichter oder Kennzeichen lesbar, gelten aber als Aufnahmen des Geländes.

## Wenn etwas nicht geht

| Problem | Abhilfe |
|---|---|
| `ping` ohne Antwort | 24 V und LED an der Kamera prüfen, 20 s warten, Laptop-IP prüfen, anderes Kabel/Port |
| „Kamera nicht erreichbar“ in der Live-Ansicht | IP in `vision\config\anlagen\kameratest.yaml` (`source.ip`) prüfen; Firewall-Abfrage zulassen |
| SICK-Bibliothek lässt sich nicht installieren | https://github.com/SICKAG/sick_visionary_python_base als ZIP herunterladen, entpacken, dann `.venv\Scripts\python -m pip install <Ordner>` |
| Punktwolke lückenhaft | Abstand zu klein (< 0,5 m) oder zu groß (> 8 m), direkte Sonne, Spiegelungen |
| IP der Kamera unbekannt | SICK SOPAS ET (kostenlos von sick.com) findet die Kamera im Netz |
