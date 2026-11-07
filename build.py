#!/usr/bin/env python3
"""Buduje statyczną stronę z raportów Markdown.

Swing: reports/*.md -> index.html, reports/<data>.html, archiwum.html.
Dywidendy: dywidendy/*.md -> dywidendy.html, dywidendy/<data>.html, dywidendy-archiwum.html.
Wymaga pakietu `markdown` (pip install markdown).
"""
import datetime as dt
import html
import re
import sys
from pathlib import Path

import markdown

import charts
from charts import deco_svg, render_charts
import portfel

ROOT = Path(__file__).resolve().parent
_cname = ROOT / "CNAME"
SITE = "https://" + (_cname.read_text().strip() if _cname.exists() else "www.gpwradar.pl")  # adres serwisu = plik CNAME
BRAND = "GPW Radar"
PAGES = []  # rejestr stron (do sitemap.xml): uzupełniany przez page()
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
html{color-scheme:dark;scroll-padding-top:64px}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}
main:focus{outline:none}
.skip{position:absolute;left:12px;top:-64px;z-index:100;background:var(--accent);color:#04120a;padding:8px 14px;border-radius:8px;font-weight:700;text-decoration:none}
.skip:focus{top:10px}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
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
header nav{position:relative;margin-top:10px;font-size:14px;display:flex;flex-wrap:wrap;gap:6px 18px}
header nav>a,header nav .dd-b{color:var(--accent2);text-decoration:none;padding-bottom:2px;border-bottom:1px solid transparent;white-space:nowrap}
header nav>a:hover,header nav .dd-b:hover,header nav .dd.open .dd-b{color:var(--accent);border-bottom-color:var(--accent)}
header nav>a.on,header nav .dd.on .dd-b{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
/* Zakładka z rozwijanym menu (strategia): przycisk + lista linków. Otwiera ją klik, najechanie myszą i klawiatura (NAV_JS); bez JS działają :hover i :focus-within. */
.dd{position:relative;display:flex}
.dd-b{display:flex;align-items:center;gap:5px;margin:0;padding:0;border:0;background:none;font:inherit;line-height:inherit;cursor:pointer}
.dd-c{width:10px;height:10px;flex:none;transition:transform .15s ease}
.dd.open .dd-c{transform:rotate(180deg)}
.dd-m{display:none;position:absolute;z-index:60;left:-19px;top:calc(100% + 10px);min-width:232px;margin:0;padding:6px;list-style:none;background:rgba(12,18,16,.97);border:1px solid var(--line);border-radius:12px;box-shadow:0 0 0 1px rgba(43,255,136,.05),0 16px 36px rgba(0,0,0,.55);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)}
.dd-m::before{content:"";position:absolute;left:0;right:0;top:-12px;height:12px}
.dd.open .dd-m,html:not(.js) .dd:hover .dd-m,html:not(.js) .dd:focus-within .dd-m{display:block}
.dd-m li{margin:0}
.dd-m a{display:block;padding:9px 12px;border-radius:8px;color:var(--fg);font-size:14px;text-decoration:none;white-space:nowrap}
.dd-m a:hover{background:rgba(43,255,136,.09);color:var(--strong)}
.dd-m a[aria-current=page]{background:rgba(43,255,136,.07);color:var(--accent);font-weight:600}
@media (prefers-reduced-motion:reduce){.dd-c{transition:none}}
@media (max-width:640px){.dd{position:static}.dd-m{left:0;right:0;min-width:0;top:calc(100% + 8px)}.dd-m a{padding:11px 12px;font-size:15px}}
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
/* Tabela siedzi w przewijanym kontenerze (dostępnym z klawiatury); cienie na brzegach pokazują, że jest więcej kolumn. */
.tw{overflow-x:auto;max-width:100%;margin:14px 0;border:1px solid var(--line);border-radius:10px;background-color:rgba(15,22,20,.9);
  background-image:linear-gradient(90deg,#0F1614,rgba(15,22,20,0)),linear-gradient(270deg,#0F1614,rgba(15,22,20,0)),
    radial-gradient(farthest-side at 0 50%,rgba(43,255,136,.28),rgba(43,255,136,0)),radial-gradient(farthest-side at 100% 50%,rgba(43,255,136,.28),rgba(43,255,136,0));
  background-position:left center,right center,left center,right center;background-size:36px 100%,36px 100%,14px 100%,14px 100%;
  background-repeat:no-repeat;background-attachment:local,local,scroll,scroll}
table{border-collapse:separate;border-spacing:0;font-size:13px;min-width:100%}
th,td{border-bottom:1px solid var(--line);padding:7px 10px;text-align:left;white-space:nowrap}
tr:last-child td{border-bottom:0}
th{background:var(--panel2);color:var(--accent);font-weight:600}
tbody tr:hover td{background:rgba(43,255,136,.06)}
.tw.stk1 :is(th,td):first-child,.tw.stk2 :is(th,td):nth-child(-n+2){position:sticky;z-index:1;background:#0F1614}
.tw.stk1 th:first-child,.tw.stk2 th:nth-child(-n+2){background:var(--panel2)}
.tw.stk1 :is(th,td):first-child{left:0;box-shadow:1px 0 0 var(--line)}
.tw.stk2 :is(th,td):first-child{left:0;width:40px;min-width:40px;max-width:40px;text-align:center}
.tw.stk2 :is(th,td):nth-child(2){left:40px;box-shadow:1px 0 0 var(--line)}
.tw.stk1 tbody tr:hover td:first-child,.tw.stk2 tbody tr:hover td:nth-child(-n+2){background:#11201a}
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
.chart-card svg{display:block;width:100%;height:auto}
.chart-card .cv-c{display:none}
@media (max-width:760px){.chart-card .cv-d{display:none}.chart-card .cv-c{display:block}}
.chart-card svg.c .lbl{font-size:14.5px}
.chart-card svg.c .tick{font-size:13px}
.chart-card svg.c .val{font-size:14px}
.chart-card svg.c .pos,.chart-card svg.c .neg,.chart-card svg.c .warn{font-size:13px}
.chart-card h2.ch{margin:0 0 2px;padding:0;border:0;font-size:17px;color:var(--strong);text-shadow:none}
.chart-card h2.ch::before{display:none}
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
/* Lepki pasek skrótów do sekcji długiego raportu */
.toc{position:sticky;top:0;z-index:20;margin:14px -16px 6px;padding:8px 16px;background:rgba(11,12,16,.88);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border-bottom:1px solid var(--line);overflow-x:auto;white-space:nowrap;scrollbar-width:none}
.toc::-webkit-scrollbar{display:none}
.toc a{display:inline-block;margin-right:8px;padding:4px 12px;border:1px solid var(--line);border-radius:999px;background:rgba(15,22,20,.9);color:var(--accent2);font-size:13px;text-decoration:none}
.toc a:hover{color:var(--accent);border-color:var(--accent)}
/* Karty TOP 3 na górze raportu */
.top3{margin:20px 0 6px}
.top3-t{margin:0 0 8px;color:var(--muted);font-size:12px;letter-spacing:.07em;text-transform:uppercase}
.top3-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.t3{position:relative;display:block;overflow:hidden;padding:12px 14px 12px 17px;color:inherit;text-decoration:none;background:rgba(15,22,20,.92);border:1px solid var(--line);border-radius:12px;box-shadow:0 0 0 1px rgba(43,255,136,.04),0 10px 24px rgba(0,0,0,.3)}
.t3::before{content:"";position:absolute;inset:0 auto 0 0;width:3px;background:linear-gradient(var(--accent),var(--cyan))}
.t3:hover{border-color:var(--accent);color:inherit}
.t3-h{display:flex;align-items:baseline;gap:4px 8px;flex-wrap:wrap}
.t3-n{color:var(--accent);font-size:20px;font-weight:800}
.t3-tic{color:var(--strong);font-size:19px;font-weight:800}
.t3-co{color:var(--muted);font-size:13px}
.t3-bd{margin-left:auto;display:inline-flex;align-items:center;gap:8px}
.t3-sc{color:var(--strong);font-size:15px;font-weight:700}
.cls-b{display:inline-block;min-width:24px;padding:1px 8px;border:1px solid var(--line);border-radius:999px;font-size:12px;font-weight:800;text-align:center}
.cls-A{background:rgba(43,255,136,.16);color:var(--up);border-color:rgba(43,255,136,.4)}
.cls-B{background:rgba(102,252,241,.12);color:var(--cyan);border-color:rgba(102,252,241,.35)}
.cls-C{background:rgba(255,179,71,.12);color:var(--warn);border-color:rgba(255,179,71,.35)}
.t3 dl{display:grid;grid-template-columns:repeat(3,minmax(0,auto));justify-content:start;gap:8px 18px;margin:10px 0 0}
.t3 dt{color:var(--muted);font-size:11px;letter-spacing:.04em;text-transform:uppercase}
.t3 dd{margin:0;color:var(--strong);font-size:14px;font-weight:600;white-space:nowrap}
.t3 dl>.w{grid-column:1/-1}
.t3 dd.dn{color:var(--down)}
.t3-w{margin-top:9px;color:var(--muted);font-size:12px}
.t3-w.warn{color:var(--warn);font-weight:600}
/* Archiwum */
.ar-list{list-style:none;padding:0;margin:8px 0}
.ar-list li.ar{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 12px;margin:8px 0;padding:10px 14px;background:rgba(15,22,20,.88);border:1px solid var(--line);border-radius:10px}
.ar-d{font-weight:600}
.ar-l{color:var(--muted);font-size:12px;letter-spacing:.05em;text-transform:uppercase}
.tk{display:inline-block;margin-right:4px;padding:1px 9px;border:1px solid var(--line);border-radius:999px;background:var(--panel2);color:var(--strong);font-size:13px;font-weight:600}
.ar-md{margin-left:auto;color:var(--muted);font-size:12px}
.nf{margin:28px 0 8px;font-size:72px;font-weight:800;line-height:1;background:linear-gradient(90deg,#8DF2B8,#4FA7AB);-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent}
@media (max-width:700px){header .deco{display:none}body{font-size:15px}h1{font-size:23px}h2{font-size:19px}.t3 dl{grid-template-columns:repeat(3,minmax(0,auto));gap:8px 14px}}
@media (max-width:360px){.t3 dl{grid-template-columns:repeat(2,minmax(0,auto))}}
"""

CSS += portfel.CSS_EXTRA

PAGE = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0B0C10">
<script>document.documentElement.classList.add("js")</script>
<link rel="icon" type="image/svg+xml" href="{root}favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="{root}favicon-32.png">
<link rel="apple-touch-icon" href="{root}apple-touch-icon.png">
<link rel="manifest" href="{root}manifest.webmanifest">
<title>{title}</title>
<meta name="description" content="{desc}">
{robots}{seo}
<style>{css}</style>
</head>
<body>
<a class="skip" href="#main">{skip}</a>
<header>
{deco}
<div class="topbar">{langsw}</div>
<a class="brand" href="{base}index.html" aria-label="{brand}" title="GPW Radar">{logo}</a>
<nav aria-label="{navlabel}">{nav}</nav>
</header>
<main id="main" tabindex="-1">
{body}
</main>
<footer>{disclaimer}<br>{footer}</footer>
<script>{navjs}</script>
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "1968667fc753428b8344b96f81a99adb"}}'></script>
</body>
</html>
"""

# Rozwijane menu zakładek-strategii (.dd). Wzorzec „disclosure navigation": przycisk z aria-expanded + lista linków.
# Otwiera: klik/dotyk/Enter (menu zostaje otwarte aż do kliknięcia poza nim, Esc albo ponownego kliku), najechanie myszą
# (zamyka się po zjechaniu, o ile nie kliknięto), strzałka w dół na przycisku. Strzałki/Home/End chodzą po pozycjach,
# Esc zamyka i wraca na przycisk; jednocześnie otwarte jest co najwyżej jedno menu.
NAV_JS = """(function(){
var groups=[].slice.call(document.querySelectorAll(".dd"));
if(!groups.length)return;
groups.forEach(function(g){
var btn=g.querySelector(".dd-b"),items=[].slice.call(g.querySelectorAll(".dd-m a")),pinned=false,timer;
function isOpen(){return g.classList.contains("open")}
function open(){clearTimeout(timer);groups.forEach(function(o){if(o!==g)o.close()});g.classList.add("open");btn.setAttribute("aria-expanded","true")}
function close(){clearTimeout(timer);pinned=false;g.classList.remove("open");btn.setAttribute("aria-expanded","false")}
g.close=close;
btn.addEventListener("click",function(){if(!isOpen()){open();pinned=true}else if(!pinned)pinned=true;else close()});
g.addEventListener("pointerenter",function(e){if(e.pointerType==="mouse")open()});
g.addEventListener("pointerleave",function(e){if(e.pointerType==="mouse"&&!pinned)timer=setTimeout(close,160)});
g.addEventListener("keydown",function(e){
var i=items.indexOf(document.activeElement),k=e.key;
if(k==="Escape"){if(isOpen()){close();btn.focus()}}
else if(k==="ArrowDown"){e.preventDefault();if(!isOpen()){open();pinned=true}items[Math.min(i+1,items.length-1)].focus()}
else if(k==="ArrowUp"&&i>=0){e.preventDefault();if(i>0)items[i-1].focus();else btn.focus()}
else if(k==="Home"&&i>=0){e.preventDefault();items[0].focus()}
else if(k==="End"&&i>=0){e.preventDefault();items[items.length-1].focus()}
});
});
function outside(e){groups.forEach(function(g){if(!g.contains(e.target))g.close()})}
document.addEventListener("pointerdown",outside);
document.addEventListener("focusin",outside);
window.addEventListener("pageshow",function(e){if(e.persisted)groups.forEach(function(g){g.close()})});
})();"""


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
        "groups": {"swing": "Swing"},
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
        "arch_h1": "Archiwum raportów — {t}",
        "arch_t": {"swing": "Archiwum raportów swing", "div": "Archiwum raportów dywidendowych"},
        "t_swing": "Swing Raport", "t_div": "Raport dywidendowy",
        "desc_rep": {"swing": "Raport swing GPW z {d}. TOP 3: {t}. Dzienny skaner przed otwarciem sesji.",
                     "div": "Raport dywidendowy GPW z {d}. TOP 3: {t}. Spółki regularnie płacące dywidendę, w trendzie wzrostowym, przed ogłoszeniem."},
        "skip": "Przejdź do treści", "navlabel": "Główna nawigacja", "langlabel": "Język", "table": "tabela",
        "toc": "Skróty do sekcji", "top3": "TOP 3 na teraz", "top3_lbl": "TOP 3",
        "f_price": "Kurs", "f_entry": "Wejście", "f_stop": "Stop", "f_targets": "Cele C1 / C2", "f_r": "R", "f_window": "Okno ogłoszenia",
        "f_earn": "Raport", "f_earn_in": "Raport kwartalny",
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
        "groups": {"swing": "Swing"},
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
        "arch_h1": "Report archive — {t}",
        "arch_t": {"swing": "Swing report archive", "div": "Dividend report archive"},
        "t_swing": "Swing Report", "t_div": "Dividend report",
        "desc_rep": {"swing": "GPW swing report of {d}. TOP 3: {t}. Daily scanner before the open.",
                     "div": "GPW dividend report of {d}. TOP 3: {t}. Regular dividend payers in an uptrend, before the announcement."},
        "skip": "Skip to content", "navlabel": "Main navigation", "langlabel": "Language", "table": "table",
        "toc": "Jump to section", "top3": "TOP 3 right now", "top3_lbl": "TOP 3",
        "f_price": "Price", "f_entry": "Entry", "f_stop": "Stop", "f_targets": "Targets T1 / T2", "f_r": "R", "f_window": "Announcement window",
        "f_earn": "Earnings", "f_earn_in": "Quarterly results",
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


PL_MONTHS = ["styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec", "lipiec", "sierpień", "wrzesień", "październik", "listopad", "grudzień"]


def sdate(stem, lang="pl"):
    """Krótka data do tytułów: 6.11.2026 / 6 Nov 2026."""
    d = dt.date.fromisoformat(stem)
    return f"{d.day} {MONTHS_EN[d.month - 1][:3]} {d.year}" if lang == "en" else f"{d.day}.{d.month:02d}.{d.year}"


def month_name(stem, lang="pl"):
    d = dt.date.fromisoformat(stem)
    return f"{(MONTHS_EN if lang == 'en' else PL_MONTHS)[d.month - 1]} {d.year}"


LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d{1,2}[.)])\s+\S")


def fix_lists(text):
    """Python-Markdown wymaga pustej linii przed listą. Raporty często zaczynają listę tuż pod pogrubioną etykietą
    (\"**Dlaczego interesująca**\" + \"- punkt\"), co bez poprawki skleja punkty w jeden akapit. Wstawiamy brakującą
    pustą linię (poza blokami kodu)."""
    out, fence = [], False
    for ln in text.split("\n"):
        if ln.lstrip().startswith("```"):
            fence = not fence
        prev = out[-1] if out else ""
        if (not fence and LIST_ITEM.match(ln) and prev.strip() and not LIST_ITEM.match(prev)
                and not prev.startswith((" ", "\t", "#", ">"))):
            out.append("")
        out.append(ln)
    return "\n".join(out)


def md_html(text, extensions=("sane_lists",), **cfg):
    return markdown.Markdown(extensions=list(extensions), **cfg).convert(fix_lists(text))


H_OR_TABLE = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>|<table>(.*?)</table>", re.S)


def wrap_tables(body, label_word):
    """Owija każdą tabelę w przewijany kontener (role=region, tabindex=0 => dostępny z klawiatury), dodaje scope do <th>.
    Tabele z kolumnami „# | Tic" dostają przyklejone dwie pierwsze kolumny, a z „Tic" na początku — pierwszą."""
    last = ""

    def rep(m):
        nonlocal last
        if m.group(1):
            last = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
            return m.group(0)
        inner = m.group(3)
        ths = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<th(?:\s[^>]*)?>(.*?)</th>", inner, re.S)]
        inner = re.sub(r"<th>", '<th scope="col">', inner)
        cls = "tw"
        if len(ths) > 2 and ths[0] == "#" and ths[1] == "Tic":
            cls += " stk2"
        elif ths and ths[0] == "Tic":
            cls += " stk1"
        name = f"{last} — {label_word}" if last else label_word
        return f'<div class="{cls}" role="region" aria-label="{html.escape(name, quote=True)}" tabindex="0"><table>{inner}</table></div>'

    return H_OR_TABLE.sub(rep, body)


# ---- karty TOP 3 i pasek sekcji --------------------------------------------------------------------------------
SHORT = [(r"Szczegółowa analiza TOP 5", "Analiza TOP 5"), (r"Rozliczenie", "Rozliczenie"), (r"Metoda i zastrzeżenia", "Metoda"),
         (r"Watchlista", "Watchlista"), (r"Kalendarz okien", "Kalendarz okien"), (r"Detailed analysis of the TOP 5", "TOP 5 analysis"),
         (r"Review of the previous scan", "Review"), (r"Method and caveats", "Method"), (r"Calendar of", "Calendar")]


def short_label(t):
    t = re.sub(r"\s*\(.*?\)", "", t).strip()
    for pat, label in SHORT:
        if re.match(pat, t):
            return label
    return t if len(t) <= 24 else t[:23].rstrip() + "…"


def _cell(row, names=(), prefixes=()):
    for k, v in row.items():
        if k in names or any(k.startswith(x) for x in prefixes):
            return v
    return ""


def top3_rows(md):
    """Wiersze tabeli rankingu dla trzech pozycji z sekcji „TOP 3". Zwraca [] jeśli czegoś nie da się jednoznacznie dopasować."""
    head, rows = charts.parse_ranking(md)
    m = re.search(r"^##\s+.*TOP\s*3.*$", md, re.M)
    if not head or not rows or not m:
        return []
    seg = md[m.end():]
    nxt = re.search(r"^##\s", seg, re.M)
    seg = seg[:nxt.start()] if nxt else seg
    names = re.findall(r"^\s*\d+[.)]\s+\*\*(.+?)\*\*", seg, re.M)[:3]
    found = []
    for nm in names:
        key = nm.strip().casefold()
        row = next((r for r in rows if r.get("Tic", "").casefold() == key), None)
        if row is None:
            row = next((r for r in rows if _cell(r, ("Spółka", "Company")).casefold() == key), None)
        if row is None:
            row = next((r for r in rows if key and _cell(r, ("Spółka", "Company")).casefold().startswith(key)), None)
        if row is None:
            return []
        found.append(row)
    return found if len(found) == 3 else []


def top3_names(md):
    return [(_cell(r, ("Spółka", "Company")) or r.get("Tic", "")) for r in top3_rows(md)]


def cards_html(md, out, lang, kind):
    rows = top3_rows(md)
    if not rows:
        return ""
    u = UI[lang]
    cards = []
    for n, r in enumerate(rows, 1):
        tic, name = r.get("Tic", ""), _cell(r, ("Spółka", "Company"))
        kl = re.match(r"\s*([ABC])", _cell(r, ("Klasa", "Class"), ("Klasa", "Class")))
        score = _cell(r, ("Suma", "Total"))
        r_ = _cell(r, ("R",), ("R (",))
        tg = " / ".join(x for x in (_cell(r, ("C1", "T1")), _cell(r, ("C2", "T2"))) if x)
        win = " – ".join(x for x in (_cell(r, ("Okno od", "Window from")), _cell(r, ("Okno do", "Window to"))) if x)
        items = []
        if kind == "div" and win:
            items.append((u["f_window"], win, "", "w"))   # długa wartość: cały wiersz
        items += [(u["f_price"], _cell(r, (), ("Kurs", "Price")), "", ""),
                  (u["f_entry"], _cell(r, ("Wejście", "Entry"), ("Wej", "Entry")), "", ""), (u["f_stop"], _cell(r, ("Stop",)), "dn", ""),
                  (u["f_targets"], tg, "", ""), (u["f_r"], r_, "", "")]
        dl = "".join(f'<div{" class=w" if w else ""}><dt>{html.escape(k)}</dt><dd class="{c}">{html.escape(v)}</dd></div>'
                     for k, v, c, w in items if v and v not in ("—", "-"))
        earn = _cell(r, ("Raport", "Earnings", "Report"))
        days = re.search(r"\((\d+)\s*(?:dni|dzień|days?)\b", earn)
        warn = bool(days and int(days.group(1)) <= 14)
        ew = (f'<div class="t3-w{" warn" if warn else ""}">{html.escape(u["f_earn_in"])}: {html.escape(earn)}</div>'
              if earn and earn not in ("—", "-") else "")
        m = re.search(r'<h3 id="(' + re.escape(tic.lower()) + r'-[^"]*)"', out)
        g = None if m else re.search(r'<h2 id="([^"]*top-3[^"]*)"', out)
        href = "#" + (m.group(1) if m else g.group(1) if g else "")
        badge = (f'<span class="cls-b cls-{kl.group(1)}">{kl.group(1)}</span>' if kl else "") + (f'<span class="t3-sc">{html.escape(score)}</span>' if score else "")
        co = f'<span class="t3-co">{html.escape(name)}</span>' if name and name.casefold() != tic.casefold() else ""
        cards.append(f'<a class="t3" href="{href}"><div class="t3-h"><span class="t3-n">{n}</span><span class="t3-tic">{html.escape(tic)}</span>'
                     f'{co}<span class="t3-bd">{badge}</span></div><dl>{dl}</dl>{ew}</a>')
    return (f'<section class="top3" aria-label="{html.escape(u["top3"], quote=True)}"><p class="top3-t">{html.escape(u["top3"])}</p>'
            f'<div class="top3-grid">{"".join(cards)}</div></section>\n')


def toc_html(out, lang):
    hs = re.findall(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', out, re.S)
    if len(hs) < 4:
        return ""
    chips = "".join(
        f'<a href="#{i}" title="{html.escape(html.unescape(re.sub(r"<[^>]+>", "", t)), quote=True)}">'
        f'{html.escape(short_label(html.unescape(re.sub(r"<[^>]+>", "", t))))}</a>' for i, t in hs)
    return f'<nav class="toc" aria-label="{html.escape(UI[lang]["toc"], quote=True)}">{chips}</nav>\n'


def add_snapshot(out, md, lang, kind):
    """Wstawia pasek sekcji i karty TOP 3 przed pierwszym nagłówkiem sekcji (po wstępie raportu)."""
    i = out.find("<h2")
    if i < 0:
        return out
    return out[:i] + toc_html(out, lang) + cards_html(md, out, lang, kind) + out[i:]


def render_md(text, ref=None, lang="pl", chart_text=None, kind=None):
    """text: treść do pokazania; chart_text: polski Markdown, z którego budujemy wykresy (domyślnie text)."""
    md = markdown.Markdown(extensions=["tables", "sane_lists", "toc"], extension_configs={"toc": {"toc_depth": "2-3"}})
    out = md.convert(fix_lists(text))
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
    if kind:
        out = add_snapshot(out, text, lang, kind)
    return out


# Menu główne w nagłówku. ("link", klucz strony) = zwykła zakładka; ("menu", klucz grupy, [klucze stron]) = zakładka z rozwijanym menu
# (jedna strategia: raport, portfel, metodologia, archiwum — w tej kolejności). Klucze stron jak w FILES oraz "port-<strategia>"
# (pozycja portfela znika, gdy nie ma paper/<strategia>/state.json). Nazwa grupy: UI[lang]["groups"][klucz grupy].
# Kolejna strategia = kolejny wpis „menu" na tej liście.
MENU = [
    ("link", "news"),
    ("menu", "swing", ["swing", "port-swing", "meth", "arch"]),
    ("link", "div"),
]
NAV_ALIAS = {"darch": "div"}  # archiwum dywidend należy do zakładki Dywidendy (archiwum swing jest w menu Swing)


def tab_label(key, lang):
    u = UI[lang]["tabs"]
    return u["port"].format(n=key.split("-", 1)[1].capitalize()) if key.startswith("port-") else u[key]


def fname(key, lang):
    i = LANGS.index(lang)
    if key in FILES:
        return FILES[key][i]
    k = key.split("-", 1)[1]  # port-<strategia>
    return (f"portfel-{k}.html", f"portfolio-{k}.html")[i]


PORTS = []  # uzupełniane w main()


def nav_html(active, lang, base):
    """Menu w nagłówku: zwykłe zakładki i grupy z rozwijanym menu (patrz MENU). active = klucz bieżącej strony (None = żadna)."""
    active = NAV_ALIAS.get(active, active)
    out = []
    for entry in MENU:
        if entry[0] == "link":
            key = entry[1]
            cur = ' class="on" aria-current="page"' if key == active else ""
            out.append(f'<a href="{base}{fname(key, lang)}"{cur}>{html.escape(tab_label(key, lang))}</a>')
            continue
        _, group, keys = entry
        keys = [k for k in keys if not k.startswith("port-") or k.split("-", 1)[1] in PORTS]
        current = ' aria-current="page"'
        items = "".join(
            f'<li><a href="{base}{fname(k, lang)}"{current if k == active else ""}>{html.escape(tab_label(k, lang))}</a></li>'
            for k in keys)
        name = html.escape(UI[lang]["groups"][group])
        out.append(
            f'<div class="dd{" on" if active in keys else ""}">'
            f'<button type="button" class="dd-b" aria-expanded="false" aria-controls="dd-{group}">{name}'
            '<svg class="dd-c" viewBox="0 0 12 12" aria-hidden="true" focusable="false"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" '
            'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
            f'<ul class="dd-m" id="dd-{group}">{items}</ul></div>')
    return "".join(out)


def canon(path):
    """Pełny adres kanoniczny strony; index.html skracamy do katalogu."""
    u = f"{SITE}/{path}"
    return u[:-len("index.html")] if u.endswith("/index.html") else u


def page(title, body, lang="pl", active="swing", desc="", sub=False, counter=None, lastmod=None, abs_root=False, noindex=False):
    """sub: strona leży w podkatalogu (reports/<data>.html). counter: (ścieżka PL, ścieżka EN) tej samej strony,
    każda względem korzenia swojej wersji językowej. lastmod: data (RRRR-MM-DD) do sitemap.xml.
    abs_root: linki od korzenia serwisu (dla 404.html, serwowanej spod dowolnej ścieżki)."""
    u = UI[lang]
    base = "/" if abs_root else ("../" if sub else "")
    root = "/" if abs_root else (base if lang == "pl" else base + "../")      # ścieżka do korzenia serwisu
    en_root = root + "en/"
    pl_href = root + counter[0] if counter else root + "index.html"
    en_href = en_root + counter[1] if counter else en_root + "index.html"
    if lang == "pl":
        sw = f'<span class="cur">PL</span><a href="{en_href}" hreflang="en" lang="en" title="English">EN</a>'
    else:
        sw = f'<a href="{pl_href}" hreflang="pl" lang="pl" title="Polski">PL</a><span class="cur">EN</span>'
    full_title = title if BRAND in title else f"{title} · {BRAND}"
    seo = ""
    if counter:
        url_pl, url_en = canon(counter[0]), canon("en/" + counter[1])
        url = url_pl if lang == "pl" else url_en
        t, d = html.escape(full_title, quote=True), html.escape(desc, quote=True)
        other = "en_US" if lang == "pl" else "pl_PL"
        seo = (f'<link rel="canonical" href="{url}">\n'
               f'<link rel="alternate" hreflang="pl" href="{url_pl}">\n<link rel="alternate" hreflang="en" href="{url_en}">\n'
               f'<link rel="alternate" hreflang="x-default" href="{url_pl}">\n'
               f'<link rel="alternate" type="application/atom+xml" title="{BRAND}" href="{SITE}/{"feed.xml" if lang == "pl" else "en/feed.xml"}">\n'
               f'<meta property="og:type" content="website">\n<meta property="og:site_name" content="{BRAND}">\n'
               f'<meta property="og:title" content="{t}">\n<meta property="og:description" content="{d}">\n'
               f'<meta property="og:url" content="{url}">\n<meta property="og:locale" content="{"pl_PL" if lang == "pl" else "en_US"}">\n'
               f'<meta property="og:locale:alternate" content="{other}">\n'
               f'<meta property="og:image" content="{SITE}/og-{lang}.png">\n<meta property="og:image:width" content="1200">\n'
               f'<meta property="og:image:height" content="630">\n<meta property="og:image:alt" content="{BRAND}">\n'
               f'<meta name="twitter:card" content="summary_large_image">\n'
               f'<meta name="twitter:image" content="{SITE}/og-{lang}.png">\n')
        PAGES.append({"url": url, "pl": url_pl, "en": url_en, "lastmod": lastmod})
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    body = wrap_tables(body, u["table"])
    return PAGE.format(title=html.escape(full_title), css=CSS, base=base, body=body, disclaimer=u["disclaimer"], footer=u["footer"],
                       deco=deco_svg(), nav=nav_html(active, lang, base), desc=html.escape(desc), lang=lang,
                       langsw=f'<div class="lang" role="group" aria-label="{u["langlabel"]}">{sw}</div>', brand=u["brand"], logo=LOGO, root=root,
                       seo=seo, robots=robots, skip=u["skip"], navlabel=u["navlabel"], navjs=NAV_JS)


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
    md = lambda t: cardify(md_html(t))
    note = lambda ok: "" if ok else f'<div class="banner">{u["untranslated"]}</div>\n'

    def issue(f):
        text, _, ok = md_text(lang, NEWS, f.stem, "news")
        return md(text), ok

    for f in files:
        body, ok = issue(f)
        banner = f'<div class="banner">{u["news_label"]} <strong>{pretty_date(f.stem, lang)}</strong> · <a href="../{out_name}">{u["news_latest"]}</a></div>\n'
        (out_root / sub / f"{f.stem}.html").write_text(
            page(f"{u['news_title']} {sdate(f.stem, lang)}", banner + note(ok) + '<div class="news">' + body + "</div>", lang, "news", desc, sub=True,
                 counter=(f"newsy/{f.stem}.html", f"news/{f.stem}.html"), lastmod=f.stem), encoding="utf-8")
    latest = files[-1]
    body, ok = issue(latest)
    older = [f for f in reversed(files[:-1])]
    prev = ""
    if older:
        items = "\n".join(f'<li><a href="{sub}/{f.stem}.html">{pretty_date(f.stem, lang)}</a></li>' for f in older)
        prev = f'\n<h2>{u["news_prev"]}</h2>\n<ul class="list">\n{items}\n</ul>'
    banner = f'<div class="banner">{u["news_latest"]}: <strong>{pretty_date(latest.stem, lang)}</strong></div>\n'
    (out_root / out_name).write_text(
        page(f"{u['news_title']} {sdate(latest.stem, lang)}", banner + note(ok) + '<div class="news">' + body + "</div>" + prev, lang, "news", desc, counter=counter,
             lastmod=latest.stem),
        encoding="utf-8")
    return latest.stem


def atom_feed(lang, entries):
    """Kanał Atom 1.0 z najnowszymi raportami swing. entries: [(data RRRR-MM-DD, tytuł, adres, opis)] od najnowszego."""
    home = f"{SITE}/" if lang == "pl" else f"{SITE}/en/"
    x = ['<?xml version="1.0" encoding="UTF-8"?>', f'<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="{lang}">',
         f"<title>{html.escape(BRAND)}</title>", f"<subtitle>{html.escape(UI[lang]['desc_swing'])}</subtitle>",
         f'<link rel="self" type="application/atom+xml" href="{home}feed.xml"/>', f'<link rel="alternate" type="text/html" href="{home}"/>',
         f"<id>{home}</id>", f"<updated>{entries[0][0]}T00:00:00Z</updated>"]
    for stem, title, url, summary in entries:
        x += ["<entry>", f"<title>{html.escape(title)}</title>", f'<link rel="alternate" type="text/html" href="{url}"/>', f"<id>{url}</id>",
              f"<updated>{stem}T00:00:00Z</updated>", f"<summary>{html.escape(summary)}</summary>", "</entry>"]
    x.append("</feed>")
    return "\n".join(x) + "\n"


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
    ptitle = u["t_swing"] if kind == "swing" else u["t_div"]
    sub_en = SUBDIRS["en"][0 if kind == "swing" else 1]

    def report_desc(text, stem):
        names = top3_names(text)
        return u["desc_rep"][kind].format(d=sdate(stem, lang), t=", ".join(names)) if names else desc

    feed = []
    for f in files:
        stem = f.stem
        text, pl, ok = md_text(lang, folder_pl, stem, kind)
        if kind == "swing":
            feed.append((stem, f"{ptitle} {sdate(stem, lang)}", canon(f"{'' if lang == 'pl' else 'en/'}{sub}/{stem}.html"), report_desc(text, stem)))
        body = (f'<div class="banner">{label} {u["of_day"]} <strong>{pretty_date(stem, lang)}</strong> · '
                f'<a href="../{arch_name}">{u["archive"]}</a></div>\n' + note(ok)
                + render_md(text, dt.date.fromisoformat(stem), lang, pl, kind))
        (out_root / sub / f"{stem}.html").write_text(
            page(f"{ptitle} {sdate(stem, lang)}", body, lang, key, report_desc(text, stem), sub=True,
                 counter=(f"{sub_pl}/{stem}.html", f"{sub_en}/{stem}.html"), lastmod=stem),
            encoding="utf-8")
    if kind == "swing":
        (out_root / "feed.xml").write_text(atom_feed(lang, feed[::-1][:20]), encoding="utf-8")
    stem = files[-1].stem
    text, pl, ok = md_text(lang, folder_pl, stem, kind)
    body = (f'<div class="banner">{u["latest"]}: <strong>{pretty_date(stem, lang)}</strong>. '
            f'<a href="{arch_name}">{u["prev"]}</a></div>\n' + note(ok)
            + render_md(text, dt.date.fromisoformat(stem), lang, pl, kind))
    (out_root / out_name).write_text(
        page(f"{ptitle} {sdate(stem, lang)}", body, lang, key, report_desc(text, stem), counter=(fname(key, "pl"), fname(key, "en")), lastmod=stem),
        encoding="utf-8")
    # Archiwum: miesiące, przy każdym raporcie TOP 3 (z polskiego Markdownu, więc zawsze dostępne) i dyskretny link do źródła .md
    groups = {}
    for f in reversed(files):
        _, pl_f, ok_f = md_text(lang, folder_pl, f.stem, kind)
        if lang == "pl":
            mdlink, tag = f'{sub}/{f.name}', ""
        else:
            mdlink = f'../{MD_SRC["en"][0 if kind == "swing" else 1].name}/{f.name}' if ok_f else f'../{sub_pl}/{f.name}'
            tag = "" if ok_f else " (PL)"
        tics = [r.get("Tic", "") for r in top3_rows(pl_f)]
        chips = (f' <span class="ar-l">{u["top3_lbl"]}</span> ' + " ".join(f'<span class="tk">{html.escape(t)}</span>' for t in tics)) if tics else ""
        groups.setdefault(month_name(f.stem, lang), []).append(
            f'<li class="ar"><a class="ar-d" href="{sub}/{f.stem}.html">{pretty_date(f.stem, lang)}</a>{tag}{chips}'
            f'<a class="ar-md" href="{mdlink}" title="Markdown">.md</a></li>')
    arch = (subtabs(lang, akey) + f'<h1>{u["arch_h1"].format(t=title_prefix)}</h1>\n'
            + "\n".join(f'<h2>{html.escape(m)}</h2>\n<ul class="ar-list">\n' + "\n".join(lis) + "\n</ul>" for m, lis in groups.items()))
    (out_root / arch_name).write_text(
        page(u["arch_t"][kind], arch, lang, akey, desc, counter=(fname(akey, "pl"), fname(akey, "en")), lastmod=stem), encoding="utf-8")
    return stem


def write_site_files():
    """sitemap.xml (z hreflang), robots.txt, manifest.webmanifest i 404.html. Adres serwisu bierzemy z pliku CNAME."""
    import json

    pages = sorted({p["url"]: p for p in PAGES}.values(), key=lambda p: p["url"])
    x = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in pages:
        x.append("<url>")
        x.append(f"<loc>{html.escape(p['url'])}</loc>")
        if p["lastmod"]:
            x.append(f"<lastmod>{p['lastmod']}</lastmod>")
        for hl, href in (("pl", p["pl"]), ("en", p["en"]), ("x-default", p["pl"])):
            x.append(f'<xhtml:link rel="alternate" hreflang="{hl}" href="{html.escape(href)}"/>')
        x.append("</url>")
    x.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(x) + "\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    manifest = {
        "name": BRAND, "short_name": BRAND, "lang": "pl", "start_url": "/", "scope": "/", "display": "standalone",
        "description": UI["pl"]["desc_swing"], "background_color": "#0B0C10", "theme_color": "#0B0C10",
        "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
                  {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
    }
    (ROOT / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    body = ('<div class="nf" aria-hidden="true">404</div>\n<h1>Nie ma takiej strony</h1>\n'
            '<p>Adres mógł się zmienić albo raport jeszcze nie powstał. <a href="/index.html">Najnowszy raport</a> · '
            '<a href="/archiwum.html">archiwum</a> · <a href="/newsy.html">newsy dnia</a>.</p>\n'
            '<p lang="en"><strong>Page not found.</strong> <a href="/en/index.html">Latest report</a> · '
            '<a href="/en/archive.html">archive</a> · <a href="/en/news.html">news of the day</a>.</p>')
    (ROOT / "404.html").write_text(
        page("Nie ma takiej strony / Page not found", body, "pl", None, "Nie ma takiej strony. Page not found.", abs_root=True, noindex=True),
        encoding="utf-8")


def main():
    import json

    reports = report_files()
    if not reports:
        print("Brak raportów w reports/", file=sys.stderr)
        return 1
    # Dane rankingu obok każdego raportu (reports/RRRR-MM-DD.json); problemy w najnowszym raporcie wypisujemy, ale nie psują buildu.
    import ranking
    for f in reports:
        problems = ranking.check(ranking.write_sidecar(f))
        if f == reports[-1]:
            for p in problems:
                print(f"UWAGA ranking {f.name} {p['tic'] or ''}: {p['msg']}", file=sys.stderr)
    (ROOT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (ROOT / "logo.svg").write_text(
        '<svg viewBox="0 0 250 48" xmlns="http://www.w3.org/2000/svg">' + MARK +
        '<text x="60" y="34" font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif" font-size="28" font-weight="800" fill="#F2F7F5">GPW '
        '<tspan fill="url(#lg)">Radar</tspan></text></svg>', encoding="utf-8")
    PORTS[:] = [ps.parent.name for ps in sorted((ROOT / "paper").glob("*/state.json"))]
    PAGES.clear()
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
                     counter=(fname(f"port-{key}", "pl"), fname(f"port-{key}", "en")),
                     lastmod=(st["equity"][-1]["date"] if st["equity"] else st["start_date"])), encoding="utf-8")
        # Metodologia: PL z metodologia-swing.md, EN z metodologia-swing.en.md (brak => polski tekst + informacja).
        mp = ROOT / ("metodologia-swing.md" if lang == "pl" else "metodologia-swing.en.md")
        banner = ""
        if not mp.exists() and lang == "en":
            mp, banner = ROOT / "metodologia-swing.md", f'<div class="banner">{u["untranslated"]}</div>\n'
        if mp.exists():
            mbody = banner + md_html(mp.read_text(encoding="utf-8"), ("tables", "sane_lists"))
            (out_root / fname("meth", lang)).write_text(
                page(u["title_meth"], mbody, lang, "meth", u["desc_meth"], counter=(fname("meth", "pl"), fname("meth", "en"))), encoding="utf-8")
        msg.append(f"{lang}: newsy {len(md_files(NEWS))} (najnowszy {nw}); swing {len(report_files())} (najnowszy {sw})" + (f", dywidendy {len(md_files(DIVS))} (najnowszy {dv})" if dv else ""))
    write_site_files()
    print("Zbudowano: " + "; ".join(msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
