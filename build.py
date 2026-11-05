#!/usr/bin/env python3
"""Buduje statyczną stronę z raportów Markdown w reports/.

Wynik: index.html (najnowszy raport), reports/<data>.html, archiwum.html.
Wymaga pakietu `markdown` (pip install markdown).
"""
import html
import re
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
DAYS = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
DISCLAIMER = "Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna."

CSS = """
:root{
  --bg:#0B0C10;--panel:#14181F;--panel2:#1F2833;--line:#2A3441;
  --fg:#C5C6C7;--strong:#F2F4F5;--muted:#8A94A0;
  --accent:#66FCF1;--accent2:#45A29E;--violet:#9B6BFF;
  --up:#2BFF88;--down:#FF5C7A;--warn:#FFB347;
}
*{box-sizing:border-box}
html{color-scheme:dark}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  background-image:radial-gradient(900px 380px at 85% -120px,rgba(155,107,255,.16),transparent 70%),radial-gradient(800px 360px at 5% -140px,rgba(102,252,241,.12),transparent 70%);
  background-repeat:no-repeat}
header,main,footer{max-width:1100px;margin:0 auto;padding:0 16px}
header{padding-top:22px;padding-bottom:12px;border-bottom:1px solid var(--line)}
header a.brand{font-weight:800;font-size:19px;letter-spacing:.2px;color:var(--strong);text-decoration:none}
header a.brand::before{content:"";display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--up);box-shadow:0 0 10px var(--up);margin-right:10px;vertical-align:middle}
nav{margin-top:8px;font-size:14px}
nav a{color:var(--accent2);margin-right:16px;text-decoration:none;padding-bottom:2px;border-bottom:1px solid transparent}
nav a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.banner{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:11px 14px;margin:18px 0;font-size:14px;color:var(--fg)}
.banner strong{color:var(--strong)}
h1{font-size:27px;line-height:1.25;margin:22px 0 8px;color:var(--strong);letter-spacing:-.2px}
h2{font-size:21px;margin:34px 0 10px;padding-top:12px;color:var(--accent);border-top:1px solid var(--line);position:relative}
h2::before{content:"";position:absolute;top:-1px;left:0;width:56px;height:2px;background:linear-gradient(90deg,var(--accent),var(--violet))}
h3{font-size:17px;margin:24px 0 6px;color:var(--strong)}
strong{color:var(--strong)}
a{color:var(--accent)}
a:hover{color:#fff}
code{background:var(--panel2);color:var(--accent);padding:1px 6px;border-radius:4px;font-size:.92em}
table{border-collapse:separate;border-spacing:0;font-size:13px;margin:14px 0;display:block;overflow-x:auto;max-width:100%;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
th,td{border-bottom:1px solid var(--line);padding:7px 10px;text-align:left;white-space:nowrap}
tr:last-child td{border-bottom:0}
th{background:var(--panel2);color:var(--accent);font-weight:600;position:sticky;top:0;text-transform:none}
tbody tr:hover td{background:rgba(102,252,241,.05)}
td.up{color:var(--up);font-weight:600}
td.down{color:var(--down);font-weight:600}
ul{padding-left:22px}
li{margin:4px 0}
li::marker{color:var(--accent2)}
hr{border:0;border-top:1px solid var(--line)}
footer{color:var(--muted);font-size:13px;padding-top:26px;padding-bottom:44px;border-top:1px solid var(--line);margin-top:36px}
.list li{margin:9px 0}
::selection{background:var(--violet);color:#fff}
@media (max-width:600px){body{font-size:15px}h1{font-size:23px}h2{font-size:19px}}
"""

PAGE = """<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0B0C10">
<title>{title}</title>
<meta name="description" content="Dzienny skaner swing GPW — raport przed otwarciem sesji.">
<style>{css}</style>
</head>
<body>
<header>
<a class="brand" href="{base}index.html">romangpw.pl · skaner swing GPW</a>
<nav><a href="{base}index.html">Najnowszy raport</a><a href="{base}archiwum.html">Archiwum</a></nav>
</header>
<main>
{body}
</main>
<footer>{disclaimer}<br>Dane z publicznych źródeł (m.in. biznesradar.pl, bankier.pl), mogą zawierać błędy lub opóźnienia. Raport generowany automatycznie w dni robocze przed otwarciem GPW.</footer>
</body>
</html>
"""


def report_files():
    return sorted(REPORTS.glob("20??-??-??.md"))


def pretty_date(stem):
    import datetime as dt

    d = dt.date.fromisoformat(stem)
    return f"{DAYS[d.weekday()]} {d.day}.{d.month:02d}.{d.year}"


def render_md(text):
    md = markdown.Markdown(extensions=["tables", "sane_lists", "toc"], extension_configs={"toc": {"toc_depth": "2-3"}})
    out = md.convert(text)
    # Koloruje komórki z samą zmianą procentową: +x% zielony, −x% czerwony.
    out = re.sub(r"<td>(\+\s?\d[\d\s,.]*%)</td>", r'<td class="up">\1</td>', out)
    out = re.sub(r"<td>([\u2212-]\s?\d[\d\s,.]*%)</td>", r'<td class="down">\1</td>', out)
    return out


def page(title, body, base=""):
    return PAGE.format(title=html.escape(title), css=CSS, base=base, body=body, disclaimer=DISCLAIMER)


def main():
    files = report_files()
    if not files:
        print("Brak raportów w reports/", file=sys.stderr)
        return 1

    for f in files:
        stem = f.stem
        text = f.read_text(encoding="utf-8")
        body = f'<div class="banner">Raport z dnia <strong>{pretty_date(stem)}</strong> · <a href="../archiwum.html">archiwum</a></div>\n' + render_md(text)
        (REPORTS / f"{stem}.html").write_text(page(f"GPW swing {stem}", body, base="../"), encoding="utf-8")

    latest = files[-1]
    stem = latest.stem
    body = (
        f'<div class="banner">Najnowszy raport: <strong>{pretty_date(stem)}</strong>. '
        'Aktualizacja w dni robocze przed otwarciem GPW. <a href="archiwum.html">Poprzednie raporty</a></div>\n'
        + render_md(latest.read_text(encoding="utf-8"))
    )
    (ROOT / "index.html").write_text(page(f"GPW swing — {stem}", body), encoding="utf-8")

    items = "\n".join(
        f'<li><a href="reports/{f.stem}.html">{pretty_date(f.stem)}</a> · <a href="reports/{f.name}">.md</a></li>'
        for f in reversed(files)
    )
    arch = f'<h1>Archiwum raportów</h1>\n<ul class="list">\n{items}\n</ul>'
    (ROOT / "archiwum.html").write_text(page("Archiwum — GPW swing", arch), encoding="utf-8")
    print(f"Zbudowano {len(files)} raport(ów); najnowszy: {stem}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
