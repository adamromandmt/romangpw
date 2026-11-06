#!/usr/bin/env python3
"""Pobiera dzienne notowania (OHLCV) spółek i indeksów GPW do data/market/<TIC>.csv.

Uruchamiany przez GitHub Actions (.github/workflows/quotes.yml), bo tylko tam jest dostęp do internetu.
Tylko biblioteka standardowa. Źródła po kolei (pierwsze, które zwróci sensowne dane, wygrywa):
  1. EODHD   — jeśli ustawiony sekret EODHD_API_KEY (giełda WAR = GPW),
  2. stooq.pl (opcjonalnie STOOQ_APIKEY, jeśli stooq zacznie go wymagać),
  3. stooq.com,
  4. biznesradar.pl (tabela notowań historycznych).
Nowe wiersze scalane są z istniejącym plikiem (po dacie), zostaje ostatnich HISTORY sesji.
Wynik: data/market/<TIC>.csv (date,open,high,low,close,volume), indeksy jako _WIG.csv itd.
oraz data/market/_status.json (źródło i ostatnia data każdego symbolu, lista błędów).

Użycie: python3 fetch_quotes.py [--only TIC,TIC] [--history 500] [--workers 4]
Kod wyjścia: 0 gdy pobrano >= 50% symboli, 1 w przeciwnym razie (workflow i tak commituje to, co jest).
"""
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "market"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


RAW = {}  # ostatnia odpowiedź na wątek (tylko do diagnostyki w logu)


def http(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pl,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        text = r.read().decode("utf-8", "replace")
    RAW[threading.get_ident()] = (url, text)
    return text


def num(s):
    s = re.sub(r"<[^>]+>", "", s).replace("\xa0", "").replace(" ", "").replace(" ", "").strip()
    s = s.replace(",", ".")
    return float(s)


def sane(row):
    o, h, l, c, v = row["open"], row["high"], row["low"], row["close"], row["volume"]
    eps = 1e-6 + 0.002 * c
    return c > 0 and h + eps >= max(o, c) and l - eps <= min(o, c) and h + eps >= l and v >= 0


def parse_csv(text):
    """Stooq / EODHD CSV: Data|Date, Otwarcie|Open, Najwyzszy|High, Najnizszy|Low, Zamkniecie|Close, [Adjusted_close], Wolumen|Volume."""
    rd = csv.reader(io.StringIO(text.strip()))
    head = next(rd, None)
    if not head or len(head) < 5:
        raise ValueError("brak nagłówka CSV: " + (text[:80].replace("\n", " ") if text else "pusta odpowiedź"))
    h = [x.strip().lower() for x in head]
    idx = {}
    for key, names in (("date", ("data", "date")), ("open", ("otwarcie", "open")), ("high", ("najwyzszy", "high")),
                       ("low", ("najnizszy", "low")), ("close", ("zamkniecie", "close")), ("volume", ("wolumen", "volume"))):
        for n in names:
            if n in h:
                idx[key] = h.index(n)
                break
    if len(idx) < 5 or "date" not in idx:
        raise ValueError("nieznany nagłówek CSV: " + ",".join(head)[:80])
    rows = []
    for r in rd:
        try:
            d = r[idx["date"]].strip()
            if not DATE.match(d):
                continue
            row = {"date": d, "open": float(r[idx["open"]]), "high": float(r[idx["high"]]), "low": float(r[idx["low"]]),
                   "close": float(r[idx["close"]]), "volume": float(r[idx["volume"]]) if "volume" in idx and r[idx["volume"]] not in ("", "null") else 0.0}
        except (ValueError, IndexError):
            continue
        if sane(row):
            rows.append(row)
    if not rows:
        raise ValueError("CSV bez poprawnych wierszy")
    return sorted(rows, key=lambda x: x["date"])


def src_eodhd(sym, kind, entry):
    key = os.environ.get("EODHD_API_KEY")
    if not key or kind != "stock":
        raise ValueError("EODHD pominięty")
    frm = (dt.date.today() - dt.timedelta(days=800)).isoformat()
    return parse_csv(http(f"https://eodhd.com/api/eod/{sym}.WAR?api_token={key}&fmt=csv&period=d&from={frm}"))


def src_stooq(host):
    def f(sym, kind, entry):
        s = entry["stooq"] if kind == "index" else sym.lower()
        url = f"https://{host}/q/d/l/?s={s}&i=d"
        if os.environ.get("STOOQ_APIKEY"):
            url += "&apikey=" + os.environ["STOOQ_APIKEY"]
        return parse_csv(http(url))
    return f


def src_biznesradar(sym, kind, entry):
    name = entry["br"] if kind == "index" else entry.get("br", sym)
    html = http(f"https://www.biznesradar.pl/notowania-historyczne/{name}")
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.S):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S)
        if not cells:
            continue
        d = re.sub(r"<[^>]+>", "", cells[0]).strip()
        if not DATE.match(d):
            continue
        try:
            n = [num(c) for c in cells[1:6]]
        except ValueError:
            continue
        if len(n) < 5:
            continue
        row = {"date": d, "open": n[0], "high": n[1], "low": n[2], "close": n[3], "volume": n[4]}
        if sane(row):
            rows.append(row)
    if not rows:
        raise ValueError("biznesradar: brak poprawnych wierszy")
    return sorted(rows, key=lambda x: x["date"])


SOURCES = [("eodhd", src_eodhd), ("stooq.pl", src_stooq("stooq.pl")), ("stooq.com", src_stooq("stooq.com")), ("biznesradar", src_biznesradar)]


def load(path):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as fh:
        return {r["date"]: {k: (r[k] if k == "date" else float(r[k])) for k in ("date", "open", "high", "low", "close", "volume")}
                for r in csv.DictReader(fh)}


def save(path, rows, history):
    rows = sorted(rows.values(), key=lambda r: r["date"])[-history:]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "open", "high", "low", "close", "volume"])
        for r in rows:
            w.writerow([r["date"], f"{r['open']:g}", f"{r['high']:g}", f"{r['low']:g}", f"{r['close']:g}", f"{r['volume']:.0f}"])
    return rows


DISABLED = {}          # źródło -> powód wyłączenia (próba startowa albo za dużo kolejnych błędów)
STREAK = {}            # źródło -> liczba kolejnych błędów bez żadnego sukcesu
GOOD = set()           # źródła, które choć raz zadziałały
LOCK = threading.Lock()
DEADLINE = [None]
MAX_FAIL_STREAK = 8


def note(name, ok, err=""):
    with LOCK:
        if ok:
            GOOD.add(name)
            STREAK[name] = 0
            return
        STREAK[name] = STREAK.get(name, 0) + 1
        if name not in GOOD and STREAK[name] >= MAX_FAIL_STREAK and name not in DISABLED:
            DISABLED[name] = f"{MAX_FAIL_STREAK} błędów z rzędu, ostatni: {err[:100]}"
            print(f"!! źródło {name} wyłączone: {DISABLED[name]}", flush=True)


def probe():
    """Szybka próba każdego źródła na PKO (z miarą czasu). Wyłącza źródła, które nie działają. Zwraca słownik z wynikami."""
    out = {}
    for name, fn in SOURCES:
        t0 = time.time()
        try:
            rows = fn("PKO", "stock", {"br": "PKO"})
            out[name] = {"ok": True, "last": rows[-1]["date"], "rows": len(rows), "sec": round(time.time() - t0, 1)}
            GOOD.add(name)
        except Exception as e:  # noqa: BLE001
            out[name] = {"ok": False, "error": str(e)[:160], "sec": round(time.time() - t0, 1)}
            raw = RAW.get(threading.get_ident())
            if raw:  # diagnostyka tylko do logu Actions (nic nie trafia do repozytorium)
                url, text = raw
                title = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.S | re.I)
                visible = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", text, flags=re.S)))
                print(f"  diagnostyka {name}: {url} długość={len(text)} tytuł={title.group(1).strip()[:80] if title else None!r} "
                      f"<table>={text.count('<table')} <tr>={text.count('<tr')} tekst={visible.strip()[:300]!r}", flush=True)
            if "pominięty" in str(e):
                DISABLED[name] = "pominięty (brak klucza)"
            else:
                DISABLED[name] = "nie przeszło próby: " + str(e)[:100]
        print(f"próba {name}: {out[name]}", flush=True)
    return out


def fetch_one(job):
    sym, kind, entry, history = job
    errs = []
    if DEADLINE[0] and time.time() > DEADLINE[0]:
        return sym, None, ["przekroczony budżet czasu"]
    for name, fn in SOURCES:
        if name in DISABLED:
            continue
        try:
            rows = fn(sym, kind, entry)
        except Exception as e:  # noqa: BLE001 — każdy błąd źródła tylko przechodzi do następnego
            errs.append(f"{name}: {str(e)[:90]}")
            note(name, False, str(e))
            continue
        note(name, True)
        fname = ("_" + sym) if kind == "index" else sym
        path = OUT / f"{fname}.csv"
        merged = load(path)
        for r in rows:
            merged[r["date"]] = r
        kept = save(path, merged, history)
        return sym, {"source": name, "last": kept[-1]["date"], "rows": len(kept), "new": len(rows)}, None
    return sym, None, errs


def main(argv):
    uni = json.loads((ROOT / "data" / "universe.json").read_text(encoding="utf-8"))
    history = int(argv[argv.index("--history") + 1]) if "--history" in argv else 500
    workers = int(argv[argv.index("--workers") + 1]) if "--workers" in argv else 4
    only = set(argv[argv.index("--only") + 1].upper().split(",")) if "--only" in argv else None
    budget = int(argv[argv.index("--budget") + 1]) if "--budget" in argv else 600
    OUT.mkdir(parents=True, exist_ok=True)
    probes = probe()
    if all(n in DISABLED for n, _ in SOURCES):
        status = {"run_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "probe": probes, "ok": 0,
                  "note": "żadne źródło nie przeszło próby na PKO"}
        (OUT / "_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
        print("Żadne źródło nie działa — koniec.", flush=True)
        return 1
    DEADLINE[0] = time.time() + budget
    jobs = []
    for t in uni["stocks"]:
        if only and t not in only:
            continue
        jobs.append((t, "stock", {"br": uni.get("biznesradar_alias", {}).get(t, t)}, history))
    for t, e in uni["indices"].items():
        if only and t not in only:
            continue
        jobs.append((t, "index", e, history))
    ok, failed, t0 = {}, {}, time.time()

    def run(job):
        time.sleep(0.25)
        res = fetch_one(job)
        print(f"{'OK ' if res[1] else 'ERR'} {res[0]} {res[1]['source'] + ' ' + res[1]['last'] if res[1] else '; '.join(res[2])[:150]}", flush=True)
        return res

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for sym, res, errs in ex.map(run, jobs):
            if res:
                ok[sym] = res
            else:
                failed[sym] = errs
    last = max((v["last"] for v in ok.values()), default=None)
    stale = sorted(s for s, v in ok.items() if last and v["last"] < last)
    status = {"run_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "probe": probes,
              "disabled_sources": DISABLED, "latest_session": last,
              "ok": len(ok), "failed": failed, "behind_latest_session": stale,
              "sources": {s: v["source"] for s, v in sorted(ok.items())},
              "last_date": {s: v["last"] for s, v in sorted(ok.items())}}
    if only is None:
        (OUT / "_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
    by_src = {}
    for v in ok.values():
        by_src[v["source"]] = by_src.get(v["source"], 0) + 1
    print(f"Pobrano {len(ok)}/{len(jobs)} symboli w {time.time() - t0:.0f}s; ostatnia sesja {last}; źródła {by_src}")
    if failed:
        print("Błędy:", ", ".join(f"{s} ({'; '.join(e)[:120]})" for s, e in sorted(failed.items())[:12]), "...")
    return 0 if len(ok) >= 0.5 * len(jobs) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
