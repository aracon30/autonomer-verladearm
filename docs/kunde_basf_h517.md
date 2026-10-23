# BASF Verladestelle H517 – Stand der Aufnahme

Quelle: Projektdokumentation S. Kaestel (BASF E-EDE/OE), 22.10.2026, und Mail vom 23.10.2026.
Die Fotos sind **vertraulich** und werden nicht im Repository abgelegt; hier nur die für die
Auslegung nötigen Angaben.

## Angaben BASF

| Thema | Angabe |
|---|---|
| Produkte | hauptsächlich **Acronal**, außerdem Lhydran und Lurapret (Polymerdispersionen) |
| Eintauchtiefe | optimal **2–3 cm unter dem Füllspiegel**; heute wegen paralleler Bedienung mehrerer Tankzüge in der Praxis nicht eingehalten |
| Mannloch | Innendurchmesser **0,5 m** bei allen gemessenen Fahrzeugen, Wandstärke 5 mm; Verschlussart und Aufbau unterschiedlich |
| Ex-Schutz | keine Ex-Zone; Maschinenrichtlinie 2006/42/EG bzw. ab Januar Verordnung (EU) 2023/1230 |
| Verladebrücke | Länge 1,75 m; Abstand Steg bis Mannloch ca. 2 m (je nach Stellung des Tankzugs) |
| Heutiger Arm | Aufhängung zur Decke, Abstand Aufhängung zum Boden 2,30 m [Bezug prüfen]; mittlerer schräger Teil 2,8–3 m; Füllrohr 2 m (1,5 m bis Flansch); Füllrohrverlängerung mit Kupplung 1,3 m |
| Absperrung heute | manuelle Stellklappe am Arm DN 80, PN 10, −10 … +100 °C |
| Grundstellung heute | optischer Näherungsschalter mit Reflektor |
| Überfüllsicherung heute | Liquiphant auf einem Halter, der auf dem Domkasten aufliegt und das Füllrohr mit einem Ring umfasst – von Hand gesetzt |
| Fahrzeugstatistik | in Arbeit |

## Beobachtungen aus den Fotos

- Verladung in einer **überdachten Halle** mit mehreren Spuren nebeneinander (Arme 1, 2, 6, 8, 10):
  wenig Wind, Licht gleichmäßiger; Nachbarspur und Nachbararme liegen im Blickfeld der Kamera →
  Auswertebereich auf die eigene Spur begrenzen.
- Der Dom sitzt in einem **Domkasten** (Edelstahlwanne mit Rand) mit Armaturen (Belüftung,
  Anschlüsse, Bügel); der Deckel ist aufgeklappt (stehend oder auf den Laufsteg gelegt), Verschluss
  mit Knebeln. Kastenrand, Armaturen und Deckel sind Hindernisse – werden von der Kamera erfasst.
- Laufstege mit Gitterrosten entlang des Tanks; rote Klapptreppe/Bühne neben dem Fahrzeug.
- Der heutige Liquiphant-Halter entspricht dem HETA-Konzept der **aufliegenden Lanze**
  (`docs/fuellstand_ueberfuellsicherung.md`).
- Der Arm wird nach der Verladung in eine Wanne **gespült**.

## Folgen für das Projekt

- Mannloch 0,5 m: Referenzflansch Ø 220 mm passt, tiefes Eintauchen möglich (Grenze dann Reichweite
  und Tankboden).
- Nachziehen auf **2–3 cm** auslegen statt 10–20 cm: kleine, häufige Schritte → besser
  kontinuierlich nachziehen (Geschwindigkeit an den Spiegelanstieg angepasst, siehe Stützpunkte
  nachschieben). Simulation umgestellt auf 2–5 cm.
- Messstab und Koaxialrohr: Dispersionen trocknen an → Reinigung/Spülen berücksichtigen.
- Parkstellung über einer Spülwanne vorsehen? Spülablauf klären.
- Schnittstelle DN 80 (heute) ↔ DN 100 (HETA-Arm) klären.

## Offene Fragen an BASF

1. Höhe der Decke bzw. Aufhängung über der Fahrbahn, Lage der Spuren zueinander (Kamera, Arm).
2. Tiefe Domrand bis Tankboden, typische Füllmenge je Kammer und Füllleistung (m³/h).
3. Produkttemperatur und Schäumen beim Befüllen.
4. Liquiphant: Typ, Einhängelänge unter dem Rand, Auswertung (Relais, PLS).
5. Spülen: wann und wo (Parkstellung über der Wanne?).
