#!/usr/bin/env python3
"""Analiza historii dywidend spółek GPW.

Wejście: data/dividends/raw_YYYY.csv (biznesradar.pl/dywidendy/akcje_gpw,<rok>,3,1;
kolumny: ticker,company,fiscal_year,agm_date,last_cum_date,pay_date,dps_pln,status).

Wyjście: data/dividends/pool.json — spółki regularnie wypłacające dywidendę wraz z
oczekiwanym terminem kolejnej decyzji (WZA), szacowanym oknem rekomendacji zarządu
i statusem bieżącego sezonu. Okno rekomendacji jest szacunkiem z dat WZA (rekomendacje
zarządu nie są w tym źródle); dla krótkiej listy doprecyzowuje je analiza ESPI.

Użycie:
    python3 dividends.py pool [--today YYYY-MM-DD]
    python3 dividends.py show TICKER
"""
import csv
import datetime as dt
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "dividends"
MONTHS = {"sty": 1, "lut": 2, "mar": 3, "kwi": 4, "maj": 5, "cze": 6, "lip": 7,
          "sie": 8, "wrz": 9, "paź": 10, "paz": 10, "lis": 11, "gru": 12}
PAID = {"wypłacona", "wyplacona", "uchwalona", "rekomendowana"}


def pdate(s):
    """'05 gru 25' -> date(2025,12,5); 'bd.'/'' -> None."""
    s = (s or "").strip().lower()
    parts = s.split()
    if len(parts) != 3 or parts[1] not in MONTHS:
        return None
    try:
        y = int(parts[2])
        y = y + 2000 if y < 100 else y
        return dt.date(y, MONTHS[parts[1]], int(parts[0]))
    except ValueError:
        return None


def load_events():
    seen, events = set(), []
    for f in sorted(DATA.glob("raw_*.csv")):
        with f.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                try:
                    fy = int(str(r["fiscal_year"]).strip())
                except (ValueError, TypeError):
                    continue
                dps = None
                try:
                    dps = float(str(r["dps_pln"]).replace(",", "."))
                except (ValueError, TypeError):
                    pass
                ev = {"tic": r["ticker"].strip().upper(), "name": r["company"].strip(), "fy": fy,
                      "agm": pdate(r["agm_date"]), "cum": pdate(r["last_cum_date"]),
                      "pay": pdate(r["pay_date"]), "dps": dps,
                      "status": (r.get("status") or "").strip().lower()}
                key = (ev["tic"], ev["fy"], ev["agm"], ev["cum"], ev["pay"], ev["dps"])
                if key in seen:
                    continue
                seen.add(key)
                events.append(ev)
    return events


def _next_occurrence(d, today):
    """Najbliższa data po `today` o tym samym dniu i miesiącu co `d`."""
    for year in (today.year, today.year + 1, today.year + 2):
        try:
            c = d.replace(year=year)
        except ValueError:  # 29 lutego
            c = d.replace(year=year, day=28)
        if c > today:
            return c
    return None


def _cluster(dates, gap=40):
    """Grupuje daty po dniu roku (okrągle) — kotwice sezonowe, np. 'styczeń', 'czerwiec'."""
    doy = sorted((d.timetuple().tm_yday, d) for d in dates)
    groups = []
    for y, d in doy:
        if groups and y - groups[-1][-1][0] <= gap:
            groups[-1].append((y, d))
        else:
            groups.append([(y, d)])
    if len(groups) > 1 and groups[0][0][0] + 365 - groups[-1][-1][0] <= gap:
        groups[0] = groups[-1] + groups[0]
        groups.pop()
    return [[d for _, d in g] for g in groups]


def analyse(today=None):
    today = today or dt.date.today()
    events = [e for e in load_events() if e["status"] in PAID or e["status"] == ""]
    by = defaultdict(list)
    for e in events:
        by[e["tic"]].append(e)
    out = []
    for tic, evs in by.items():
        evs.sort(key=lambda e: (e["agm"] or dt.date.min, e["cum"] or dt.date.min))
        fys = defaultdict(float)
        for e in evs:
            if e["dps"] is not None and e["status"] in PAID:
                fys[e["fy"]] += e["dps"]
        last5 = [y for y in range(2021, 2026) if fys.get(y, 0) > 0]
        reg5 = len(last5)
        agms = [e["agm"] for e in evs if e["agm"]]
        recent_agms = [d for d in agms if d >= today - dt.timedelta(days=800)]
        if not recent_agms:
            continue
        anchors = []
        for grp in _cluster(recent_agms):
            ref = max(grp)
            nxt = _next_occurrence(ref, today)
            # czy w bieżącym sezonie kotwica już się zdarzyła (WZA w ±45 dni od daty w tym roku, przed dziś)?
            this_year = None
            try:
                this_year = ref.replace(year=today.year)
            except ValueError:
                this_year = ref.replace(year=today.year, day=28)
            season_done = None
            if this_year <= today:
                season_done = any(abs((d - this_year).days) <= 45 for d in agms if d.year == today.year)
            doys = [d.timetuple().tm_yday for d in grp]
            spread = max(doys) - min(doys) if max(doys) - min(doys) < 200 else 0
            anchors.append({"ref": ref.isoformat(), "next_agm": nxt.isoformat() if nxt else None,
                            "n": len(grp), "spread_days": spread, "season_done": season_done})
        anchors.sort(key=lambda a: a["next_agm"] or "9999")
        pend = [a for a in anchors if a["next_agm"]]
        if not pend:
            continue
        nxt = pend[0]
        nxt_agm = dt.date.fromisoformat(nxt["next_agm"])
        lag = 50 if 5 <= nxt_agm.month <= 7 else 25
        rec = nxt_agm - dt.timedelta(days=lag)
        half = max(7, nxt["spread_days"] // 2 + 5)
        w0, w1 = rec - dt.timedelta(days=half + 7), rec + dt.timedelta(days=half)
        last = max((e for e in evs if e["agm"]), key=lambda e: e["agm"], default=None)
        out.append({
            "tic": tic, "name": evs[-1]["name"], "reg5": reg5, "fys": {str(k): round(v, 2) for k, v in sorted(fys.items())},
            "last_agm": last["agm"].isoformat() if last else None,
            "last_cum": last["cum"].isoformat() if last and last["cum"] else None,
            "last_dps": last["dps"] if last else None,
            "next_agm": nxt["next_agm"], "agm_spread_days": nxt["spread_days"],
            "rec_est": rec.isoformat(), "win0": w0.isoformat(), "win1": w1.isoformat(),
            "days_to_win": (w0 - today).days, "season_missing": [a["ref"] for a in anchors if a["season_done"] is False],
            "anchors": anchors,
        })
    out.sort(key=lambda r: r["win0"])
    return out


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "pool"
    today = dt.date.today()
    if "--today" in argv:
        today = dt.date.fromisoformat(argv[argv.index("--today") + 1])
    res = analyse(today)
    if cmd == "show":
        for r in res:
            if r["tic"] == argv[2].upper():
                print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "pool.json").write_text(json.dumps({"today": today.isoformat(), "rows": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    reg = [r for r in res if r["reg5"] >= 4]
    print(f"spółek z danymi: {len(res)}; regularnych (>=4 z 5 FY): {len(reg)}")
    near = [r for r in reg if r["days_to_win"] <= 200]
    print(f"regularnych z oknem rekomendacji w ciągu 200 dni: {len(near)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
