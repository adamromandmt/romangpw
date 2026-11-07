"""Silnik wirtualnych portfeli strategii uzupełniających (paper/<slug>/state.json).

Dwa tryby:
  * "targets" (Kompas, Pęd, Złoty Środek, Przystań): sygnał podaje docelowy skład; transakcje wykonują się po cenie otwarcia
    najbliższej sesji po dniu sygnału. Wypadające spółki sprzedajemy w całości, nowe kupujemy za equity / liczba pozycji
    (razy waga wejścia). Pozycji, które zostają, nie dokupujemy ani nie obcinamy (mniej transakcji i kosztów).
  * "events" (Dryf): zlecenia kupna po otwarciu sesji następującej po zdarzeniu, stała kwota na pozycję, stop na cenie sprzed
    zdarzenia, wyjście po zamknięciu poniżej stopu albo po upływie okna (liczonego w sesjach).

Wspólne założenia: kapitał 100 000 PLN, koszt 0,2% od każdej transakcji, dywidendy księgowane w dniu odcięcia (brutto, bez
podatku), brak odsetek od gotówki, ceny surowe z data/market. To symulacja: żadne prawdziwe zlecenia nie są składane.
"""
import copy
import datetime as dt
import json
import math

from . import lib

DEFAULT_CFG = {
    "start_capital": 100000.0, "fee_pct": 0.2, "fractional": False, "max_wait_sessions": 5,
    "position_value": 5000.0, "max_open": 20, "max_hold_sessions": 40,
}


# ------------------------------------------------------------------ stan

def state_path(slug):
    return lib.PAPER_DIR / slug / "state.json"


def new_state(kind, start_date, bench_close=None, cfg=None):
    c = copy.deepcopy(DEFAULT_CFG)
    c.update(cfg or {})
    cap = c["start_capital"]
    return {"kind": kind, "config": c, "start_date": start_date, "cash": cap, "processed_through": start_date, "pending": None,
            "orders": [], "positions": [], "closed": [], "equity": [{"date": start_date, "equity": cap, "cash": cap, "invested": 0.0,
                                                                        "bench": bench_close}], "log": [], "next_id": 1}


def load(slug):
    p = state_path(slug)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def save(slug, st):
    p = state_path(slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def log(st, day, pl, en):
    st["log"].append({"date": day, "pl": pl, "en": en})
    del st["log"][:-300]


def fee(st):
    return st["config"]["fee_pct"] / 100.0


def equity(st):
    return st["cash"] + sum(p["shares"] * p["last_close"] for p in st["positions"])


def _g(x):
    return f"{x:g}"


def _qty(st, x):
    """Liczba jednostek: pełne akcje albo (Kompas) ułamki do 4 miejsc, zawsze w dół."""
    return math.floor(x * 10000) / 10000 if st["config"]["fractional"] else math.floor(x)


# ------------------------------------------------------------------ transakcje

def _buy(st, tic, name, budget, price, day, **extra):
    unit = price * (1 + fee(st))
    n = _qty(st, min(budget, st["cash"]) / unit)
    if n <= 0:
        return None
    cost = n * unit
    st["cash"] -= cost
    pos = {"tic": tic, "name": name, "shares": n, "entry": round(price, 4), "entry_date": day, "cost": cost, "last_close": price,
           "last_date": day, "divs": 0.0, "stop": None, **extra}
    st["positions"].append(pos)
    log(st, day, f"Kupno {tic}: {_g(n)} szt. po {_g(price)}", f"Bought {tic}: {_g(n)} units at {_g(price)}")
    return pos


def _sell(st, pos, price, day, why_pl, why_en):
    proceeds = pos["shares"] * price * (1 - fee(st))
    st["cash"] += proceeds
    pnl = proceeds + pos["divs"] - pos["cost"]
    st["closed"].append({
        "tic": pos["tic"], "name": pos["name"], "shares": pos["shares"], "entry": pos["entry"], "entry_date": pos["entry_date"],
        "event_date": pos.get("event_date"), "exit": round(price, 4), "exit_date": day, "why_pl": why_pl, "why_en": why_en, "divs": round(pos["divs"], 2),
        "pnl": round(pnl, 2), "pnl_pct": round(pnl / pos["cost"] * 100, 2),
        "days": (dt.date.fromisoformat(day) - dt.date.fromisoformat(pos["entry_date"])).days})
    st["positions"] = [p for p in st["positions"] if p is not pos]
    log(st, day, f"Sprzedaż {pos['tic']}: {_g(pos['shares'])} szt. po {_g(price)} ({why_pl})",
        f"Sold {pos['tic']}: {_g(pos['shares'])} units at {_g(price)} ({why_en})")


# ------------------------------------------------------------------ sygnały

def queue_targets(st, signal_date, targets, why, size_factor=1.0, exit_reasons=None):
    """Zapisuje docelowy skład do wykonania na otwarciu najbliższej sesji. targets: [{tic, name, weight?}] w kolejności rankingu.
    why: {"pl": ..., "en": ...}; exit_reasons: {tic: {"pl": ..., "en": ...}} dla spółek wypadających z portfela."""
    if st.get("pending"):
        log(st, signal_date, "Nowy sygnał zastępuje niewykonane zlecenia z poprzedniego", "A new signal replaces the unexecuted orders of the previous one")
    st["pending"] = {"signal_date": signal_date, "targets": targets, "waited": 0, "why": why, "size_factor": size_factor,
                     "exit_reasons": exit_reasons or {}}
    names = ", ".join(t["tic"] for t in targets) or "gotówka"
    log(st, signal_date, f"Sygnał: docelowy skład {names}", f"Signal: target holdings {', '.join(t['tic'] for t in targets) or 'cash'}")


def queue_order(st, signal_date, tic, name, stop, event_date, note):
    """Zlecenie kupna po otwarciu następnej sesji (tryb zdarzeń). Jedno zlecenie na spółkę."""
    if any(o["tic"] == tic for o in st["orders"]) or any(p["tic"] == tic for p in st["positions"]):
        return False
    st["orders"].append({"id": st["next_id"], "tic": tic, "name": name, "signal_date": signal_date, "event_date": event_date,
                         "stop": stop, "note": note, "waited": 0})
    st["next_id"] += 1
    log(st, signal_date, f"Zlecenie kupna {tic}: otwarcie następnej sesji, stop {_g(stop)}", f"Buy order {tic}: next session open, stop {_g(stop)}")
    return True


# ------------------------------------------------------------------ symulacja dnia

def _credit_dividends(st, day, ctx):
    for pos in st["positions"]:
        s = ctx.stock(pos["tic"])
        dps = s.ex.get(day) if s else None
        if dps:
            amt = pos["shares"] * dps
            st["cash"] += amt
            pos["divs"] += amt
            log(st, day, f"Dywidenda {pos['tic']}: {dps:g} zł na akcję, razem {amt:,.0f} zł".replace(",", " "),
                f"Dividend {pos['tic']}: PLN {dps:g} per share, total PLN {amt:,.0f}")


def _execute_targets(st, day, ctx):
    pend = st["pending"]
    cfg = st["config"]
    targets = pend["targets"]
    tset = {t["tic"] for t in targets}
    for pos in list(st["positions"]):
        if pos["tic"] in tset:
            continue
        s = ctx.ser(pos["tic"])
        k = s.index_of(day) if s else None
        if k is None:
            continue
        r = pend["exit_reasons"].get(pos["tic"]) or {"pl": "wypadła z listy docelowej", "en": "dropped from the target list"}
        _sell(st, pos, s.o[k], day, r["pl"], r["en"])
    exits_left = [p["tic"] for p in st["positions"] if p["tic"] not in tset]
    held = {p["tic"] for p in st["positions"]}
    opens = {}
    for p in st["positions"]:
        s = ctx.ser(p["tic"])
        k = s.index_of(day) if s else None
        opens[p["tic"]] = s.o[k] if k is not None else p["last_close"]
    eq = st["cash"] + sum(p["shares"] * opens[p["tic"]] for p in st["positions"])
    tv = eq / len(targets) if targets else 0.0
    entries_left = []
    for t in targets:
        if t["tic"] in held:
            continue
        s = ctx.ser(t["tic"])
        k = s.index_of(day) if s else None
        if k is None:
            entries_left.append(t["tic"])
            continue
        w = t.get("weight", 1.0) * pend.get("size_factor", 1.0)
        pos = _buy(st, t["tic"], t.get("name") or t["tic"], tv * w, s.o[k], day, sector=t.get("sector"))
        if pos is None:
            log(st, day, f"Nie kupiono {t['tic']}: brak środków lub zbyt mała kwota", f"{t['tic']} not bought: insufficient cash or amount too small")
    if exits_left or entries_left:
        pend["waited"] += 1
        if pend["waited"] >= cfg["max_wait_sessions"]:
            log(st, day, f"Niewykonane (brak notowań): {', '.join(exits_left + entries_left)}",
                f"Not executed (no quotes): {', '.join(exits_left + entries_left)}")
            st["pending"] = None
        return
    st["pending"] = None


def _events_day(st, day, ctx, sess_pos):
    cfg = st["config"]
    for pos in list(st["positions"]):
        s = ctx.stock(pos["tic"])
        k = s.index_of(day) if s else None
        if k is None or pos["entry_date"] == day:
            continue
        held = sess_pos.get(day, 0) - sess_pos.get(pos["entry_date"], 0)
        if pos["stop"] is not None and s.o[k] <= pos["stop"]:
            _sell(st, pos, s.o[k], day, "stop (luka)", "stop (gap)")
        elif pos["stop"] is not None and s.l[k] <= pos["stop"]:
            _sell(st, pos, pos["stop"], day, "stop (zamknięcie luki)", "stop (gap filled)")
        elif held >= cfg["max_hold_sessions"]:
            _sell(st, pos, s.c[k], day, f"koniec okna ({cfg['max_hold_sessions']} sesji)", f"window ended ({cfg['max_hold_sessions']} sessions)")
    for o in list(st["orders"]):
        if o["signal_date"] >= day:
            continue
        s = ctx.stock(o["tic"])
        k = s.index_of(day) if s else None
        if k is None:
            o["waited"] += 1
            if o["waited"] >= cfg["max_wait_sessions"]:
                st["orders"].remove(o)
                log(st, day, f"Zlecenie {o['tic']} wygasło (brak notowań)", f"Order {o['tic']} expired (no quotes)")
            continue
        st["orders"].remove(o)
        if len(st["positions"]) >= cfg["max_open"]:
            log(st, day, f"Zlecenie {o['tic']} pominięte: limit {cfg['max_open']} pozycji", f"Order {o['tic']} skipped: limit of {cfg['max_open']} positions")
            continue
        if s.o[k] <= o["stop"]:
            log(st, day, f"Zlecenie {o['tic']} anulowane: otwarcie {_g(s.o[k])} poniżej stopu {_g(o['stop'])}",
                f"Order {o['tic']} cancelled: open {_g(s.o[k])} below stop {_g(o['stop'])}")
            continue
        pos = _buy(st, o["tic"], o["name"], cfg["position_value"], s.o[k], day, event_date=o["event_date"])
        if pos is None:
            log(st, day, f"Nie kupiono {o['tic']}: kwota na pozycję mniejsza niż cena jednej akcji albo brak środków",
                f"{o['tic']} not bought: the position amount is below the price of one share, or insufficient cash")
            continue
        pos["stop"] = o["stop"]
        if s.l[k] <= o["stop"]:
            _sell(st, pos, o["stop"], day, "stop (zamknięcie luki)", "stop (gap filled)")


def _mark(st, day, ctx):
    for pos in st["positions"]:
        s = ctx.ser(pos["tic"])
        k = s.index_of(day) if s else None
        if k is not None:
            pos["last_close"], pos["last_date"] = s.c[k], day
    inv = sum(p["shares"] * p["last_close"] for p in st["positions"])
    b = ctx.indices.get(lib.BENCH)
    pt = {"date": day, "equity": round(st["cash"] + inv, 2), "cash": round(st["cash"], 2), "invested": round(inv, 2),
          "bench": b.at(day, "c") if b else None}
    st["equity"] = [e for e in st["equity"] if e["date"] != day] + [pt]


def advance(st, asof, ctx):
    """Przetwarza sesje po `processed_through` do `asof` włącznie. Zwraca listę ostrzeżeń."""
    warns = []
    sess_pos = {d: i for i, d in enumerate(ctx.sessions)}
    for day in [d for d in ctx.sessions if st["processed_through"] < d <= asof]:
        _credit_dividends(st, day, ctx)
        if st["kind"] == "targets":
            if st.get("pending") and st["pending"]["signal_date"] < day:
                _execute_targets(st, day, ctx)
        else:
            _events_day(st, day, ctx, sess_pos)
        _mark(st, day, ctx)
        st["processed_through"] = day
    for pos in st["positions"]:
        if pos["last_date"] < asof and sess_pos.get(asof, 0) - sess_pos.get(pos["last_date"], 0) > 10:
            warns.append(f"brak notowań {pos['tic']} od {pos['last_date']}")
    return warns


# ------------------------------------------------------------------ statystyki

def stats(st):
    pts = st["equity"]
    eq = [e["equity"] for e in pts] or [st["cash"]]
    peak, dd = eq[0], 0.0
    for v in eq:
        peak = max(peak, v)
        dd = min(dd, v / peak - 1)
    cap = st["config"]["start_capital"]
    cl = st["closed"]
    wins = [c for c in cl if c["pnl"] > 0]
    b0 = next((e["bench"] for e in pts if e.get("bench")), None)
    b1 = next((e["bench"] for e in reversed(pts) if e.get("bench")), None)
    ret = (equity(st) / cap - 1) * 100
    bret = (b1 / b0 - 1) * 100 if b0 and b1 else None
    expo = [e["invested"] / e["equity"] for e in pts if e.get("equity")]
    return {"equity": equity(st), "ret": ret, "bench_ret": bret, "vs_bench": ret - bret if bret is not None else None,
            "closed": len(cl), "win_rate": len(wins) / len(cl) * 100 if cl else None, "realized": sum(c["pnl"] for c in cl),
            "max_dd": dd * 100, "divs": sum(p["divs"] for p in st["positions"]) + sum(c["divs"] for c in cl),
            "exposure": sum(expo) / len(expo) * 100 if expo else 0.0, "cash_pct": st["cash"] / equity(st) * 100 if equity(st) else 100.0}
