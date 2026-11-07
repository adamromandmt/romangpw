"""Pięć strategii portfelowych obok Swing: Kompas, Pęd, Złoty Środek, Przystań, Dryf.

Każda strategia ma stan w strategies/<klucz>/state.json (portfel wirtualny 100 000 PLN od 6.11.2026, pierwsze zlecenia na otwarciu
9.11.2026). Brak danych nie zatrzymuje budowy strony: strategia zostaje w gotówce, a raport pokazuje, czego brakuje („czeka na dane").
Uruchomienie: python3 strategies.py   (po fetch_quotes.py; zapisuje stany). Strony renderuje build.py (render_report, render_portfolio,
render_archive).

Uproszczenia (opisane też w metodologiach): indeksy cenowe zamiast TR, gotówka bez odsetek, wykonanie po cenie otwarcia, dywidendy
jeszcze nie są doliczane do portfela, kurs bez korekt (surowe notowania).
"""
import csv
import datetime as dt
import glob
import html
import json
import math
import statistics
import sys
from pathlib import Path

import quotes

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "strategies"
START_DATE = "2026-11-06"
FIRST_ORDERS = "2026-11-09"
CAPITAL = 100_000.0
FEE_PCT = 0.2
KEYS = ["kompas", "ped", "zloty-srodek", "przystan", "dryf"]
NAMES = {
    "kompas": ("Kompas", "Compass"), "ped": ("Pęd", "Momentum"), "zloty-srodek": ("Złoty Środek", "Golden Mean"),
    "przystan": ("Przystań", "Harbor"), "dryf": ("Dryf", "Drift"),
}
RHYTHM = {
    "kompas": ("miesięcznie", "monthly"), "ped": ("miesięcznie", "monthly"), "zloty-srodek": ("maj i październik", "May and October"),
    "przystan": ("kwartalnie (mar, cze, wrz, gru)", "quarterly (Mar, Jun, Sep, Dec)"), "dryf": ("codziennie w oknach raportów", "daily in report windows"),
}
ONE_LINE = {
    "kompas": ("Rotacja WIG20 / mWIG40 / sWIG80 z filtrem trendu: najsilniejszy indeks albo gotówka.",
               "Rotation among WIG20 / mWIG40 / sWIG80 with a trend filter: the strongest index, or cash."),
    "ped": ("12 spółek o najwyższej stopie zwrotu 12-1, powyżej SMA200, maks. 3 z sektora.",
            "The 12 stocks with the highest 12-1 return, above the SMA200, at most 3 per sector."),
    "zloty-srodek": ("20 tanich i solidnych spółek: F-score Piotroskiego ≥ 7, dodatni FCF, niskie zadłużenie, bez banków i ubezpieczycieli.",
                     "20 cheap, sound stocks: Piotroski F-score ≥ 7, positive FCF, low leverage, no banks or insurers."),
    "przystan": ("16 spółek z najniższą zmiennością 12M (kwintyl), maks. 4 z sektora, obsunięcie ≤ 30%.",
                 "16 stocks from the lowest 12M volatility quintile, at most 4 per sector, drawdown ≤ 30%."),
    "dryf": ("Luka w górę ≥ 2% na wolumenie ≥ 2,5× średniej w oknie raportu; stop = poprzednie zamknięcie, wyjście po 40 sesjach.",
             "A gap up of ≥ 2% on volume ≥ 2.5× average inside a report window; stop = previous close, exit after 40 sessions."),
}
INDEX_KEYS = {"WIG20": "_WIG20", "mWIG40": "_MWIG40", "sWIG80": "_SWIG80"}
FUND_COLS = ["tic", "sector", "f_score", "fcf", "net_debt_ebitda", "ev_ebit", "gross_profit_assets", "is_financial", "is_energy"]

# Brakujące dane: kod -> (PL, EN)
MISS = {
    "history": ("za krótka historia notowań ({have} z {need} sesji); uruchom fetch_quotes.py --history 520",
                "price history too short ({have} of {need} sessions); run fetch_quotes.py --history 520"),
    "index": ("brak plików indeksów w data/market ({names})", "index files missing in data/market ({names})"),
    "fund": ("data/fundamentals.csv ma tylko nagłówek (brak danych fundamentalnych)", "data/fundamentals.csv holds only a header (no fundamentals)"),
    "earn": ("brak kalendarza raportów kwartalnych", "no quarterly-report calendar"),
}


def miss(code, **kw):
    return {"code": code, **kw}


# ---------------------------------------------------------------- dane
class Data:
    def __init__(self, stocks=None, indices=None, sectors=None, names=None, earnings=None, fundamentals=None):
        self.stocks = stocks or {}      # tic -> lista świec
        self.indices = indices or {}    # nazwa -> lista świec
        self.sectors = sectors or {}
        self.names = names or {}
        self.earnings = earnings or {}  # tic -> zbiór dat (RRRR-MM-DD)
        self.fund = fundamentals or []
        self.sessions = sorted({c["date"] for v in self.stocks.values() for c in v})

    def candles(self, name):
        return self.stocks.get(name) or self.indices.get(name)


def load_data():
    uni = json.loads((ROOT / "data" / "universe.json").read_text(encoding="utf-8"))
    stocks = {t: c for t in uni["stocks"] if (c := quotes.load(t))}
    indices = {n: c for n, f in INDEX_KEYS.items() if (c := quotes.read_csv(quotes.MARKET / f"{f}.csv"))}
    sectors, names = {}, {}
    jp = ROOT / "data" / "dividends" / "judgement.json"
    if jp.exists():
        for t, j in json.loads(jp.read_text(encoding="utf-8")).items():
            sectors[t], names[t] = j.get("sector", ""), j.get("name", t)
    earnings = {}
    for f in sorted(glob.glob(str(ROOT / "reports" / "*.json"))):
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
        except ValueError:
            continue
        for c in d.get("candidates", []):
            e = c.get("earnings") or {}
            if e.get("date"):
                earnings.setdefault(c["tic"], set()).add(e["date"])
            if c.get("sector"):
                sectors.setdefault(c["tic"], c["sector"])
            if c.get("name"):
                names.setdefault(c["tic"], c["name"])
    ep = ROOT / "data" / "earnings.csv"   # opcjonalnie: tic,date
    if ep.exists():
        with ep.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                earnings.setdefault(r["tic"], set()).add(r["date"])
    fund = []
    fp = ROOT / "data" / "fundamentals.csv"
    if fp.exists():
        with fp.open(encoding="utf-8", newline="") as fh:
            fund = list(csv.DictReader(fh))
    return Data(stocks, indices, sectors, names, earnings, fund)


def upto(candles, date):
    """Świece o dacie < date (stan danych przed otwarciem sesji `date`)."""
    return [c for c in candles if c["date"] < date]


# ---------------------------------------------------------------- selektory (czyste funkcje)
def month_closes(candles):
    """Ostatnie zamknięcie każdego miesiąca (ostatni punkt = bieżący, niepełny miesiąc)."""
    by = {}
    for c in candles:
        by[c["date"][:7]] = c["close"]
    return [by[k] for k in sorted(by)]


def kompas_pick(idx_candles):
    """idx_candles: nazwa -> świece. Zwraca (nazwa albo None, wiersze, braki)."""
    rows, short = [], False
    for n, cs in idx_candles.items():
        m = month_closes(cs)
        if len(m) < 13:
            short = True
            rows.append({"name": n, "r6": None, "r12": None, "avg10": None, "close": cs[-1]["close"] if cs else None, "score": None})
            continue
        r6, r12 = m[-1] / m[-7] - 1, m[-1] / m[-13] - 1
        rows.append({"name": n, "r6": r6, "r12": r12, "avg10": sum(m[-10:]) / 10, "close": m[-1], "score": (r6 + r12) / 2})
    if short or len(rows) < len(INDEX_KEYS):
        return None, rows, True
    best = max(rows, key=lambda r: r["score"])
    return (best["name"] if best["close"] > best["avg10"] else "CASH"), rows, False


def ped_rank(stock_candles, sectors, n=12, per_sector=3):
    """12-1: zwrot od 252 do 21 sesji wstecz; kurs > SMA200. Zwraca (wybrane, wszystkie wiersze)."""
    rows = []
    for t, cs in stock_candles.items():
        cl = [c["close"] for c in cs]
        if len(cl) < 253:
            continue
        sma = sum(cl[-200:]) / 200
        rows.append({"tic": t, "ret": cl[-22] / cl[-253] - 1, "close": cl[-1], "sma200": sma, "ok": cl[-1] > sma})
    rows.sort(key=lambda r: -r["ret"])
    chosen, cnt = [], {}
    for r in rows:
        if not r["ok"]:
            continue
        sec = sectors.get(r["tic"]) or f"?{r['tic']}"   # nieznany sektor nie jest łączony z innymi
        if cnt.get(sec, 0) >= per_sector:
            continue
        cnt[sec] = cnt.get(sec, 0) + 1
        chosen.append(r)
        if len(chosen) == n:
            break
    return chosen, rows


def zs_rank(fund, n=20, energy_cap=8):
    def num(r, k):
        try:
            return float(str(r[k]).replace(",", "."))
        except (KeyError, ValueError, TypeError):
            return None
    elig = []
    for r in fund:
        if str(r.get("is_financial", "")).strip().lower() in ("1", "true", "tak", "yes"):
            continue
        f, fcf, nd, ev, gp = (num(r, k) for k in ("f_score", "fcf", "net_debt_ebitda", "ev_ebit", "gross_profit_assets"))
        if None in (f, fcf, nd, ev, gp) or f < 7 or fcf <= 0 or nd > 3 or ev <= 0:
            continue
        elig.append({"tic": r["tic"], "sector": r.get("sector", ""), "f": f, "ev_ebit": ev, "gp": gp,
                     "energy": str(r.get("is_energy", "")).strip().lower() in ("1", "true", "tak", "yes")})
    by_ev = {r["tic"]: i for i, r in enumerate(sorted(elig, key=lambda r: r["ev_ebit"]))}
    by_gp = {r["tic"]: i for i, r in enumerate(sorted(elig, key=lambda r: -r["gp"]))}
    for r in elig:
        r["rank"] = by_ev[r["tic"]] + by_gp[r["tic"]]
    elig.sort(key=lambda r: (r["rank"], r["tic"]))
    chosen, en = [], 0
    for r in elig:
        if r["energy"]:
            if en >= energy_cap:
                continue
            en += 1
        chosen.append(r)
        if len(chosen) == n:
            break
    return chosen, elig


def max_drawdown(cl):
    peak, dd = cl[0], 0.0
    for v in cl:
        peak = max(peak, v)
        dd = max(dd, 1 - v / peak)
    return dd


def przystan_rank(stock_candles, sectors, n=16, per_sector=4):
    rows = []
    for t, cs in stock_candles.items():
        cl = [c["close"] for c in cs][-253:]
        if len(cl) < 253:
            continue
        rets = [cl[i] / cl[i - 1] - 1 for i in range(1, len(cl))]
        rows.append({"tic": t, "vol": statistics.pstdev(rets) * math.sqrt(252), "dd": max_drawdown(cl[-252:])})
    if not rows:
        return [], []
    rows.sort(key=lambda r: r["vol"])
    q = rows[:max(1, len(rows) // 5)]
    chosen, cnt = [], {}
    for r in q:
        if r["dd"] > 0.30:
            continue
        sec = sectors.get(r["tic"]) or f"?{r['tic']}"
        if cnt.get(sec, 0) >= per_sector:
            continue
        cnt[sec] = cnt.get(sec, 0) + 1
        chosen.append(r)
        if len(chosen) == n:
            break
    return chosen, rows


def in_window(date, report_dates, sessions, after=3):
    """Czy `date` leży w oknie raportu: od dnia raportu do `after` sesji po nim."""
    for e in report_dates:
        if e <= date:
            idx = [s for s in sessions if e <= s <= date]
            if len(idx) <= after + 1:
                return True
    return False


def dryf_events(tic, cs, report_dates, sessions):
    """Zdarzenia luki w oknach raportów: lista (data, 'up'|'down', stop). Wolumen vs średnia z 20 poprzednich sesji."""
    out = []
    for i in range(21, len(cs)):
        c, p = cs[i], cs[i - 1]
        avg = sum(x["volume"] for x in cs[i - 20:i]) / 20
        if avg <= 0 or c["volume"] < 2.5 * avg or not in_window(c["date"], report_dates, sessions):
            continue
        if c["open"] >= p["close"] * 1.02:
            out.append((c["date"], "up", p["close"]))
        elif c["open"] <= p["close"] * 0.98:
            out.append((c["date"], "down", None))
    return out


# ---------------------------------------------------------------- decyzje
def is_rebalance(key, date, prev_date):
    """Czy sesja `date` jest pierwszą sesją okresu rebalansu (poprzednia sesja jest w innym miesiącu)."""
    first = prev_date is None or prev_date[:7] != date[:7]
    if not first:
        return False
    m = int(date[5:7])
    return {"kompas": True, "ped": True, "zloty-srodek": m in (5, 10), "przystan": m in (3, 6, 9, 12)}.get(key, False)


def decide(key, d, date):
    """Zwraca dict: status ('ok'/'waiting'), missing, targets {tic: waga}, info (tabele do raportu), lub None, gdy to nie dzień decyzji.
    Dane przed sesją `date` (bez niej)."""
    hist = {t: upto(cs, date) for t, cs in d.stocks.items()}
    hist = {t: cs for t, cs in hist.items() if cs}
    longest = max((len(cs) for cs in hist.values()), default=0)
    res = {"status": "ok", "missing": [], "targets": {}, "tables": []}
    if key == "kompas":
        idx = {n: upto(cs, date) for n, cs in d.indices.items()}
        absent = [n for n in INDEX_KEYS if n not in idx]
        pick, rows, short = kompas_pick(idx)
        if absent:
            res["missing"].append(miss("index", names=", ".join(absent)))
        elif short:
            res["missing"].append(miss("history", have=min(len(month_closes(c)) for c in idx.values()) * 21, need=13 * 21))
        res["tables"].append(("kompas", rows))
        if pick and pick != "CASH":
            res["targets"] = {pick: 1.0}
        res["pick"] = pick
    elif key == "ped":
        if longest < 253:
            res["missing"].append(miss("history", have=longest, need=253))
        chosen, rows = ped_rank(hist, d.sectors)
        k = decide("kompas", d, date)
        half = 0.5 if (k["status"] == "ok" and k.get("pick") == "CASH") else 1.0
        for r in chosen:
            r["name"] = d.names.get(r["tic"], "")
        res["targets"] = {r["tic"]: half / 12 for r in chosen}
        res["half"] = half < 1
        res["tables"].append(("ped", chosen))
    elif key == "zloty-srodek":
        if not d.fund:
            res["missing"].append(miss("fund"))
        else:
            chosen, rows = zs_rank(d.fund)
            res["targets"] = {r["tic"]: 1 / 20 for r in chosen}
            res["tables"].append(("zs", chosen))
    elif key == "przystan":
        if longest < 253:
            res["missing"].append(miss("history", have=longest, need=253))
        chosen, rows = przystan_rank(hist, d.sectors)
        res["targets"] = {r["tic"]: 1 / 16 for r in chosen}
        res["tables"].append(("przystan", chosen))
    elif key == "dryf":
        if not d.earnings:
            res["missing"].append(miss("earn"))
    if res["missing"]:
        res["status"] = "waiting"
        res["targets"] = {}
    return res


# ---------------------------------------------------------------- silnik portfela
def new_state(key):
    return {"key": key, "config": {"start_capital": CAPITAL, "fee_pct": FEE_PCT, "start_date": START_DATE, "first_orders": FIRST_ORDERS},
            "cash": CAPITAL, "positions": [], "closed": [], "orders": [], "equity": [{"date": START_DATE, "equity": CAPITAL}],
            "log": [], "decisions": [], "processed": START_DATE, "report": {}}


def fee(v):
    return abs(v) * FEE_PCT / 100


def price_at(d, tic, date, field):
    for c in d.candles(tic) or []:
        if c["date"] == date:
            return c[field]
    return None


def last_close(d, tic, date):
    cs = [c for c in (d.candles(tic) or []) if c["date"] <= date]
    return cs[-1]["close"] if cs else None


def equity_at(st, d, date):
    return st["cash"] + sum(p["shares"] * (last_close(d, p["tic"], date) or p["entry"]) for p in st["positions"])


def sell(st, d, p, date, price, reason):
    val = p["shares"] * price
    st["cash"] += val - fee(val)
    st["positions"].remove(p)
    pnl = val - fee(val) - p["cost"]
    st["closed"].append({"tic": p["tic"], "entry": p["entry"], "entry_date": p["entry_date"], "exit": price, "exit_date": date,
                         "shares": p["shares"], "pnl": round(pnl, 2), "pnl_pct": round(pnl / p["cost"] * 100, 2), "reason": reason})
    st["log"].append({"date": date, "text": f"SELL|{p['tic']}|{p['shares']:g}|{price:.2f}|{reason}"})


def buy(st, d, tic, date, price, value, stop=None):
    frac = tic in d.indices
    shares = value / (price * (1 + FEE_PCT / 100)) if frac else math.floor(value / (price * (1 + FEE_PCT / 100)))
    if shares <= 0:
        return
    cost = shares * price + fee(shares * price)
    if cost > st["cash"]:
        return
    st["cash"] -= cost
    st["positions"].append({"tic": tic, "name": d.names.get(tic, tic), "shares": round(shares, 4) if frac else shares, "entry": price,
                            "entry_date": date, "cost": cost, "stop": stop, "last_close": price})
    st["log"].append({"date": date, "text": f"BUY|{tic}|{shares:g}|{price:.2f}|"})


def run_day(st, d, key, date, prev):
    """Jedna sesja: wykonanie decyzji na otwarciu, stopy/wyjścia czasowe Dryfu, wycena na zamknięciu."""
    first = st["processed"] == START_DATE and date >= FIRST_ORDERS
    if key == "dryf":
        _dryf_day(st, d, date, prev)
    elif first or is_rebalance(key, date, prev):
        dec = decide(key, d, date)
        st["decisions"].append({"date": date, "status": dec["status"], "missing": dec["missing"], "targets": dec["targets"]})
        if dec["status"] == "ok":
            eq = equity_at(st, d, prev) if prev else st["cash"]
            for p in list(st["positions"]):
                if p["tic"] not in dec["targets"]:
                    px = price_at(d, p["tic"], date, "open")
                    if px:
                        sell(st, d, p, date, px, "rebalans")
            for tic, w in dec["targets"].items():
                if not any(p["tic"] == tic for p in st["positions"]):
                    px = price_at(d, tic, date, "open")
                    if px:
                        buy(st, d, tic, date, px, eq * w)
        else:
            st["log"].append({"date": date, "text": "WAIT|" + "; ".join(m["code"] for m in dec["missing"])})
    for p in st["positions"]:
        p["last_close"] = last_close(d, p["tic"], date) or p["last_close"]
    st["equity"].append({"date": date, "equity": round(equity_at(st, d, date), 2)})
    st["processed"] = date


def _dryf_day(st, d, date, prev):
    sess = d.sessions
    nobuy = st.setdefault("nobuy", {})
    for p in list(st["positions"]):
        o, lo = price_at(d, p["tic"], date, "open"), price_at(d, p["tic"], date, "low")
        held = len([s for s in sess if p["entry_date"] < s <= date])
        if o is not None and p["stop"] and lo is not None and lo <= p["stop"]:
            sell(st, d, p, date, min(o, p["stop"]), "stop")
        elif held >= 40:
            sell(st, d, p, date, price_at(d, p["tic"], date, "close") or p["last_close"], "czas (40 sesji)")
    if not prev:
        return
    eq = equity_at(st, d, prev)
    for tic, cs in d.stocks.items():
        ev = [e for e in dryf_events(tic, upto(cs, date), d.earnings.get(tic, ()), [s for s in sess if s < date]) if e[0] == prev]
        for _, kind, stop in ev:
            if kind == "down":
                nobuy[tic] = prev
            elif nobuy.get(tic) and len([s for s in sess if nobuy[tic] < s <= date]) <= 60:
                continue
            elif not any(p["tic"] == tic for p in st["positions"]) and len(st["positions"]) < 20:
                px = price_at(d, tic, date, "open")
                if px and px > stop:
                    buy(st, d, tic, date, px, min(eq * 0.05, st["cash"]), stop)


def dryf_preview(d, asof):
    """Sygnały z ostatniej sesji (zlecenia na następne otwarcie) i lista „nie kupuj"."""
    sess = d.sessions
    up, down = [], []
    for tic, cs in d.stocks.items():
        for dte, kind, stop in dryf_events(tic, cs, d.earnings.get(tic, ()), sess):
            if dte == asof:
                (up if kind == "up" else down).append({"tic": tic, "stop": stop, "close": cs[-1]["close"]})
    return up, down


def build_state(key, d, old=None):
    """Odtwarza stan od zera z danych (deterministycznie), więc ponowne uruchomienie niczego nie psuje."""
    st = new_state(key)
    sess = [s for s in d.sessions if s >= START_DATE]
    for i, s in enumerate(sess):
        if s <= START_DATE:
            continue
        prev = sess[i - 1] if i else None
        run_day(st, d, key, s, prev)
    asof = d.sessions[-1] if d.sessions else START_DATE
    st["asof"] = asof
    nxt = FIRST_ORDERS if asof < FIRST_ORDERS else None
    # raport: stan decyzji na dziś
    rep = {"asof": asof, "tables": [], "missing": [], "status": "ok", "pending": [], "nobuy": []}
    if key == "dryf":
        if not d.earnings:
            rep["status"], rep["missing"] = "waiting", [miss("earn")]
        else:
            up, down = dryf_preview(d, asof)
            rep["pending"] = [{"tic": u["tic"], "stop": u["stop"], "ref": u["close"]} for u in up]
            rep["nobuy"] = [x["tic"] for x in down] + sorted(st.get("nobuy", {}))
            rep["windows"] = sum(1 for v in d.earnings.values() for e in v if e >= asof)
    else:
        probe_date = (dt.date.fromisoformat(asof) + dt.timedelta(days=1)).isoformat()
        dec = decide(key, d, probe_date)
        rep["status"], rep["missing"] = dec["status"], dec["missing"]
        rep["pending"] = [{"tic": t, "w": w} for t, w in dec["targets"].items()]
        rep["half"] = dec.get("half", False)
        rep["pick"] = dec.get("pick")
        rep["tables"] = [{"kind": k, "rows": rows} for k, rows in dec["tables"]]
        if key == "kompas" and dec.get("status") == "waiting":
            rep["tables"] = [{"kind": k, "rows": rows} for k, rows in dec["tables"]]
    st["report"] = rep
    st["status"] = rep["status"]
    st["sessions"] = len(d.sessions)
    return st


def main():
    d = load_data()
    fp = ROOT / "data" / "fundamentals.csv"
    if not fp.exists():
        fp.write_text(",".join(FUND_COLS) + "\n", encoding="utf-8")
    for key in KEYS:
        st = build_state(key, d)
        p = OUT / key / "state.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(st, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{key}: {st['status']}, sesji danych {st['sessions']}, pozycji {len(st['positions'])}")
    return 0


# ---------------------------------------------------------------- strony
def _L(lang):
    return (lambda pl, en: en) if lang == "en" else (lambda pl, en: pl)


def esc(s):
    return html.escape(str(s))


def missing_text(m, lang):
    pl, en = MISS[m["code"]]
    return (en if lang == "en" else pl).format(**{k: v for k, v in m.items() if k != "code"})


def _pct(v, lang):
    if v is None:
        return "—"
    s = f"{v * 100:+.1f}%"
    return s.replace("-", "−") if lang == "en" else s.replace(".", ",").replace("-", "−")


def _tbl(head, rows, empty):
    if not rows:
        return f'<p class="empty">{esc(empty)}</p>'
    th = "".join(f"<th>{esc(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"


def _num(v, nd=2, lang="pl"):
    s = f"{v:,.{nd}f}"
    return s if lang == "en" else s.replace(",", " ").replace(".", ",")


def render_report(st, key, lang="pl"):
    L = _L(lang)
    rep = st["report"]
    nm = NAMES[key][1 if lang == "en" else 0]
    out = [f"<h1>{esc(nm)} — {L('Raport', 'Report')}</h1>",
           f'<div class="banner">{esc(ONE_LINE[key][1 if lang == "en" else 0])} '
           f'{L("Rytm", "Rhythm")}: <strong>{esc(RHYTHM[key][1 if lang == "en" else 0])}</strong>. '
           f'{L("Dane do", "Data to")}: <strong>{rep["asof"]}</strong>. '
           f'{L("Ćwiczenie przesiewowe, nie porada inwestycyjna.", "A screening exercise, not investment advice.")}</div>']
    if rep["status"] == "waiting":
        items = "".join(f"<li>{esc(missing_text(m, lang))}</li>" for m in rep["missing"])
        out.append(f'<h2>{L("Czeka na dane", "Waiting for data")}</h2>\n<p>'
                   f'{L("Strategia nie ma jeszcze kompletu danych, więc portfel pozostaje w gotówce (100 000 PLN). Brakuje:", "The strategy does not have complete data yet, so the portfolio stays in cash (PLN 100,000). Missing:")}</p><ul class="list">{items}</ul>')
    for t in rep["tables"]:
        k, rows = t["kind"], t["rows"]
        if not rows and rep["status"] == "waiting":
            continue
        if k == "kompas":
            body = [[f"<strong>{esc(r['name'])}</strong>", _pct(r["r6"], lang), _pct(r["r12"], lang), _pct(r["score"], lang),
                     _num(r["close"], 2, lang) if r["close"] else "—", _num(r["avg10"], 2, lang) if r["avg10"] else "—"] for r in rows]
            out.append(f'<h2>{L("Momentum indeksów", "Index momentum")}</h2>' +
                       _tbl([L("Indeks", "Index"), "6M", "12M", L("Średnia 6M/12M", "Average 6M/12M"), L("Zamknięcie", "Close"),
                             L("Średnia 10 miesięcy", "10-month average")], body, "—"))
            if rep.get("pick"):
                out.append(f'<p><strong>{L("Decyzja", "Decision")}:</strong> '
                           f'{esc(L("gotówka", "cash") if rep["pick"] == "CASH" else rep["pick"])}</p>')
        elif k == "ped":
            body = [[str(i), f"<strong>{esc(r['tic'])}</strong>", esc(r.get("name", "")), _pct(r["ret"], lang),
                     _num(r["close"], 2, lang), _num(r["sma200"], 2, lang)] for i, r in enumerate(rows, 1)]
            out.append(f'<h2>{L("Wybrane do portfela (12-1)", "Selected for the portfolio (12-1)")}</h2>' +
                       _tbl(["#", "Tic", L("Spółka", "Company"), "12-1", L("Kurs", "Price"), "SMA200"], body, "—"))
            if rep.get("half"):
                out.append(f'<p class="warn">{L("Kompas jest w gotówce, więc nowe pozycje mają połowę wielkości.", "Compass is in cash, so new positions are half size.")}</p>')
        elif k == "zs":
            body = [[str(i), f"<strong>{esc(r['tic'])}</strong>", esc(r["sector"]), f"{r['f']:g}", _num(r["ev_ebit"], 1, lang),
                     _num(r["gp"], 2, lang)] for i, r in enumerate(rows, 1)]
            out.append(f'<h2>{L("Ranking jakości i wyceny", "Quality and value ranking")}</h2>' +
                       _tbl(["#", "Tic", L("Sektor", "Sector"), "F-score", "EV/EBIT", L("Zysk brutto/aktywa", "Gross profit/assets")], body, "—"))
        elif k == "przystan":
            body = [[str(i), f"<strong>{esc(r['tic'])}</strong>", _pct(r["vol"], lang).replace("+", ""), _pct(r["dd"], lang).replace("+", "")]
                    for i, r in enumerate(rows, 1)]
            out.append(f'<h2>{L("Najspokojniejsze spółki", "Calmest stocks")}</h2>' +
                       _tbl(["#", "Tic", L("Zmienność 12M", "12M volatility"), L("Maks. obsunięcie", "Max drawdown")], body, "—"))
    if key == "dryf" and rep["status"] == "ok":
        body = [[f"<strong>{esc(p['tic'])}</strong>", _num(p["ref"], 2, lang), _num(p["stop"], 2, lang)] for p in rep["pending"]]
        out.append(f'<h2>{L("Sygnały z ostatniej sesji (kupno na następnym otwarciu)", "Signals from the last session (buy at the next open)")}</h2>' +
                   _tbl([L("Tic", "Tic"), L("Zamknięcie", "Close"), "Stop"], body, L("Brak sygnałów.", "No signals.")))
        nb = ", ".join(esc(t) for t in rep["nobuy"]) or L("brak", "none")
        out.append(f'<p><strong>{L("Lista „nie kupuj” (60 sesji)", "Do-not-buy list (60 sessions)")}:</strong> {nb}</p>')
    elif rep["status"] == "ok" and rep["pending"] and key != "dryf":
        pass
    if rep["status"] == "ok" and not rep["tables"] and key != "dryf":
        out.append(f'<p>{L("Brak kandydatów spełniających kryteria.", "No candidates meet the criteria.")}</p>')
    return "\n".join(out)


def render_portfolio(st, key, lang="pl"):
    import portfel
    portfel.LANG = lang
    L = _L(lang)
    cfg = st["config"]
    eq = st["equity"][-1]["equity"]
    ret = (eq / cfg["start_capital"] - 1) * 100
    invested = sum(p["shares"] * p["last_close"] for p in st["positions"])
    card = lambda k, v, s="": f'<div class="card"><div class="k">{k}</div><div class="v">{v}</div><div class="s">{s}</div></div>'
    cards = "".join([
        card(L("Wartość portfela", "Portfolio value"), f"{portfel.n0(eq)} PLN", f"{L('start', 'start')} {portfel.n0(cfg['start_capital'])} PLN"),
        card(L("Wynik", "Return"), portfel.sg(ret, 2, "%")),
        card(L("Gotówka", "Cash"), f"{portfel.n0(st['cash'])} PLN", f"{L('w pozycjach', 'in positions')} {portfel.n0(invested)} PLN"),
        card(L("Otwarte pozycje", "Open positions"), str(len(st["positions"]))),
        card(L("Zamknięte transakcje", "Closed trades"), str(len(st["closed"]))),
    ])
    nm = NAMES[key][1 if lang == "en" else 0]
    out = [f"<h1>{L('Portfel', 'Portfolio')} {esc(nm)}</h1>",
           f'<div class="banner">{L("Stan na", "As of")} <strong>{st["equity"][-1]["date"]}</strong>. '
           f'{L("Wirtualny kapitał 100 000 PLN od 6.11.2026, pierwsze zlecenia na otwarciu 9.11.2026. To symulacja, nie porada inwestycyjna.", "Virtual capital of PLN 100,000 from 6 Nov 2026, first orders at the open on 9 Nov 2026. A simulation, not investment advice.")}</div>',
           f'<div class="cards">{cards}</div>']
    if st["status"] == "waiting" and not st["positions"]:
        out.append('<p>' + L("Portfel czeka na dane, dlatego jest w gotówce. Szczegóły w zakładce Raport.",
                             "The portfolio is waiting for data and is therefore in cash. See the Report tab for details.") + "</p>")
    if len(st["equity"]) > 1:
        out.append(portfel.equity_chart(st))
    rows = [[f"<strong>{esc(p['tic'])}</strong>", esc(p["name"]), f"{p['shares']:g}", portfel.px(p["entry"]), p["entry_date"],
             portfel.px(p["last_close"]), portfel.sg((p["last_close"] / p["entry"] - 1) * 100, 2, "%")] for p in st["positions"]]
    out.append(f"<h2>{L('Otwarte pozycje', 'Open positions')}</h2>" +
               _tbl(["Tic", L("Spółka", "Company"), L("Szt.", "Qty"), L("Wejście", "Entry"), L("Data", "Date"), L("Kurs", "Price"),
                     L("Wynik", "Return")], rows, L("Brak otwartych pozycji.", "No open positions.")))
    rows = [[f"<strong>{esc(c['tic'])}</strong>", c["entry_date"], c["exit_date"], portfel.sg(c["pnl_pct"], 2, "%"), portfel.sg(c["pnl"], 0),
             esc(c["reason"])] for c in reversed(st["closed"])]
    out.append(f"<h2>{L('Zamknięte transakcje', 'Closed trades')}</h2>" +
               _tbl([L("Tic", "Tic"), L("Wejście", "Entry"), L("Wyjście", "Exit"), "%", "PLN", L("Powód", "Reason")], rows,
                    L("Jeszcze nie zamknięto żadnej transakcji.", "No trades closed yet.")))
    return "\n".join(out)


def render_archive(st, key, lang="pl"):
    L = _L(lang)
    nm = NAMES[key][1 if lang == "en" else 0]
    out = [f"<h1>{L('Archiwum decyzji', 'Decision archive')} — {esc(nm)}</h1>"]
    decs = list(reversed(st["decisions"]))
    if not decs:
        out.append("<p>" + L("Pierwsza decyzja zapadnie na otwarciu sesji 9.11.2026. Tu pojawi się historia każdej decyzji portfela.",
                              "The first decision will be taken at the open on 9 Nov 2026. The history of each portfolio decision will appear here.") + "</p>")
    for dc in decs:
        if dc["status"] == "waiting":
            txt = L("brak danych, gotówka: ", "no data, staying in cash: ") + "; ".join(missing_text(m, lang) for m in dc["missing"])
        else:
            txt = ", ".join(f"{esc(t)} ({w * 100:.1f}%)" for t, w in dc["targets"].items()) or L("gotówka", "cash")
        out.append(f"<h2>{dc['date']}</h2><p>{txt}</p>")
    return "\n".join(out)


if __name__ == "__main__":
    sys.exit(main())
