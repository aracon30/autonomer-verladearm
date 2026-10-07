# PDF im HETA-Briefbogen erzeugen: python docs/extern/pdf_erzeugen.py <html> <pdf> (Playwright/Chromium)
import sys, pathlib, base64
from playwright.sync_api import sync_playwright
src = pathlib.Path(sys.argv[1]).resolve(); out = sys.argv[2]
logo = base64.b64encode((src.parent / "heta_logo.png").read_bytes()).decode()
F = "font-family:'Liberation Sans',Arial,sans-serif;"
header = f"""<div style="{F}width:100%;height:30mm;position:relative;-webkit-print-color-adjust:exact;">
  <div style="position:absolute;left:21mm;top:11mm;font-size:20px;color:#8EA2B6;letter-spacing:0.2px;transform:scaleX(0.86);transform-origin:left;">// HETA Verfahrenstechnik GmbH</div>
  <div style="position:absolute;left:0;top:20.5mm;width:172mm;border-top:1.2px solid #819AB0;"></div>
  <img src="data:image/png;base64,{logo}" style="position:absolute;right:13mm;top:6mm;height:24mm;">
</div>"""
col = "display:inline-block;vertical-align:top;margin-right:6mm;"
footer = f"""<div style="{F}width:100%;padding:0 13mm 0 21mm;font-size:6.6px;color:#7A8592;line-height:1.35;-webkit-print-color-adjust:exact;">
  <div style="display:flex;justify-content:space-between;align-items:flex-end;">
    <div>
      <span style="{col}">HETA Verfahrenstechnik GmbH<br>Filtration + Separation<br>Gottlieb-Daimler-Straße 7<br>35423 Lich, Germany</span>
      <span style="{col}">Tel.: +49 (0) 6404 6677-0<br>Fax: +49 (0) 6404 6677-20<br>E-Mail: sales@heta.de<br>www.heta.de</span>
      <span style="{col}">Geschäftsführer:<br>Heiko Hensel<br>Handelsregister: Gießen HRB 6111</span>
    </div>
    <div style="font-size:7px;">Seite <span class="pageNumber"></span> von <span class="totalPages"></span></div>
  </div>
  <div style="border-top:1px solid #819AB0;margin-top:2mm;padding-top:1mm;text-align:right;">// Member of PACO GRUPPE</div>
</div>"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(); pg.goto(src.as_uri()); pg.wait_for_timeout(500)
    pg.pdf(path=out, format="A4", print_background=True, display_header_footer=True,
           header_template=header, footer_template=footer,
           margin={"top": "36mm", "bottom": "30mm", "left": "21mm", "right": "18mm"})
    b.close()
