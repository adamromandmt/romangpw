#!/usr/bin/env python3
"""Buduje statyczną stronę z raportów Markdown.

Swing: reports/*.md -> index.html, reports/<data>.html, archiwum.html.
Dywidendy: dywidendy/*.md -> dywidendy.html, dywidendy/<data>.html, dywidendy-archiwum.html.
Wymaga pakietu `markdown` (pip install markdown).
"""
import html
import re
import sys
from pathlib import Path

import markdown

from charts import deco_svg, render_charts

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
DAYS = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
DISCLAIMER = "Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna."

CSS = """
:root{
  --bg:#0B0C10;--panel:#0F1614;--panel2:#15221E;--line:#1F3330;
  --fg:#C5CFCB;--strong:#F2F7F5;--muted:#86948E;
  --accent:#2BFF88;--accent2:#45A29E;--cyan:#66FCF1;--violet:#9B6BFF;
  --up:#2BFF88;--down:#FF5C7A;--warn:#FFB347;
}
*{box-sizing:border-box}
html{color-scheme:dark}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
body::before{content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;
  background:
    radial-gradient(900px 520px at 6% -6%,rgba(43,255,136,.22),transparent 65%),
    radial-gradient(820px 480px at 96% 0%,rgba(69,162,158,.20),transparent 65%),
    radial-gradient(760px 520px at 58% 108%,rgba(43,255,136,.10),transparent 65%),
    radial-gradient(520px 380px at 100% 70%,rgba(155,107,255,.10),transparent 65%)}
body::after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
  background-image:linear-gradient(rgba(43,255,136,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(43,255,136,.055) 1px,transparent 1px);
  background-size:46px 46px;
  -webkit-mask-image:radial-gradient(ellipse 90% 70% at 50% 0%,#000 0%,transparent 75%);
  mask-image:radial-gradient(ellipse 90% 70% at 50% 0%,#000 0%,transparent 75%)}
header,main,footer{max-width:1100px;margin:0 auto;padding:0 16px}
header{position:relative;padding-top:24px;padding-bottom:14px;min-height:100px;border-bottom:1px solid var(--line)}
header .deco{position:absolute;right:0;top:0;height:100%;width:60%;max-width:520px;opacity:.6;pointer-events:none}
header a.brand{position:relative;font-weight:800;font-size:20px;letter-spacing:.2px;color:var(--strong);text-decoration:none}
header a.brand::before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--up);box-shadow:0 0 12px var(--up),0 0 26px rgba(43,255,136,.55);margin-right:11px;vertical-align:middle}
nav{position:relative;margin-top:10px;font-size:14px}
nav a{color:var(--accent2);margin-right:18px;text-decoration:none;padding-bottom:2px;border-bottom:1px solid transparent}
nav a:hover{color:var(--accent);border-bottom-color:var(--accent)}
nav a.on{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
.banner{background:rgba(15,22,20,.85);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:11px 14px;margin:18px 0;font-size:14px;color:var(--fg);backdrop-filter:blur(4px)}
.banner strong{color:var(--accent)}
h1{font-size:27px;line-height:1.25;margin:22px 0 8px;color:var(--strong);letter-spacing:-.2px}
h2{font-size:21px;margin:36px 0 10px;padding-top:12px;color:var(--accent);border-top:1px solid var(--line);position:relative;text-shadow:0 0 22px rgba(43,255,136,.35)}
h2::before{content:"";position:absolute;top:-1px;left:0;width:64px;height:2px;background:linear-gradient(90deg,var(--accent),var(--cyan));box-shadow:0 0 10px rgba(43,255,136,.6)}
h3{font-size:17px;margin:24px 0 6px;color:var(--strong)}
strong{color:var(--strong)}
a{color:var(--cyan)}
a:hover{color:#fff}
code{background:var(--panel2);color:var(--accent);padding:1px 6px;border-radius:4px;font-size:.92em}
table{border-collapse:separate;border-spacing:0;font-size:13px;margin:14px 0;display:block;overflow-x:auto;max-width:100%;border:1px solid var(--line);border-radius:10px;background:rgba(15,22,20,.9)}
th,td{border-bottom:1px solid var(--line);padding:7px 10px;text-align:left;white-space:nowrap}
tr:last-child td{border-bottom:0}
th{background:var(--panel2);color:var(--accent);font-weight:600;position:sticky;top:0}
tbody tr:hover td{background:rgba(43,255,136,.06)}
td.up{color:var(--up);font-weight:600}
td.down{color:var(--down);font-weight:600}
ul{padding-left:22px}
li{margin:4px 0}
li::marker{color:var(--accent)}
hr{border:0;border-top:1px solid var(--line)}
.charts h2{margin-top:30px}
.chart-card{background:rgba(15,22,20,.9);border:1px solid var(--line);border-radius:12px;padding:14px 14px 10px;margin:16px 0;overflow-x:auto;box-shadow:0 0 0 1px rgba(43,255,136,.04),0 12px 30px rgba(0,0,0,.35)}
.chart-card h3{margin:0 0 2px;color:var(--strong)}
.chart-card .sub{margin:0 0 8px;color:var(--muted);font-size:13px}
.chart-card svg{display:block;width:100%;min-width:680px;height:auto}
.chart-card svg text{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.chart-card svg .lbl{fill:var(--strong);font-size:13px;font-weight:700}
.chart-card svg .cls{fill:var(--muted);font-weight:600}
.chart-card svg .tick{fill:var(--muted);font-size:11.5px}
.chart-card svg .val{fill:var(--strong);font-size:12.5px;font-weight:700;paint-order:stroke;stroke:#0F1614;stroke-width:3.5px;stroke-linejoin:round}
.chart-card svg .pos{fill:var(--up);font-size:11.5px;font-weight:700}
.chart-card svg .neg{fill:var(--down);font-size:11.5px;font-weight:700}
.chart-card svg .warn{fill:var(--warn);font-size:11.5px;font-weight:700}
.chart-card svg .grid{stroke:var(--line);stroke-width:1}
footer{color:var(--muted);font-size:13px;padding-top:26px;padding-bottom:44px;border-top:1px solid var(--line);margin-top:36px}
.list li{margin:9px 0}
::selection{background:var(--accent);color:#04120a}
@media (max-width:700px){header .deco{display:none}body{font-size:15px}h1{font-size:23px}h2{font-size:19px}}
"""

PAGE = """<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0B0C10">
<title>{title}</title>
<meta name="description" content="{desc}">
<style>{css}</style>
</head>
<body>
<header>
{deco}
<a class="brand" href="{base}index.html">romangpw.pl · skaner GPW</a>
<nav>{nav}</nav>
</header>
<main>
{body}
</main>
<footer>{disclaimer}<br>Dane z publicznych źródeł (m.in. biznesradar.pl, bankier.pl), mogą zawierać błędy lub opóźnienia. Raporty generowane automatycznie.</footer>
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "dee8fe193ffe4484bef9d4691b8d77d2"}}'></script>
</body>
</html>
"""


DIVS = ROOT / "dywidendy"
DESC_SWING = "Dzienny skaner swing GPW — raport przed otwarciem sesji."
DESC_DIV = "Spółki GPW regularnie wypłacające dywidendę, w trendzie wzrostowym, przed spodziewanym ogłoszeniem dywidendy."
TABS = [("swing", "index.html", "Swing"), ("div", "dywidendy.html", "Dywidendy"),
        ("arch", "archiwum.html", "Archiwum swing"), ("darch", "dywidendy-archiwum.html", "Archiwum dywidend")]


def md_files(folder):
    return sorted(folder.glob("20??-??-??.md")) if folder.exists() else []


def report_files():
    return md_files(REPORTS)


def pretty_date(stem):
    import datetime as dt

    d = dt.date.fromisoformat(stem)
    return f"{DAYS[d.weekday()]} {d.day}.{d.month:02d}.{d.year}"


def render_md(text, ref=None):
    md = markdown.Markdown(extensions=["tables", "sane_lists", "toc"], extension_configs={"toc": {"toc_depth": "2-3"}})
    out = md.convert(text)
    # Koloruje komórki z samą zmianą procentową: +x% zielony, −x% czerwony.
    out = re.sub(r"<td>(\+\s?\d[\d\s,.]*%)</td>", r'<td class="up">\1</td>', out)
    out = re.sub(r"<td>([\u2212-]\s?\d[\d\s,.]*%)</td>", r'<td class="down">\1</td>', out)
    charts = render_charts(text, ref)
    if charts:
        for m in re.finditer(r"<table>.*?</table>", out, flags=re.S):
            if "<th>Suma</th>" in m.group(0):
                out = out[:m.end()] + "\n" + charts + out[m.end():]
                break
    return out


def nav_html(active, base):
    return "".join(
        f'<a href="{base}{href}"' + (' class="on"' if key == active else "") + f">{label}</a>"
        for key, href, label in TABS
    )


def page(title, body, base="", active="swing", desc=DESC_SWING):
    return PAGE.format(title=html.escape(title), css=CSS, base=base, body=body, disclaimer=DISCLAIMER,
                       deco=deco_svg(), nav=nav_html(active, base), desc=html.escape(desc))


def build_section(files, folder, out_name, arch_name, label, active, arch_active, desc, title_prefix, root_base):
    """Buduje raporty jednego rodzaju. Zwraca najnowszą datę albo None."""
    import datetime as dt

    if not files:
        if out_name != "index.html":
            body = ('<div class="banner">Pierwszy raport w przygotowaniu. Zakładka pokaże spółki regularnie wypłacające '
                    'dywidendę, które jeszcze jej nie ogłosiły, z szacowanym oknem ogłoszenia.</div>')
            (ROOT / out_name).write_text(page(title_prefix, body, active=active, desc=desc), encoding="utf-8")
        return None
    sub = folder.name
    for f in files:
        stem = f.stem
        body = (f'<div class="banner">{label} z dnia <strong>{pretty_date(stem)}</strong> · '
                f'<a href="../{arch_name}">archiwum</a></div>\n' + render_md(f.read_text(encoding="utf-8"), dt.date.fromisoformat(stem)))
        (folder / f"{stem}.html").write_text(page(f"{title_prefix} {stem}", body, base="../", active=active, desc=desc), encoding="utf-8")
    latest = files[-1]
    stem = latest.stem
    body = (f'<div class="banner">Najnowszy raport: <strong>{pretty_date(stem)}</strong>. '
            f'<a href="{arch_name}">Poprzednie raporty</a></div>\n'
            + render_md(latest.read_text(encoding="utf-8"), dt.date.fromisoformat(stem)))
    (ROOT / out_name).write_text(page(f"{title_prefix} — {stem}", body, active=active, desc=desc), encoding="utf-8")
    items = "\n".join(
        f'<li><a href="{sub}/{f.stem}.html">{pretty_date(f.stem)}</a> · <a href="{sub}/{f.name}">.md</a></li>'
        for f in reversed(files)
    )
    arch = f'<h1>Archiwum raportów — {title_prefix.lower()}</h1>\n<ul class="list">\n{items}\n</ul>'
    (ROOT / arch_name).write_text(page(f"Archiwum — {title_prefix}", arch, active=arch_active, desc=desc), encoding="utf-8")
    return stem


def main():
    sw = build_section(report_files(), REPORTS, "index.html", "archiwum.html", "Raport", "swing", "arch",
                       DESC_SWING, "GPW swing", "")
    if sw is None:
        print("Brak raportów w reports/", file=sys.stderr)
        return 1
    dv = build_section(md_files(DIVS), DIVS, "dywidendy.html", "dywidendy-archiwum.html", "Raport dywidendowy", "div", "darch",
                       DESC_DIV, "Dywidendy GPW", "")
    print(f"Zbudowano: swing {len(report_files())} (najnowszy {sw}); dywidendy {len(md_files(DIVS))}" + (f" (najnowszy {dv})" if dv else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
