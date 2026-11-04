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
:root{--bg:#fff;--fg:#1a1d21;--muted:#5b6470;--line:#d9dee5;--accent:#0b5cad;--head:#f1f4f8;--warn:#fff4e0}
@media (prefers-color-scheme:dark){:root{--bg:#14171b;--fg:#e6e9ee;--muted:#9aa4b2;--line:#2c333b;--accent:#6db3ff;--head:#1d2228;--warn:#2b2417}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header,main,footer{max-width:1100px;margin:0 auto;padding:0 16px}
header{padding-top:20px;padding-bottom:8px;border-bottom:1px solid var(--line)}
header a.brand{font-weight:700;font-size:18px;color:var(--fg);text-decoration:none}
nav{margin-top:6px;font-size:14px}
nav a{color:var(--accent);margin-right:14px;text-decoration:none}
.banner{background:var(--warn);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:16px 0;font-size:14px}
h1{font-size:26px;line-height:1.25;margin:20px 0 8px}
h2{font-size:21px;margin:30px 0 8px;padding-top:6px;border-top:1px solid var(--line)}
h3{font-size:17px;margin:22px 0 6px}
a{color:var(--accent)}
code{background:var(--head);padding:1px 5px;border-radius:4px;font-size:.92em}
table{border-collapse:collapse;font-size:13px;margin:12px 0;display:block;overflow-x:auto;max-width:100%}
th,td{border:1px solid var(--line);padding:5px 8px;text-align:left;white-space:nowrap}
th{background:var(--head);position:sticky;top:0}
ul{padding-left:22px}
li{margin:3px 0}
footer{color:var(--muted);font-size:13px;padding-top:24px;padding-bottom:40px}
.list li{margin:8px 0}
"""

PAGE = """<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
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
    return md.convert(text)


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
