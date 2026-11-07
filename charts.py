"""Wykresy SVG budowane z tabeli rankingu w raporcie Markdown.

Bez zależności zewnętrznych. Jeśli tabela ma inny układ albo dane są niepełne,
funkcje po cichu pomijają wykres (strona i tak się zbuduje).

Tabela rankingu musi mieć kolumny: Tic, Suma i opcjonalnie Fund/30, Klasa, Kurs,
Wejście, Stop, C1, C2, R (C1 / C2).
"""
import datetime as dt
import html
import math
import re

NUM = r"\d[\d  ]*(?:,\d+)?"
W = 800  # szerokość viewBox
MINUS = "−"

# Język etykiet wykresów: "pl" (domyślnie) albo "en". Liczby w tabeli wejściowej są zawsze w formacie polskim
# (wykresy budujemy z polskiego Markdownu), zmienia się tylko tekst i format liczb na wykresie.
LANG = "pl"
EN = {
    "Dywidenda i timing (z 50)": "Dividend and timing (of 50)",
    "Trend i technika (z 50)": "Trend and technicals (of 50)",
    "Fundamenty (z 30)": "Fundamentals (of 30)",
    "Technika i reszta": "Technicals and the rest",
    "pkt": "pts", "fundamenty": "fundamentals", "reszta": "rest",
    "Ranking punktowy kandydatów": "Candidate score ranking",
    "ryzyko do stopu": "risk to stop", "potencjał do celów": "upside to targets", "strefa wejścia": "entry zone",
    "kurs": "price", "wejście": "entry", "cel 1": "target 1", "cel 2": "target 2",
    "względem kursu": "relative to price",
    "Mapa ryzyka i zysku względem kursu": "Risk and reward map relative to price",
    "R do celu 1": "R to target 1", "R do celu 2": "R to target 2", "do celu 2": "to target 2",
    "min. 1:2": "min. 1:2",
    "Stosunek zysku do ryzyka (R) dla celów 1 i 2": "Reward-to-risk (R) for targets 1 and 2",
    "dziś": "today", "okno ogłoszenia": "announcement window",
    "Okna oczekiwanego ogłoszenia dywidendy": "Expected dividend announcement windows",
    "Wykresy z rankingu": "Charts from the ranking",
    "Kalendarz oczekiwanych ogłoszeń": "Calendar of expected announcements",
    "Okno, w którym najpewniej pojawi się rekomendacja dywidendy; intensywność koloru rośnie z wynikiem.":
        "The window in which a dividend recommendation is most likely to appear; colour intensity grows with the score.",
    "Ranking punktowy": "Score ranking",
    "Suma punktów: dywidenda i timing oraz trend i technika (0–100).": "Total points: dividend and timing plus trend and technicals (0–100).",
    "Suma punktów z podziałem na fundamenty i resztę oceny (0–100).": "Total points split into fundamentals and the rest of the score (0–100).",
    "Mapa ryzyka i zysku": "Risk and reward map",
    "Stop, strefa wejścia i cele jako odchylenie od ostatniego kursu (pierwsze 6 setupów z kompletem poziomów).":
        "Stop, entry zone and targets as a deviation from the last price (first 6 setups with a full set of levels).",
    "Stosunek zysku do ryzyka": "Reward-to-risk",
    "R do celu 1 i celu 2 liczone od środka strefy wejścia; framework preferuje co najmniej ok. 1:2.":
        "R to target 1 and target 2 measured from the middle of the entry zone; the framework prefers at least about 1:2.",
}


def T(k):
    return EN.get(k, k) if LANG == "en" else k


def esc(s):
    return html.escape(str(s), quote=True)


def _f(s):
    return float(s.replace(" ", "").replace(" ", "").replace(",", "."))


def _first(s):
    m = re.search(NUM, s or "")
    return _f(m.group(0)) if m else None


def _range(s):
    m = re.search(rf"({NUM})\s*[–—-]\s*({NUM})", s or "")
    if m:
        a, b = _f(m.group(1)), _f(m.group(2))
        return min(a, b), max(a, b)
    n = _first(s)
    return (n, n) if n is not None else (None, None)


def _iso(s):
    m = re.search(r"\d{4}-\d{2}-\d{2}", s or "")
    try:
        return dt.date.fromisoformat(m.group(0)) if m else None
    except ValueError:
        return None


def _cells(line):
    return [c.strip().replace("**", "").strip() for c in line.strip().strip("|").split("|")]


def parse_ranking(md):
    lines = md.splitlines()
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("|") and "Tic" in ln and ("Suma" in ln or "Total" in ln):
            head = _cells(ln)
            rows = []
            for ln2 in lines[i + 2:]:
                if not ln2.lstrip().startswith("|"):
                    break
                cells = _cells(ln2)
                if len(cells) == len(head):
                    rows.append(dict(zip(head, cells)))
            return head, rows
    return None, []


def _col(head, *names, prefix=False):
    for h in head:
        for n in names:
            if h == n or (prefix and h.startswith(n)):
                return h
    return None


def build_items(head, rows):
    c_tic = _col(head, "Tic")
    c_sum = _col(head, "Suma", "Total")
    c_fund = _col(head, "Fund", "Dyw", "Div", prefix=True)
    c_w0 = _col(head, "Okno od", "Window from")
    c_w1 = _col(head, "Okno do", "Window to")
    c_kl = _col(head, "Klasa", "Class", prefix=True)
    c_price = _col(head, "Kurs", "Price", prefix=True)
    c_in = _col(head, "Wej", "Entry", prefix=True)
    c_stop = _col(head, "Stop")
    c_c1 = _col(head, "C1", "T1")
    c_c2 = _col(head, "C2", "T2")
    c_r = _col(head, "R") or _col(head, "R (", prefix=True)
    items = []
    for r in rows:
        g = lambda c: r.get(c, "") if c else ""
        lo, hi = _range(g(c_in))
        rr = re.findall(r"\d+(?:,\d+)?", g(c_r).split("(")[0]) if c_r else []
        m = re.match(r"\s*([ABC])\b", g(c_kl))
        items.append({
            "tic": g(c_tic) or "?",
            "suma": _first(g(c_sum)),
            "fund": _first(g(c_fund)),
            "kl": m.group(1) if m else "",
            "price": _first(g(c_price)),
            "lo": lo, "hi": hi,
            "stop": _first(g(c_stop)),
            "c1": _first(g(c_c1)),
            "c2": _first(g(c_c2)),
            "win0": _iso(g(c_w0)), "win1": _iso(g(c_w1)),
            "r1": _f(rr[0]) if len(rr) >= 1 else None,
            "r2": _f(rr[1]) if len(rr) >= 2 else None,
        })
    return items


def _pl(v, digits=1, sign=False):
    s = f"{v:+.{digits}f}" if sign else f"{v:.{digits}f}"
    s = s.replace("-", MINUS)
    return s if LANG == "en" else s.replace(".", ",")


WC = 400  # szerokość viewBox wariantu kompaktowego (telefon)


def _svg(h, label, body, w=None, cls=""):
    c = f' class="{cls}"' if cls else ""
    return (f'<svg{c} viewBox="0 0 {w or W} {h}" role="img" aria-label="{esc(label)}" '
            f'xmlns="http://www.w3.org/2000/svg">{body}</svg>')


def _legend(items, x, y, maxw=None):
    """Legenda w jednym rzędzie (szerokości z krotek). Przy maxw zawija do kolejnych rzędów (szerokość tekstu szacowana).
    Zwraca (svg, liczba rzędów)."""
    out, cx, cy, rows = [], x, y, 1
    for color, text, w in items:
        if maxw is not None:
            w = 18 + len(text) * 7.0 + 16
            if cx > x and cx + w - 16 > maxw:
                cx, cy, rows = x, cy + 18, rows + 1
        out.append(f'<rect x="{cx:g}" y="{cy - 9}" width="12" height="12" rx="3" style="fill:{color}"/>')
        out.append(f'<text class="tick" x="{cx + 18:g}" y="{cy + 1}">{esc(text)}</text>')
        cx += w
    return "".join(out), rows


def chart_scores(items, div=False, c=False):
    rows = [i for i in items if i["suma"] is not None]
    if len(rows) < 2:
        return ""
    w = WC if c else W
    x0, x1, rh = (76, w - 34, 30) if c else (150, w - 70, 30)
    sc = (x1 - x0) / 100
    leg = ([("var(--up)", T("Dywidenda i timing (z 50)"), 220), ("var(--accent2)", T("Trend i technika (z 50)"), 210)] if div
           else [("var(--up)", T("Fundamenty (z 30)"), 160), ("var(--accent2)", T("Technika i reszta"), 170)])
    lg, nrows = _legend(leg, 10 if c else x0, 14, maxw=w - 10 if c else None)
    top = 52 + (nrows - 1) * 18
    h = top + rh * len(rows) + 8
    p = [lg]
    for v in (0, 25, 50, 75, 100):
        x = x0 + v * sc
        p.append(f'<line class="grid" x1="{x:.1f}" y1="{top - 10}" x2="{x:.1f}" y2="{h - 4}"/>')
        p.append(f'<text class="tick" x="{x:.1f}" y="{top - 16}" text-anchor="middle">{v}</text>')
    for n, it in enumerate(rows):
        y = top + n * rh
        suma, fund = it["suma"], it["fund"]
        cls = f' <tspan class="cls">· {it["kl"]}</tspan>' if it["kl"] else ""
        p.append(f'<text class="lbl" x="{x0 - 10}" y="{y + 17}" text-anchor="end">{esc(it["tic"])}{cls}</text>')
        if fund is not None and 0 <= fund <= suma:
            w1, w2 = fund * sc, (suma - fund) * sc
            tip = f'{it["tic"]}: {suma:g} {T("pkt")} ({T("fundamenty")} {fund:g}, {T("reszta")} {suma - fund:g})'
            p.append(f'<g><title>{esc(tip)}</title>'
                     f'<rect x="{x0}" y="{y + 6}" width="{max(w1, 1):.1f}" height="16" rx="3" style="fill:var(--up)"/>'
                     f'<rect x="{x0 + w1:.1f}" y="{y + 6}" width="{max(w2, 1):.1f}" height="16" rx="3" style="fill:var(--accent2)"/></g>')
        else:
            p.append(f'<g><title>{esc(it["tic"])}: {suma:g} {T("pkt")}</title>'
                     f'<rect x="{x0}" y="{y + 6}" width="{suma * sc:.1f}" height="16" rx="3" style="fill:var(--accent2)"/></g>')
        p.append(f'<text class="val" x="{x0 + suma * sc + 8:.1f}" y="{y + 18}">{suma:g}</text>')
    return _svg(h, T("Ranking punktowy kandydatów"), "".join(p), w, "c" if c else "")


def chart_ladder(items, limit=6, c=False):
    ok = []
    for i in items:
        if None in (i["price"], i["lo"], i["hi"], i["stop"], i["c1"], i["c2"]):
            continue
        if i["price"] > 0 and i["stop"] < i["lo"] <= i["hi"] < i["c1"] < i["c2"]:
            ok.append(i)
    ok = ok[:limit]
    if len(ok) < 2:
        return ""
    w = WC if c else W
    pct = lambda it, v: (v / it["price"] - 1) * 100
    pmin = min(min(pct(i, i["stop"]) for i in ok), 0) - 2
    pmax = max(max(pct(i, i["c2"]) for i in ok), 0) + 2.5
    x0, x1, rh = (80, w - 22, 56) if c else (110, w - 30, 56)
    lg, nrows = _legend([("var(--down)", T("ryzyko do stopu"), 150), ("var(--up)", T("potencjał do celów"), 170),
                         ("rgba(102,252,241,.35)", T("strefa wejścia"), 140)], 10 if c else x0, 14, maxw=w - 10 if c else None)
    top = 50 + (nrows - 1) * 18
    h = top + rh * len(ok) + 28
    X = lambda v: x0 + (v - pmin) / (pmax - pmin) * (x1 - x0)
    p = [lg]
    step = 5 if pmax - pmin > 18 else 2
    t = math.ceil(pmin / step) * step
    while t <= pmax:
        x = X(t)
        p.append(f'<line class="grid" x1="{x:.1f}" y1="{top - 12}" x2="{x:.1f}" y2="{h - 22}"/>')
        p.append(f'<text class="tick" x="{x:.1f}" y="{h - 6}" text-anchor="middle">{_pl(t, 0, True) if t else T("kurs")}{"%" if t else ""}</text>')
        t += step
    p.append(f'<line x1="{X(0):.1f}" y1="{top - 12}" x2="{X(0):.1f}" y2="{h - 22}" style="stroke:var(--strong);stroke-dasharray:4 4;opacity:.6"/>')
    for n, it in enumerate(ok):
        cy = top + n * rh + 26
        ps, pl_, ph, p1, p2 = (pct(it, it[k]) for k in ("stop", "lo", "hi", "c1", "c2"))
        pm = (pl_ + ph) / 2
        cls = f' <tspan class="cls">· {it["kl"]}</tspan>' if it["kl"] else ""
        p.append(f'<text class="lbl" x="{x0 - 12}" y="{cy + 4}" text-anchor="end">{esc(it["tic"])}{cls}</text>')
        tip = (f'{it["tic"]}: stop {_pl(ps, 1, True)}%, {T("wejście")} {_pl(pl_, 1, True)}…{_pl(ph, 1, True)}%, '
               f'{T("cel 1")} {_pl(p1, 1, True)}%, {T("cel 2")} {_pl(p2, 1, True)}% {T("względem kursu")}')
        zw = max(X(ph) - X(pl_), 5)
        p.append(f'<g><title>{esc(tip)}</title>'
                 f'<rect x="{X(ps):.1f}" y="{cy - 5}" width="{X(pm) - X(ps):.1f}" height="10" rx="3" style="fill:var(--down);opacity:.85"/>'
                 f'<rect x="{X(pm):.1f}" y="{cy - 5}" width="{X(p2) - X(pm):.1f}" height="10" rx="3" style="fill:var(--up);opacity:.9"/>'
                 f'<rect x="{X(pl_):.1f}" y="{cy - 13}" width="{zw:.1f}" height="26" rx="5" style="fill:rgba(102,252,241,.18);stroke:var(--cyan);stroke-width:1.5"/>'
                 f'<circle cx="{X(p1):.1f}" cy="{cy}" r="5.5" style="fill:#0B0C10;stroke:var(--up);stroke-width:2"/>'
                 f'<circle cx="{X(p2):.1f}" cy="{cy}" r="5.5" style="fill:var(--up);stroke:#0B0C10;stroke-width:2"/></g>')
        p.append(f'<text class="neg" x="{X(ps):.1f}" y="{cy - 17}" text-anchor="middle">{_pl(ps, 1, True)}%</text>')
        # Na wąskim wykresie etykiety obu celów mogą na siebie wchodzić: rozsuwamy je na boki.
        close = c and abs(X(p2) - X(p1)) < 40
        a1, a2 = ("end", "start") if close else ("middle", "middle")
        d1, d2 = (4, -4) if close else (0, 0)
        p.append(f'<text class="pos" x="{X(p1) + d1:.1f}" y="{cy - 17}" text-anchor="{a1}">{_pl(p1, 1, True)}%</text>')
        p.append(f'<text class="pos" x="{X(p2) + d2:.1f}" y="{cy - 17}" text-anchor="{a2}">{_pl(p2, 1, True)}%</text>')
    return _svg(h, T("Mapa ryzyka i zysku względem kursu"), "".join(p), w, "c" if c else "")


def chart_rr(items, c=False):
    ok = [i for i in items if i["r1"] is not None and i["r2"] is not None][:12]
    if len(ok) < 2:
        return ""
    w = WC if c else W
    x0, x1, rh = (80, w - 44, 40) if c else (110, w - 60, 40)
    lg, nrows = _legend([("var(--accent2)", T("R do celu 1"), 140), ("var(--up)", T("R do celu 2"), 140)],
                        10 if c else x0, 14, maxw=w - 10 if c else None)
    top = 52 + (nrows - 1) * 18
    h = top + rh * len(ok) + 8
    rmax = max(4.0, max(i["r2"] for i in ok) + 0.6)
    X = lambda v: x0 + v / rmax * (x1 - x0)
    p = [lg]
    v = 0
    while v <= rmax:
        p.append(f'<line class="grid" x1="{X(v):.1f}" y1="{top - 10}" x2="{X(v):.1f}" y2="{h - 4}"/>')
        p.append(f'<text class="tick" x="{X(v):.1f}" y="{top - 16}" text-anchor="middle">{v:g}</text>')
        v += 1
    p.append(f'<line x1="{X(2):.1f}" y1="{top - 10}" x2="{X(2):.1f}" y2="{h - 4}" style="stroke:var(--warn);stroke-dasharray:5 4;stroke-width:1.5"/>')
    p.append(f'<text class="warn" x="{X(2) + 6:.1f}" y="{top - 16}">{T("min. 1:2")}</text>')
    for n, it in enumerate(ok):
        y = top + n * rh
        cls = f' <tspan class="cls">· {it["kl"]}</tspan>' if it["kl"] else ""
        p.append(f'<text class="lbl" x="{x0 - 10}" y="{y + 22}" text-anchor="end">{esc(it["tic"])}{cls}</text>')
        p.append(f'<g><title>{esc(it["tic"])}: {T("R do celu 1")} = {_pl(it["r1"])}, {T("do celu 2")} = {_pl(it["r2"])}</title>'
                 f'<rect x="{x0}" y="{y + 5}" width="{max(X(it["r1"]) - x0, 1):.1f}" height="12" rx="3" style="fill:var(--accent2)"/>'
                 f'<rect x="{x0}" y="{y + 20}" width="{max(X(it["r2"]) - x0, 1):.1f}" height="12" rx="3" style="fill:var(--up)"/></g>')
        p.append(f'<text class="val" x="{X(it["r1"]) + 7:.1f}" y="{y + 15}">{_pl(it["r1"])}</text>')
        p.append(f'<text class="val" x="{X(it["r2"]) + 7:.1f}" y="{y + 30}">{_pl(it["r2"])}</text>')
    return _svg(h, T("Stosunek zysku do ryzyka (R) dla celów 1 i 2"), "".join(p), w, "c" if c else "")


PL_MON = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"]
EN_MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def mon(i):
    return (EN_MON if LANG == "en" else PL_MON)[i]


def dm(d):
    return f"{d.day} {EN_MON[d.month - 1]}" if LANG == "en" else f"{d.day}.{d.month:02d}"


def chart_calendar(items, ref, c=False):
    """Oś czasu okien oczekiwanego ogłoszenia dywidendy (kolumny Okno od / Okno do)."""
    rows = [i for i in items if i["win0"] and i["win1"] and i["win0"] <= i["win1"]][:16]
    if len(rows) < 2 or ref is None:
        return ""
    w = WC if c else W
    start = ref
    end = min(max(max(i["win1"] for i in rows), ref + dt.timedelta(days=150)), ref + dt.timedelta(days=420))
    span = (end - start).days or 1
    x0, x1, top, rh = (80, w - 12, 56, 30) if c else (110, w - 40, 56, 30)
    h = top + rh * len(rows) + 12
    X = lambda d: x0 + (min(max(d, start), end) - start).days / span * (x1 - x0)
    # Na wąskim wykresie podpisujemy co kilka miesięcy, żeby etykiety nie wchodziły na siebie.
    stride = max(1, math.ceil(34 / ((x1 - x0) * 30.44 / span))) if c else 1
    p = []
    m = dt.date(start.year, start.month, 1)
    k = 0
    while m <= end:
        if m >= start:
            x = X(m)
            p.append(f'<line class="grid" x1="{x:.1f}" y1="{top - 12}" x2="{x:.1f}" y2="{h - 6}"/>')
            if k % stride == 0:
                lab = mon(m.month - 1) + ((f" '{m.year % 100}" if LANG == "en" else f" {m.year % 100}") if m.month == 1 or m == dt.date(start.year, start.month, 1) else "")
                p.append(f'<text class="tick" x="{x + 3:.1f}" y="{top - 18}">{lab}</text>')
            k += 1
        m = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    p.append(f'<line x1="{X(start):.1f}" y1="{top - 12}" x2="{X(start):.1f}" y2="{h - 6}" style="stroke:var(--strong);stroke-dasharray:4 4;opacity:.7"/>')
    p.append(f'<text class="warn" x="{X(start) + 4:.1f}" y="{top - 32}">{T("dziś")}</text>')
    for n, it in enumerate(rows):
        y = top + n * rh
        cls = f' <tspan class="cls">· {it["kl"]}</tspan>' if it["kl"] else ""
        p.append(f'<text class="lbl" x="{x0 - 12}" y="{y + 19}" text-anchor="end">{esc(it["tic"])}{cls}</text>')
        xa, xb = X(it["win0"]), X(it["win1"])
        bw = max(xb - xa, 6)
        op = 0.45 + 0.55 * min(max((it["suma"] or 50) / 100, 0), 1)
        tip = f'{it["tic"]}: {T("okno ogłoszenia")} {it["win0"].isoformat()} … {it["win1"].isoformat()}'
        p.append(f'<g><title>{esc(tip)}</title><rect x="{xa:.1f}" y="{y + 7}" width="{bw:.1f}" height="16" rx="4" style="fill:var(--up);opacity:{op:.2f}"/></g>')
        lab = f'{dm(it["win0"])}–{dm(it["win1"])}'
        if c:
            est = len(lab) * 7.0
            if xb + 8 + est <= w - 4:
                tx, anchor, kls = xb + 8, "start", "tick"
            elif xa - 8 - est >= x0:
                tx, anchor, kls = xa - 8, "end", "tick"
            else:  # okno rozciąga się na prawie całą oś: podpis w środku paska
                tx, anchor, kls = (xa + xb) / 2, "middle", "val"
        else:
            tx = xb + 8 if xb + 8 < x1 - 70 else xa - 8
            anchor, kls = ("start" if xb + 8 < x1 - 70 else "end"), "tick"
        p.append(f'<text class="{kls}" x="{tx:.1f}" y="{y + 19}" text-anchor="{anchor}">{lab}</text>')
    return _svg(h, T("Okna oczekiwanego ogłoszenia dywidendy"), "".join(p), w, "c" if c else "")


def chart_bars(rows, unit="%", c=False, label=""):
    """Poziome słupki z osią zerową (dodatnie na zielono, ujemne na czerwono) dla raportów strategii. rows: [(etykieta, wartość)]."""
    rows = [(str(l), float(v)) for l, v in rows if v is not None]
    if not rows:
        return ""
    w = WC if c else W
    x0, x1 = (88, w - 56) if c else (150, w - 96)
    lo, hi = min(0.0, min(v for _, v in rows)), max(0.0, max(v for _, v in rows))
    if hi - lo < 1e-9:
        hi = lo + 1
    pad = (hi - lo) * 0.04
    lo, hi = (lo - pad if lo < 0 else 0.0), (hi + pad if hi > 0 else 0.0)
    sc = (x1 - x0) / (hi - lo)
    zx = x0 - lo * sc
    rh, top = 28, 26
    h = top + rh * len(rows) + 8
    d = 0 if max(abs(v) for _, v in rows) >= 100 else 1
    fmt = lambda v, sign=False: _pl(v, d, sign) + unit
    p = []
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        x = x0 + (v - lo) * sc
        p.append(f'<line class="grid" x1="{x:.1f}" y1="{top - 10}" x2="{x:.1f}" y2="{h - 4}"/>')
        p.append(f'<text class="tick" x="{x:.1f}" y="{top - 14}" text-anchor="middle">{fmt(v)}</text>')
    for i, (lab, v) in enumerate(rows):
        y = top + i * rh
        bw = max(abs(v) * sc, 1.0)
        bx = zx if v >= 0 else zx - bw
        col = "var(--up)" if v >= 0 else "var(--down)"
        p.append(f'<text class="lbl" x="{x0 - 10}" y="{y + 17}" text-anchor="end">{esc(lab)}</text>')
        p.append(f'<g><title>{esc(lab)}: {fmt(v, True)}</title><rect x="{bx:.1f}" y="{y + 5}" width="{bw:.1f}" height="16" rx="3" style="fill:{col}"/></g>')
        tx, anchor = (bx + bw + 8, "start") if v >= 0 else (bx - 8, "end")
        p.append(f'<text class="val" x="{tx:.1f}" y="{y + 18}" text-anchor="{anchor}">{fmt(v, True)}</text>')
    p.append(f'<line x1="{zx:.1f}" y1="{top - 10}" x2="{zx:.1f}" y2="{h - 4}" style="stroke:var(--muted);stroke-width:1.2"/>')
    return _svg(h, label, "".join(p), w, "c" if c else "")


def strategy_chart(spec, lang="pl"):
    """Karta wykresu dla raportu strategii (znacznik <!-- chart --> w Markdownie). spec: {unit, rows, title{pl,en}, sub{pl,en}}.
    Pusty wynik, gdy brak danych."""
    global LANG
    old, LANG = LANG, lang
    try:
        rows = spec.get("rows") or []
        title, sub = spec["title"][lang], spec["sub"][lang]
        wide, compact = chart_bars(rows, spec.get("unit", "%"), False, title), chart_bars(rows, spec.get("unit", "%"), True, title)
        if not wide:
            return ""
        return (f'<div class="chart-card"><h2 class="ch">{esc(title)}</h2><p class="sub">{esc(sub)}</p>'
                f'<div class="cv-d">{wide}</div><div class="cv-c">{compact}</div></div>')
    except (KeyError, TypeError, ValueError):
        return ""
    finally:
        LANG = old


def render_charts(md, ref=None):
    """Zwraca HTML sekcji z wykresami albo pusty tekst, gdy nie da się ich zbudować.
    Każdy wykres powstaje w dwóch wariantach: szerokim (komputer) i kompaktowym (telefon); CSS pokazuje jeden z nich."""
    try:
        head, rows = parse_ranking(md)
        if not head or not rows:
            return ""
        items = build_items(head, rows)
        div = any(h.startswith(("Dyw", "Div")) for h in head)
        specs = []
        if div:
            specs.append((T("Kalendarz oczekiwanych ogłoszeń"), T("Okno, w którym najpewniej pojawi się rekomendacja dywidendy; intensywność koloru rośnie z wynikiem."), lambda c: chart_calendar(items, ref, c)))
        specs += [
            (T("Ranking punktowy"), T("Suma punktów: dywidenda i timing oraz trend i technika (0–100)." if div else "Suma punktów z podziałem na fundamenty i resztę oceny (0–100)."), lambda c: chart_scores(items, div, c)),
            (T("Mapa ryzyka i zysku"), T("Stop, strefa wejścia i cele jako odchylenie od ostatniego kursu (pierwsze 6 setupów z kompletem poziomów)."), lambda c: chart_ladder(items, 6, c)),
            (T("Stosunek zysku do ryzyka"), T("R do celu 1 i celu 2 liczone od środka strefy wejścia; framework preferuje co najmniej ok. 1:2."), lambda c: chart_rr(items, c)),
        ]
        cards = []
        for t, sub, build in specs:
            wide, compact = build(False), build(True)
            if wide:
                cards.append(f'<div class="chart-card"><h3>{esc(t)}</h3><p class="sub">{esc(sub)}</p>'
                             f'<div class="cv-d">{wide}</div><div class="cv-c">{compact}</div></div>')
        if not cards:
            return ""
        return '<section class="charts">\n<h2 id="charts">' + esc(T("Wykresy z rankingu")) + '</h2>\n' + "\n".join(cards) + "\n</section>"
    except Exception:
        return ""


def deco_svg():
    """Dekoracyjne świece i linia trendu do nagłówka (czysto ozdobne)."""
    closes = [92, 88, 96, 90, 98, 104, 99, 108, 112, 106, 116, 122, 117, 126, 131, 138]
    y = lambda v: 132 - (v - 80) * 1.5
    out, prev, pts = [], 90, []
    for i, c in enumerate(closes):
        x = 24 + 31 * i
        hi, lo = max(prev, c) + 5, min(prev, c) - 5
        col = "#2BFF88" if c >= prev else "#FF5C7A"
        out.append(f'<line x1="{x + 7}" y1="{y(hi):.1f}" x2="{x + 7}" y2="{y(lo):.1f}" stroke="{col}" stroke-width="1.5"/>')
        top_, bot = y(max(prev, c)), y(min(prev, c))
        out.append(f'<rect x="{x}" y="{top_:.1f}" width="14" height="{max(bot - top_, 2):.1f}" rx="2" fill="{col}"/>')
        pts.append(f"{x + 7},{y(c):.1f}")
        prev = c
    return ('<svg class="deco" viewBox="0 0 520 140" preserveAspectRatio="xMaxYMid meet" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
            '<defs><linearGradient id="fadeg" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#000"/><stop offset=".5" stop-color="#fff"/></linearGradient>'
            '<mask id="fadem"><rect width="520" height="140" fill="url(#fadeg)"/></mask></defs>'
            '<g mask="url(#fadem)">' + "".join(out) +
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="#66FCF1" stroke-width="2" opacity=".8"/></g></svg>')
