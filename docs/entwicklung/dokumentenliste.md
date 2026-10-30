# Dokumentenliste (ISO 9001, 8.3.5 / 7.5)

Stand 30.10.2026 · Entwurf

Entwicklungsergebnisse mit Stand und Freigabestatus. Version = Datum des letzten Stands bzw.
Versionsnummer im Dokument; der genaue Stand ist über die Git-Historie nachvollziehbar.

Status: **E** = Entwurf · **P** = in Prüfung · **F** = freigegeben

## Anforderungen und Konzept

| Dokument | Ablage | Stand | Status | Freigabe |
|---|---|---|---|---|
| Lastenheft | `docs/lastenheft.html` | V0.1 | E (Update nach R1) | [ ] |
| Architektur (ADR 0001, 0002) | `docs/adr/` | 29.09. / 06.10.2026 | E | [ ] |
| Kinematik und Bahnplanung | `docs/kinematik.md` | laufend | E | [ ] |
| Füllstand, Nachziehen, Überfüllsicherung | `docs/fuellstand_ueberfuellsicherung.md` | 27.10.2026 | E | [ ] |
| Kunde BASF H517 (ohne vertrauliche Fotos) | `docs/kunde_basf_h517.md` | 27.10.2026 | E | – |
| Projektstand, Entscheidungen | `docs/projektstand.md` | 27.10.2026 | laufend | – |

## Hardware

| Dokument | Ablage | Stand | Status | Freigabe |
|---|---|---|---|---|
| Antriebsauslegung | `hardware/antriebe.md` | 26.10.2026 | E | [ ] |
| Antriebsliste (für Schaltschrankbauer) | `hardware/antriebsliste.md`, `docs/extern/Antriebsliste_Verladearm.pdf` | 21.10.2026 | E | [ ] |
| Stückliste | `hardware/stueckliste.csv` | 27.10.2026 | E | [ ] |
| Kamera SICK | `docs/sensor_sick.md` | laufend | E | – |
| Skizze Überfüll-Lanze | `docs/skizzen/ueberfuell_lanze.svg` | 15.10.2026 | E (überholt: Lanze kürzer, keine Gleithülse) | – |
| Prinzipskizze Abtropfsicherung | `docs/skizzen/Prinzipskizze_Abtropfsicherung_Rev3.pdf` | Rev. 3, 29.10.2026 | E | [ ] |
| Konstruktionszeichnungen | [HETA Konstruktion] | – | offen | [ ] |
| Stromlaufplan, Schaltschrank | [Peter] | – | offen | [ ] |
| Risikobeurteilung (EN ISO 12100), Sicherheitsfunktionen (EN ISO 13849) | – | – | **offen** | [ ] |

## Software und Schnittstelle

| Dokument | Ablage | Stand | Status | Freigabe |
|---|---|---|---|---|
| Schnittstelle Vision-PC ↔ SPS | `docs/schnittstelle.md`, `plc/DB_Vision.db` | Version 3 | E (Freigabe SPS offen) | [ ] |
| Vision-Software | `vision/` | Git `main` | E (Prototyp) | [ ] |
| Automatische Tests | `vision/tests/` | 139 Tests | laufend | – |
| SPS-Simulator, Simulation | `tools/` | laufend | – | – |
| Kalibrierung | `docs/kalibrierung.md` | laufend | E | – |
| Inbetriebnahme | `docs/inbetriebnahme.md` | 29.10.2026 | E | [ ] |
| Betrieb | `docs/betrieb.md` | laufend | E | – |

## Dokumentation für den Kunden

| Dokument | Ablage | Stand | Status | Freigabe |
|---|---|---|---|---|
| Betriebsanleitung OMIM-4793 (VO (EU) 2023/1230) | `docs/extern/OMIM-4793_Betriebsanleitung_autonom_Entwurf.docx` | Entwurf | E | [ ] |
| Softwaredokumentation SWD-4793 | `docs/extern/SWD-4793_Softwaredokumentation_Entwurf.docx` | Entwurf, Schnittstelle V3 | E | [ ] |
| Technische Zusammenfassung (an BASF) | `docs/extern/` | gesendet | – | – |
| Konformitätserklärung | – | – | offen (Phase 6) | [ ] |
