# Quellen der Handbücher (Word)

Erzeugt die Word-Entwürfe aus der HETA-Vorlage `vorlage_OMIM-4793.docx` (Formatierung, Deckblatt,
Kopf- und Fußzeile bleiben erhalten). Inhalt in `content.py` (Betriebsanleitung OMIM-4793) bzw.
`content_swd.py` (Softwaredokumentation SWD-4793); offene Punkte in eckigen Klammern werden gelb
markiert.

```bash
mkdir -p /tmp/hb && cd /tmp/hb && unzip -q -o <repo>/docs/extern/handbuch_quellen/vorlage_OMIM-4793.docx -d x
cp <repo>/docs/extern/handbuch_quellen/*.py . && rm -rf out && cp -r x out
python3 build.py content_swd          # bzw. content
(cd out && zip -q -Xr ../ergebnis.docx .)
```
