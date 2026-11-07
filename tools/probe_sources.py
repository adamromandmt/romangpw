#!/usr/bin/env python3
"""Tymczasowa próba archiwum notowań GPW z runnera GitHub Actions (diagnostyka; nic nie zapisuje do repozytorium)."""
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import xlrd

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BASE = "https://www.gpw.pl/archiwum-notowan?fetch=1&type={t}&instrument=&date={d}&show_x=Poka%C5%BC+wyniki"
SNAP = "https://www.gpw.pl/ajaxindex.php?action=GPWQuotations&start=showTable&tab=all&lang=PL&full=1&format=html&mode="


def get(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pl,en;q=0.8", "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read()


def sheet(body):
    return xlrd.open_workbook(file_contents=body).sheet_by_index(0)


print("=== A. indeksy (type=1), 06-11-2026 ===", flush=True)
st, h, b = get(BASE.format(t=1, d="06-11-2026"))
sh = sheet(b)
for r in range(min(4, sh.nrows)):
    print(f"   [{r}] {sh.row_values(r)}", flush=True)
for r in range(sh.nrows):
    row = sh.row_values(r)
    if any(str(c).upper() in ("WIG", "WIG20", "MWIG40", "SWIG80", "WIG-POLAND") or str(c).upper().startswith(("WIG20", "MWIG", "SWIG")) for c in row[:3]):
        print(f"   * [{r}] {row}", flush=True)

print("=== B. głębokość archiwum (type=10) ===", flush=True)
for d in ("06-11-2025", "02-05-2025", "05-11-2024", "06-11-2023", "05-11-2020"):
    st, h, b = get(BASE.format(t=10, d=d))
    ok = b[:4] == b"\xd0\xcf\x11\xe0"
    print(f"{d}: HTTP {st} xls={ok} len={len(b)} nrows={sheet(b).nrows if ok else None}", flush=True)
    time.sleep(0.8)

print("=== C. migawka -> mapa ISIN/ticker i pokrycie universe.json ===", flush=True)
st, h, b = get(SNAP)
text = b.decode("utf-8", "replace")
isin2tic, name2tic = {}, {}
for r_ in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S):
    cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r_, flags=re.S)]
    if len(cells) > 15 and re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}\d", cells[3] or ""):
        isin2tic[cells[3]] = cells[4]
        name2tic[cells[2]] = cells[4]
uni = json.loads((ROOT / "data" / "universe.json").read_text(encoding="utf-8"))
tics = set(isin2tic.values())
miss = [t for t in uni["stocks"] if t not in tics]
print(f"mapa ISIN->ticker: {len(isin2tic)}; spółek universe: {len(uni['stocks'])}; brak w migawce: {len(miss)}: {miss}", flush=True)

print("=== D. zgodność archiwum GPW z data/market (biznesradar) ===", flush=True)
for d, iso in (("06-11-2026", "2026-11-06"), ("30-10-2026", "2026-10-30"), ("15-10-2026", "2026-10-15")):
    st, h, b = get(BASE.format(t=10, d=d))
    if b[:4] != b"\xd0\xcf\x11\xe0":
        print(d, "brak xls", flush=True)
        continue
    sh = sheet(b)
    hdr = sh.row_values(0)
    ix = {n: i for i, n in enumerate(hdr)}
    seen = same = diff = nodata = 0
    samples = []
    for r in range(1, sh.nrows):
        row = sh.row_values(r)
        tic = isin2tic.get(row[ix["ISIN"]])
        if not tic or tic not in uni["stocks"]:
            continue
        p = ROOT / "data" / "market" / f"{tic}.csv"
        if not p.exists():
            nodata += 1
            continue
        mk = {x["date"]: x for x in csv.DictReader(open(p, encoding="utf-8"))}
        if iso not in mk:
            continue
        seen += 1
        m = mk[iso]
        g = [row[ix["Kurs otwarcia"]], row[ix["Kurs max"]], row[ix["Kurs min"]], row[ix["Kurs zamknięcia"]], row[ix["Wolumen"]]]
        e = [float(m["open"]), float(m["high"]), float(m["low"]), float(m["close"]), float(m["volume"])]
        if all(abs(a - b_) <= 1e-6 * max(1, abs(b_)) for a, b_ in zip(g, e)):
            same += 1
        else:
            diff += 1
            if len(samples) < 5:
                samples.append((tic, g, e))
    print(f"{iso}: porównano {seen}, zgodne {same}, różne {diff}, bez pliku {nodata}", flush=True)
    for s in samples:
        print("   różnica:", s, flush=True)
    time.sleep(0.8)
print("koniec próby", flush=True)
sys.exit(0)
