#!/usr/bin/env python3
"""Ranking z raportu dziennego jako dane: tabela Markdown -> JSON z walidacją.

Raport (reports/RRRR-MM-DD.md) jest tym, co czyta człowiek. Tabelę rankingu parsujemy tylko tutaj, raz, do słownika
o stałym schemacie (schemas/ranking.schema.json). Korzysta z niego portfel wirtualny (paper.py), a build.py zapisuje
go obok raportu jako reports/RRRR-MM-DD.json (publiczne dane maszynowe). Walidacja wyłapuje błędy, które łatwo
przeoczyć przy ręcznym pisaniu tabeli: kolejność poziomów, sumę punktów, kolejność wierszy oraz R niezgodne
z poziomami wejście, stop i cele (R liczymy od środka strefy wejścia, a przy wejściu na wybiciu od poziomu wybicia).

Użycie:
    python3 ranking.py check reports/RRRR-MM-DD.md   # podsumowanie i problemy; kod 1, gdy są błędy
    python3 ranking.py write reports/RRRR-MM-DD.md   # to samo i zapis reports/RRRR-MM-DD.json
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

import charts

SCHEMA_VERSION = 1
R_TOLERANCE = 0.15       # R w tabeli jest zaokrąglone do 0,1, a poziomy do groszy lub złotówek
SCORE_TOLERANCE = 1.0
EARN = re.compile(r"(\d{1,2})\.(\d{2})")
PRICE_DATE = re.compile(r"\((\d{1,2})\.(\d{1,2})\)")


def _clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("**", "")).strip()


def _signed(s):
    """Pierwsza liczba z komórki wraz ze znakiem (także „−”), np. „−3,5% (…)” -> -3.5; None, gdy brak."""
    m = re.match(r"\s*([−–\-+]?)\s*(" + charts.NUM + ")", s or "")
    if not m:
        return None
    v = charts._f(m.group(2))
    return -v if m.group(1) in ("−", "–", "-") else v


def _nearest(m, ref):
    """Data dd.mm z dopasowania regexu w roku, który daje datę najbliższą referencji; None, gdy dzień/miesiąc nieprawidłowy."""
    best = None
    for y in (ref.year - 1, ref.year, ref.year + 1):
        try:
            d = dt.date(y, int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        if best is None or abs((d - ref).days) < abs((best - ref).days):
            best = d
    return best


def extract(md, report_date):
    """Dane rankingu z tekstu raportu (tabela Markdown z kolumnami Tic i Suma) -> słownik zgodny ze schemas/ranking.schema.json."""
    head, rows = charts.parse_ranking(md)
    data = {"schema": SCHEMA_VERSION, "date": report_date.isoformat(), "columns": head or [], "candidates": []}
    if not head:
        return data
    col = lambda *names, prefix=False: charts._col(head, *names, prefix=prefix)  # noqa: E731
    c_rank, c_name, c_sector = col("#"), col("Spółka", "Company"), col("Sektor", "Sector")
    c_price, c_off = col("Kurs", "Price", prefix=True), col("Od maks", "From", prefix=True)
    c_trend, c_sup, c_rsi = col("Trend"), col("Wsparcie", "Support"), col("RSI")
    c_tech, c_r = col("Tech", prefix=True), col("R") or col("R (", prefix=True)
    c_earn = col("Raport", "Earnings", prefix=True)
    c_entry = col("Wej", "Entry", prefix=True)
    for i, (it, row) in enumerate(zip(charts.build_items(head, rows), rows)):
        g = lambda c: row.get(c, "") if c else ""  # noqa: E731
        entry_cell = g(c_entry)
        entry = None
        if it["lo"] is not None and it["hi"] is not None:
            entry = {"lo": it["lo"], "hi": it["hi"], "breakout": ">" in entry_cell}
        pm = PRICE_DATE.search(g(c_price))
        pd = _nearest(pm, report_date) if pm else None
        if pd and pd > report_date:
            pd = pd.replace(year=pd.year - 1)
        em = EARN.search(g(c_earn))
        ed = _nearest(em, report_date) if em else None
        rank = g(c_rank)
        data["candidates"].append({
            "rank": int(rank) if rank.isdigit() else i + 1,
            "tic": it["tic"], "name": g(c_name) or None, "sector": g(c_sector) or None,
            "price": it["price"], "price_asof": pd.isoformat() if pd else None,
            "off_high_pct": _signed(g(c_off)), "rsi": charts._first(g(c_rsi)),
            "trend": _clean(g(c_trend)) or None, "support": _clean(g(c_sup)) or None,
            "fund": it["fund"], "tech": charts._first(g(c_tech)), "score": it["suma"],
            "class": it["kl"] or None, "class_note": _clean(re.sub(r"^\s*[ABC]\b[\s:,;—–-]*", "", g(charts._col(head, "Klasa", "Class", prefix=True)))),
            "entry": entry, "stop": it["stop"], "t1": it["c1"], "t2": it["c2"],
            "r1": it["r1"], "r2": it["r2"],
            "r_basis": "price" if re.search(r"od kursu|from (the )?price", g(c_r), re.I) else "entry",
            "earnings": ({"text": _clean(g(c_earn)), "date": ed.isoformat() if ed else None,
                          "days": (ed - report_date).days if ed else None} if g(c_earn) else None),
        })
    return data


def _pl(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def check(data):
    """Problemy w danych rankingu: lista {level: 'error'|'warning', tic, msg}. Błędy uniemożliwiają użycie rankingu."""
    out = []

    def add(level, tic, msg):
        out.append({"level": level, "tic": tic, "msg": msg})
    cands = data["candidates"]
    if not cands:
        add("error", None, "brak tabeli rankingu (potrzebne kolumny Tic i Suma) albo tabela jest pusta")
        return out
    seen, prev = set(), None
    for c in cands:
        t = c["tic"]
        if t in seen:
            add("error", t, "ticker powtórzony w rankingu")
        seen.add(t)
        s = c["score"]
        if s is None:
            add("error", t, "brak sumy punktów")
        elif not 0 <= s <= 100:
            add("error", t, f"suma punktów poza zakresem 0–100: {s:g}")
        if None not in (c["fund"], c["tech"], s) and abs(c["fund"] + c["tech"] - s) > SCORE_TOLERANCE:
            add("warning", t, f"Fund + Tech ({c['fund']:g} + {c['tech']:g}) nie równa się sumie {s:g}")
        if s is not None:
            if prev is not None and s > prev:
                add("warning", t, f"ranking nie jest posortowany malejąco po sumie ({s:g} po {prev:g})")
            prev = s
        if c["class"] is None:
            add("warning", t, "brak klasy (A/B/C)")
        e = c["entry"]
        if e is None or None in (c["stop"], c["t1"], c["t2"]):
            add("warning", t, "niekompletne poziomy (wejście, stop, C1, C2): wykresy i portfel wirtualny pominą ten wiersz")
            continue
        if not (c["stop"] < e["lo"] <= e["hi"] < c["t1"] < c["t2"]):
            add("warning", t, "poziomy nie rosną zgodnie z regułą stop < wejście < C1 < C2")
            continue
        if c["r1"] is None or c["r2"] is None:
            add("warning", t, "brak R do C1 i C2 w tabeli")
            continue
        if c["r_basis"] == "price":
            base, label = c["price"], "od kursu"
        elif e["breakout"]:
            base, label = e["lo"], f"od poziomu wybicia {e['lo']:g}"
        else:
            base, label = (e["lo"] + e["hi"]) / 2, "od środka strefy wejścia"
        if base is None or base <= c["stop"]:
            add("warning", t, "baza R (wejście lub kurs) nie leży powyżej stopu")
            continue
        r1, r2 = (c["t1"] - base) / (base - c["stop"]), (c["t2"] - base) / (base - c["stop"])
        if abs(r1 - c["r1"]) > R_TOLERANCE or abs(r2 - c["r2"]) > R_TOLERANCE:
            add("warning", t, f"R w tabeli {_pl(c['r1'])} / {_pl(c['r2'])} różni się od policzonego z poziomów ({label}): "
                              f"{_pl(r1)} / {_pl(r2)}")
    return out


def sidecar_path(md_path):
    return Path(md_path).with_suffix(".json")


def build(md_path):
    """Dane rankingu z pliku raportu o nazwie RRRR-MM-DD.md."""
    p = Path(md_path)
    return extract(p.read_text(encoding="utf-8"), dt.date.fromisoformat(p.stem))


def write_sidecar(md_path):
    """Zapisuje reports/RRRR-MM-DD.json (tylko gdy treść się zmieniła) i zwraca dane."""
    data = build(md_path)
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    out = sidecar_path(md_path)
    if not out.exists() or out.read_text(encoding="utf-8") != text:
        out.write_text(text, encoding="utf-8")
    return data


def main(argv):
    if len(argv) != 3 or argv[1] not in ("check", "write"):
        print(__doc__)
        return 2
    data = write_sidecar(argv[2]) if argv[1] == "write" else build(argv[2])
    cands = data["candidates"]
    print(f"{argv[2]}: {len(cands)} kandydatów" + (f" ({', '.join(c['tic'] for c in cands)})" if cands else ""))
    problems = check(data)
    for p in problems:
        print(f"  {'BŁĄD  ' if p['level'] == 'error' else 'uwaga '} {p['tic'] or '-':6} {p['msg']}")
    if not problems:
        print("  bez uwag")
    return 1 if any(p["level"] == "error" for p in problems) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
