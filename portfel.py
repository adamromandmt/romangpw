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
