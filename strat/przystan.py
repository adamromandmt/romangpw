"""Przystań: niska zmienność (defensywny portfel akcji). Sygnał raz na kwartał.

Reguła: z płynnych spółek (mediana obrotu z 60 sesji co najmniej 300 tys. zł, notowania w co najmniej 90% sesji, maksymalne
obsunięcie z 12 miesięcy nie głębsze niż 30% jako zastępczy bezpiecznik jakości) bierzemy dolny kwintyl rocznej zmienności
dziennych zwrotów (ceny skorygowane o dywidendy). Portfel: do 16 spółek o równych wagach,
histereza (spółka zostaje, dopóki jest w najspokojniejszych 40% uniwersum), maksymalnie 4 spółki z jednego sektora (25%).
Brak filtra jakości z danych fundamentalnych (nie ma ich w repozytorium); lista ręcznych wykluczeń: strategie/wykluczenia.json.
"""
import datetime as dt
import math
import statistics

from . import lib

SLUG = "przystan"
KIND = "targets"
MONTHS = {3, 6, 9, 12}
N, SECTOR_CAP, MIN_TURNOVER, MAX_DD = 16, 4, 300_000, -0.30


def evaluate(ctx, S, held):
    ok, bad = lib.screen(ctx, S, MIN_TURNOVER)
    master = [d for d in ctx.sessions if d <= S]
    d = dt.date.fromisoformat(S)
    t12 = lib.iso(lib.add_months(d, -12))
    rows = []
    for tic, info in ok.items():
        s = info["ser"]
        vol = lib.vol_annual(s, S, master)
        if vol is None:
            bad[tic] = "sparse"
            continue
        dd = lib.max_drawdown(s, S)
        if dd < MAX_DD:
            bad[tic] = "drawdown"
            continue
        rows.append({"tic": tic, "ser": s, "vol": vol, "r12": lib.price_ret(s, t12, S), "dd": dd,
                     "close": s.c[s.n(S) - 1], "turn": info["turn"]})
    rows.sort(key=lambda r: r["vol"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    quint = max(1, math.ceil(len(rows) * 0.2))
    keep = max(quint, math.ceil(len(rows) * 0.4))
    chosen, skipped = lib.pick(rows, held, N, quint, keep, SECTOR_CAP, lambda x: True, ctx.sector)
    return rows, chosen, skipped, bad, quint, keep


def _t(lang, pl, en):
    return en if lang == "en" else pl


def build_md(ctx, S, rows, chosen, skipped, bad, quint, keep, held, prev, initial, lang):
    L = lambda pl, en: _t(lang, pl, en)
    p = lambda x, d=1: lib.pct(x, d, True, lang)
    names = ctx.names()
    cset = {c["tic"] for c in chosen}
    title = f"# {L('Przystań', 'Harbor')} — {L('sygnał po sesji', 'signal after the session of')} {lib.weekday(S, lang)} {lib.date_pl(S, lang)}"
    intro = L(
        f"Dane: notowania {len(ctx.tickers)} spółek z archiwum GPW ({len(ctx.sessions)} sesji, do {lib.date_pl(S, lang)}), ceny skorygowane o dywidendy. "
        "Zmienność roczna = odchylenie standardowe dziennych zwrotów z ostatnich ok. 250 sesji × √252. Uniwersum: mediana obrotu z 60 sesji co najmniej 0,3 mln zł dziennie, "
        "notowania w co najmniej 90% sesji (spółki rzadko notowane mają sztucznie niską zmienność), maksymalne obsunięcie z 12 miesięcy nie głębsze niż 30% (zastępczy bezpiecznik jakości).",
        f"Data: quotes of {len(ctx.tickers)} stocks from the GPW archive ({len(ctx.sessions)} sessions, through {lib.date_pl(S, lang)}), prices adjusted for dividends. "
        "Annual volatility = standard deviation of daily returns over the last ~250 sessions × √252. Universe: 60-session median turnover of at least PLN 0.3m a day, "
        "quoted in at least 90% of sessions (rarely traded stocks have artificially low volatility), 12-month maximum drawdown no deeper than 30% (a stand-in quality safeguard).")
    if initial:
        intro += L(" **Raport startowy:** pierwszy skład portfela wirtualnego, poza cyklem kwartalnym (kolejne: ostatnia sesja marca, czerwca, września i grudnia).",
                   " **Starting report:** the first holdings of the virtual portfolio, outside the quarterly cycle (next ones: the last session of March, June, September and December).")
    new = [c for c in chosen if c["tic"] not in held]
    out = [t for t in held if t not in cset]
    med_all = statistics.median(r["vol"] for r in rows) if rows else None
    avg_sel = statistics.mean(c["vol"] for c in chosen) if chosen else None
    verdict = L(f"**Docelowy skład: {lib.count_stocks(len(chosen), 'pl')}** ({len(new)} nowych, {len(chosen) - len(new)} zostaje, {len(out)} wypada). "
                f"Średnia zmienność portfela {p(avg_sel, 1).lstrip('+')} wobec mediany uniwersum {p(med_all, 1).lstrip('+')}.",
                f"**Target holdings: {lib.count_stocks(len(chosen), 'en')}** ({len(new)} new, {len(chosen) - len(new)} kept, {len(out)} dropped). "
                f"Average portfolio volatility {p(avg_sel, 1).lstrip('+')} versus the universe median {p(med_all, 1).lstrip('+')}.")
    funnel = L(f"Lejek: {len(ctx.tickers)} spółek w uniwersum → {len(rows)} z płynnością i danymi → najspokojniejszy kwintyl to pierwsze {quint} pozycji "
               f"(próg zostawania: {keep}) → {len(chosen)} w portfelu.",
               f"Funnel: {len(ctx.tickers)} stocks in the universe → {len(rows)} with liquidity and data → the calmest quintile is the first {quint} names "
               f"(retention threshold: {keep}) → {len(chosen)} in the portfolio.")
    head = ["#", "Tic", L("Spółka", "Company"), L("Sektor", "Sector"), L("Kurs", "Price"), L("Zmienność roczna", "Annual volatility"), L("Zwrot 12M", "12M return"),
            L("Maks. obsunięcie 12M", "Max drawdown 12M"), L("Obrót (mln zł)", "Turnover (PLN m)"), "Status"]
    def row(r, status):
        return [r["rank"], r["tic"], names.get(r["tic"], r["tic"]), lib.sector_name(ctx.sector(r["tic"]), lang), lib.px(r["close"], lang),
                p(r["vol"], 1).lstrip("+"), p(r["r12"]), p(r["dd"]), lib.num(r["turn"] / 1e6, 1, lang), status]
    body = [row(c, L("nowa", "new") if c["tic"] not in held else L("zostaje", "kept")) for c in chosen]
    top = []
    for r in rows[:min(len(rows), max(quint + 5, 25))]:
        if r["tic"] in cset:
            st = L("w portfelu", "in portfolio")
        elif skipped.get(r["tic"]) == "sector":
            st = L("pominięta: limit sektora", "skipped: sector limit")
        elif r["rank"] > quint:
            st = L("poza kwintylem", "outside the quintile")
        else:
            st = L("poza portfelem", "not selected")
        top.append(row(r, st))
    rk = {r["tic"]: r for r in rows}
    drop_rows = []
    for t in out:
        r = rk.get(t)
        why = (L("poza uniwersum (płynność lub dane)", "outside the universe (liquidity or data)") if r is None else
               L(f"zmienność spadła w rankingu na {r['rank']}. miejsce (próg {keep})", f"volatility rank fell to {r['rank']} (threshold {keep})") if r["rank"] > keep else
               L("limit sektora", "sector limit"))
        drop_rows.append([t, names.get(t, t), why])
    limits = [
        L("Niska zmienność nie gwarantuje wyniku lepszego od WIG20TR; główna korzyść to niższe ryzyko, a w silnych hossach portfel zostaje w tyle (zob. metodologia).",
          "Low volatility does not guarantee beating the WIG20TR; the main benefit is lower risk, and in strong bull markets the portfolio lags (see methodology)."),
        L("Brak filtra jakości z danych fundamentalnych (zysk, kapitał własny, zadłużenie): w repozytorium ich nie ma. Zastępuje go tylko limit obsunięcia (30%), więc spółka o niskiej zmienności może być spółką w kłopotach.",
          "No quality filter from fundamental data (earnings, equity, debt): the repository has none. Only the drawdown cap (30%) stands in, so a low-volatility stock can be a stock in trouble."),
        L("Spółki w wezwaniu lub przymusowym wykupie mają sztucznie niską zmienność: dopisz je do strategie/wykluczenia.json.",
          "Stocks under a tender offer or squeeze-out have artificially low volatility: add them to strategie/wykluczenia.json."),
        L("Zmienność liczona z ok. roku danych (nie 3 lat jak w badaniach), więc ranking jest mniej stabilny.",
          "Volatility is computed from about a year of data (not 3 years as in research), so the ranking is less stable."),
    ]
    disc = L("Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.", "Screening exercise under the given framework, not investment advice.")
    md = [title, "", intro, "", "## " + L("Sygnał", "Signal"), "", verdict, "", funnel, "",
          "## " + L("Portfel docelowy", "Target portfolio"), "", lib.md_table(head, body), "", "<!-- chart -->", ""]
    if drop_rows:
        md += ["## " + L("Wypadają z portfela", "Dropped from the portfolio"), "", lib.md_table(["Tic", L("Spółka", "Company"), L("Powód", "Reason")], drop_rows), ""]
    md += ["## " + L("Najspokojniejsze spółki", "Calmest stocks"), "", lib.md_table(head, top), "",
           "## " + L("Ograniczenia", "Limitations"), ""] + ["- " + x for x in limits] + ["", disc, ""]
    return "\n".join(md)


def signal(ctx, S, prev, initial=False, st=None):
    held = {t["tic"] for t in (prev or {}).get("targets", [])}
    rows, chosen, skipped, bad, quint, keep = evaluate(ctx, S, held)
    names = ctx.names()
    targets = [{"tic": c["tic"], "name": names.get(c["tic"], c["tic"]), "weight": 1.0, "sector": ctx.sector(c["tic"])} for c in chosen]
    cset = {c["tic"] for c in chosen}
    out = [t for t in held if t not in cset]
    return {
        "date": S, "initial": initial, "targets": targets, "size_factor": 1.0, "chips": [c["tic"] for c in chosen[:6]],
        "headline": {"pl": f"{lib.count_stocks(len(chosen), 'pl')} o najniższej zmienności: {', '.join(c['tic'] for c in chosen[:3])}…",
                     "en": f"{lib.count_stocks(len(chosen), 'en')} with the lowest volatility: {', '.join(c['tic'] for c in chosen[:3])}…"},
        "why": {"pl": "Sygnał Przystani", "en": "Harbor signal"},
        "exit_reasons": {t: {"pl": "wypadła z listy niskiej zmienności", "en": "dropped from the low-volatility list"} for t in out},
        "md": {lang: build_md(ctx, S, rows, chosen, skipped, bad, quint, keep, held, prev, initial, lang) for lang in ("pl", "en")},
        "chart": {"unit": "%", "rows": [[c["tic"], round(c["vol"] * 100, 1)] for c in chosen],
                  "title": {"pl": "Roczna zmienność spółek w portfelu", "en": "Annual volatility of portfolio stocks"},
                  "sub": {"pl": "Odchylenie standardowe dziennych zwrotów × √252; im niżej, tym spokojniej.", "en": "Standard deviation of daily returns × √252; the lower, the calmer."}},
        "data": {"eligible": len(rows), "quintile": quint},
    }
