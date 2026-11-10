"""Strona „Portfel <strategia>" (wirtualny portfel) generowana ze stanu paper/<strategia>/state.json. Bez JS, wykres to inline SVG."""
import datetime as dt
import html

from charts import W, WC, _svg, esc
from paper import equity, stats

CSS_EXTRA = """
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0}
.card{background:rgba(15,22,20,.9);border:1px solid var(--line);border-radius:12px;padding:12px 14px;box-shadow:0 0 0 1px rgba(43,255,136,.04),0 10px 24px rgba(0,0,0,.3)}
.card .k{color:var(--muted);font-size:12px;letter-spacing:.03em;text-transform:uppercase}
.card .v{color:var(--strong);font-size:22px;font-weight:700;margin-top:2px}
.card .v.up{color:var(--up)}.card .v.down{color:var(--down)}
.card .s{color:var(--muted);font-size:12px}
.rules li{margin:4px 0}
.chart-card svg .eq{fill:none;stroke:var(--up);stroke-width:2.4;stroke-linejoin:round}
.chart-card svg .base{stroke:var(--warn);stroke-dasharray:5 4;stroke-width:1.3}
.chart-card svg .bm{fill:none;stroke:var(--violet);stroke-width:2;stroke-dasharray:6 4;stroke-linejoin:round}
.note{margin:12px 0;padding:10px 14px;border:1px solid var(--line);border-left:3px solid var(--warn);border-radius:8px;background:rgba(255,179,71,.06);color:var(--fg);font-size:14px}
"""

import re

LANG = "pl"  # "pl" albo "en"; ustawiane przez render(..., lang=)

EN = {
    "Krzywa kapitału": "Equity curve",
    "Pojawi się po kilku sesjach, gdy portfel zacznie handlować.": "It will appear after a few sessions, once the portfolio starts trading.",
    "kapitał startowy": "starting capital",
    "Krzywa kapitału wirtualnego portfela": "Equity curve of the virtual portfolio",
    "Wartość portfela (gotówka plus pozycje po cenach zamknięcia) w PLN.": "Portfolio value (cash plus positions at closing prices) in PLN.",
    "Wartość portfela": "Portfolio value", "start": "start",
    "Wynik": "Return", "Gotówka": "Cash", "w pozycjach": "in positions",
    "Otwarte pozycje": "Open positions", "zleceń oczekujących": "pending orders",
    "Zamknięte transakcje": "Closed trades", "zrealizowane": "realised", "jeszcze brak": "none yet",
    "Trafność": "Hit rate", "udział zyskownych": "share of winners",
    "Średnie R": "Average R", "wynik w jednostkach ryzyka": "result in risk units",
    "Maks. obsunięcie": "Max drawdown", "od szczytu kapitału": "from peak equity",
    "cel 1 zrealizowany, stop na wejściu": "target 1 hit, stop at entry", "w grze": "in play",
    "Portfel": "Portfolio",
    "Tic": "Tic", "Spółka": "Company", "Szt.": "Qty", "Wejście": "Entry", "Data": "Date", "Kurs": "Price",
    "Wynik %": "Return %", "Wynik PLN": "P/L PLN", "Stop": "Stop", "C1": "T1", "C2": "T2", "Dni": "Days", "Status": "Status",
    "Limit kupna": "Buy limit", "Ważne": "Valid", "Klasa · suma": "Class · score", "Wartość PLN": "Value PLN",
    "Wyjście": "Exit", "R": "R", "Powód": "Reason",
    "Brak otwartych pozycji.": "No open positions.", "Brak oczekujących zleceń.": "No pending orders.",
    "Jeszcze nie zamknięto żadnej transakcji.": "No trades closed yet.",
    "Otwarte pozycje h": "Open positions", "Zlecenia oczekujące": "Pending orders",
    "Dziennik": "Log", "Zasady symulacji": "Simulation rules",
    "Stan na": "As of", "(zamknięcie sesji)": "(session close)",
    "stop (luka)": "stop (gap)", "stop na wejściu (luka)": "stop at entry (gap)", "stop": "stop",
    "stop na wejściu": "stop at entry", "cel 1": "target 1", "cel 2": "target 2",
}
MON_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

LOG_EN = [
    (r"Zlecenie kupna (\S+): (\d+) szt\., limit (\S+), stop (\S+), C1 (\S+), C2 (\S+) \(suma (\S+), klasa (\S+)\)",
     r"Buy order \1: \2 shares, limit \3, stop \4, T1 \5, T2 \6 (score \7, class \8)"),
    (r"Sprzedaż (\S+): (\d+) szt\. po (\S+) \((.*)\)", None),
    (r"Anulowano zlecenie (\S+): otwarcie (\S+) poniżej stopu (\S+)", r"Order \1 cancelled: open \2 below stop \3"),
    (r"Anulowano zlecenie (\S+): brak środków", r"Order \1 cancelled: insufficient funds"),
    (r"Kupno (\S+): (\d+) szt\. po (\S+) \(limit (\S+), stop (\S+)\)", r"Bought \1: \2 shares at \3 (limit \4, stop \5)"),
    (r"Zlecenie (\S+) wygasło bez realizacji \(limit (\S+)\)", r"Order \1 expired unfilled (limit \2)"),
]


def T(k):
    return EN.get(k, k) if LANG == "en" else k


def reason(r):
    if LANG != "en":
        return r
    m = re.fullmatch(r"czas \((\d+) dni\)", r)
    return f"time exit ({m.group(1)} days)" if m else EN.get(r, r)


def logtxt(t):
    if LANG != "en":
        return t
    for pat, repl in LOG_EN:
        m = re.fullmatch(pat, t)
        if m:
            if repl is None:
                return f"Sold {m.group(1)}: {m.group(2)} shares at {m.group(3)} ({reason(m.group(4))})"
            return m.expand(repl)
    return t


def n0(v):
    s = f"{v:,.0f}"
    return s if LANG == "en" else s.replace(",", " ")


def n2(v):
    s = f"{v:,.2f}"
    return s if LANG == "en" else s.replace(",", " ").replace(".", ",")


def px(v):
    if abs(v) >= 1000:
        return n0(v)
    return f"{v:.2f}" if LANG == "en" else f"{v:.2f}".replace(".", ",")


def sg(v, d=2, unit=""):
    s = f"{v:+,.{d}f}"
    if LANG != "en":
        s = s.replace(",", " ").replace(".", ",")
    return s.replace("-", "−") + unit


def cls(v):
    return "up" if v > 0 else "down" if v < 0 else ""


def dshort(s):
    d = dt.date.fromisoformat(s)
    return f"{d.day} {MON_EN[d.month - 1]}" if LANG == "en" else f"{d.day}.{d.month:02d}"


def dfull(s):
    d = dt.date.fromisoformat(s)
    return f"{d.day} {MON_EN[d.month - 1]} {d.year}" if LANG == "en" else f"{d.day}.{d.month:02d}.{d.year}"


def table(head, rows, empty):
    if not rows:
        return f'<p class="muted">{esc(T(empty))}</p>'
    th = "".join(f"<th>{esc(T(h))}</th>" for h in head)
    return f"<table><thead><tr>{th}</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def td(txt, c=""):
    return f'<td class="{c}">{txt}</td>' if c else f"<td>{txt}</td>"


def equity_chart(st):
    pts = st["equity"]
    start = st["config"]["start_capital"]
    title, sub = T("Krzywa kapitału"), T("Wartość portfela (gotówka plus pozycje po cenach zamknięcia) w PLN.")
    if len(pts) < 2:
        return f'<div class="chart-card"><h2 class="ch">{title}</h2><p class="sub">{T("Pojawi się po kilku sesjach, gdy portfel zacznie handlować.")}</p></div>'
    ds = [dt.date.fromisoformat(p["date"]) for p in pts]
    d0, d1 = ds[0], ds[-1]
    span = max((d1 - d0).days, 1)
    vals = [p["equity"] for p in pts] + [start]
    lo, hi = min(vals), max(vals)
    pad = max((hi - lo) * 0.15, start * 0.002)
    lo, hi = lo - pad, hi + pad

    def draw(c):
        w = WC if c else W
        x0, x1, top, bot, h = (66, w - 16, 20, 200, 240) if c else (70, w - 40, 20, 220, 260)
        X = lambda d: x0 + (d - d0).days / span * (x1 - x0)
        Y = lambda v: bot - (v - lo) / (hi - lo) * (bot - top)
        p = []
        for k in range(5):
            v = lo + (hi - lo) * k / 4
            p.append(f'<line class="grid" x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}"/>')
            p.append(f'<text class="tick" x="{x0 - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{n0(v)}</text>')
        p.append(f'<line class="base" x1="{x0}" y1="{Y(start):.1f}" x2="{x1}" y2="{Y(start):.1f}"/>')
        p.append(f'<text class="warn" x="{x1}" y="{Y(start) - 5:.1f}" text-anchor="end">{T("kapitał startowy")} {n0(start)}</text>')
        path = " ".join(f"{X(d):.1f},{Y(pt['equity']):.1f}" for d, pt in zip(ds, pts))
        area = f"{X(ds[0]):.1f},{bot} {path} {X(ds[-1]):.1f},{bot}"
        gid = "eqgc" if c else "eqg"
        p.append(f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2BFF88" stop-opacity=".28"/>'
                 '<stop offset="1" stop-color="#2BFF88" stop-opacity="0"/></linearGradient></defs>')
        p.append(f'<polygon points="{area}" style="fill:url(#{gid})"/>')
        p.append(f'<polyline class="eq" points="{path}"/>')
        for d, pt in zip(ds, pts):
            p.append(f'<circle cx="{X(d):.1f}" cy="{Y(pt["equity"]):.1f}" r="3" style="fill:var(--up)"><title>{dshort(pt["date"])}: {n0(pt["equity"])} PLN</title></circle>')
        p.append(f'<text class="val" x="{X(ds[-1]):.1f}" y="{Y(pts[-1]["equity"]) - 10:.1f}" text-anchor="end">{n0(pts[-1]["equity"])}</text>')
        step = max(1, len(pts) // (4 if c else 6))
        for i in range(0, len(pts), step):
            p.append(f'<text class="tick" x="{X(ds[i]):.1f}" y="{bot + 20}" text-anchor="middle">{dshort(pts[i]["date"])}</text>')
        return _svg(h, T("Krzywa kapitału wirtualnego portfela"), "".join(p), w, "c" if c else "")

    return (f'<div class="chart-card"><h2 class="ch">{title}</h2><p class="sub">{sub}</p>'
            f'<div class="cv-d">{draw(False)}</div><div class="cv-c">{draw(True)}</div></div>')


def render(st, name="Swing", lang="pl"):
    global LANG
    LANG = lang
    cfg, s = st["config"], stats(st)
    eq = equity(st)
    ret = (eq / cfg["start_capital"] - 1) * 100
    asof = st["equity"][-1]["date"] if st["equity"] else st["start_date"]
    invested = sum(p["shares"] * p["last_close"] for p in st["positions"])
    card = lambda k, v, sub="", c="": f'<div class="card"><div class="k">{k}</div><div class="v {c}">{v}</div><div class="s">{sub}</div></div>'
    cards = "".join([
        card(T("Wartość portfela"), f"{n0(eq)} PLN", f"{T('start')} {n0(cfg['start_capital'])} PLN"),
        card(T("Wynik"), sg(ret, 2, "%"), f"{sg(eq - cfg['start_capital'], 0)} PLN", cls(ret)),
        card(T("Gotówka"), f"{n0(st['cash'])} PLN", f"{T('w pozycjach')} {n0(invested)} PLN"),
        card(T("Otwarte pozycje"), str(len(st["positions"])), f"{T('zleceń oczekujących')}: {len(st['orders'])}"),
        card(T("Zamknięte transakcje"), str(s["closed"]), f"{T('zrealizowane')} {sg(s['realized'], 0)} PLN" if s["closed"] else T("jeszcze brak")),
        card(T("Trafność"), f"{s['win_rate']:.0f}%" if s["win_rate"] is not None else "—", T("udział zyskownych")),
        card(T("Średnie R"), sg(s["avg_r"], 2) if s["avg_r"] is not None else "—", T("wynik w jednostkach ryzyka")),
        card(T("Maks. obsunięcie"), (n2(s["max_dd"]).replace("-", "−") + "%") if st["equity"] else "—", T("od szczytu kapitału")),
    ])
    pos_rows = []
    for p in sorted(st["positions"], key=lambda p: p["entry_date"]):
        pnl_pos = p["shares"] * p["last_close"] + p["realized"] - p["cost"]
        pct = pnl_pos / p["cost"] * 100
        days = (dt.date.fromisoformat(p["last_date"]) - dt.date.fromisoformat(p["entry_date"])).days
        status = T("cel 1 zrealizowany, stop na wejściu") if p["c1_done"] else T("w grze")
        pos_rows.append("<tr>" + td(f"<strong>{esc(p['tic'])}</strong>") + td(esc(p["name"])) + td(str(p["shares"])) +
                        td(px(p["entry"])) + td(dshort(p["entry_date"])) + td(px(p["last_close"])) +
                        td(sg(pct, 2, "%"), cls(pct)) + td(sg(pnl_pos, 0), cls(pnl_pos)) + td(px(p["stop"])) +
                        td(px(p["c1"])) + td(px(p["c2"])) + td(str(days)) + td(status) + "</tr>")
    ord_rows = []
    for o in st["orders"]:
        ord_rows.append("<tr>" + td(f"<strong>{esc(o['tic'])}</strong>") + td(esc(o["name"])) + td(str(o["shares"])) +
                        td(px(o["limit"])) + td(px(o["stop"])) + td(px(o["c1"])) + td(px(o["c2"])) +
                        td(f"{dshort(o['valid_from'])}–{dshort(o['expires'])}") + td(f"{o['cls']} · {o['score']:g}") +
                        td(n0(o["shares"] * o["limit"])) + "</tr>")
    cl_rows = []
    for c in reversed(st["closed"]):
        legs = ", ".join(f"{l['qty']}×{px(l['price'])}" for l in c["legs"])
        cl_rows.append("<tr>" + td(f"<strong>{esc(c['tic'])}</strong>") + td(f"{dshort(c['entry_date'])} @ {px(c['entry'])}") +
                       td(f"{dshort(c['exit_date'])} ({esc(legs)})") + td(str(c["shares"])) +
                       td(sg(c["pnl_pct"], 2, "%"), cls(c["pnl"])) + td(sg(c["pnl"], 0), cls(c["pnl"])) +
                       td(sg(c["r"], 2) if c["r"] is not None else "—", cls(c["r"] or 0)) + td(str(c["days"])) +
                       td(esc(reason(c["exit_reason"]))) + "</tr>")
    log_rows = [f"<li><strong>{dshort(e['date'])}</strong> {esc(logtxt(e['text']))}</li>" for e in reversed(st["log"][-25:])]
    fee = str(cfg["fee_pct"]) if LANG == "en" else str(cfg["fee_pct"]).replace(".", ",")
    sd = dfull(st["start_date"])
    if LANG == "en":
        rules = f"""
<ul class="rules">
<li><strong>Capital:</strong> {n0(cfg['start_capital'])} virtual PLN from {sd}. This is a simulation; no real orders are placed.</li>
<li><strong>Where positions come from:</strong> the ranking table of the daily report ({esc(name.lower())}). We take classes A and B with a total score of at least {cfg['min_score']}, R to target 1 of at least {cfg['min_r1']:g} and to target 2 of at least {cfg['min_r2']:g}, no quarterly results within {cfg['skip_earnings_days']} days, at most {cfg['max_new_per_day']} new orders per day.</li>
<li><strong>Entry:</strong> a limit order at the upper edge of the entry zone, valid for 5 sessions. It fills at the lower of the open and the limit if price traded down to the limit. If the session opens below the stop, the order is cancelled.</li>
<li><strong>Position size:</strong> one position costs at most {n0(cfg['position_value'])} PLN (whole shares). Shares priced above {n0(cfg['position_value'])} PLN each (e.g. LPP) are skipped. Profits from sales return to cash; a loss at the stop reduces it. When all cash is committed to positions and orders, new orders wait until a position is closed (target or stop).</li>
<li><strong>Exits:</strong> stop (at the open price on a gap), target 1 (sell half, move the stop to the entry price), target 2 (the rest), or after {cfg['max_hold_days']} days at the session close.</li>
<li><strong>Daily candles:</strong> when one candle touches both stop and target, the stop counts (pessimistic assumption). On the entry day only the stop is checked.</li>
<li><strong>Costs:</strong> {fee}% per transaction. Capital gains tax (19%) is not included.</li>
</ul>"""
        body = (
            f'<h1>Portfolio {esc(name)}</h1>\n<div class="banner">As of <strong>{dfull(asof)}</strong> (session close). '
            f'A check of the forecasts: would the stocks from the scanner ranking ({esc(name.lower())}) really have reached the target before the stop? Virtual capital, <strong>not investment advice</strong>.</div>\n'
            f'<div class="cards">{cards}</div>\n{equity_chart(st)}\n'
        )
    else:
        rules = f"""
<ul class="rules">
<li><strong>Kapitał:</strong> {n0(cfg['start_capital'])} PLN wirtualnych od {sd}. To symulacja, żadne prawdziwe zlecenia nie są składane.</li>
<li><strong>Skąd pozycje:</strong> z tabeli rankingu codziennego raportu ({esc(name.lower())}). Bierzemy klasy A i B z sumą co najmniej {cfg['min_score']}, R do celu 1 co najmniej {cfg['min_r1']:g} i do celu 2 co najmniej {cfg['min_r2']:g}, bez raportu kwartalnego w ciągu {cfg['skip_earnings_days']} dni, maks. {cfg['max_new_per_day']} nowych zleceń dziennie.</li>
<li><strong>Wejście:</strong> zlecenie z limitem na górnej granicy strefy wejścia, ważne 5 sesji. Realizuje się po niższej z cen: otwarcie lub limit, jeśli kurs zszedł do limitu. Gdy sesja otwiera się poniżej stopu, zlecenie jest anulowane.</li>
<li><strong>Wielkość pozycji:</strong> jedna pozycja kosztuje najwyżej {n0(cfg['position_value'])} PLN (pełne akcje). Akcje droższe niż {n0(cfg['position_value'])} PLN za sztukę (np. LPP) są pomijane. Zysk ze sprzedaży wraca do gotówki, strata po stopie ją pomniejsza. Gdy cała gotówka jest zaangażowana w pozycje i zlecenia, nowe zlecenia czekają, aż któraś pozycja zostanie zamknięta (cel albo stop).</li>
<li><strong>Wyjścia:</strong> stop (przy luce po cenie otwarcia), cel 1 (sprzedaż połowy, stop przesuwany na cenę wejścia), cel 2 (reszta), albo po {cfg['max_hold_days']} dniach po zamknięciu sesji.</li>
<li><strong>Świece dzienne:</strong> gdy jedna świeca dotyka i stopu, i celu, liczymy stop (założenie pesymistyczne). W dniu wejścia sprawdzamy tylko stop.</li>
<li><strong>Koszty:</strong> {fee}% od każdej transakcji. Podatek od zysków kapitałowych (19%) nie jest uwzględniony.</li>
</ul>"""
        body = (
            f'<h1>Portfel {esc(name)}</h1>\n<div class="banner">Stan na <strong>{dfull(asof)}</strong> (zamknięcie sesji). '
            f'Sprawdzian prognoz: czy spółki z rankingu skanera ({esc(name.lower())}) rzeczywiście osiągnęłyby cel przed stopem. Wirtualny kapitał, <strong>nie porada inwestycyjna</strong>.</div>\n'
            f'<div class="cards">{cards}</div>\n{equity_chart(st)}\n'
        )
    H = (lambda a, b: b) if LANG == "en" else (lambda a, b: a)
    body += (
        f'<h2>{H("Otwarte pozycje", "Open positions")}</h2>\n'
        + table(["Tic", "Spółka", "Szt.", "Wejście", "Data", "Kurs", "Wynik %", "Wynik PLN", "Stop", "C1", "C2", "Dni", "Status"], pos_rows, "Brak otwartych pozycji.")
        + f'\n<h2>{H("Zlecenia oczekujące", "Pending orders")}</h2>\n'
        + table(["Tic", "Spółka", "Szt.", "Limit kupna", "Stop", "C1", "C2", "Ważne", "Klasa · suma", "Wartość PLN"], ord_rows, "Brak oczekujących zleceń.")
        + f'\n<h2>{H("Zamknięte transakcje", "Closed trades")}</h2>\n'
        + table(["Tic", "Wejście", "Wyjście", "Szt.", "Wynik %", "Wynik PLN", "R", "Dni", "Powód"], cl_rows, "Jeszcze nie zamknięto żadnej transakcji.")
        + f'\n<h2>{H("Dziennik", "Log")}</h2>\n<ul class="list">' + "".join(log_rows) + "</ul>"
        + f'\n<h2>{H("Zasady symulacji", "Simulation rules")}</h2>' + rules
    )
    return body


# ---------------------------------------------------------------------------------------------------------------------------
# Portfele strategii uzupełniających (Kompas, Pęd, Złoty Środek, Przystań, Dryf): stan z paper/<slug>/state.json (strat/engine.py)

def strategy_equity_chart(st, lang):
    """Krzywa kapitału portfela i, przeskalowany do kapitału startowego, WIG20 (indeks cenowy) z tych samych sesji."""
    global LANG
    LANG = lang
    pts = st["equity"]
    start = st["config"]["start_capital"]
    H = (lambda a, b: b) if lang == "en" else (lambda a, b: a)
    title = H("Krzywa kapitału i WIG20", "Equity curve and WIG20")
    sub = H("Wartość portfela (gotówka plus pozycje po cenach zamknięcia) w PLN; fioletowa linia to WIG20 przeskalowany do kapitału startowego (indeks cenowy, bez dywidend).",
            "Portfolio value (cash plus positions at closing prices) in PLN; the violet line is the WIG20 rescaled to the starting capital (a price index, no dividends).")
    if len(pts) < 2:
        return f'<div class="chart-card"><h2 class="ch">{title}</h2><p class="sub">{H("Pojawi się po kilku sesjach, gdy portfel zacznie handlować.", "It will appear after a few sessions, once the portfolio starts trading.")}</p></div>'
    b0 = next((p["bench"] for p in pts if p.get("bench")), None)
    bench = [start * p["bench"] / b0 if (b0 and p.get("bench")) else None for p in pts]
    ds = [dt.date.fromisoformat(p["date"]) for p in pts]
    d0, d1 = ds[0], ds[-1]
    span = max((d1 - d0).days, 1)
    vals = [p["equity"] for p in pts] + [b for b in bench if b] + [start]
    lo, hi = min(vals), max(vals)
    pad = max((hi - lo) * 0.15, start * 0.002)
    lo, hi = lo - pad, hi + pad

    def draw(c):
        w = WC if c else W
        x0, x1, top, bot, h = (66, w - 16, 34, 214, 254) if c else (70, w - 40, 34, 234, 274)
        X = lambda d: x0 + (d - d0).days / span * (x1 - x0)
        Y = lambda v: bot - (v - lo) / (hi - lo) * (bot - top)
        p = [f'<rect x="{x0}" y="8" width="12" height="12" rx="3" style="fill:var(--up)"/><text class="tick" x="{x0 + 18}" y="18">{H("Portfel", "Portfolio")}</text>',
             f'<rect x="{x0 + (96 if c else 110)}" y="8" width="12" height="12" rx="3" style="fill:var(--violet)"/><text class="tick" x="{x0 + (114 if c else 128)}" y="18">WIG20</text>']
        for k in range(5):
            v = lo + (hi - lo) * k / 4
            p.append(f'<line class="grid" x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}"/>')
            p.append(f'<text class="tick" x="{x0 - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{n0(v)}</text>')
        p.append(f'<line class="base" x1="{x0}" y1="{Y(start):.1f}" x2="{x1}" y2="{Y(start):.1f}"/>')
        bp = " ".join(f"{X(d):.1f},{Y(b):.1f}" for d, b in zip(ds, bench) if b)
        if bp.count(",") >= 2:
            p.append(f'<polyline class="bm" points="{bp}"/>')
        path = " ".join(f"{X(d):.1f},{Y(pt['equity']):.1f}" for d, pt in zip(ds, pts))
        gid = "seqc" if c else "seq"
        p.append(f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2BFF88" stop-opacity=".22"/>'
                 '<stop offset="1" stop-color="#2BFF88" stop-opacity="0"/></linearGradient></defs>')
        p.append(f'<polygon points="{X(ds[0]):.1f},{bot} {path} {X(ds[-1]):.1f},{bot}" style="fill:url(#{gid})"/>')
        p.append(f'<polyline class="eq" points="{path}"/>')
        step = max(1, len(pts) // (60 if not c else 40))
        for i in range(0, len(pts), step):
            pt = pts[i]
            p.append(f'<circle cx="{X(ds[i]):.1f}" cy="{Y(pt["equity"]):.1f}" r="2.2" style="fill:var(--up)"><title>{dshort(pt["date"])}: {n0(pt["equity"])} PLN</title></circle>')
        p.append(f'<text class="val" x="{X(ds[-1]):.1f}" y="{Y(pts[-1]["equity"]) - 10:.1f}" text-anchor="end">{n0(pts[-1]["equity"])}</text>')
        step = max(1, len(pts) // (4 if c else 6))
        for i in range(0, len(pts), step):
            p.append(f'<text class="tick" x="{X(ds[i]):.1f}" y="{bot + 20}" text-anchor="middle">{dshort(pts[i]["date"])}</text>')
        return _svg(h, title, "".join(p), w, "c" if c else "")

    return (f'<div class="chart-card"><h2 class="ch">{title}</h2><p class="sub">{sub}</p>'
            f'<div class="cv-d">{draw(False)}</div><div class="cv-c">{draw(True)}</div></div>')


def render_strategy(st, strat, lang="pl", sig=None):
    """Treść strony „Portfel <strategia>". st: stan z strat/engine.py, strat: wpis z strat/registry.py, sig: ostatni sygnał (dict z JSON) albo None."""
    global LANG
    from strat import engine
    LANG = lang
    H = (lambda a, b: b) if lang == "en" else (lambda a, b: a)
    name = strat["name"][lang]
    cfg, s = st["config"], engine.stats(st)
    eq = engine.equity(st)
    asof = st["equity"][-1]["date"] if st["equity"] else st["start_date"]
    invested = sum(p["shares"] * p["last_close"] for p in st["positions"])
    card = lambda k, v, sub="", c="": f'<div class="card"><div class="k">{k}</div><div class="v {c}">{v}</div><div class="s">{sub}</div></div>'
    bret = s["bench_ret"]
    cards = "".join([
        card(H("Wartość portfela", "Portfolio value"), f"{n0(eq)} PLN", f"{H('start', 'start')} {n0(cfg['start_capital'])} PLN"),
        card(H("Wynik", "Return"), sg(s["ret"], 2, "%"), f"{sg(eq - cfg['start_capital'], 0)} PLN", cls(s["ret"])),
        card(H("WIG20 w tym czasie", "WIG20 over the same time"), sg(bret, 2, "%") if bret is not None else "—",
             (H("różnica ", "difference ") + sg(s["vs_bench"], 2, " pp")) if s["vs_bench"] is not None else H("indeks cenowy", "price index"), cls(bret or 0)),
        card(H("Gotówka", "Cash"), f"{n0(st['cash'])} PLN", f"{H('w pozycjach', 'in positions')} {n0(invested)} PLN"),
        card(H("Otwarte pozycje", "Open positions"), str(len(st["positions"])),
             f"{H('średnio zainwestowane', 'avg invested')} {s['exposure']:.0f}%".replace(".", ",") if lang == "pl" else f"avg invested {s['exposure']:.0f}%"),
        card(H("Zamknięte transakcje", "Closed trades"), str(s["closed"]), f"{H('zrealizowane', 'realised')} {sg(s['realized'], 0)} PLN" if s["closed"] else H("jeszcze brak", "none yet")),
        card(H("Trafność", "Hit rate"), f"{s['win_rate']:.0f}%" if s["win_rate"] is not None else "—", H("udział zyskownych", "share of winners")),
        card(H("Maks. obsunięcie", "Max drawdown"), (n2(s["max_dd"]).replace("-", "−") + "%") if st["equity"] else "—", H("od szczytu kapitału", "from peak equity")),
    ])
    events = st["kind"] == "events"
    pos_rows = []
    for p in sorted(st["positions"], key=lambda p: (p["entry_date"], p["tic"])):
        total = p["shares"] * p["last_close"] + p["divs"] - p["cost"]
        pct = total / p["cost"] * 100
        days = (dt.date.fromisoformat(p["last_date"]) - dt.date.fromisoformat(p["entry_date"])).days
        row = (td(f"<strong>{esc(p['tic'])}</strong>") + td(esc(p["name"])) + td(f"{p['shares']:g}") + td(px(p["entry"])) + td(dshort(p["entry_date"])) +
               td(px(p["last_close"])) + td(sg(pct, 2, "%"), cls(pct)) + td(sg(total, 0), cls(total)) + td(n0(p["divs"])))
        if events:
            row += td(px(p["stop"]) if p.get("stop") else "—")
        pos_rows.append("<tr>" + row + td(str(days)) + "</tr>")
    pend = st.get("pending")
    plan_rows = []
    if pend:
        held = {p["tic"] for p in st["positions"]}
        tset = {t["tic"] for t in pend["targets"]}
        for p in st["positions"]:
            if p["tic"] not in tset:
                r = pend["exit_reasons"].get(p["tic"]) or {"pl": "wypadła z listy docelowej", "en": "dropped from the target list"}
                plan_rows.append("<tr>" + td(f"<strong>{esc(p['tic'])}</strong>") + td(esc(p["name"])) + td(H("Sprzedaż", "Sell")) +
                                 td(H("na otwarciu następnej sesji: ", "at the next session's open: ") + esc(r[lang])) + "</tr>")
        for t in pend["targets"]:
            if t["tic"] not in held:
                w = t.get("weight", 1.0) * pend.get("size_factor", 1.0)
                note = H("na otwarciu następnej sesji", "at the next session's open") + (H(f", połowa zwykłej wielkości", ", half the usual size") if w < 1 else "")
                plan_rows.append("<tr>" + td(f"<strong>{esc(t['tic'])}</strong>") + td(esc(t.get("name") or t["tic"])) + td(H("Kupno", "Buy")) + td(note) + "</tr>")
    for o in st["orders"]:
        plan_rows.append("<tr>" + td(f"<strong>{esc(o['tic'])}</strong>") + td(esc(o["name"])) + td(H("Kupno", "Buy")) +
                         td(H(f"na otwarciu następnej sesji, stop {px(o['stop'])}", f"at the next session's open, stop {px(o['stop'])}")) + "</tr>")
    cl_rows = []
    for c in reversed(st["closed"]):
        cl_rows.append("<tr>" + td(f"<strong>{esc(c['tic'])}</strong>") + td(f"{dshort(c['entry_date'])} @ {px(c['entry'])}") + td(f"{dshort(c['exit_date'])} @ {px(c['exit'])}") +
                       td(f"{c['shares']:g}") + td(sg(c["pnl_pct"], 2, "%"), cls(c["pnl"])) + td(sg(c["pnl"], 0), cls(c["pnl"])) + td(n0(c["divs"])) +
                       td(str(c["days"])) + td(esc(c["why_en"] if lang == "en" else c["why_pl"])) + "</tr>")
    log_rows = [f"<li><strong>{dshort(e['date'])}</strong> {esc(e[lang])}</li>" for e in reversed(st["log"][-25:])]
    fee = str(cfg["fee_pct"]) if lang == "en" else str(cfg["fee_pct"]).replace(".", ",")
    own = "".join(f"<li>{_md_inline(x)}</li>" for x in strat["rules"][lang])
    if lang == "en":
        common = (f"<li><strong>Capital:</strong> {n0(cfg['start_capital'])} virtual PLN from {dfull(st['start_date'])}. This is a simulation; no real orders are placed.</li>"
                  f"<li><strong>Prices and timing:</strong> raw prices from the GPW archive; orders execute at the open of the first session after the report is published. Costs: {fee}% per transaction. "
                  "Dividends are credited gross on the ex-dividend date; capital gains tax (19%) is not included. Cash earns no interest.</li>"
                  "<li><strong>Benchmark:</strong> WIG20, a price index without dividends, so it understates the index's total return. The portfolio sits partly in cash, so the comparison is not like for like.</li>")
        banner = (f'<div class="banner">As of <strong>{dfull(asof)}</strong> (session close). A forward check of the {esc(name)} strategy: what a virtual portfolio would have done '
                  'since the start date. Virtual capital, <strong>not investment advice</strong>.</div>')
        h1 = f"{esc(name)} Portfolio"
        hs = ("Open positions", "Planned trades", "Closed trades", "Log", "Portfolio rules")
        heads = (["Tic", "Company", "Qty", "Entry", "Date", "Price", "Return %", "Return PLN", "Dividends PLN"] + (["Stop"] if events else []) + ["Days"],
                 ["Tic", "Company", "Action", "Details"], ["Tic", "Entry", "Exit", "Qty", "Return %", "Return PLN", "Dividends PLN", "Days", "Reason"])
        empty = ("No open positions.", "No pending orders.", "No trades closed yet.")
    else:
        common = (f"<li><strong>Kapitał:</strong> {n0(cfg['start_capital'])} PLN wirtualnych od {dfull(st['start_date'])}. To symulacja, żadne prawdziwe zlecenia nie są składane.</li>"
                  f"<li><strong>Ceny i terminy:</strong> ceny surowe z archiwum GPW; zlecenia wykonują się na otwarciu pierwszej sesji po publikacji raportu. Koszt: {fee}% od każdej transakcji. "
                  "Dywidendy księgujemy brutto w dniu odcięcia; podatek od zysków kapitałowych (19%) nie jest uwzględniony. Gotówka nie przynosi odsetek.</li>"
                  "<li><strong>Wzorzec porównania:</strong> WIG20, indeks cenowy bez dywidend, więc zaniża całkowity zwrot indeksu. Portfel bywa częściowo w gotówce, więc porównanie nie jest równe.</li>")
        banner = (f'<div class="banner">Stan na <strong>{dfull(asof)}</strong> (zamknięcie sesji). Sprawdzian prognoz strategii {esc(name)}: co zrobiłby wirtualny portfel od dnia startu. '
                  'Wirtualny kapitał, <strong>nie porada inwestycyjna</strong>.</div>')
        h1 = f"Portfel {esc(name)}"
        hs = ("Otwarte pozycje", "Plan transakcji", "Zamknięte transakcje", "Dziennik", "Zasady portfela")
        heads = (["Tic", "Spółka", "Szt.", "Wejście", "Data", "Kurs", "Wynik %", "Wynik PLN", "Dywidendy PLN"] + (["Stop"] if events else []) + ["Dni"],
                 ["Tic", "Spółka", "Akcja", "Szczegóły"], ["Tic", "Wejście", "Wyjście", "Szt.", "Wynik %", "Wynik PLN", "Dywidendy PLN", "Dni", "Powód"])
        empty = ("Brak otwartych pozycji.", "Brak oczekujących zleceń.", "Jeszcze nie zamknięto żadnej transakcji.")
    notes = []
    if len(st["equity"]) < 60:
        notes.append(H("Portfel działa od krótkiego czasu: wynik z kilkudziesięciu sesji nie mówi nic o strategii. Porównanie z WIG20 ma sens dopiero po wielu miesiącach.",
                       "The portfolio has been running only briefly: a result from a few dozen sessions says nothing about the strategy. A comparison with the WIG20 makes sense only after many months."))
    if sig and sig.get("data", {}).get("status") == "no_data":
        notes.append(H("Złoty Środek czeka na dane fundamentalne (plik data/fundamentals.csv), dlatego portfel jest w całości w gotówce.",
                       "Golden Mean is waiting for fundamental data (data/fundamentals.csv), so the portfolio is entirely in cash."))
    note_html = "".join(f'<div class="note">{esc(n)}</div>' for n in notes)
    body = (f"<h1>{h1}</h1>\n{banner}\n{note_html}<div class=\"cards\">{cards}</div>\n{strategy_equity_chart(st, lang)}\n"
            f"<h2>{hs[0]}</h2>\n" + table_raw(heads[0], pos_rows, empty[0]) +
            f"\n<h2>{hs[1]}</h2>\n" + table_raw(heads[1], plan_rows, empty[1]) +
            f"\n<h2>{hs[2]}</h2>\n" + table_raw(heads[2], cl_rows, empty[2]) +
            f"\n<h2>{hs[3]}</h2>\n<ul class=\"list\">" + "".join(log_rows) + "</ul>"
            f"\n<h2>{hs[4]}</h2>\n<ul class=\"rules\">{own}{common}</ul>\n")
    return body


def table_raw(head, rows, empty):
    """Tabela HTML z gotowymi nagłówkami (bez słownika tłumaczeń swinga)."""
    if not rows:
        return f'<p class="muted">{esc(empty)}</p>'
    return "<table><thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def _md_inline(text):
    """**pogrubienie** i `kod` w krótkich zdaniach z rejestru strategii (reszta jest zabezpieczona przed HTML)."""
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)
