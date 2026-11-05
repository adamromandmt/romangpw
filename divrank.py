#!/usr/bin/env python3
"""Ranking „dywidenda przed ogłoszeniem": łączy trend.json (notowania), verify/*.json
(weryfikacja ESPI: okno rekomendacji) i judgement.json (oceny ręczne analityka).

Wyjście: tabela Markdown (kolumny jak w METHOD-DYWIDENDY.md) na stdout.
Użycie: python3 divrank.py [--today YYYY-MM-DD] [--json]

judgement.json: {TIC: {"sector":"", "stab":0-10, "health":0-5, "exp_dps":"", "last_dps":"", "years":"5/5",
                       "note":""}}
Punktacja Dyw/50: regularność (0-15, z lat serii) + stab (0-10) + pewność okna (0-10) + bliskość okna (0-10) + health (0-5)
Tech/50: trend (0-15) + pozycja/RSI (0-10) + wolumen (0-10) + płynność (0-10) + R:R (0-5)
"""
import datetime as dt
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
D = ROOT / "data" / "dividends"


def fnum(x, d=2):
    s = f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
    return s.rstrip("0").rstrip(",") if d and "," in s and d > 2 else s


def _comma(row):
    import re
    return re.sub(r'(?<=\d)\.(?=\d)', ',', row)


def price(x):
    if x >= 1000:
        return f"{x:,.0f}".replace(",", " ")
    return f"{x:.2f}".replace(".", ",")


def levels(m):
    c, e20, s50 = m["close"], m["ema20"], m["sma50"]
    hi, low20 = m["hi_n"], m["low20"]
    if c > e20 * 1.03:  # wydłużony ponad EMA20: czekaj na cofnięcie
        z0, z1 = e20 * 0.99, e20 * 1.01
    else:
        z0, z1 = min(c, e20) * 0.99, max(c, e20)
    mid = (z0 + z1) / 2
    stop = min(low20 * 0.995, s50 * 0.99) if s50 else low20 * 0.995
    stop = max(stop, mid * 0.88)  # nie dalej niż 12% od wejścia
    if stop >= mid:
        stop = mid * 0.95
    c1 = hi if hi > mid * 1.04 else mid * 1.06
    c2 = c1 + 0.618 * max(c1 - low20, mid * 0.04)
    risk = mid - stop
    return {"z0": z0, "z1": z1, "mid": mid, "stop": stop, "c1": c1, "c2": c2,
            "r1": (c1 - mid) / risk, "r2": (c2 - mid) / risk}


def tech_points(m, lv):
    c = m["close"]
    up50 = m["above_base"] and m["ema20_gt_sma50"] is not False
    if up50:
        trend = 15 if m["off_high_pct"] > -8 else 12
    elif m["above_base"] or m["ema20_gt_sma50"]:
        trend = 8
    else:
        trend = 3
    rsi = m["rsi"] or 50
    pos = 9 if 45 <= rsi <= 62 else 6 if 62 < rsi <= 68 or 40 <= rsi < 45 else 4 if rsi > 68 else 3
    vr = m["vol_up_ratio"] or 1
    vol = 9 if vr >= 1.3 else 6 if vr >= 1.0 else 3
    t = m["turnover20"]
    liq = 10 if t >= 10e6 else 8 if t >= 3e6 else 6 if t >= 1e6 else 4 if t >= 3e5 else 1
    rr = 5 if lv["r1"] >= 2 else 3 if lv["r1"] >= 1.2 else 1
    return trend + pos + vol + liq + rr, {"trend": trend, "pos": pos, "vol": vol, "liq": liq, "rr": rr}


def div_points(reg5, j, v, days):
    reg = {5: 15, 4: 10}.get(reg5, 5)
    conf = {"wysoka": 10, "średnia": 6, "niska": 3}.get((v.get("confidence") or "").lower(), 3)
    near = 10 if days <= 30 else 8 if days <= 90 else 6 if days <= 150 else 4 if days <= 200 else 2
    return reg + j["stab"] + conf + near + j["health"], {"reg": reg, "stab": j["stab"], "conf": conf, "near": near, "health": j["health"]}


def main(argv):
    today = dt.date.fromisoformat(argv[argv.index("--today") + 1]) if "--today" in argv else dt.date.today()
    trend = json.loads((D / "trend.json").read_text(encoding="utf-8"))
    pool = {r["tic"]: r for r in json.loads((D / "pool.json").read_text(encoding="utf-8"))["rows"]}
    judge = json.loads((D / "judgement.json").read_text(encoding="utf-8"))
    rows = []
    for f in sorted(glob.glob(str(D / "verify" / "*.json"))):
        v = json.loads(Path(f).read_text(encoding="utf-8"))
        t = v["tic"]
        if v.get("announced_current_cycle") == "tak" or t not in trend or t not in judge:
            continue
        m, j = trend[t], judge[t]
        w = v.get("expected_rec_window") or {}
        w0, w1 = dt.date.fromisoformat(w["from"]), dt.date.fromisoformat(w["to"])
        days = (w0 - today).days
        lv = levels(m)
        tp, tparts = tech_points(m, lv)
        dp, dparts = div_points(pool.get(t, {}).get("reg5", 5), j, v, days)
        total = dp + tp
        up = m["above_base"] and m["ema20_gt_sma50"] is not False
        cls = "A" if total >= 75 and days <= 60 and up and lv["r1"] >= 1.5 else "B" if total >= 60 and up else "C"
        rows.append({"tic": t, "name": j.get("name", m["name"]), "sector": j["sector"], "m": m, "j": j, "lv": lv,
                     "w0": w0, "w1": w1, "days": days, "dp": dp, "tp": tp, "total": total, "cls": cls,
                     "parts": {**dparts, **{"t_" + k: x for k, x in tparts.items()}}, "up": up})
    rows.sort(key=lambda r: -r["total"])
    if "--all" not in argv:
        for r in rows:
            if not r["up"]:
                print(f"# bez trendu wzrostowego: {r['tic']} (suma {r['total']})", file=sys.stderr)
        rows = [r for r in rows if r["up"]]
    if "--json" in argv:
        out = [{k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in r.items()} for r in rows]
        print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
        return 0
    print("| # | Tic | Spółka | Sektor | Kurs | Trend | Od maks. | RSI | Seria (lata) | Ost. DPS | Oczek. DPS | Okno od | Okno do | Dni do okna | Dyw/50 | Tech/50 | Suma | Klasa | Wejście | Stop | C1 | C2 | R (C1 / C2) | Raport |")
    print("|" + "---|" * 24)
    for i, r in enumerate(rows, 1):
        m, lv, j = r["m"], r["lv"], r["j"]
        trend_s = "wzrostowy" if r["up"] else "boczny/słabnący" if m["above_base"] or m["ema20_gt_sma50"] else "spadkowy"
        row = (f"| {i} | {r['tic']} | {r['name']} | {r['sector']} | {price(m['close'])} | {trend_s} | {m['off_high_pct']:.1f}% | {m['rsi']:.0f} | "
              f"{j['years']} | {j['last_dps']} | {j['exp_dps']} | {r['w0'].isoformat()} | {r['w1'].isoformat()} | {r['days']} | "
              f"{r['dp']} | {r['tp']} | {r['total']} | {r['cls']} | {price(lv['z0'])}–{price(lv['z1'])} | {price(lv['stop'])} | "
              f"{price(lv['c1'])} | {price(lv['c2'])} | {lv['r1']:.1f} / {lv['r2']:.1f} | {j.get('report','')} |")
        print(row.replace('.', ',') if False else _comma(row))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
