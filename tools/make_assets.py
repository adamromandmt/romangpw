#!/usr/bin/env python3
"""Generuje statyczne obrazy strony z logo zdefiniowanego w build.py:
favicon-32.png, favicon.ico, apple-touch-icon.png, icon-192/512.png, icon-maskable-512.png,
og-pl.png i og-en.png (podgląd linku 1200x630 w komunikatorach i mediach społecznościowych).

Uruchamiać ręcznie po zmianie logo lub brandingu (codzienny build tych plików nie rusza):
    pip install playwright pillow && python3 tools/make_assets.py
Wymaga Chromium dla Playwrighta oraz czcionki Inter (tylko do obrazków OG)."""
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402
import charts  # noqa: E402
from PIL import Image  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

BG = "#0F1614"
# Sam znak radaru bez ramki: do ikon pełnoekranowych (iOS i Android same przycinają rogi).
GLYPH = re.sub(r"<rect[^>]*/>", "", build.MARK, count=1)

TAGLINE = {
    "pl": "Dzienny skaner swing GPW — raport przed otwarciem sesji",
    "en": "Daily swing scanner for the Warsaw Stock Exchange",
}


def svg_doc(inner, view="0 0 48 48", size=1024):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" width="{size}" height="{size}">{inner}</svg>'


def shot(pw_page, html, w, h, transparent=False):
    pw_page.set_viewport_size({"width": w, "height": h})
    pw_page.set_content(html)
    pw_page.wait_for_timeout(150)
    return Image.open(io.BytesIO(pw_page.screenshot(omit_background=transparent)))


def icon_page(inner, view, bg):
    return (f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;padding:0;background:{bg}}}'
            f'svg{{display:block}}</style>{svg_doc(inner, view)}')


def og_html(lang):
    deco = charts.deco_svg()
    tag = TAGLINE[lang]
    return f"""<!doctype html><meta charset="utf-8">
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0}}
body{{width:1200px;height:630px;position:relative;overflow:hidden;background:#0B0C10;
  font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#F2F7F5}}
.bg{{position:absolute;inset:0;background:
  radial-gradient(900px 520px at 10% -8%,rgba(43,255,136,.24),transparent 62%),
  radial-gradient(760px 460px at 102% 112%,rgba(155,107,255,.16),transparent 62%),
  linear-gradient(180deg,#0B0C10,#09100E)}}
.grid{{position:absolute;inset:0;background-image:
  linear-gradient(rgba(43,255,136,.055) 1px,transparent 1px),
  linear-gradient(90deg,rgba(43,255,136,.055) 1px,transparent 1px);
  background-size:48px 48px;
  -webkit-mask-image:radial-gradient(ellipse at 30% 30%,#000 10%,transparent 72%);mask-image:radial-gradient(ellipse at 30% 30%,#000 10%,transparent 72%)}}
.deco{{position:absolute;right:30px;bottom:26px;width:760px;height:206px}}
.deco svg{{width:100%;height:100%}}
.brand{{position:absolute;left:84px;top:92px;display:flex;align-items:center;gap:32px}}
.brand svg.mk{{width:132px;height:132px;filter:drop-shadow(0 0 28px rgba(43,255,136,.35))}}
.wm{{font-size:104px;font-weight:800;letter-spacing:-.025em;line-height:1}}
.wm b{{background:linear-gradient(135deg,#8DF2B8,#4FA7AB);-webkit-background-clip:text;background-clip:text;color:transparent}}
.tag{{position:absolute;left:84px;top:290px;width:780px;font-size:42px;line-height:1.28;font-weight:500;color:#C5CFCB;letter-spacing:-.005em}}
.url{{position:absolute;left:84px;bottom:58px;font-size:30px;font-weight:700;color:#2BFF88;letter-spacing:.01em}}
.bar{{position:absolute;left:84px;top:262px;width:96px;height:4px;border-radius:2px;background:linear-gradient(90deg,#2BFF88,#66FCF1);box-shadow:0 0 16px rgba(43,255,136,.6)}}
</style>
<div class="bg"></div><div class="grid"></div>
<div class="deco">{deco}</div>
<div class="brand"><svg class="mk" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">{build.MARK}</svg>
<div class="wm">GPW <b>Radar</b></div></div>
<div class="bar"></div>
<div class="tag">{tag}</div>
<div class="url">www.gpwradar.pl</div>"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(device_scale_factor=1)

        # Znak z ramką i przezroczystymi rogami: favicon i ikony „any".
        mark = shot(pg, icon_page(build.MARK, "0 0 48 48", "transparent"), 1024, 1024, transparent=True)
        mark32 = mark.resize((32, 32), Image.LANCZOS)
        mark32.save(ROOT / "favicon-32.png", optimize=True)
        mark.resize((192, 192), Image.LANCZOS).save(ROOT / "icon-192.png", optimize=True)
        mark.resize((512, 512), Image.LANCZOS).save(ROOT / "icon-512.png", optimize=True)
        mark.save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

        # Apple touch icon: pełny kadr, ciemne tło, większy znak (iOS sam zaokrągla rogi).
        apple = shot(pg, icon_page(GLYPH, "4.5 5.5 39 39", BG), 1024, 1024)
        apple.convert("RGB").resize((180, 180), Image.LANCZOS).save(ROOT / "apple-touch-icon.png", optimize=True)

        # Ikona maskable: znak mieści się w strefie bezpiecznej (środkowe 80%).
        mask = shot(pg, icon_page(GLYPH, "-2 -1 52 52", BG), 1024, 1024)
        mask.convert("RGB").resize((512, 512), Image.LANCZOS).save(ROOT / "icon-maskable-512.png", optimize=True)

        # Obrazki OG.
        for lang in ("pl", "en"):
            og = shot(pg, og_html(lang), 1200, 630)
            og.convert("RGB").save(ROOT / f"og-{lang}.png", optimize=True)
        b.close()

    for name in ("favicon-32.png", "favicon.ico", "apple-touch-icon.png", "icon-192.png",
                 "icon-512.png", "icon-maskable-512.png", "og-pl.png", "og-en.png"):
        f = ROOT / name
        im = Image.open(f)
        print(f"{name:24s} {im.size[0]}x{im.size[1]}  {f.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
