# Entwicklungsreviews (ISO 9001, 8.3.4)

Stand 30.10.2026 · Entwurf

Bewertung der Entwicklungsergebnisse je Phase bzw. bei wichtigen Entscheidungen. Die Einträge
R0-1 bis R0-6 sind **rückwirkend** aus Besprechungen, Entscheidungen und Kundenterminen
zusammengestellt (Quelle angegeben) und noch nicht formal freigegeben. Ab jetzt je Review die
Vorlage unten verwenden.

## Übersicht

| Nr. | Datum | Anlass | Teilnehmer | Ergebnis | Quelle | Freigabe |
|---|---|---|---|---|---|---|
| R0-1 | 29.09.2026 | Architektur Vision-PC ↔ SPS | HETA | PC misst und plant, SPS fährt und prüft; Sicherheit nur über zertifizierte Komponenten | `docs/adr/0001-architektur.md` | [ ] |
| R0-2 | 30.09.2026 | Antriebe J1–J3 | HETA, Konstruktion | J1/J2 Servo + Zahnkranz (i 10,6), J3 IMO + SEW, Geber am Motor | `hardware/antriebe.md`, Projektstand | [ ] |
| R0-3 | 06.10.2026 | Automatisierung | HETA, Peter | Gelenkwinkel-Stützpunkte vom PC (ADR 0002), Antriebsliste, F-CPU-Frage | `docs/besprechungen/2026-10-06_automatisierung.md`, `docs/adr/0002-gelenkwinkel-vom-pc.md` | [ ] |
| R0-4 | 15.–16.10.2026 | Kunde BASF, Antriebsangebot | HETA, BASF, SEW | keine Ex-Zone, Nachziehen gefordert, Überfüllsicherung an aufliegender Lanze; Umrichter mit Positioning Drive; elektrische Freigabe Servos/Umrichter (Peter) | Projektstand | [ ] |
| R0-5 | 19.10.2026 | Bedienkonzept | HETA | kein Display, Leuchttaster, Leitstelle, Handbetrieb nur vor Ort | `docs/schnittstelle.md`, Projektstand | [ ] |
| R0-6 | 26.–27.10.2026 | Füllende, Nachziehen, Mehrkammer, Termin BASF | HETA, BASF | Schutzebenen Füllende; 2 Grenzschalter; Überfüllsicherung schaltet Pumpe; Schnittstelle V3 (mehrere Dome); Sensortest durch BASF | `docs/fuellstand_ueberfuellsicherung.md`, `docs/kunde_basf_h517.md` | [ ] |

## Geplante Reviews

| Nr. | Phase | Gegenstand | Voraussetzung | Teilnehmer |
|---|---|---|---|---|
| R1 | Konzept | Lastenheft V1.0 mit Abweichungen und neuen Anforderungen (`anforderungsnachweis.md`) | Antworten BASF | HETA, BASF |
| R2 | Software | Software-Stand für den Prototyp, Schnittstelle V3 mit SPS | Peter hat V3 gesichtet | HETA, Peter |
| R3 | Design | Konstruktion (Antriebsanbau, Isolierung über J1, Abtropfsicherung, Halter Sensoren), Stromlaufplan, **Risikobeurteilung** | vor Bestellung/Fertigung | HETA, Konstruktion, Peter |
| R4 | Prototyp | Aufbau und Inbetriebnahme Werkstatt | Prototyp fertig | HETA, Peter |
| R5 | Verifizierung | Nachweise je Anforderung (Kameratest, Sensortest, Dauertest) | Tests durchgeführt | HETA, BASF |
| R6 | Validierung | Abnahme an H517, CE-Konformität | Montage BASF | HETA, BASF |

## Vorlage

```
## R<n> – <Gegenstand>
Datum:            <TT.MM.JJJJ>
Phase:            <1–6>
Teilnehmer:       <Name, Firma, Rolle>
Unterlagen:       <Dokumente mit Version / Git-Stand>

Bewertung:
- Anforderungen erfüllt?       <ja / nein / teilweise – Verweis Anforderungsnachweis>
- Probleme / Risiken:          <…>
- Entscheidungen:              <…>

Maßnahmen:
| Nr | Maßnahme | Wer | Bis | Erledigt |
|---|---|---|---|---|

Ergebnis:         <freigegeben / mit Auflagen / nicht freigegeben>
Freigabe:         <Name, Datum>
```
