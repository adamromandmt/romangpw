#!/usr/bin/env python3
"""Tymczasowa próba źródeł notowań z runnera GitHub Actions (diagnostyka; nic nie zapisuje do repozytorium)."""
import re
import sys
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

URLS = [
    # archiwum notowań GPW: różne warianty zapytania o całą sesję
    "https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=06-11-2026&show_x=Poka%C5%BC+wyniki",
    "https://www.gpw.pl/archiwum-notowan?fetch=1&type=10&instrument=&date=06-11-2026",
    "https://www.gpw.pl/archiwum-notowan?type=10&instrument=&date=06-11-2026",
    "https://www.gpw.pl/archiwum-notowan-full?type=10&instrument=&date=06-11-2026",
    "https://www.gpw.pl/archiwum-notowan",
    # bieżące notowania GPW (migawka całego rynku)
    "https://www.gpw.pl/notowania",
    "https://www.gpw.pl/ajaxindex.php?action=GPWQuotations&start=showTable&tab=all&lang=PL&full=1&format=html&mode=",
    # inne hurtowe listy
    "https://www.biznesradar.pl/gielda/akcje_gpw",
    "https://www.bankier.pl/gielda/notowania/akcje",
    # Yahoo z innego hosta / bez historii
    "https://query2.finance.yahoo.com/v8/finance/chart/LPP.WA?range=5d&interval=1d",
    "https://query1.finance.yahoo.com/v8/finance/chart/LPP.WA?range=5d&interval=1d",
    "https://stooq.pl/q/d/l/?s=lpp&i=d",
]


def show(url):
    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pl,en;q=0.8", "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read()
            status, final = r.status, r.geturl()
            hdr = {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        print(f"[{url}]\n  HTTP {e.code} {e.reason} w {time.time() - t0:.1f}s; ct={e.headers.get('content-type')}", flush=True)
        try:
            print("  treść:", e.read(200)[:200], flush=True)
        except Exception:  # noqa: BLE001
            pass
        return
    except Exception as e:  # noqa: BLE001
        print(f"[{url}]\n  BŁĄD {type(e).__name__}: {e} po {time.time() - t0:.1f}s", flush=True)
        return
    magic = body[:8].hex()
    kind = ("xls(OLE2)" if body[:4] == b"\xd0\xcf\x11\xe0" else "zip/xlsx" if body[:2] == b"PK"
            else "gzip" if body[:2] == b"\x1f\x8b" else "tekst")
    print(f"[{url}]\n  HTTP {status} w {time.time() - t0:.1f}s; final={final if final != url else '='}; "
          f"ct={hdr.get('content-type')}; cd={hdr.get('content-disposition')}; len={len(body)}; magic={magic} ({kind})", flush=True)
    if kind == "tekst":
        text = body.decode("utf-8", "replace")
        title = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.S | re.I)
        vis = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", text, flags=re.S)))
        print(f"  title={title.group(1).strip()[:90] if title else None!r} <table={text.count('<table')} <tr={text.count('<tr')} "
              f"tekst={vis.strip()[:260]!r}", flush=True)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S)
        for r_ in rows[:4]:
            cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r_, flags=re.S)]
            print("  wiersz:", cells[:16], flush=True)
        if text.lstrip().startswith("{"):
            print("  json:", text[:300].replace("\n", " "), flush=True)
    elif kind == "gzip":
        import gzip
        try:
            print("  gunzip:", gzip.decompress(body)[:300], flush=True)
        except Exception as e:  # noqa: BLE001
            print("  gunzip błąd", e, flush=True)


for u in URLS:
    show(u)
    time.sleep(1.5)
print("koniec próby", flush=True)
sys.exit(0)
