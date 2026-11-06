#!/usr/bin/env python3
"""Portfel wirtualny (paper trading) strategii swing: sprawdza, jak wypadły prognozy z rankingu codziennego skanera.

Zasady (parametry w paper/state.json -> "config"):
  * kapitał startowy 100 000 PLN; pojedyncza pozycja za co najwyżej 5 000 PLN (liczba sztuk = 5 000 / limit,
    w dół do pełnych akcji; akcja droższa niż 5 000 PLN jest pomijana); zyski wracają do gotówki, straty
    po stopie ją pomniejszają; gdy cała gotówka jest zaangażowana (pozycje i zlecenia), nowych zleceń
    nie ma do czasu zamknięcia którejś pozycji; koszt 0,2% od każdej transakcji;
  * sygnał: pozycja z tabeli rankingu raportu o klasie A lub B, Suma >= 60, R do C1 >= 1,0 i do C2 >= 2,0,
    bez wyników kwartalnych w ciągu 7 dni; maks. 3 nowe zlecenia dziennie (najwyższa Suma);
  * zlecenie: kup z limitem na górnej granicy strefy wejścia, ważne 5 sesji; wypełnia się po
    min(otwarcie, limit), gdy minimum sesji <= limit; otwarcie poniżej stopu = zlecenie anulowane;
  * wyjścia (świece dzienne, zakładamy najgorszą kolejność w świecy): stop (luka: po otwarciu),
    C1 — sprzedaż połowy i stop na cenę wejścia, C2 — sprzedaż reszty, po 30 dniach — wyjście po zamknięciu;
    jeśli świeca dotyka i stopu, i celu, liczy się stop; w dniu wejścia sprawdzany jest tylko stop.

Użycie:
    (opcja --strategy NAZWA, domyślnie swing: stan w paper/<NAZWA>/)
    python3 paper.py init
    python3 paper.py update --asof YYYY-MM-DD          # przetwarza paper/quotes/<TIC>.csv do podanej sesji
    python3 paper.py signal reports/RRRR-MM-DD.md [--valid-from YYYY-MM-DD]
    python3 paper.py mark --asof YYYY-MM-DD            # dopisuje punkt krzywej kapitału
    python3 paper.py show
"""
import copy
import csv
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

from charts import build_items, parse_ranking

ROOT = Path(__file__).resolve().parent
STRATEGY = "swing"  # kolejne strategie dostają własny katalog paper/<nazwa>/ (state.json, quotes/)
PAPER = ROOT / "paper" / STRATEGY
STATE = PAPER / "state.json"
QUOTES = PAPER / "quotes"


def use_strategy(name):
    """Przełącza ścieżki stanu i notowań na paper/<name>/."""
    global STRATEGY, PAPER, STATE, QUOTES
    STRATEGY, PAPER = name, ROOT / "paper" / name
    STATE, QUOTES = PAPER / "state.json", PAPER / "quotes"

DEFAULT_CFG = {
    "start_capital": 100000.0, "position_value": 5000.0, "max_open": 20, "fee_pct": 0.2,
    "max_hold_days": 30, "order_days": 6, "min_score": 60, "min_r1": 1.0, "min_r2": 2.0,
    "classes": ["A", "B"], "max_new_per_day": 5, "skip_earnings_days": 7, "partial_frac": 0.5,
}


# ---------------------------------------------------------------- stan

def new_state(start_date=None):
    cfg = copy.deepcopy(DEFAULT_CFG)
    return {"config": cfg, "start_date": start_date or dt.date.today().isoformat(), "cash": cfg["start_capital"],
            "processed_through": None, "orders": [], "positions": [], "closed": [], "equity": [], "log": [], "next_id": 1}


def load():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return new_state()


def save(st):
    PAPER.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def log(st, date, text):
    st["log"].append({"date": date, "text": text})
    del st["log"][:-200]


def bars(tic):
    f = QUOTES / f"{tic}.csv"
    if not f.exists():
        return None
    out = []
    with f.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                out.append((r["date"], float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])))
            except (KeyError, ValueError, TypeError):
                continue
    out.sort()
    return out


def fee(st):
    return st["config"]["fee_pct"] / 100.0


def equity(st):
    return st["cash"] + sum(p["shares"] * p["last_close"] for p in st["positions"])


def reserved(st):
    return sum(o["shares"] * o["limit"] * (1 + fee(st)) for o in st["orders"])


# ---------------------------------------------------------------- sygnały

def _earnings_in_days(cell, report_date):
    """Pierwsza data dd.mm z komórki „Raport" -> liczba dni od daty raportu (None, gdy brak)."""
    m = re.search(r"(\d{1,2})\.(\d{2})", cell or "")
    if not m:
        return None
    best = None
    for y in (report_date.year - 1, report_date.year, report_date.year + 1):
        try:
            d = dt.date(y, int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        if best is None or abs((d - report_date).days) < abs((best - report_date).days):
            best = d
    return (best - report_date).days if best else None


def signal(st, report_path, valid_from=None):
    md = Path(report_path).read_text(encoding="utf-8")
    report_date = dt.date.fromisoformat(Path(report_path).stem)
    vf = dt.date.fromisoformat(valid_from) if valid_from else report_date
    head, rows = parse_ranking(md)
    if not head:
        return ["Brak tabeli rankingu w raporcie"]
    items = build_items(head, rows)
    cfg = st["config"]
    notes, cand = [], []
    held = {p["tic"] for p in st["positions"]} | {o["tic"] for o in st["orders"]}
    for it, row in zip(items, rows):
        t = it["tic"]
        why = None
        if t in held:
            why = "już w portfelu/zleceniu"
        elif it["kl"] not in cfg["classes"]:
            why = f"klasa {it['kl'] or '?'}"
        elif (it["suma"] or 0) < cfg["min_score"]:
            why = f"suma {it['suma']}"
        elif any(it[k] is None for k in ("hi", "stop", "c1", "c2", "r1", "r2")):
            why = "brak poziomów"
        elif ">" in row.get(next((h for h in head if h.startswith("Wej")), ""), ""):
            why = "wejście na wybiciu (nieobsługiwane)"
        elif it["r1"] < cfg["min_r1"] or it["r2"] < cfg["min_r2"]:
            why = f"R {it['r1']}/{it['r2']}"
        elif not (it["stop"] < it["hi"] < it["c1"]):
            why = "niespójne poziomy"
        else:
            d = _earnings_in_days(row.get("Raport", ""), report_date)
            if d is not None and 0 <= d <= cfg["skip_earnings_days"]:
                why = f"raport kwartalny za {d} dni"
        if why:
            notes.append(f"pominięto {t}: {why}")
        else:
            cand.append((it, row))
    cand.sort(key=lambda x: -(x[0]["suma"] or 0))
    created = 0
    for it, row in cand:
        if created >= cfg["max_new_per_day"]:
            notes.append(f"pominięto {it['tic']}: limit {cfg['max_new_per_day']} zleceń dziennie")
            continue
        if len(st["positions"]) + len(st["orders"]) >= cfg["max_open"]:
            notes.append(f"pominięto {it['tic']}: limit {cfg['max_open']} pozycji")
            continue
        limit, stop = it["hi"], it["stop"]
        unit = limit * (1 + fee(st))
        n = math.floor(cfg["position_value"] / unit)
        if n < 1:
            notes.append(f"pominięto {it['tic']}: cena akcji {limit:g} przekracza limit {cfg['position_value']:g} PLN na pozycję")
            continue
        avail = st["cash"] - reserved(st)
        n = min(n, math.floor(avail / unit))
        if n < 1:
            notes.append(f"pominięto {it['tic']}: cała gotówka zaangażowana, czekamy na zamknięcie pozycji")
            continue
        spolka = row.get("Spółka", it["tic"])
        order = {"id": st["next_id"], "tic": it["tic"], "name": spolka, "shares": n, "limit": limit, "zone_lo": it["lo"],
                 "stop": stop, "c1": it["c1"], "c2": it["c2"], "score": it["suma"], "cls": it["kl"], "report": report_date.isoformat(),
                 "valid_from": vf.isoformat(), "expires": (vf + dt.timedelta(days=cfg["order_days"])).isoformat(), "checked_through": None}
        st["next_id"] += 1
        st["orders"].append(order)
        created += 1
        log(st, report_date.isoformat(), f"Zlecenie kupna {it['tic']}: {n} szt., limit {limit:g}, stop {stop:g}, C1 {it['c1']:g}, C2 {it['c2']:g} (suma {it['suma']:g}, klasa {it['kl']})")
        notes.append(f"zlecenie {it['tic']}: {n} szt. @ limit {limit:g}")
    return notes


# ---------------------------------------------------------------- symulacja

def _sell(st, pos, qty, price, date, reason):
    qty = min(qty, pos["shares"])
    if qty <= 0:
        return
    proceeds = qty * price * (1 - fee(st))
    st["cash"] += proceeds
    pos["realized"] += proceeds
    pos["shares"] -= qty
    pos["legs"].append({"date": date, "qty": qty, "price": round(price, 4), "reason": reason})
    log(st, date, f"Sprzedaż {pos['tic']}: {qty} szt. po {price:g} ({reason})")
    if pos["shares"] == 0:
        pnl = pos["realized"] - pos["cost"]
        risk0 = pos["shares0"] * (pos["entry"] - pos["stop0"])
        st["closed"].append({
            "tic": pos["tic"], "name": pos["name"], "shares": pos["shares0"], "entry": pos["entry"], "entry_date": pos["entry_date"],
            "exit_date": date, "exit_reason": reason, "stop0": pos["stop0"], "c1": pos["c1"], "c2": pos["c2"],
            "pnl": round(pnl, 2), "pnl_pct": round(pnl / pos["cost"] * 100, 2), "r": round(pnl / risk0, 2) if risk0 > 0 else None,
            "days": (dt.date.fromisoformat(date) - dt.date.fromisoformat(pos["entry_date"])).days, "legs": pos["legs"],
            "score": pos["score"], "cls": pos["cls"], "report": pos["report"]})
        st["positions"] = [p for p in st["positions"] if p is not pos]


def _process_position(st, pos, b):
    date, o, h, l, c = b
    cfg = st["config"]
    pos["last_close"], pos["last_date"] = c, date
    entry_day = date == pos["entry_date"]
    if o <= pos["stop"] and not entry_day:
        _sell(st, pos, pos["shares"], o, date, "stop (luka)" if not pos["c1_done"] else "stop na wejściu (luka)")
        return
    if l <= pos["stop"]:
        _sell(st, pos, pos["shares"], pos["stop"], date, "stop" if not pos["c1_done"] else "stop na wejściu")
        return
    if entry_day:
        return
    if not pos["c1_done"] and h >= pos["c1"]:
        qty = math.floor(pos["shares"] * cfg["partial_frac"])
        _sell(st, pos, qty, max(o, pos["c1"]), date, "cel 1")
        pos["c1_done"] = True
        pos["stop"] = max(pos["stop"], pos["entry"])
        if pos["shares"] > 0 and h >= pos["c2"]:
            _sell(st, pos, pos["shares"], max(o, pos["c2"]), date, "cel 2")
            return
    elif pos["c1_done"] and h >= pos["c2"]:
        _sell(st, pos, pos["shares"], max(o, pos["c2"]), date, "cel 2")
        return
    if pos["shares"] > 0 and (dt.date.fromisoformat(date) - dt.date.fromisoformat(pos["entry_date"])).days >= cfg["max_hold_days"]:
        _sell(st, pos, pos["shares"], c, date, f"czas ({cfg['max_hold_days']} dni)")


def _process_order(st, order, b):
    """Zwraca True, gdy zlecenie zostało zamknięte (wypełnione albo anulowane)."""
    date, o, h, l, c = b
    if l > order["limit"]:
        return False
    price = min(o, order["limit"])
    if price <= order["stop"]:
        log(st, date, f"Anulowano zlecenie {order['tic']}: otwarcie {o:g} poniżej stopu {order['stop']:g}")
        return True
    n = order["shares"]
    n = min(n, math.floor(st["cash"] / (price * (1 + fee(st)))))
    if n < 1:
        log(st, date, f"Anulowano zlecenie {order['tic']}: brak środków")
        return True
    cost = n * price * (1 + fee(st))
    st["cash"] -= cost
    pos = {"tic": order["tic"], "name": order["name"], "shares": n, "shares0": n, "entry": round(price, 4), "entry_date": date,
           "stop": order["stop"], "stop0": order["stop"], "c1": order["c1"], "c2": order["c2"], "c1_done": False,
           "cost": cost, "realized": 0.0, "legs": [], "last_close": c, "last_date": date, "score": order["score"],
           "cls": order["cls"], "report": order["report"]}
    st["positions"].append(pos)
    log(st, date, f"Kupno {order['tic']}: {n} szt. po {price:g} (limit {order['limit']:g}, stop {order['stop']:g})")
    _process_position(st, pos, b)  # w dniu wejścia działa tylko stop
    return True


def update(st, asof):
    warnings = []
    asof_d = dt.date.fromisoformat(asof)
    cache = {}

    def get(t):
        if t not in cache:
            cache[t] = bars(t)
        return cache[t]

    for t in sorted({p["tic"] for p in st["positions"]} | {o["tic"] for o in st["orders"]}):
        bs = get(t)
        if bs is None:
            warnings.append(f"brak notowań {t}")
        elif dt.date.fromisoformat(bs[-1][0]) < asof_d - dt.timedelta(days=6):
            warnings.append(f"notowania {t} kończą się {bs[-1][0]}")
    through = st["processed_through"] or "0000-00-00"
    dates = sorted({b[0] for t in {p["tic"] for p in st["positions"]} | {o["tic"] for o in st["orders"]} for b in (get(t) or [])
                    if through < b[0] <= asof})
    for d in dates:
        for pos in list(st["positions"]):
            for b in (get(pos["tic"]) or []):
                if b[0] == d and b[0] > pos["entry_date"]:
                    _process_position(st, pos, b)
        for order in list(st["orders"]):
            if not (order["valid_from"] <= d <= order["expires"]):
                continue
            for b in (get(order["tic"]) or []):
                if b[0] == d and _process_order(st, order, b):
                    st["orders"] = [x for x in st["orders"] if x is not order]
    for order in list(st["orders"]):
        if asof > order["expires"]:
            st["orders"] = [x for x in st["orders"] if x is not order]
            log(st, asof, f"Zlecenie {order['tic']} wygasło bez realizacji (limit {order['limit']:g})")
    if st["processed_through"] is None or asof > st["processed_through"]:
        st["processed_through"] = asof
    return warnings


def mark(st, asof):
    inv = sum(p["shares"] * p["last_close"] for p in st["positions"])
    pt = {"date": asof, "equity": round(st["cash"] + inv, 2), "cash": round(st["cash"], 2), "invested": round(inv, 2)}
    st["equity"] = [e for e in st["equity"] if e["date"] != asof] + [pt]
    st["equity"].sort(key=lambda e: e["date"])
    return pt


def stats(st):
    cl = st["closed"]
    wins = [c for c in cl if c["pnl"] > 0]
    losses = [c for c in cl if c["pnl"] <= 0]
    eq = [e["equity"] for e in st["equity"]] or [st["cash"]]
    peak, dd = eq[0], 0.0
    for v in eq:
        peak = max(peak, v)
        dd = min(dd, v / peak - 1)
    gl = -sum(c["pnl"] for c in losses)
    rs = [c["r"] for c in cl if c["r"] is not None]
    return {"closed": len(cl), "win_rate": len(wins) / len(cl) * 100 if cl else None,
            "avg_r": sum(rs) / len(rs) if rs else None, "realized": sum(c["pnl"] for c in cl),
            "profit_factor": (sum(c["pnl"] for c in wins) / gl) if gl > 0 else None, "max_dd": dd * 100,
            "equity": equity(st), "ret": (equity(st) / st["config"]["start_capital"] - 1) * 100}


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "show"
    arg = lambda k: argv[argv.index(k) + 1] if k in argv else None
    if arg("--strategy"):
        use_strategy(arg("--strategy"))
    st = load()
    if cmd == "init":
        if STATE.exists():
            print("stan już istnieje:", STATE)
            return 1
        st = new_state(arg("--start") or dt.date.today().isoformat())
        save(st)
        print("zainicjowano portfel:", st["cash"])
        return 0
    if cmd == "update":
        for w in update(st, arg("--asof") or dt.date.today().isoformat()):
            print("UWAGA:", w)
    elif cmd == "signal":
        for n in signal(st, argv[2], arg("--valid-from")):
            print(n)
    elif cmd == "mark":
        print(mark(st, arg("--asof") or dt.date.today().isoformat()))
    elif cmd == "show":
        print(json.dumps(stats(st), ensure_ascii=False, indent=1))
        print("gotówka", round(st["cash"], 2), "| pozycje", [(p["tic"], p["shares"]) for p in st["positions"]],
              "| zlecenia", [(o["tic"], o["shares"], o["limit"]) for o in st["orders"]])
        return 0
    else:
        print(__doc__)
        return 1
    save(st)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
