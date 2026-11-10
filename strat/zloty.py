"""Złoty Środek: jakość + wycena (wskaźnik Piotroskiego, zyskowność brutto Novy-Marksa i wycena EV/EBIT w duchu Magic Formula).
Sygnał dwa razy w roku, na koniec maja i października. Model czyta tylko roczne sprawozdania, więc sygnał październikowy odświeża głównie wycenę.

Dane fundamentalne czyta z data/fundamentals.csv (roczne sprawozdania spółek niefinansowych, kwoty w tys. zł, `shares` w sztukach).
Repozytorium nie dostarcza ich samo: plik wypełnia się osobno (zob. METHOD-ZLOTY-SRODEK.md). Bez danych strategia zostaje w gotówce
i raport mówi to wprost. Banki i ubezpieczyciele są poza zakresem tej wersji (potrzebują innych mierników).

Reguła: z niefinansowych spółek o wystarczającej płynności bierzemy te z F-score co najmniej 7 (dodatni zysk, przepływ operacyjny,
poprawa zyskowności i płynności, brak emisji akcji), dodatnim wolnym przepływem pieniężnym i długiem netto do EBITDA nie wyższym niż 3.
Ranking: suma pozycji w rankingu EV/EBIT (im taniej, tym lepiej) i zyskowności brutto do aktywów (im wyżej, tym lepiej).
Portfel: 20 spółek o równych wagach, histereza (zostaje przy F-score co najmniej 5, długu netto do EBITDA do 4 i miejscu w czołowych 30),
maksymalnie 4 spółki z sektora i 8 łącznie z sektorów wrażliwych regulacyjnie (energetyka, paliwa).
"""
import csv
import datetime as dt

from . import lib

SLUG = "zloty-srodek"
KIND = "targets"
MONTHS = {5, 10}
N, SECTOR_CAP, REG_CAP, MIN_TURNOVER, KEEP_RANK = 20, 4, 8, 300_000, 30
F_ENTRY, F_HOLD, ND_ENTRY, ND_HOLD = 7, 5, 3.0, 4.0
EXCLUDED_SECTORS = {"banki", "fin"}
FUND_PATH = lib.DATA / "fundamentals.csv"
FIELDS = ["tic", "fy", "period_end", "published", "revenue", "gross_profit", "ebit", "ebitda", "net_income", "cfo", "capex",
          "total_assets", "equity", "current_assets", "current_liabilities", "debt", "cash", "shares", "source"]
NUMERIC = FIELDS[4:-1]
NEED = ["revenue", "gross_profit", "ebit", "ebitda", "net_income", "cfo", "capex", "total_assets", "equity",
        "current_assets", "current_liabilities", "debt", "cash", "shares"]


def load_fundamentals(path=None):
    """{tic: {rok_obrotowy: wiersz}} z pliku CSV; puste pola numeryczne to None. Brak pliku to pusty wynik."""
    p = path or FUND_PATH
    out = {}
    try:
        with open(p, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                tic, fy = (r.get("tic") or "").strip(), (r.get("fy") or "").strip()
                if not tic or not fy.isdigit():
                    continue
                row = {"tic": tic, "fy": int(fy), "period_end": (r.get("period_end") or "").strip(), "published": (r.get("published") or "").strip(),
                       "source": (r.get("source") or "").strip()}
                for k in NUMERIC:
                    v = (r.get(k) or "").strip().replace(" ", "").replace(",", ".")
                    try:
                        row[k] = float(v) if v else None
                    except ValueError:
                        row[k] = None
                out.setdefault(tic, {})[row["fy"]] = row
    except OSError:
        pass
    return out


def available_from(row):
    """Od kiedy wolno użyć sprawozdania (ochrona przed wyprzedzaniem): data publikacji albo koniec okresu + 120 dni."""
    if row.get("published"):
        return row["published"]
    end = row.get("period_end") or f"{row['fy']}-12-31"
    try:
        return (dt.date.fromisoformat(end) + dt.timedelta(days=120)).isoformat()
    except ValueError:
        return f"{row['fy'] + 1}-05-01"


def metrics(cur, prv, price):
    """Wskaźniki z dwóch kolejnych lat (cur, prv) i ceny. None, gdy brakuje danych albo wskaźników nie da się policzyć."""
    if any(cur.get(k) is None for k in NEED) or any(prv.get(k) is None for k in NEED):
        return None
    ta, pta = cur["total_assets"], prv["total_assets"]
    if min(ta, pta, cur["revenue"], prv["revenue"], cur["current_liabilities"], prv["current_liabilities"], cur["shares"]) <= 0:
        return None
    roa, proa = cur["net_income"] / ta, prv["net_income"] / pta
    tests = {
        "roa": roa > 0, "cfo": cur["cfo"] > 0, "droa": roa > proa, "accrual": cur["cfo"] / ta > roa,
        "lever": cur["debt"] / ta < prv["debt"] / pta,
        "liquid": cur["current_assets"] / cur["current_liabilities"] > prv["current_assets"] / prv["current_liabilities"],
        "shares": cur["shares"] <= prv["shares"] * 1.005,
        "margin": cur["gross_profit"] / cur["revenue"] > prv["gross_profit"] / prv["revenue"],
        "turn": cur["revenue"] / ta > prv["revenue"] / pta,
    }
    nd = cur["debt"] - cur["cash"]
    nd_ebitda = 0.0 if nd <= 0 else (nd / cur["ebitda"] if cur["ebitda"] > 0 else None)
    mcap = price * cur["shares"] / 1000.0
    ev = mcap + nd
    return {"f": sum(tests.values()), "tests": tests, "fcf": cur["cfo"] - cur["capex"], "nd_ebitda": nd_ebitda, "mcap": mcap, "ev": ev,
            "ev_ebit": ev / cur["ebit"] if cur["ebit"] > 0 and ev > 0 else None, "gpa": cur["gross_profit"] / ta, "equity": cur["equity"],
            "fy": cur["fy"]}


def evaluate(ctx, S, held, fund=None):
    """Zwraca (rows, chosen, skipped, info). rows: uszeregowane spółki z kompletem wskaźników; info: liczniki lejka i powody odrzuceń."""
    fund = load_fundamentals() if fund is None else fund
    info = {"universe": len(ctx.tickers), "with_data": 0, "financial": 0, "liquid": 0, "complete": 0, "rankable": 0, "pass_entry": 0, "fund_rows": sum(len(v) for v in fund.values())}
    ok, bad = lib.screen(ctx, S, MIN_TURNOVER)
    rows = []
    for tic in ctx.tickers:
        years = {fy: r for fy, r in fund.get(tic, {}).items() if available_from(r) <= S}
        if not years:
            continue
        info["with_data"] += 1
        if ctx.sector(tic) in EXCLUDED_SECTORS:
            info["financial"] += 1
            continue
        if tic not in ok:
            continue
        info["liquid"] += 1
        fy = max(years)
        if fy - 1 not in years:
            continue
        s = ok[tic]["ser"]
        price = s.c[s.n(S) - 1]
        m = metrics(years[fy], years[fy - 1], price)
        if m is None:
            continue
        info["complete"] += 1
        if m["ev_ebit"] is None or m["equity"] <= 0:
            continue
        info["rankable"] += 1
        div12 = sum(d for cum, d in ctx.div.get(tic, ()) if S >= cum.isoformat() > lib.iso(dt.date.fromisoformat(S) - dt.timedelta(days=365)))
        rows.append({"tic": tic, "price": price, "turn": ok[tic]["turn"], "div_yield": div12 / price if price else None, **m})
    ev_rank = {r["tic"]: i for i, r in enumerate(sorted(rows, key=lambda r: r["ev_ebit"]), 1)}
    gp_rank = {r["tic"]: i for i, r in enumerate(sorted(rows, key=lambda r: -r["gpa"]), 1)}
    for r in rows:
        r["score"] = ev_rank[r["tic"]] + gp_rank[r["tic"]]
        r["ok_new"] = r["f"] >= F_ENTRY and r["fcf"] > 0 and r["nd_ebitda"] is not None and r["nd_ebitda"] <= ND_ENTRY
        r["ok_hold"] = r["f"] >= F_HOLD and r["nd_ebitda"] is not None and r["nd_ebitda"] <= ND_HOLD
    rows.sort(key=lambda r: (r["score"], -r["f"], r["ev_ebit"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    info["pass_entry"] = sum(1 for r in rows if r["ok_new"])
    reg = lambda tic: "reg" if ctx.sector(tic) in lib.REGULATED else None
    chosen, skipped = lib.pick(rows, held, N, None, KEEP_RANK, SECTOR_CAP, lambda x: x["ok_hold"] if x["tic"] in held else x["ok_new"],
                               ctx.sector, group_of=reg, group_cap=REG_CAP)
    return rows, chosen, skipped, info


def _t(lang, pl, en):
    return en if lang == "en" else pl


def build_md(ctx, S, rows, chosen, skipped, info, held, carried, initial, lang):
    L = lambda pl, en: _t(lang, pl, en)
    p = lambda x, d=1: lib.pct(x, d, True, lang)
    names = ctx.names()
    cset = {c["tic"] for c in chosen}
    title = f"# {L('Złoty Środek', 'Golden Mean')} — {L('sygnał po sesji', 'signal after the session of')} {lib.weekday(S, lang)} {lib.date_pl(S, lang)}"
    intro = L(
        "Dane: notowania z archiwum GPW oraz roczne sprawozdania spółek niefinansowych z pliku data/fundamentals.csv (kwoty w tys. zł). Sprawozdanie liczy się dopiero od dnia "
        "publikacji (bez wyprzedzania). Banki i ubezpieczyciele są poza zakresem tej wersji. Sektory: robocza klasyfikacja własna (data/sectors.json).",
        "Data: quotes from the GPW archive and annual statements of non-financial companies from data/fundamentals.csv (amounts in PLN thousand). A statement counts only from its "
        "publication date (no look-ahead). Banks and insurers are outside the scope of this version. Sectors: a rough in-house classification (data/sectors.json).")
    if initial:
        intro += L(" **Raport startowy:** pierwszy sygnał portfela wirtualnego, poza cyklem półrocznym (kolejne: ostatnia sesja maja i października).",
                   " **Starting report:** the first signal of the virtual portfolio, outside the half-yearly cycle (next ones: the last session of May and October).")
    disc = L("Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.", "Screening exercise under the given framework, not investment advice.")
    limits = [
        L("Najtrudniejsza strategia do zautomatyzowania: wymaga danych fundamentalnych, które w repozytorium wypełnia się osobno i które trzeba sprawdzać ręcznie.",
          "The hardest strategy to automate: it needs fundamental data that is filled in separately in the repository and must be checked by hand."),
        L("Bank i ubezpieczyciel nie są oceniani (potrzebują P/B, ROE i buforów kapitałowych), a bonus za zwrot dla akcjonariuszy (dywidendy i skupy) nie wchodzi do rankingu: kolumna dywidendy jest informacyjna.",
          "Banks and insurers are not assessed (they need P/B, ROE and capital buffers), and the shareholder-yield bonus (dividends and buybacks) is not in the ranking: the dividend column is informational."),
        L("Tanie spółki bywają tanie z powodów politycznych lub regulacyjnych (pułapki wartości); limit 8 spółek z sektorów wrażliwych regulacyjnie jest tylko częściową ochroną.",
          "Cheap stocks are often cheap for political or regulatory reasons (value traps); the cap of 8 stocks from regulation-sensitive sectors is only partial protection."),
        L("Model czyta tylko roczne sprawozdania, więc sygnał październikowy odświeża głównie wycenę (kurs), a nie jakość; wyniki półroczne nie wchodzą do ocen.",
          "The model reads annual statements only, so the October signal mainly refreshes the valuation (the price), not the quality; half-year results do not enter the assessment."),
        L("Rzadki rebalans (dwa razy w roku) oznacza długie trwanie w złym reżimie. Nie ma testu wstecznego na danych GPW.",
          "A rare rebalance (twice a year) means a long time in a bad regime. There is no backtest on GPW data."),
    ]
    if not rows and not carried:
        verdict = L("**Czeka na dane fundamentalne.** Plik data/fundamentals.csv nie zawiera sprawozdań dostępnych na ten dzień, więc strategia nie wskazuje spółek, a portfel wirtualny pozostaje w gotówce.",
                    "**Waiting for fundamental data.** data/fundamentals.csv holds no statements available on this date, so the strategy names no stocks and the virtual portfolio stays in cash.")
        how = [L("Jak dostarczyć dane: patrz METHOD-ZLOTY-SRODEK.md (kolumny, jednostki, zasada daty publikacji). Po uzupełnieniu pliku uruchom `python3 -m strat daily --only zloty-srodek --force`.",
                 "How to supply data: see METHOD-ZLOTY-SRODEK.md (columns, units, the publication-date rule). After filling the file run `python3 -m strat daily --only zloty-srodek --force`.")]
        md = [title, "", intro, "", "## " + L("Sygnał", "Signal"), "", verdict, "", "## " + L("Co dalej", "What next"), ""] + ["- " + x for x in how]
        md += ["", "## " + L("Ograniczenia", "Limitations"), ""] + ["- " + x for x in limits] + ["", disc, ""]
        return "\n".join(md)
    if carried:
        verdict = L("**Brak świeżych danych fundamentalnych:** zostaje poprzedni skład portfela bez zmian.",
                    "**No fresh fundamental data:** the previous holdings stay unchanged.")
        md = [title, "", intro, "", "## " + L("Sygnał", "Signal"), "", verdict, "", "## " + L("Ograniczenia", "Limitations"), ""]
        md += ["- " + x for x in limits] + ["", disc, ""]
        return "\n".join(md)
    new = [c for c in chosen if c["tic"] not in held]
    out = [t for t in held if t not in cset]
    verdict = L(f"**Docelowy skład: {lib.count_stocks(len(chosen), 'pl')}** ({len(new)} nowych, {len(chosen) - len(new)} zostaje, {len(out)} wypada).",
                f"**Target holdings: {lib.count_stocks(len(chosen), 'en')}** ({len(new)} new, {len(chosen) - len(new)} kept, {len(out)} dropped).")
    funnel = L(f"Lejek: {info['universe']} spółek w uniwersum → {info['with_data']} ze sprawozdaniami → {info['with_data'] - info['financial']} niefinansowych → {info['liquid']} płynnych → "
               f"{info['complete']} z kompletem danych z dwóch lat → {info['rankable']} do rankingu → {info['pass_entry']} spełnia progi wejścia (F-score co najmniej {F_ENTRY}, FCF dodatni, dług netto/EBITDA do {ND_ENTRY:g}) → {len(chosen)} w portfelu.",
               f"Funnel: {info['universe']} stocks in the universe → {info['with_data']} with statements → {info['with_data'] - info['financial']} non-financial → {info['liquid']} liquid → "
               f"{info['complete']} with two years of complete data → {info['rankable']} rankable → {info['pass_entry']} meet the entry thresholds (F-score at least {F_ENTRY}, positive FCF, net debt/EBITDA up to {ND_ENTRY:g}) → {len(chosen)} in the portfolio.")
    head = ["#", "Tic", L("Spółka", "Company"), L("Sektor", "Sector"), L("Kurs", "Price"), "EV/EBIT", L("Zyskowność brutto / aktywa", "Gross profit / assets"), "F-score",
            L("FCF (mln zł)", "FCF (PLN m)"), L("Dług netto / EBITDA", "Net debt / EBITDA"), L("Dywidenda 12M", "Dividend 12M"), "Status"]

    def row(r, status):
        nd = "—" if r["nd_ebitda"] is None else (L("gotówka netto", "net cash") if r["nd_ebitda"] == 0 else lib.num(r["nd_ebitda"], 1, lang))
        return [r["rank"], r["tic"], names.get(r["tic"], r["tic"]), lib.sector_name(ctx.sector(r["tic"]), lang), lib.px(r["price"], lang), lib.num(r["ev_ebit"], 1, lang),
                p(r["gpa"], 1).lstrip("+"), r["f"], lib.num(r["fcf"] / 1000, 1, lang), nd, p(r["div_yield"], 1).lstrip("+") if r["div_yield"] else "—", status]
    body = [row(c, L("nowa", "new") if c["tic"] not in held else L("zostaje", "kept")) for c in chosen]
    top = []
    for r in rows[:KEEP_RANK]:
        if r["tic"] in cset:
            st = L("w portfelu", "in portfolio")
        elif skipped.get(r["tic"]) == "sector":
            st = L("pominięta: limit sektora", "skipped: sector limit")
        elif not (r["ok_hold"] if r["tic"] in held else r["ok_new"]):
            st = L("nie spełnia progów", "fails the thresholds")
        else:
            st = L("poza portfelem", "not selected")
        top.append(row(r, st))
    rk = {r["tic"]: r for r in rows}
    drop = []
    for t in out:
        r = rk.get(t)
        if r is None:
            why = L("poza rankingiem (dane lub płynność)", "outside the ranking (data or liquidity)")
        elif not r["ok_hold"]:
            why = L(f"F-score {r['f']} lub dług netto/EBITDA poza progiem utrzymania", f"F-score {r['f']} or net debt/EBITDA beyond the retention threshold")
        elif r["rank"] > KEEP_RANK:
            why = L(f"ranking spadł do {r['rank']}. miejsca (próg {KEEP_RANK})", f"rank fell to {r['rank']} (threshold {KEEP_RANK})")
        else:
            why = L("limit sektora", "sector limit")
        drop.append([t, names.get(t, t), why])
    md = [title, "", intro, "", "## " + L("Sygnał", "Signal"), "", verdict, "", funnel, "", "## " + L("Portfel docelowy", "Target portfolio"), "", lib.md_table(head, body), "", "<!-- chart -->", ""]
    if drop:
        md += ["## " + L("Wypadają z portfela", "Dropped from the portfolio"), "", lib.md_table(["Tic", L("Spółka", "Company"), L("Powód", "Reason")], drop), ""]
    md += ["## " + L(f"Ranking ({KEEP_RANK} najlepszych)", f"Ranking (top {KEEP_RANK})"), "", lib.md_table(head, top), "",
           "## " + L("Ograniczenia", "Limitations"), ""] + ["- " + x for x in limits] + ["", disc, ""]
    return "\n".join(md)


def signal(ctx, S, prev, initial=False, st=None, fund=None):
    held = {t["tic"] for t in (prev or {}).get("targets", [])}
    fund = load_fundamentals() if fund is None else fund
    rows, chosen, skipped, info = evaluate(ctx, S, held, fund)
    names = ctx.names()
    carried = not rows and bool(held)                    # brak świeżych danych: zostaje poprzedni skład
    if carried:
        targets = [t for t in prev["targets"]]
        chosen_names = [t["tic"] for t in targets]
    else:
        targets = [{"tic": c["tic"], "name": names.get(c["tic"], c["tic"]), "weight": 1.0, "sector": ctx.sector(c["tic"])} for c in chosen]
        chosen_names = [c["tic"] for c in chosen]
    cset = set(chosen_names)
    out = [t for t in held if t not in cset]
    if not rows and not carried:
        head = {"pl": "Czeka na dane fundamentalne", "en": "Waiting for fundamental data"}
    elif carried:
        head = {"pl": "Brak świeżych danych, skład bez zmian", "en": "No fresh data, holdings unchanged"}
    else:
        head = {"pl": f"{lib.count_stocks(len(chosen), 'pl')}: {', '.join(chosen_names[:3])}…", "en": f"{lib.count_stocks(len(chosen), 'en')}: {', '.join(chosen_names[:3])}…"}
    return {
        "date": S, "initial": initial, "targets": targets, "size_factor": 1.0, "chips": chosen_names[:6] or ["GOTÓWKA"], "headline": head,
        "why": {"pl": "Sygnał Złotego Środka", "en": "Golden Mean signal"},
        "exit_reasons": {t: {"pl": "wypadła z listy jakości i wyceny", "en": "dropped from the quality-and-value list"} for t in out},
        "md": {lang: build_md(ctx, S, rows, chosen, skipped, info, held, carried, initial, lang) for lang in ("pl", "en")},
        "chart": {"unit": "×", "rows": [] if carried else [[c["tic"], round(c["ev_ebit"], 1)] for c in chosen],
                  "title": {"pl": "Wycena EV/EBIT spółek w portfelu", "en": "EV/EBIT of portfolio stocks"},
                  "sub": {"pl": "Im niżej, tym taniej względem zysku operacyjnego.", "en": "The lower the bar, the cheaper relative to operating profit."}},
        "data": {"with_data": info["with_data"], "ranked": len(rows), "fund_rows": info["fund_rows"], "status": "ok" if rows else ("carried" if carried else "no_data")},
    }
