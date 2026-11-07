#!/usr/bin/env python3
"""Pobiera dzienne notowania (OHLCV) spółek i indeksów GPW do data/market/<TIC>.csv.

Źródło: oficjalne archiwum notowań GPW (https://www.gpw.pl/archiwum-notowan). Jedno zapytanie zwraca plik .xls z całą
sesją (wszystkie spółki), więc backfill ok. 260 sesji to ok. 520 zapytań (akcje + indeksy), a dzienna aktualizacja
to 2-4. Wcześniej pobieranie per spółka z biznesradaru kończyło się blokadą runnera po ok. 100 zapytaniach, Yahoo
zwraca 429, a stooq wymaga JavaScriptu. Ceny są surowe (bez korekt o dywidendy i splity); wolumen to pełny wolumen
sesji (z transakcjami pakietowymi), więc bywa wyższy niż na biznesradarze. Dni bez obrotu (wolumen 0) nie dają
świecy, więc słabo płynne spółki mają luki w serii.

Uruchamiany przez GitHub Actions (.github/workflows/quotes.yml); wymaga `pip install -r requirements.txt` (xlrd).
Mapowanie wiersza archiwum na ticker: ISIN -> ticker z migawki notowań ciągłych GPW (zapamiętywane w
data/market/_names.json), a dla spółek spoza migawki (np. notowanych w systemie jednolitym) alias nazwy GPW
w data/universe.json ("gpw_alias").

Wynik: data/market/<TIC>.csv (date,open,high,low,close,volume); indeksy jako _WIG.csv, _WIG20.csv, _MWIG40.csv,
_SWIG80.csv (w kolumnie volume jest obrót w tys. zł); _status.json (pokrycie, luki, uwagi), _calendar.json (pobrane
sesje i dni bez sesji) oraz _names.json (mapa ISIN/nazwa -> ticker). Pobieranie jest wznawialne: najnowsze sesje
najpierw, zaległe w kolejnych przebiegach.

Użycie: python3 fetch_quotes.py [--days 380] [--history 520] [--budget 1500] [--pause 0.6] [--today RRRR-MM-DD]
                                [--only-dates 2026-11-06,...]
Kod wyjścia: 0, gdy najnowsza sesja jest świeża i obejmuje >= 85% rozpoznanych spółek z universe, a ostatnie sesje
nie zakończyły się błędem; 1 w przeciwnym razie.
"""
import csv
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import xlrd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "market"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
ARCHIVE = "https://www.gpw.pl/archiwum-notowan?fetch=1&type={t}&instrument=&date={d}&show_x=Poka%C5%BC+wyniki"
SNAPSHOT = "https://www.gpw.pl/ajaxindex.php?action=GPWQuotations&start=showTable&tab=all&lang=PL&full=1&format=html&mode="
STOCKS, INDICES = 10, 1          # parametr type archiwum: 10 = akcje (Główny Rynek i NewConnect), 1 = indeksy
OLE2 = b"\xd0\xcf\x11\xe0"       # początek pliku .xls; dzień bez sesji zwraca stronę HTML
ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}\d$")
FIELDS = ("open", "high", "low", "close", "volume")
MIN_COVERAGE = 0.85              # odsetek rozpoznanych spółek z notowaniem w najnowszej sesji
MIN_ROWS = 50                    # tyle wierszy z datą sesji musi mieć plik akcji (normalnie ok. 400)
MAX_CONSECUTIVE_ERRORS = 5       # tyle błędów sesji z rzędu uznajemy za blokadę/awarię i kończymy przebieg
RETRY_DELAY = 3                  # sekundy; mnożone przez numer próby
CONFIRM_DELAY = 2                # sekundy przed potwierdzeniem, że zamiast .xls przyszła strona HTML
RECHECK_DAYS = 14                # dni bez sesji z ostatnich tylu dni sprawdzamy ponownie


def http_get(url, timeout=40, tries=3):
    """GET z ponawianiem przy błędach sieci, 429 i 5xx (inne błędy HTTP zwracamy od razu)."""
    last = None
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pl,en;q=0.8", "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code < 500 and e.code != 429:
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
        time.sleep(RETRY_DELAY * (attempt + 1))
    raise last


# ---------------------------------------------------------------- parsowanie

CELL = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.S)
TAGS = re.compile(r"<[^>]+>")


def row_cells(tr):
    return [re.sub(r"\s+", " ", html.unescape(TAGS.sub(" ", c))).strip() for c in CELL.findall(tr)]


def parse_snapshot(text):
    """Migawka notowań ciągłych GPW (HTML) -> ({ISIN: ticker}, {nazwa GPW: ticker}); kolumny wg nagłówka (Nazwa, ISIN, Skrót)."""
    by_isin, by_name, ix = {}, {}, None
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S):
        c = row_cells(tr)
        if ix is None:
            if "Skrót" in c and "ISIN" in c and "Nazwa" in c:
                ix = (c.index("Nazwa"), c.index("ISIN"), c.index("Skrót"))
            continue
        if len(c) > max(ix) and ISIN.match(c[ix[1]]) and c[ix[2]]:
            by_isin[c[ix[1]]] = c[ix[2]]
            by_name[c[ix[0]]] = c[ix[2]]
    return by_isin, by_name


def parse_xls(body):
    """Arkusz archiwum GPW (.xls) -> lista słowników; kolumny rozpoznawane po nagłówku."""
    sh = xlrd.open_workbook(file_contents=body).sheet_by_index(0)
    ix = {str(n).strip(): i for i, n in enumerate(sh.row_values(0))}
    need = ("Data", "Nazwa", "ISIN", "Kurs otwarcia", "Kurs max", "Kurs min", "Kurs zamknięcia", "Wolumen", "Obrót")
    miss = [n for n in need if n not in ix]
    if miss:
        raise ValueError("archiwum GPW: brak kolumn " + ", ".join(miss))
    out = []
    for r in range(1, sh.nrows):
        v = sh.row_values(r)

        def f(n):
            x = v[ix[n]]
            return float(x) if isinstance(x, (int, float)) else None
        out.append({"date": str(v[ix["Data"]]).strip()[:10], "name": str(v[ix["Nazwa"]]).strip(), "isin": str(v[ix["ISIN"]]).strip(),
                    "open": f("Kurs otwarcia"), "high": f("Kurs max"), "low": f("Kurs min"), "close": f("Kurs zamknięcia"),
                    "volume": f("Wolumen"), "turnover": f("Obrót")})
    return out


def bar(r, index=False):
    """((open, high, low, close, volume), poprawiono) albo None, gdy tego dnia nie było obrotu lub brak cen.
    Dla indeksu w polu volume trafia obrót (tys. zł). Gdy max/min nie obejmuje otwarcia lub zamknięcia
    (zaokrąglenia GPW), korygujemy je do tych wartości i oznaczamy bar jako poprawiony."""
    o, h, l, c = r["open"], r["high"], r["low"], r["close"]
    if None in (o, h, l, c) or min(o, h, l, c) <= 0:
        return None
    v = r["turnover"] if index else r["volume"]
    if v is None or v < 0 or (not index and v == 0):
        return None
    h2, l2 = max(h, o, c), min(l, o, c)
    return (o, h2, l2, c, v), (h2 - h > 1e-9 or l - l2 > 1e-9)


# ---------------------------------------------------------------- pliki

def fnum(x):
    return f"{x:.6f}".rstrip("0").rstrip(".")


def load_csv(path):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as fh:
        return {r["date"]: tuple(float(r[k]) for k in FIELDS) for r in csv.DictReader(fh)}


def save_csv(path, rows, history):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", *FIELDS])
        for d in sorted(rows)[-history:]:
            w.writerow([d, *(fnum(x) for x in rows[d])])


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save_json(path, obj):
    text = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True)
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def weekdays(start, end):
    d = start
    while d <= end:
        if d.weekday() < 5:
            yield d
        d += dt.timedelta(days=1)


def ddmmyyyy(iso):
    y, m, d = iso.split("-")
    return f"{d}-{m}-{y}"


def fetch_xls(d, typ):
    """Plik .xls albo None, gdy GPW zwraca stronę HTML (dzień bez sesji lub archiwum jeszcze niegotowe)."""
    url = ARCHIVE.format(t=typ, d=ddmmyyyy(d))
    body = http_get(url)
    if body[:4] != OLE2:
        time.sleep(CONFIRM_DELAY)               # potwierdzenie, by chwilowa strona błędu nie uchodziła za święto
        body = http_get(url)
    return body if body[:4] == OLE2 else None


# ---------------------------------------------------------------- przebieg

def main(argv):
    def opt(name, default):
        return type(default)(argv[argv.index(name) + 1]) if name in argv else default
    days, history, budget, pause = opt("--days", 380), opt("--history", 520), opt("--budget", 1500), opt("--pause", 0.6)
    only = argv[argv.index("--only-dates") + 1].split(",") if "--only-dates" in argv else None
    today = dt.date.fromisoformat(opt("--today", "")) if "--today" in argv else dt.date.today()
    OUT.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    uni = json.loads((ROOT / "data" / "universe.json").read_text(encoding="utf-8"))
    stocks, indices, alias = list(uni["stocks"]), list(uni["indices"]), uni.get("gpw_alias", {})
    wanted, idx_by_name = set(stocks), {i.upper(): i for i in indices}
    warns = []

    # 1) mapowanie ISIN / nazwa GPW -> ticker (migawka notowań ciągłych + zapamiętane wcześniej + aliasy)
    names = load_json(OUT / "_names.json", {"isin": {}, "name": {}})
    names_before = json.dumps(names, sort_keys=True)
    try:
        by_isin, by_name = parse_snapshot(http_get(SNAPSHOT).decode("utf-8", "replace"))
        if len(by_isin) < 100:
            raise ValueError(f"migawka podejrzanie mała ({len(by_isin)} pozycji)")
        names["isin"].update(by_isin)
        names["name"].update(by_name)
    except Exception as e:  # noqa: BLE001 — zostaje mapowanie z poprzednich przebiegów
        warns.append(f"migawka GPW: {type(e).__name__}: {str(e)[:100]}")
        print("!! " + warns[-1], flush=True)
    isin2tic = names["isin"]
    name2tic = dict(names["name"])
    name2tic.update({nm: t for t, nm in alias.items()})
    known = set(isin2tic.values()) | set(name2tic.values())

    # 2) które sesje trzeba pobrać (najnowsze najpierw; ostatnia znana sesja zawsze od nowa,
    #    a niedawne dni bez pliku sprawdzamy ponownie, by chwilowa awaria nie zrobiła z sesji święta)
    cal = load_json(OUT / "_calendar.json", {"sessions": [], "closed": []})
    have, closed = set(cal["sessions"]), set(cal["closed"])
    cands = [d.isoformat() for d in weekdays(today - dt.timedelta(days=days), today)]
    recent = {(today - dt.timedelta(days=k)).isoformat() for k in range(RECHECK_DAYS + 1)}
    latest_known = max(have) if have else None
    needed = only or [d for d in reversed(cands) if (d not in have and (d not in closed or d in recent)) or d == latest_known]
    print(f"sesje do pobrania: {len(needed)} (znane {len(have)}, dni bez sesji {len(closed)}); budżet {budget}s", flush=True)

    rows_s, rows_i = {}, {}          # {ticker|indeks: {data: (o,h,l,c,v)}} jeszcze niezapisane
    got, no_xls, errors, pending = [], [], [], []
    repaired = consecutive = 0

    def write_calendar():
        latest_now = max(have) if have else None
        if not only:
            closed.update(d for d in no_xls if latest_now and d < latest_now)
        closed.difference_update(have)
        floor = (today - dt.timedelta(days=days + 60)).isoformat()
        save_json(OUT / "_calendar.json", {"sessions": sorted(x for x in have if x >= floor), "closed": sorted(x for x in closed if x >= floor)})

    def flush():
        for prefix, store in (("", rows_s), ("_", rows_i)):
            for key, new in store.items():
                p = OUT / f"{prefix}{key}.csv"
                merged = load_csv(p)
                merged.update(new)
                save_csv(p, merged, history)
            store.clear()
        if json.dumps(names, sort_keys=True) != names_before:
            save_json(OUT / "_names.json", names)
        write_calendar()

    deadline = t_start + budget
    for n, d in enumerate(needed):
        if time.time() > deadline:
            pending = needed[n:]
            print(f"!! budżet czasu wyczerpany — zaległe sesje: {len(pending)}", flush=True)
            break
        try:
            body = fetch_xls(d, STOCKS)
            if body is None:
                no_xls.append(d)
                time.sleep(pause)
                continue
            rows = [r for r in parse_xls(body) if r["date"] == d]
            if len(rows) < MIN_ROWS:
                raise ValueError(f"archiwum akcji: tylko {len(rows)} wierszy z datą {d}")
            for r in rows:
                tic = isin2tic.get(r["isin"])
                if not tic:
                    tic = name2tic.get(r["name"])
                    if tic in wanted and ISIN.match(r["isin"]):
                        isin2tic[r["isin"]] = tic      # zapamiętujemy, by ISIN działał mimo zmiany nazwy
                b = bar(r) if tic in wanted else None
                if b:
                    rows_s.setdefault(tic, {})[d] = b[0]
                    repaired += b[1]
            time.sleep(pause)
            ibody = fetch_xls(d, INDICES)
            if ibody is None:
                warns.append(f"{d}: brak pliku indeksów")
            else:
                for r in parse_xls(ibody):
                    key = idx_by_name.get(r["name"].upper())
                    b = bar(r, index=True) if key and r["date"] == d else None
                    if b:
                        rows_i.setdefault(key, {})[d] = b[0]
            got.append(d)
            have.add(d)
            consecutive = 0
        except Exception as e:  # noqa: BLE001 — błąd jednej sesji nie zatrzymuje reszty; sesja zostaje na następny przebieg
            errors.append(f"{d}: {type(e).__name__}: {str(e)[:100]}")
            print("ERR " + errors[-1], flush=True)
            consecutive += 1
            if consecutive >= MAX_CONSECUTIVE_ERRORS:
                pending = needed[n + 1:]
                print(f"!! {consecutive} błędów z rzędu — przerywam (blokada lub awaria GPW?); zaległe sesje: {len(pending)}", flush=True)
                break
        time.sleep(pause)
        if len(got) % 25 == 24:
            flush()
    flush()
    latest = max(have) if have else None

    # 3) status i pokrycie
    last_date, n_rows, jumps = {}, {}, {}
    for tic in stocks:
        rows = load_csv(OUT / f"{tic}.csv")
        if rows:
            ds = sorted(rows)
            last_date[tic], n_rows[tic] = ds[-1], len(ds)
            for a, b in zip(ds[-60:], ds[-59:]):
                if rows[a][3] and abs(rows[b][3] / rows[a][3] - 1) > 0.30:
                    jumps.setdefault(tic, []).append([b, round((rows[b][3] / rows[a][3] - 1) * 100, 1)])
    ok = sorted(t for t, d in last_date.items() if d == latest)
    failed = {}
    for tic in stocks:
        if tic in ok:
            continue
        if tic not in known:
            failed[tic] = "nierozpoznana: brak w migawce GPW i w gpw_alias (wycofana z obrotu lub zmieniony ticker?)"
        elif tic in last_date:
            failed[tic] = f"bez obrotu w najnowszej sesji (ostatni wiersz {last_date[tic]})"
        else:
            failed[tic] = "brak danych w archiwum"
    resolvable = [t for t in stocks if t in known]
    coverage = len(ok) / len(resolvable) if resolvable else 0.0
    idx_last = {i: max(load_csv(OUT / f"_{i}.csv"), default=None) for i in indices}
    gaps = [d for d in cands if latest and d < latest and d not in have and d not in closed]
    status = {
        "run_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "source": "archiwum notowań GPW (gpw.pl)",
        "latest_session": latest, "universe": len(stocks), "resolvable": len(resolvable), "ok": len(ok),
        "coverage": round(coverage, 3), "failed": dict(sorted(failed.items())),
        "behind_latest_session": sorted(t for t, d in last_date.items() if latest and d < latest),
        "last_date": dict(sorted(last_date.items())), "rows_min": min(n_rows.values(), default=0),
        "short_history_under_200": sorted(t for t, k in n_rows.items() if k < 200),
        "indices_last_date": idx_last, "sessions_known": len(have), "sessions_fetched_now": len(got),
        "sessions_pending": len(pending), "calendar_gaps": len(gaps), "calendar_gaps_sample": gaps[-10:],
        "sessions_without_file_now": sorted(no_xls)[-10:], "repaired_bars": repaired,
        "errors": errors[:10], "warnings": warns[:10], "suspect_jumps_over_30pct": jumps,
        "snapshot_tickers": len(isin2tic),
    }
    if not only:
        save_json(OUT / "_status.json", status)
    print(f"Sesje: pobrano {len(got)}, zaległe {len(pending)}, błędy {len(errors)}; najnowsza {latest}; "
          f"spółki ok {len(ok)}/{len(resolvable)} rozpoznanych ({len(stocks)} w universe), pokrycie {coverage:.0%}; "
          f"indeksy {idx_last}; czas {time.time() - t_start:.0f}s", flush=True)
    if failed:
        print("Bez danych z najnowszej sesji:", ", ".join(f"{t} ({r[:28]})" for t, r in sorted(failed.items())[:25]), flush=True)
    if jumps:
        print("Skoki >30% dziennie (split? zdarzenie?):", json.dumps(jumps, ensure_ascii=False)[:400], flush=True)
    fresh = latest is not None and (today - dt.date.fromisoformat(latest)).days <= 5
    recent_err = any(e.split(":")[0] in cands[-3:] for e in errors)
    return 0 if (fresh and coverage >= MIN_COVERAGE and not recent_err) or only else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
