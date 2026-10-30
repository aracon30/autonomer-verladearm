# Änderungen (ISO 9001, 8.3.6)

Stand 30.10.2026 · Entwurf

Änderungen an Anforderungen, Konzept, Schnittstelle oder Hardware mit Grund, Auswirkung und
Freigabe. Kleine Änderungen an Software und Dokumenten sind in der Git-Historie nachvollziehbar
(`git log`); hier stehen die Änderungen, die andere Beteiligte oder den Kunden betreffen.

| Nr. | Datum | Änderung | Grund | Auswirkung | Betroffen | Freigabe |
|---|---|---|---|---|---|---|
| Ä-01 | 15.10.2026 | Geber J1 wie J2 (AZ2Z, MD071A) statt Sicherheitsgeber | Sicherheitsgeber nicht nötig, gleiche Teile | SEW-Angebot D | SEW, Peter | [ ] |
| Ä-02 | 16.10.2026 | Umrichter mit MOVIKIT Positioning Drive (Level 1) statt Velocity Drive | Positionieren im Umrichter, Synchronfahrt durch die SPS | SPS-Programm, Antriebsliste | Peter | [ ] |
| Ä-03 | 19.10.2026 | Bedienung ohne Display (Taster, Leitstelle, Handbediengerät) | Wunsch Betrieb, Bedienung aus dem PLS | Lastenheft F-30/F-32 (Abweichung), Betriebsanleitung, Schaltschrank | BASF, Peter | [ ] |
| Ä-04 | 26.10.2026 | Übersetzung J1/J2 i 10,6 ohne SEW-Rückfrage angenommen | Entscheidung P. Schreiber | Risiko Regelbarkeit, Inbetriebnahme mit flachen Rampen | SEW-Bestellung | [ ] |
| Ä-05 | 26.10.2026 | Nachziehen mit 2 kapazitiven Grenzschaltern statt Messstab | Anhaftung/Koaxrohr, Schaum, Kosten | Lastenheft F-12 (Abweichung), Stückliste Pos. 22 | BASF | [ ] |
| Ä-06 | 26.10.2026 | Schutzebenen Füllende: Sollmenge, Maximalhöhe, Überfüllsicherung nur letzte Ebene | WHG/AwSV-Grundsatz | SPS-Programm | Peter, BASF | [ ] |
| Ä-07 | 27.10.2026 | Schnittstelle Vision-PC ↔ SPS **Version 3**: `DomeNo`, `DomeCount`, `DomeSelected`, Fehler 22 | Mehrkammer-Fahrzeuge | `plc/DB_Vision.db`, SPS-Programm, Lastenheft F-05 (Abweichung) | **Peter (Freigabe nötig)** | [ ] |
| Ä-08 | 27.10.2026 | Überfüllsicherung schaltet die Pumpe ab | Gespräch BASF 27.10. | Signal an BASF/PLS bzw. Sicherheitskreis | BASF, Peter | [ ] |
| Ä-09 | 27.10.2026 | Sensortest mit Produkt durch BASF, kein eigenes LFC-Testset | BASF testet selbst | Bestellung SICK reduziert | BASF | [ ] |
| Ä-10 | 28.–29.10.2026 | Abtropfsicherung als pendelnde Tropfschale, Motorwelle versetzt (Rev. 2 → Rev. 3) | Nachtropfen (BASF: Eimer, 1 min reicht nicht) | Konstruktion, SPS (Antrieb, Endlagen S1/S2), Kollisionsmodell | Konstruktion, Peter | [ ] |
| Ä-11 | 29.10.2026 | Konfigurator: Verladestelle (Fahrtrichtung, eigene Spur), Domsuche nur in der eigenen Spur | Mehrkammer-Zählung, Nachbarspuren H517 | Anlagendatei Abschnitt `vehicle`, Inbetriebnahme | – | [ ] |

**Schnittstellen-Versionen** (Details `docs/schnittstelle.md`, Abschnitt Änderungen): V1
Zielkoordinate, V2 Aufträge und Stützpunkte, V3 mehrere Dome. Jede neue Version braucht die
Freigabe des SPS-Programmierers.
