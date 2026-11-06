"""Strona „Portfel" (wirtualny portfel) generowana ze stanu paper/state.json. Bez JS, wykres to inline SVG."""
import datetime as dt
import html

from charts import W, _svg, esc
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

MON = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"]


def n0(v):
    return f"{v:,.0f}".replace(",", " ")


def n2(v):
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


def px(v):
    return n0(v) if abs(v) >= 1000 else (f"{v:.2f}".replace(".", ","))


def sg(v, d=2, unit=""):
    s = f"{v:+,.{d}f}".replace(",", " ").replace(".", ",").replace("-", "−")
    return s + unit


def cls(v):
    return "up" if v > 0 else "down" if v < 0 else ""


def dshort(s):
    d = dt.date.fromisoformat(s)
    return f"{d.day}.{d.month:02d}"


def table(head, rows, empty):
    if not rows:
        return f'<p class="muted">{esc(empty)}</p>'
    th = "".join(f"<th>{esc(h)}</th>" for h in head)
    return f"<table><thead><tr>{th}</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def td(txt, c=""):
    return f'<td class="{c}">{txt}</td>' if c else f"<td>{txt}</td>"


def equity_chart(st):
    pts = st["equity"]
    start = st["config"]["start_capital"]
    if len(pts) < 2:
        return ('<div class="chart-card"><h3>Krzywa kapitału</h3><p class="sub">Pojawi się po kilku sesjach, gdy portfel '
                'zacznie handlować.</p></div>')
    x0, x1, top, bot, h = 70, W - 40, 20, 220, 260
    ds = [dt.date.fromisoformat(p["date"]) for p in pts]
    d0, d1 = ds[0], ds[-1]
    span = max((d1 - d0).days, 1)
    vals = [p["equity"] for p in pts] + [start]
    lo, hi = min(vals), max(vals)
    pad = max((hi - lo) * 0.15, start * 0.002)
    lo, hi = lo - pad, hi + pad
    X = lambda d: x0 + (d - d0).days / span * (x1 - x0)
    Y = lambda v: bot - (v - lo) / (hi - lo) * (bot - top)
    p = []
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        p.append(f'<line class="grid" x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}"/>')
        p.append(f'<text class="tick" x="{x0 - 8}" y="{Y(v) + 4:.1f}" text-anchor="end">{n0(v)}</text>')
    p.append(f'<line class="base" x1="{x0}" y1="{Y(start):.1f}" x2="{x1}" y2="{Y(start):.1f}"/>')
    p.append(f'<text class="warn" x="{x1}" y="{Y(start) - 5:.1f}" text-anchor="end">kapitał startowy {n0(start)}</text>')
    path = " ".join(f"{X(d):.1f},{Y(pt['equity']):.1f}" for d, pt in zip(ds, pts))
    area = f"{X(ds[0]):.1f},{bot} {path} {X(ds[-1]):.1f},{bot}"
    p.append('<defs><linearGradient id="eqg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2BFF88" stop-opacity=".28"/>'
             '<stop offset="1" stop-color="#2BFF88" stop-opacity="0"/></linearGradient></defs>')
    p.append(f'<polygon points="{area}" style="fill:url(#eqg)"/>')
    p.append(f'<polyline class="eq" points="{path}"/>')
    for d, pt in zip(ds, pts):
        p.append(f'<circle cx="{X(d):.1f}" cy="{Y(pt["equity"]):.1f}" r="3" style="fill:var(--up)"><title>{dshort(pt["date"])}: {n0(pt["equity"])} PLN</title></circle>')
    p.append(f'<text class="val" x="{X(ds[-1]):.1f}" y="{Y(pts[-1]["equity"]) - 10:.1f}" text-anchor="end">{n0(pts[-1]["equity"])}</text>')
    step = max(1, len(pts) // 6)
    for i in range(0, len(pts), step):
        p.append(f'<text class="tick" x="{X(ds[i]):.1f}" y="{bot + 20}" text-anchor="middle">{dshort(pts[i]["date"])}</text>')
    svg = _svg(h, "Krzywa kapitału wirtualnego portfela", "".join(p))
    return f'<div class="chart-card"><h3>Krzywa kapitału</h3><p class="sub">Wartość portfela (gotówka plus pozycje po cenach zamknięcia) w PLN.</p>{svg}</div>'


def render(st):
    cfg, s = st["config"], stats(st)
    eq = equity(st)
    ret = (eq / cfg["start_capital"] - 1) * 100
    asof = st["equity"][-1]["date"] if st["equity"] else st["start_date"]
    invested = sum(p["shares"] * p["last_close"] for p in st["positions"])
    card = lambda k, v, sub="", c="": f'<div class="card"><div class="k">{k}</div><div class="v {c}">{v}</div><div class="s">{sub}</div></div>'
    cards = "".join([
        card("Wartość portfela", f"{n0(eq)} PLN", f"start {n0(cfg['start_capital'])} PLN"),
        card("Wynik", sg(ret, 2, "%"), f"{sg(eq - cfg['start_capital'], 0)} PLN", cls(ret)),
        card("Gotówka", f"{n0(st['cash'])} PLN", f"w pozycjach {n0(invested)} PLN"),
        card("Otwarte pozycje", str(len(st["positions"])), f"zleceń oczekujących: {len(st['orders'])}"),
        card("Zamknięte transakcje", str(s["closed"]), f"zrealizowane {sg(s['realized'], 0)} PLN" if s["closed"] else "jeszcze brak"),
        card("Trafność", f"{s['win_rate']:.0f}%" if s["win_rate"] is not None else "—", "udział zyskownych"),
        card("Średnie R", sg(s["avg_r"], 2) if s["avg_r"] is not None else "—", "wynik w jednostkach ryzyka"),
        card("Maks. obsunięcie", (n2(s["max_dd"]).replace("-", "−") + "%") if st["equity"] else "—", "od szczytu kapitału"),
    ])
    pos_rows = []
    for p in sorted(st["positions"], key=lambda p: p["entry_date"]):
        pnl_pos = p["shares"] * p["last_close"] + p["realized"] - p["cost"]
        pct = pnl_pos / p["cost"] * 100
        days = (dt.date.fromisoformat(p["last_date"]) - dt.date.fromisoformat(p["entry_date"])).days
        status = "cel 1 zrealizowany, stop na wejściu" if p["c1_done"] else "w grze"
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
                       td(esc(c["exit_reason"])) + "</tr>")
    log_rows = [f"<li><strong>{dshort(e['date'])}</strong> {esc(e['text'])}</li>" for e in reversed(st["log"][-25:])]
    rules = f"""
<ul class="rules">
<li><strong>Kapitał:</strong> {n0(cfg['start_capital'])} PLN wirtualnych od {dshort(st['start_date'])}.{st['start_date'][:4]}. To symulacja, żadne prawdziwe zlecenia nie są składane.</li>
<li><strong>Skąd pozycje:</strong> z tabeli rankingu codziennego raportu swing. Bierzemy klasy A i B z sumą co najmniej {cfg['min_score']}, R do celu 1 co najmniej {cfg['min_r1']:g} i do celu 2 co najmniej {cfg['min_r2']:g}, bez raportu kwartalnego w ciągu {cfg['skip_earnings_days']} dni, maks. {cfg['max_new_per_day']} nowych zleceń dziennie.</li>
<li><strong>Wejście:</strong> zlecenie z limitem na górnej granicy strefy wejścia, ważne 5 sesji. Realizuje się po niższej z cen: otwarcie lub limit, jeśli kurs zszedł do limitu. Gdy sesja otwiera się poniżej stopu, zlecenie jest anulowane.</li>
<li><strong>Wielkość pozycji:</strong> jedna pozycja kosztuje najwyżej {n0(cfg['position_value'])} PLN (pełne akcje). Akcje droższe niż {n0(cfg['position_value'])} PLN za sztukę (np. LPP) są pomijane. Zysk ze sprzedaży wraca do gotówki, strata po stopie ją pomniejsza. Gdy cała gotówka jest zaangażowana w pozycje i zlecenia, nowe zlecenia czekają, aż któraś pozycja zostanie zamknięta (cel albo stop).</li>
<li><strong>Wyjścia:</strong> stop (przy luce po cenie otwarcia), cel 1 (sprzedaż połowy, stop przesuwany na cenę wejścia), cel 2 (reszta), albo po {cfg['max_hold_days']} dniach po zamknięciu sesji.</li>
<li><strong>Świece dzienne:</strong> gdy jedna świeca dotyka i stopu, i celu, liczymy stop (założenie pesymistyczne). W dniu wejścia sprawdzamy tylko stop.</li>
<li><strong>Koszty:</strong> {str(cfg['fee_pct']).replace('.', ',')}% od każdej transakcji. Podatek od zysków kapitałowych (19%) nie jest uwzględniony.</li>
</ul>"""
    body = (
        f'<h1>Portfel wirtualny</h1>\n<div class="banner">Stan na <strong>{dshort(asof)}.{asof[:4]}</strong> (zamknięcie sesji). '
        f'Symulacja na podstawie rankingu skanera swing, <strong>nie porada inwestycyjna</strong>.</div>\n'
        f'<div class="cards">{cards}</div>\n{equity_chart(st)}\n'
        f'<h2>Otwarte pozycje</h2>\n'
        + table(["Tic", "Spółka", "Szt.", "Wejście", "Data", "Kurs", "Wynik %", "Wynik PLN", "Stop", "C1", "C2", "Dni", "Status"], pos_rows, "Brak otwartych pozycji.")
        + '\n<h2>Zlecenia oczekujące</h2>\n'
        + table(["Tic", "Spółka", "Szt.", "Limit kupna", "Stop", "C1", "C2", "Ważne", "Klasa · suma", "Wartość PLN"], ord_rows, "Brak oczekujących zleceń.")
        + '\n<h2>Zamknięte transakcje</h2>\n'
        + table(["Tic", "Wejście", "Wyjście", "Szt.", "Wynik %", "Wynik PLN", "R", "Dni", "Powód"], cl_rows, "Jeszcze nie zamknięto żadnej transakcji.")
        + '\n<h2>Dziennik</h2>\n<ul class="list">' + "".join(log_rows) + "</ul>"
        + '\n<h2>Zasady symulacji</h2>' + rules
    )
    return body
