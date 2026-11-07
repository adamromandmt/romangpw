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



print("=== E. nazwy GPW bez ISIN w migawce i kandydaci dla 7 brakujących ===", flush=True)
st, h, b = get(BASE.format(t=10, d="06-11-2026"))
sh = sheet(b)
snap = get(SNAP)[2].decode("utf-8", "replace")
isin2tic, name2tic = {}, {}
for r_ in re.findall(r"<tr[^>]*>(.*?)</tr>", snap, flags=re.S):
    cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r_, flags=re.S)]
    if len(cells) > 15 and re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}\d", cells[3] or ""):
        isin2tic[cells[3]] = cells[4]
        name2tic[cells[2]] = cells[4]
unm = []
for r in range(1, sh.nrows):
    row = sh.row_values(r)
    if row[2] not in isin2tic:
        unm.append((row[1], row[2], row[9]))
print("xls wierszy:", sh.nrows - 1, "; bez ISIN w migawce:", len(unm), flush=True)
print([f"{n}:{v:.0f}" for n, i, v in unm], flush=True)
want = ["CCC", "CIE", "KVT", "LVC", "MLP", "QNT", "SPL"]
br = get("https://www.biznesradar.pl/gielda/akcje_gpw")[2].decode("utf-8", "replace")
brmap = {}
for r_ in re.findall(r"<tr[^>]*>(.*?)</tr>", br, flags=re.S):
    cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r_, flags=re.S)]
    if cells and re.match(r"^[A-Z0-9]{2,5} \(", cells[0]):
        m = re.match(r"^([A-Z0-9]{2,5}) \((.*)\)$", cells[0])
        if m:
            brmap[m[1]] = m[2]
print("biznesradar: pozycji", len(brmap), "; dla brakujących:", {t: brmap.get(t) for t in want}, flush=True)
print("koniec próby", flush=True)
sys.exit(0)
