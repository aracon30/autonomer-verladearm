# Betrieb auf dem Edge-PC

## Installation (Ubuntu 22.04/24.04)

```bash
git clone <repo> && cd autonomer-verladearm
sudo deploy/install.sh vision/config/anlagen/<anlage>.yaml
```

Das Skript legt an:

| Was | Wo |
|---|---|
| Programm (virtuelle Umgebung inkl. SICK-Bibliothek) | `/opt/verladearm/venv` |
| Konfiguration (`default.yaml` + `anlage.yaml`) | `/etc/verladearm/` |
| Arbeitsverzeichnis, Aufzeichnungen, Snapshot | `/var/lib/verladearm/data/` |
| Systemdienste | `verladearm-vision` (OPC UA zur SPS), `verladearm-viewer` (Browser, Port 8000) |

Beide Dienste starten mit dem PC und nach einem Absturz automatisch neu (3 bzw. 5 s).
Während des Neustarts fehlt der Heartbeat des PCs, die SPS geht in den sicheren Zustand.

## Bedienung

| Aufgabe | Befehl |
|---|---|
| Status | `systemctl status verladearm-vision` |
| Protokoll live | `journalctl -u verladearm-vision -f` |
| Neu starten (z. B. nach Änderung der Anlagendatei) | `sudo systemctl restart verladearm-vision verladearm-viewer` |
| Stoppen | `sudo systemctl stop verladearm-vision` |
| Live-Ansicht | Browser: `http://<IP des PCs>:8000` |
| Auswertung Aufzeichnungen | `/opt/verladearm/venv/bin/python tools/auswertung.py --dir /var/lib/verladearm/data/aufzeichnung > auswertung.csv` |

## Update

Repository aktualisieren (`git pull`) und `sudo deploy/install.sh <anlage>.yaml` erneut ausführen.
Bei geänderter `InterfaceVersion` vorher das SPS-Programm anpassen (docs/schnittstelle.md).

## Windows

Falls der PC mit Windows ausgeliefert wird: Die Software läuft auch dort (Python 3.10+).
Als Dienst z. B. mit NSSM oder der Aufgabenplanung („bei Systemstart“, „bei Fehler neu starten“)
einrichten. Getestete Zielumgebung ist Ubuntu.
