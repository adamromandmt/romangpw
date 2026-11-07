#!/usr/bin/env python3
"""Tymczasowa próba archiwum notowań GPW z runnera GitHub Actions (diagnostyka; nic nie zapisuje do repozytorium)."""
import re
import sys
import time
import urllib.error
import urllib.request

import xlrd

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BASE = "https://www.gpw.pl/archiwum-notowan?fetch=1&type={t}&instrument=&date={d}&show_x=Poka%C5%BC+wyniki"


def get(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pl,en;q=0.8", "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read()


def dump_xls(body, label, head=6, grep=()):
    try:
        wb = xlrd.open_workbook(file_contents=body)
    except Exception as e:  # noqa: BLE001
        print(f"  {label}: xlrd błąd {type(e).__name__}: {str(e)[:160]}", flush=True)
        return None
    for sh in wb.sheets():
        print(f"  arkusz {sh.name!r}: {sh.nrows} wierszy x {sh.ncols} kolumn", flush=True)
    sh = wb.sheet_by_index(0)
    for r in range(min(head, sh.nrows)):
        print(f"   [{r}] {sh.row_values(r)}", flush=True)
    for r in range(sh.nrows):
        row = sh.row_values(r)
        if any(str(c).upper().startswith(grep) for c in row[:4]):
            print(f"   * [{r}] {row}", flush=True)
    return sh


print("=== A. akcje (type=10), 06-11-2026 ===", flush=True)
st, h, b = get(BASE.format(t=10, d="06-11-2026"))
print(st, h.get("content-disposition"), len(b), flush=True)
sh = dump_xls(b, "akcje", head=8, grep=("LPP", "ALLEGRO", "PKO", "CCC", "LIVECHAT", "CIECH", "CYBER", "KGHM", "MBANK"))

print("=== B. inne typy archiwum (06-11-2026) ===", flush=True)
for t in list(range(1, 10)) + list(range(11, 25)):
    try:
        st, h, b = get(BASE.format(t=t, d="06-11-2026"))
        cd = h.get("content-disposition")
        n = None
        if b[:4] == b"\xd0\xcf\x11\xe0":
            try:
                n = xlrd.open_workbook(file_contents=b).sheet_by_index(0).nrows
            except Exception as e:  # noqa: BLE001
                n = f"xlrd:{type(e).__name__}"
        print(f"type={t}: HTTP {st} ct={h.get('content-type')} cd={cd} len={len(b)} nrows={n}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"type={t}: BŁĄD {type(e).__name__}: {e}", flush=True)
    time.sleep(0.8)

print("=== C. dni wolne i przyszłe (type=10) ===", flush=True)
for d in ("07-11-2026", "11-11-2026", "10-11-2026", "01-01-2026", "04-11-2026"):
    st, h, b = get(BASE.format(t=10, d=d))
    n = None
    if b[:4] == b"\xd0\xcf\x11\xe0":
        try:
            n = xlrd.open_workbook(file_contents=b).sheet_by_index(0).nrows
        except Exception as e:  # noqa: BLE001
            n = f"xlrd:{type(e).__name__}"
    print(f"{d}: HTTP {st} ct={h.get('content-type')} cd={h.get('content-disposition')} len={len(b)} nrows={n} "
          f"początek={b[:80]!r}" if n is None else f"{d}: HTTP {st} cd={h.get('content-disposition')} len={len(b)} nrows={n}", flush=True)
    time.sleep(0.8)

print("=== D. migawka ajaxindex: wiersze LPP/PKO/WIG20 ===", flush=True)
st, h, b = get("https://www.gpw.pl/ajaxindex.php?action=GPWQuotations&start=showTable&tab=all&lang=PL&full=1&format=html&mode=")
text = b.decode("utf-8", "replace")
rows = re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S)
hdr = None
cnt = 0
for r_ in rows:
    cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r_, flags=re.S)]
    if cells and cells[0] == "" and "Skrót" in cells:
        hdr = cells
        print("  nagłówek:", cells, flush=True)
    if len(cells) > 15 and re.fullmatch(r"[A-Z0-9]{2,5}", cells[4] if len(cells) > 4 else ""):
        cnt += 1
        if cells[4] in ("LPP", "PKO", "11B"):
            print("  wiersz:", cells, flush=True)
print("  wierszy z tickerem:", cnt, flush=True)

print("=== E. migawka: czy są indeksy? ===", flush=True)
for u in ("https://www.gpw.pl/ajaxindex.php?action=GPWIndexes&start=showTable&lang=PL&format=html",
          "https://www.gpw.pl/indeksy"):
    st, h, b = get(u)
    t = b.decode("utf-8", "replace")
    vis = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)))
    print(f"  {u} -> HTTP {st} len={len(b)} WIG20={'WIG20' in t} tekst={vis.strip()[:200]!r}", flush=True)
    time.sleep(0.8)
print("koniec próby", flush=True)
sys.exit(0)
