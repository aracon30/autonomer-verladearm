"""Erzeugt die überarbeitete Betriebsanleitung aus der Vorlage (Formatierung der Vorlage)."""
import re
import sys

sys.path.insert(0, ".")
import importlib  # noqa: E402
from split import load  # noqa: E402

MOD = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "content")
BLOCKS = MOD.BLOCKS
head, els, tail = load()
FONT = '<w:rFonts w:ascii="Arial" w:cs="Arial" w:eastAsia="Arial" w:hAnsi="Arial"/>'


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def runs(text, bold=False, italic=False, color=None, size=20):
    """**fett**, [folgt …] gelb markiert."""
    out = []
    for part in re.split(r"(\*\*.+?\*\*|\[[^\]]*\])", text):
        if not part:
            continue
        b, hl = bold, False
        if part.startswith("**") and part.endswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("[") and part.endswith("]"):
            hl = True
        rpr = FONT + ("<w:b/><w:bCs/>" if b else "") + ("<w:i/><w:iCs/>" if italic else "")
        rpr += f'<w:color w:val="{color}"/>' if color else ""
        rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
        rpr += '<w:highlight w:val="yellow"/>' if hl else ""
        out.append(f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{esc(part)}</w:t></w:r>')
    return "".join(out)


def h1(t):
    return ('<w:p><w:pPr><w:pStyle w:val="Heading1"/><w:keepNext/><w:spacing w:after="140" '
            f'w:before="280"/></w:pPr>{runs(t, bold=True, size=26)}</w:p>')


def h2(t):
    return ('<w:p><w:pPr><w:pStyle w:val="Heading2"/><w:keepNext/><w:spacing w:after="100" '
            f'w:before="200"/></w:pPr>{runs(t, bold=True, size=22)}</w:p>')


def p(t):
    return f'<w:p><w:pPr><w:spacing w:after="120"/></w:pPr>{runs(t)}</w:p>'


def sub(t):
    return ('<w:p><w:pPr><w:keepNext/><w:spacing w:after="80" w:before="140"/></w:pPr>'
            f'{runs(t, bold=True)}</w:p>')


def li(t):
    return ('<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/>'
            f'<w:numId w:val="2"/></w:numPr><w:spacing w:after="60"/></w:pPr>{runs(t)}</w:p>')


def box(color, fill, paras):
    """paras: Liste (text, art) – art: sig, title, folge, text"""
    out = []
    for i, (t, kind) in enumerate(paras):
        last = i == len(paras) - 1
        ppr = (f'<w:pPr>{"<w:keepNext/>" if not last else ""}<w:pBdr><w:left w:val="single" '
               f'w:color="{color}" w:sz="18" w:space="6"/></w:pBdr><w:shd w:fill="{fill}" '
               f'w:color="auto" w:val="clear"/><w:spacing w:after="{160 if last else 30}"/>'
               '<w:ind w:left="200"/></w:pPr>')
        if kind == "sig":
            r = runs(t, bold=True, color=color)
        elif kind == "title":
            r = runs(t, bold=True)
        elif kind == "folge":
            r = runs("Folge: ", italic=True) + runs(t)
        else:
            r = runs(t)
        out.append(f"<w:p>{ppr}{r}</w:p>")
    return "".join(out)


SIG = {"GEFAHR": ("C00000", "FBE5E5"), "WARNUNG": ("C55A11", "FCE9DA"),
       "VORSICHT": ("9C6500", "FFF4CC")}


def warn(level, title, folge, actions):
    c, f = SIG[level]
    return box(c, f, [(f"⚠ {level}", "sig"), (title, "title"), (folge, "folge")]
               + [(f"→ {a}", "text") for a in actions])


def note(*texts):
    return box("1F4E79", "EAF1F8", [("HINWEIS!", "sig")] + [(t, "text") for t in texts])


BORD = ('<w:tcBorders><w:top w:val="single" w:color="808080" w:sz="4"/><w:left w:val="single" '
        'w:color="808080" w:sz="4"/><w:bottom w:val="single" w:color="808080" w:sz="4"/>'
        '<w:right w:val="single" w:color="808080" w:sz="4"/></w:tcBorders>')
MAR = ('<w:tcMar><w:top w:type="dxa" w:w="60"/><w:left w:type="dxa" w:w="100"/><w:bottom '
       'w:type="dxa" w:w="60"/><w:right w:type="dxa" w:w="100"/></w:tcMar>')


def table(widths, rows, header=None):
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = [f'<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="{sum(widths)}"/><w:tblBorders>'
           '<w:top w:val="single" w:color="auto" w:sz="4"/><w:left w:val="single" w:color="auto" '
           'w:sz="4"/><w:bottom w:val="single" w:color="auto" w:sz="4"/><w:right w:val="single" '
           'w:color="auto" w:sz="4"/><w:insideH w:val="single" w:color="auto" w:sz="4"/>'
           '<w:insideV w:val="single" w:color="auto" w:sz="4"/></w:tblBorders></w:tblPr>'
           f"<w:tblGrid>{grid}</w:tblGrid>"]
    for hdr, row in ([(True, header)] if header else []) + [(False, r) for r in rows]:
        cells = []
        for w, t in zip(widths, row, strict=True):
            shd = '<w:shd w:fill="D9D9D9" w:color="auto" w:val="clear"/>' if hdr else ""
            paras = "".join(f"<w:p>{runs(x, bold=hdr)}</w:p>" for x in str(t).split("\n"))
            cells.append(f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{w}"/>{BORD}{shd}{MAR}</w:tcPr>'
                         f"{paras}</w:tc>")
        trpr = "<w:tblHeader/>" if hdr else '<w:tblHeader w:val="off"/>'
        out.append(f"<w:tr><w:trPr><w:cantSplit/>{trpr}</w:trPr>{''.join(cells)}</w:tr>")
    out.append("</w:tbl>")
    return "".join(out) + p("")


def keep(i):
    return els[i][1]


def render(block):
    kind, *args = block
    return {"h1": h1, "h2": h2, "p": p, "sub": sub, "li": li, "warn": warn, "note": note,
            "table": table, "keep": keep, "code": code}[kind](*args)


def code(*lines):
    out = []
    for i, t in enumerate(lines):
        last = i == len(lines) - 1
        out.append('<w:p><w:pPr><w:shd w:fill="F2F2F2" w:color="auto" w:val="clear"/>'
                   f'<w:spacing w:after="{120 if last else 0}"/><w:ind w:left="200"/></w:pPr>'
                   '<w:r><w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" '
                   'w:cs="Courier New"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
                   f'<w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>')
    return "".join(out)


# Deckblatt (Titel, Kopfdatentabelle, Inhaltsverzeichnis) übernehmen und anpassen
front = [x for _, x in els[:8]]
for i, old, new in getattr(MOD, "FRONT", [
        (2, "Obenverladearm mit elektrischem Antrieb (Heben / Senken)",
         "Autonomer Obenverladearm mit elektrischen Antrieben (Drehen J1 / J2, Heben / Senken J3)"),
        (3, ">Obenverladearm, elektrisch<", ">Autonomer Obenverladearm, elektrisch<")]):
    assert old in front[i], old
    front[i] = front[i].replace(old, new)
body = "".join(front) + "".join(render(b) for b in BLOCKS) + els[-1][1]
open("out/word/document.xml", "w", encoding="utf-8").write(head + body + tail)

hdr = open("out/word/header1.xml", encoding="utf-8").read()
for old, new in getattr(MOD, "HEADER", [("Obenverladearm elektrisch",
                                         "autonomer Obenverladearm elektrisch")]):
    hdr = hdr.replace(old, new)
open("out/word/header1.xml", "w", encoding="utf-8").write(hdr)
ftr = open("out/word/footer1.xml", encoding="utf-8").read()
for old, new in getattr(MOD, "FOOTER", []):
    ftr = ftr.replace(old, new)
open("out/word/footer1.xml", "w", encoding="utf-8").write(ftr)
print("ok", len(BLOCKS))
