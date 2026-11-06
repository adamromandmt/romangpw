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

import charts
from charts import deco_svg, render_charts
import portfel

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
DAYS = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

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
header a.brand{position:relative;display:inline-flex;align-items:center;gap:12px;text-decoration:none;color:var(--strong)}
header a.brand .logo{width:46px;height:46px;flex:none;filter:drop-shadow(0 0 14px rgba(124,240,176,.28))}
header a.brand .wm{font-size:26px;font-weight:800;letter-spacing:-.4px;line-height:1}
header a.brand .wm b{font-weight:800;background:linear-gradient(90deg,#8DF2B8,#4FA7AB);-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent}
header a.brand:hover .wm{opacity:.92}
nav{position:relative;margin-top:10px;font-size:14px}
nav a{color:var(--accent2);margin-right:18px;text-decoration:none;padding-bottom:2px;border-bottom:1px solid transparent}
nav a:hover{color:var(--accent);border-bottom-color:var(--accent)}
nav a.on{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
.topbar{position:relative;display:flex;align-items:center;margin:-6px 0 12px}
.lang{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:rgba(15,22,20,.85);font-size:12px;font-weight:700;letter-spacing:.06em}
.lang a,.lang span{padding:4px 12px;text-decoration:none;color:var(--muted)}
.lang a:hover{color:var(--accent)}
.lang .cur{background:var(--accent);color:#04120a}
.subtabs{display:inline-flex;margin:18px 0 0;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:rgba(15,22,20,.85);font-size:13px;font-weight:600}
.subtabs a,.subtabs span{padding:6px 18px;text-decoration:none;color:var(--accent2)}
.subtabs a:hover{color:var(--accent)}
.subtabs .cur{background:var(--accent);color:#04120a}
.news-item{background:rgba(15,22,20,.9);border:1px solid var(--line);border-radius:12px;padding:4px 18px 14px;margin:16px 0;box-shadow:0 0 0 1px rgba(43,255,136,.04),0 10px 24px rgba(0,0,0,.28)}
.news-item h3{margin:14px 0 8px;font-size:18px;line-height:1.35;color:var(--strong)}
.news-item p{margin:8px 0}
.news-item p em{color:var(--muted);font-size:13px}
.news>h2:first-child{margin-top:8px}
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

CSS += portfel.CSS_EXTRA

PAGE = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0B0C10">
<link rel="icon" type="image/svg+xml" href="{root}favicon.svg">
<title>{title}</title>
<meta name="description" content="{desc}">
{alt}
<style>{css}</style>
</head>
<body>
<header>
{deco}
<div class="topbar">{langsw}</div>
<a class="brand" href="{base}index.html" aria-label="{brand}" title="GPW Radar">{logo}</a>
<nav>{nav}</nav>
</header>
<main>
{body}
</main>
<footer>{disclaimer}<br>{footer}</footer>
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "1968667fc753428b8344b96f81a99adb"}}'></script>
</body>
</html>
"""


DIVS = ROOT / "dywidendy"
REPORTS_EN = ROOT / "reports-en"
DIVS_EN = ROOT / "dywidendy-en"
NEWS = ROOT / "newsy"
NEWS_EN = ROOT / "newsy-en"
LANGS = ("pl", "en")

# Logo: znak radaru (pierścienie, wskazówka skanu i „odbicie" kursu) w ramce z gradientem jasna zieleń -> złamany morski błękit + napis GPW Radar.
MARK = (
    '<defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8DF2B8"/>'
    '<stop offset="1" stop-color="#4FA7AB"/></linearGradient></defs>'
    '<rect x="1.5" y="1.5" width="45" height="45" rx="13" fill="#0F1614" stroke="url(#lg)" stroke-width="2"/>'
    '<circle cx="24" cy="25" r="14" fill="none" stroke="url(#lg)" stroke-width="2.2" opacity=".55"/>'
    '<circle cx="24" cy="25" r="7.5" fill="none" stroke="url(#lg)" stroke-width="2.2" opacity=".8"/>'
    '<path d="M24 25 L24 11 A14 14 0 0 1 36.1 18 Z" fill="url(#lg)" opacity=".32"/>'
    '<line x1="24" y1="25" x2="36.1" y2="18" stroke="url(#lg)" stroke-width="3" stroke-linecap="round"/>'
    '<circle cx="24" cy="25" r="2.6" fill="#8DF2B8"/>'
    '<circle cx="19" cy="15.5" r="2.8" fill="#8DF2B8"/>'
)
LOGO = (f'<svg class="logo" viewBox="0 0 48 48" role="img" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">{MARK}</svg>'
        '<span class="wm">GPW <b>Radar</b></span>')
FAVICON = f'<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">{MARK}</svg>'


# Nazwy plików stron: klucz -> (polska, angielska). Polska wersja leży w korzeniu, angielska w en/.
FILES = {
    "news": ("newsy.html", "news.html"),
    "swing": ("index.html", "index.html"),
    "div": ("dywidendy.html", "dividends.html"),
    "meth": ("metodologia-swing.html", "methodology-swing.html"),
    "arch": ("archiwum.html", "archive.html"),
    "darch": ("dywidendy-archiwum.html", "dividends-archive.html"),
}
# Podkatalogi z raportami dziennymi: (swing, dywidendy)
SUBDIRS = {"pl": ("reports", "dywidendy"), "en": ("reports", "dividends")}
MD_SRC = {"pl": (REPORTS, DIVS), "en": (REPORTS_EN, DIVS_EN)}

UI = {
    "pl": {
        "brand": "GPW Radar — skaner GPW",
        "disclaimer": "Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.",
        "footer": "Dane z publicznych źródeł (m.in. biznesradar.pl, bankier.pl), mogą zawierać błędy lub opóźnienia. Raporty generowane automatycznie.",
        "tabs": {"news": "Newsy dnia", "swing": "Swing Raport", "div": "Dywidendy", "port": "Portfel {n}", "meth": "Swing Metodologia",
                 "arch": "Archiwum"},
        "sub": {"arch": "Swing", "darch": "Dywidendy"},
        "desc_swing": "Dzienny skaner swing GPW — raport przed otwarciem sesji.",
        "desc_news": "Newsy dnia GPW: najważniejsze komunikaty spółek i wydarzenia rynkowe, bez emocji, ze źródłami.",
        "news_title": "Newsy dnia", "news_label": "Wydanie", "news_prev": "Wcześniejsze wydania", "news_latest": "Najnowsze wydanie",
        "news_empty": "Pierwsze wydanie w przygotowaniu. Zakładka pokazuje tylko istotne informacje; w dni bez ważnych wiadomości nie powstaje nowe wydanie.",
        "desc_div": "Spółki GPW regularnie wypłacające dywidendę, w trendzie wzrostowym, przed spodziewanym ogłoszeniem dywidendy.",
        "desc_port": "Portfel Swing: wirtualny sprawdzian prognoz ze skanera swing (kupno i sprzedaż według celów i stopów).",
        "desc_meth": "Prosty opis, jak działa dzienny skaner swing GPW: kroki i powody.",
        "title_meth": "Swing Metodologia — jak działa monitor",
        "swing_title": "GPW swing", "div_title": "Dywidendy GPW",
        "swing_label": "Raport", "div_label": "Raport dywidendowy",
        "of_day": "z dnia", "archive": "archiwum", "latest": "Najnowszy raport", "prev": "Poprzednie raporty",
        "arch_h1": "Archiwum raportów — {t}", "arch_title": "Archiwum — {t}",
        "placeholder": "Pierwszy raport w przygotowaniu. Zakładka pokaże spółki regularnie wypłacające dywidendę, "
                       "które jeszcze jej nie ogłosiły, z szacowanym oknem ogłoszenia.",
        "untranslated": "",
        "port_title": "Portfel {n}",
        "built": "Zbudowano",
    },
    "en": {
        "brand": "GPW Radar — WSE scanner",
        "disclaimer": "Screening exercise under the given framework, not investment advice.",
        "footer": "Data from public sources (incl. biznesradar.pl, bankier.pl) may contain errors or delays. Reports are generated automatically. Polish is the original language of the reports.",
        "tabs": {"news": "News of the day", "swing": "Swing Report", "div": "Dividends", "port": "{n} Portfolio", "meth": "Swing Methodology",
                 "arch": "Archive"},
        "sub": {"arch": "Swing", "darch": "Dividends"},
        "desc_swing": "Daily swing-trading scanner for the Warsaw Stock Exchange (GPW) — a report before the open.",
        "desc_news": "News of the day for the Warsaw Stock Exchange (GPW): the most important company announcements and market events, without emotion, with sources.",
        "news_title": "News of the day", "news_label": "Issue", "news_prev": "Earlier issues", "news_latest": "Latest issue",
        "news_empty": "The first issue is in preparation. This tab shows only significant information; on days without important news no new issue is published.",
        "desc_div": "GPW stocks that pay regular dividends, are in an uptrend and have not yet announced the dividend.",
        "desc_port": "Swing Portfolio: a virtual check of the swing scanner's forecasts (buying and selling at targets and stops).",
        "desc_meth": "A plain-language description of how the daily GPW swing scanner works: the steps and the reasons.",
        "title_meth": "Swing Methodology — how the monitor works",
        "swing_title": "GPW swing", "div_title": "GPW dividends",
        "swing_label": "Report", "div_label": "Dividend report",
        "of_day": "dated", "archive": "archive", "latest": "Latest report", "prev": "Previous reports",
        "arch_h1": "Report archive — {t}", "arch_title": "Archive — {t}",
        "placeholder": "The first report is in preparation. This tab will show stocks that pay regular dividends and have not yet "
                       "announced one, with an estimated announcement window.",
        "untranslated": "This page has not been translated into English yet — it is shown in Polish.",
        "port_title": "{n} Portfolio",
        "built": "Built",
    },
}

CSS += ""


def md_files(folder):
    return sorted(folder.glob("20??-??-??.md")) if folder.exists() else []


def report_files():
    return md_files(REPORTS)


def pretty_date(stem, lang="pl"):
    import datetime as dt

    d = dt.date.fromisoformat(stem)
    if lang == "en":
        return f"{DAYS_EN[d.weekday()]} {d.day} {MONTHS_EN[d.month - 1]} {d.year}"
    return f"{DAYS[d.weekday()]} {d.day}.{d.month:02d}.{d.year}"


def render_md(text, ref=None, lang="pl", chart_text=None):
    """text: treść do pokazania; chart_text: polski Markdown, z którego budujemy wykresy (domyślnie text)."""
    md = markdown.Markdown(extensions=["tables", "sane_lists", "toc"], extension_configs={"toc": {"toc_depth": "2-3"}})
    out = md.convert(text)
    # Koloruje komórki z samą zmianą procentową: +x% zielony, −x% czerwony.
    out = re.sub(r"<td>(\+\s?\d[\d\s,.]*%)</td>", r'<td class="up">\1</td>', out)
    out = re.sub(r"<td>([−-]\s?\d[\d\s,.]*%)</td>", r'<td class="down">\1</td>', out)
    charts.LANG = lang
    try:
        ch = render_charts(chart_text if chart_text is not None else text, ref)
    finally:
        charts.LANG = "pl"
    if ch:
        for m in re.finditer(r"<table>.*?</table>", out, flags=re.S):
            if "<th>Suma</th>" in m.group(0) or "<th>Total</th>" in m.group(0):
                out = out[:m.end()] + "\n" + ch + out[m.end():]
                break
    return out


def tabs_for(lang, ports):
    u = UI[lang]["tabs"]
    tabs = [("news", u["news"]), ("swing", u["swing"])]
    tabs += [(f"port-{k}", u["port"].format(n=k.capitalize())) for k in ports]
    tabs += [("meth", u["meth"]), ("div", u["div"]), ("arch", u["arch"])]
    return tabs


def fname(key, lang):
    i = LANGS.index(lang)
    if key in FILES:
        return FILES[key][i]
    k = key.split("-", 1)[1]  # port-<strategia>
    return (f"portfel-{k}.html", f"portfolio-{k}.html")[i]


PORTS = []  # uzupełniane w main()


def nav_html(active, lang, base):
    return "".join(
        f'<a href="{base}{fname(key, lang)}"' + (' class="on"' if key == active or (key == "arch" and active == "darch") else "") + f">{html.escape(label)}</a>"
        for key, label in tabs_for(lang, PORTS)
    )


def page(title, body, lang="pl", active="swing", desc="", sub=False, counter=None):
    """sub: strona leży w podkatalogu (reports/<data>.html). counter: (ścieżka PL, ścieżka EN) tej samej strony,
    każda względem korzenia swojej wersji językowej."""
    u = UI[lang]
    base = "../" if sub else ""
    root = base if lang == "pl" else base + "../"      # ścieżka do korzenia serwisu
    en_root = root + "en/"
    pl_href = root + counter[0] if counter else root + "index.html"
    en_href = en_root + counter[1] if counter else en_root + "index.html"
    if lang == "pl":
        sw = f'<span class="cur">PL</span><a href="{en_href}" hreflang="en" lang="en" title="English">EN</a>'
    else:
        sw = f'<a href="{pl_href}" hreflang="pl" lang="pl" title="Polski">PL</a><span class="cur">EN</span>'
    alt = (f'<link rel="alternate" hreflang="pl" href="{pl_href}">\n<link rel="alternate" hreflang="en" href="{en_href}">'
           if counter else "")
    return PAGE.format(title=html.escape(title), css=CSS, base=base, body=body, disclaimer=u["disclaimer"], footer=u["footer"],
                       deco=deco_svg(), nav=nav_html(active, lang, base), desc=html.escape(desc), lang=lang,
                       langsw=f'<div class="lang" role="group" aria-label="Language">{sw}</div>', brand=u["brand"], logo=LOGO, root=root, alt=alt)


def subtabs(lang, active):
    """Podzakładki archiwum (Swing / Dywidendy) — dwie strony, wspólna zakładka „Archiwum"."""
    sub = UI[lang]["sub"]
    links = "".join(
        (f'<span class="cur">{html.escape(label)}</span>' if key == active else f'<a href="{fname(key, lang)}">{html.escape(label)}</a>')
        for key, label in sub.items())
    return f'<div class="subtabs" role="group">{links}</div>\n'


def md_text(lang, folder_pl, stem, kind):
    """Zwraca (tekst do pokazania, tekst polski, czy przetłumaczone)."""
    pl = (folder_pl / f"{stem}.md").read_text(encoding="utf-8")
    if lang == "pl":
        return pl, pl, True
    src = (NEWS_EN if kind == "news" else MD_SRC["en"][0 if kind == "swing" else 1]) / f"{stem}.md"
    if src.exists():
        return src.read_text(encoding="utf-8"), pl, True
    return pl, pl, False


def cardify(out):
    """Owija każdą pozycję newsów (od <h3> do następnego nagłówka) w <article class="news-item">."""
    parts = re.split(r"(?=<h[23][ >])", out)
    return "".join(f'<article class="news-item">{p}</article>' if p.startswith("<h3") else p for p in parts)


def build_news(lang):
    """Zakładka Newsy dnia: newsy/RRRR-MM-DD.md -> newsy.html (najnowsze wydanie + lista wcześniejszych) i newsy/<data>.html."""
    import datetime as dt

    u = UI[lang]
    out_root = ROOT if lang == "pl" else ROOT / "en"
    out_root.mkdir(exist_ok=True)
    files = md_files(NEWS)
    sub = "newsy" if lang == "pl" else "news"
    out_name = fname("news", lang)
    counter = (fname("news", "pl"), fname("news", "en"))
    desc = u["desc_news"]
    if not files:
        (out_root / out_name).write_text(page(u["news_title"], f'<div class="banner">{u["news_empty"]}</div>', lang, "news", desc, counter=counter), encoding="utf-8")
        return None
    (out_root / sub).mkdir(exist_ok=True)
    md = lambda t: cardify(markdown.Markdown(extensions=["sane_lists"]).convert(t))
    note = lambda ok: "" if ok else f'<div class="banner">{u["untranslated"]}</div>\n'

    def issue(f):
        text, _, ok = md_text(lang, NEWS, f.stem, "news")
        return md(text), ok

    for f in files:
        body, ok = issue(f)
        banner = f'<div class="banner">{u["news_label"]} <strong>{pretty_date(f.stem, lang)}</strong> · <a href="../{out_name}">{u["news_latest"]}</a></div>\n'
        (out_root / sub / f"{f.stem}.html").write_text(
            page(f"{u['news_title']} {f.stem}", banner + note(ok) + '<div class="news">' + body + "</div>", lang, "news", desc, sub=True,
                 counter=(f"newsy/{f.stem}.html", f"news/{f.stem}.html")), encoding="utf-8")
    latest = files[-1]
    body, ok = issue(latest)
    older = [f for f in reversed(files[:-1])]
    prev = ""
    if older:
        items = "\n".join(f'<li><a href="{sub}/{f.stem}.html">{pretty_date(f.stem, lang)}</a></li>' for f in older)
        prev = f'\n<h2>{u["news_prev"]}</h2>\n<ul class="list">\n{items}\n</ul>'
    banner = f'<div class="banner">{u["news_latest"]}: <strong>{pretty_date(latest.stem, lang)}</strong></div>\n'
    (out_root / out_name).write_text(
        page(f"{u['news_title']} — {latest.stem}", banner + note(ok) + '<div class="news">' + body + "</div>" + prev, lang, "news", desc, counter=counter),
        encoding="utf-8")
    return latest.stem


def build_section(lang, kind):
    """Buduje raporty jednego rodzaju (swing/div) dla języka. Zwraca najnowszą datę albo None."""
    import datetime as dt

    u = UI[lang]
    out_root = ROOT if lang == "pl" else ROOT / "en"
    out_root.mkdir(exist_ok=True)
    folder_pl = REPORTS if kind == "swing" else DIVS
    files = md_files(folder_pl)  # zbiór dat zawsze z polskich raportów
    sub = SUBDIRS[lang][0 if kind == "swing" else 1]
    sub_pl = SUBDIRS["pl"][0 if kind == "swing" else 1]
    key, akey = ("swing", "arch") if kind == "swing" else ("div", "darch")
    arch_name, out_name = fname(akey, lang), fname(key, lang)
    label = u["swing_label"] if kind == "swing" else u["div_label"]
    title_prefix = u["swing_title"] if kind == "swing" else u["div_title"]
    desc = u["desc_swing"] if kind == "swing" else u["desc_div"]
    if not files:
        if kind == "div":
            body = f'<div class="banner">{u["placeholder"]}</div>'
            (out_root / out_name).write_text(page(title_prefix, body, lang, key, desc, counter=(fname(key, "pl"), fname(key, "en"))), encoding="utf-8")
        return None
    (out_root / sub).mkdir(exist_ok=True)
    note = lambda ok: "" if ok else f'<div class="banner">{u["untranslated"]}</div>\n'
    for f in files:
        stem = f.stem
        text, pl, ok = md_text(lang, folder_pl, stem, kind)
        body = (f'<div class="banner">{label} {u["of_day"]} <strong>{pretty_date(stem, lang)}</strong> · '
                f'<a href="../{arch_name}">{u["archive"]}</a></div>\n' + note(ok)
                + render_md(text, dt.date.fromisoformat(stem), lang, pl))
        (out_root / sub / f"{stem}.html").write_text(
            page(f"{title_prefix} {stem}", body, lang, key, desc, sub=True, counter=(f"{sub_pl}/{stem}.html", f"{SUBDIRS['en'][0 if kind == 'swing' else 1]}/{stem}.html")),
            encoding="utf-8")
    stem = files[-1].stem
    text, pl, ok = md_text(lang, folder_pl, stem, kind)
    body = (f'<div class="banner">{u["latest"]}: <strong>{pretty_date(stem, lang)}</strong>. '
            f'<a href="{arch_name}">{u["prev"]}</a></div>\n' + note(ok)
            + render_md(text, dt.date.fromisoformat(stem), lang, pl))
    (out_root / out_name).write_text(
        page(f"{title_prefix} — {stem}", body, lang, key, desc, counter=(fname(key, "pl"), fname(key, "en"))), encoding="utf-8")
    items = []
    for f in reversed(files):
        _, _, ok = md_text(lang, folder_pl, f.stem, kind)
        if lang == "pl":
            mdlink = f'{sub}/{f.name}'
            tag = ""
        else:
            mdlink = f'../{MD_SRC["en"][0 if kind == "swing" else 1].name}/{f.name}' if ok else f'../{sub_pl}/{f.name}'
            tag = "" if ok else " (PL)"
        items.append(f'<li><a href="{sub}/{f.stem}.html">{pretty_date(f.stem, lang)}</a>{tag} · <a href="{mdlink}">.md</a></li>')
    arch = subtabs(lang, akey) + f'<h1>{u["arch_h1"].format(t=title_prefix)}</h1>\n<ul class="list">\n' + "\n".join(items) + "\n</ul>"
    (out_root / arch_name).write_text(
        page(u["arch_title"].format(t=title_prefix), arch, lang, akey, desc, counter=(fname(akey, "pl"), fname(akey, "en"))), encoding="utf-8")
    return stem


def main():
    import json

    if not report_files():
        print("Brak raportów w reports/", file=sys.stderr)
        return 1
    (ROOT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (ROOT / "logo.svg").write_text(
        '<svg viewBox="0 0 250 48" xmlns="http://www.w3.org/2000/svg">' + MARK +
        '<text x="60" y="34" font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif" font-size="28" font-weight="800" fill="#F2F7F5">GPW '
        '<tspan fill="url(#lg)">Radar</tspan></text></svg>', encoding="utf-8")
    PORTS[:] = [ps.parent.name for ps in sorted((ROOT / "paper").glob("*/state.json"))]
    msg = []
    for lang in LANGS:
        u = UI[lang]
        out_root = ROOT if lang == "pl" else ROOT / "en"
        nw = build_news(lang)
        sw = build_section(lang, "swing")
        dv = build_section(lang, "div")
        # Portfele wirtualne: każda strategia ma paper/<nazwa>/state.json i stronę portfel-<nazwa>.html (EN: en/portfolio-<nazwa>.html).
        for key in PORTS:
            st = json.loads((ROOT / "paper" / key / "state.json").read_text(encoding="utf-8"))
            n = key.capitalize()
            (out_root / fname(f"port-{key}", lang)).write_text(
                page(u["port_title"].format(n=n), portfel.render(st, n, lang), lang, f"port-{key}", u["desc_port"],
                     counter=(fname(f"port-{key}", "pl"), fname(f"port-{key}", "en"))), encoding="utf-8")
        # Metodologia: PL z metodologia-swing.md, EN z metodologia-swing.en.md (brak => polski tekst + informacja).
        mp = ROOT / ("metodologia-swing.md" if lang == "pl" else "metodologia-swing.en.md")
        banner = ""
        if not mp.exists() and lang == "en":
            mp, banner = ROOT / "metodologia-swing.md", f'<div class="banner">{u["untranslated"]}</div>\n'
        if mp.exists():
            mbody = banner + markdown.Markdown(extensions=["tables", "sane_lists"]).convert(mp.read_text(encoding="utf-8"))
            (out_root / fname("meth", lang)).write_text(
                page(u["title_meth"], mbody, lang, "meth", u["desc_meth"], counter=(fname("meth", "pl"), fname("meth", "en"))), encoding="utf-8")
        msg.append(f"{lang}: newsy {len(md_files(NEWS))} (najnowszy {nw}); swing {len(report_files())} (najnowszy {sw})" + (f", dywidendy {len(md_files(DIVS))} (najnowszy {dv})" if dv else ""))
    print("Zbudowano: " + "; ".join(msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
