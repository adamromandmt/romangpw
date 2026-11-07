#!/usr/bin/env python3
"""Wskaźniki trendu i płynności dla puli spółek dywidendowych.

Wejście: data/market/<TIC>.csv (notowania z archiwum GPW, zob. quotes.py i fetch_quotes.py; liczone na ostatnich
         50 sesjach, bo na tym oknie dobrano progi rankingu dywidend), data/dividends/pool_list.json
Wyjście: data/dividends/trend.json  (+ tabela na stdout)

Użycie: python3 trendscan.py [--min-turnover 200000]
"""
import json
import sys
from pathlib import Path

import quotes

ROOT = Path(__file__).resolve().parent
D = ROOT / "data" / "dividends"
WINDOW = 50  # liczba ostatnich sesji w metrykach (hi_n, ret_all, off_high_pct) — jak w pierwotnych danych


def load(tic):
    rows = quotes.load(tic)
    return rows[-WINDOW:] if rows else None


def ema(vals, n):
    k = 2 / (n + 1)
    e = vals[0]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
    return e


def rsi(vals, n=14):
    if len(vals) < n + 1:
        return None
    g = l = 0.0
    for i in range(1, n + 1):
        d = vals[i] - vals[i - 1]
        g += max(d, 0)
        l += max(-d, 0)
    g, l = g / n, l / n
    for i in range(n + 1, len(vals)):
        d = vals[i] - vals[i - 1]
        g = (g * (n - 1) + max(d, 0)) / n
        l = (l * (n - 1) + max(-d, 0)) / n
    return 100.0 if l == 0 else 100 - 100 / (1 + g / l)


def metrics(rows):
    c = [r["close"] for r in rows]
    v = [r["volume"] for r in rows]
    n = len(c)
    out = {"n": n, "last_date": rows[-1]["date"], "close": c[-1]}
    out["ema20"] = ema(c, 20) if n >= 20 else None
    out["sma50"] = sum(c[-50:]) / 50 if n >= 50 else None
    out["sma20"] = sum(c[-20:]) / 20 if n >= 20 else None
    out["rsi"] = rsi(c)
    hi = max(r["high"] for r in rows)
    out["hi_n"] = hi
    out["off_high_pct"] = (c[-1] / hi - 1) * 100
    out["ret20"] = (c[-1] / c[-21] - 1) * 100 if n >= 21 else None
    out["ret_all"] = (c[-1] / c[0] - 1) * 100
    out["avg_vol20"] = sum(v[-20:]) / min(20, n)
    out["turnover20"] = sum(a * b for a, b in zip(c[-20:], v[-20:])) / min(20, n)
    out["vol_up_ratio"] = None
    # akumulacja: średni wolumen w dniach wzrostowych / spadkowych (ost. 30 sesji)
    up = [v[i] for i in range(max(1, n - 30), n) if c[i] > c[i - 1]]
    dn = [v[i] for i in range(max(1, n - 30), n) if c[i] < c[i - 1]]
    if up and dn and sum(dn):
        out["vol_up_ratio"] = (sum(up) / len(up)) / (sum(dn) / len(dn))
    # pozycja względem średnich
    base = out["sma50"] or out["sma20"]
    out["above_base"] = c[-1] > base if base else None
    out["ema20_gt_sma50"] = (out["ema20"] > out["sma50"]) if out["ema20"] and out["sma50"] else None
    out["last_close_vs_ema20_pct"] = (c[-1] / out["ema20"] - 1) * 100 if out["ema20"] else None
    out["low10"] = min(r["low"] for r in rows[-10:])
    out["low20"] = min(r["low"] for r in rows[-20:]) if n >= 20 else out["low10"]
    out["high20"] = max(r["high"] for r in rows[-20:])
    return out


def main(argv):
    pool = json.loads((D / "pool_list.json").read_text(encoding="utf-8"))
    res, missing = {}, []
    for p in pool:
        rows = load(p["tic"])
        if not rows or len(rows) < 15:
            missing.append(p["tic"])
            continue
        m = metrics(rows)
        m.update({"name": p["name"], "win0": p["win0"], "win1": p["win1"], "next_agm": p["next_agm"]})
        res[p["tic"]] = m
    (D / "trend.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"policzono: {len(res)}; brak danych: {missing}")
    hdr = f"{'tic':5} {'kurs':>8} {'n':>3} {'ost.':10} {'vsEMA20':>7} {'>SMA50':>6} {'E>S':>4} {'RSI':>5} {'od max':>7} {'r20':>6} {'obrót20 tys':>11} {'V↑/↓':>5}"
    print(hdr)
    for t, m in sorted(res.items(), key=lambda kv: kv[1]["win0"]):
        f = lambda x, d=1: "-" if x is None else f"{x:.{d}f}"
        print(f"{t:5} {m['close']:8.2f} {m['n']:3d} {m['last_date']:10} {f(m['last_close_vs_ema20_pct']):>7} "
              f"{str(m['above_base'])[0]:>6} {str(m['ema20_gt_sma50'])[0]:>4} {f(m['rsi'],0):>5} {f(m['off_high_pct']):>7} "
              f"{f(m['ret20']):>6} {m['turnover20']/1000:11.0f} {f(m['vol_up_ratio']):>5}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
