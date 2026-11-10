"""Pęd: momentum przekrojowe akcji (kupuj siłę względną). Sygnał raz w miesiącu.

Reguła: z płynnych spółek (mediana obrotu z 60 sesji co najmniej 500 tys. zł) bierzemy te, których kurs skorygowany o dywidendy
rośnie najmocniej w ostatnich 12 miesiącach z pominięciem ostatniego (ranking 12-1), pod warunkiem że kurs leży nad średnią
z 200 sesji. Portfel: 12 spółek o równych wagach, histereza (spółka zostaje, dopóki jest w czołowej 25), maksymalnie 3 spółki
z jednego sektora (banki i pozostałe instytucje finansowe liczą się razem). Gdy Kompas pokazuje gotówkę, nowe pozycje mają połowę wielkości.
"""
import datetime as dt

from . import kompas, lib

SLUG = "ped"
KIND = "targets"
MONTHS = set(range(1, 13))
N, KEEP_RANK, SECTOR_CAP, MIN_TURNOVER = 12, 25, 3, 500_000


def evaluate(ctx, S, held):
    ok, bad = lib.screen(ctx, S, MIN_TURNOVER)
    d = dt.date.fromisoformat(S)
    t1, t3, t6, t12 = (lib.iso(lib.add_months(d, -k)) for k in (1, 3, 6, 12))
    rows = []
    for tic, info in ok.items():
        s = info["ser"]
        mom = lib.price_ret(s, t12, t1)
        if mom is None:
            bad[tic] = "history"
            continue
        k = s.n(S)
        hi = max(s.a[max(0, k - 252):k])
        sma200 = lib.sma(s, S, 200)
        rows.append({"tic": tic, "ser": s, "mom": mom, "r6": lib.price_ret(s, t6, S), "r3": lib.price_ret(s, t3, S),
                     "dist": s.a[k - 1] / hi - 1, "sma200": sma200, "above": bool(sma200 and s.a[k - 1] > sma200),
                     "close": s.c[k - 1], "turn": info["turn"]})
    rows.sort(key=lambda r: -r["mom"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    chosen, skipped = lib.pick(rows, held, N, None, KEEP_RANK, SECTOR_CAP, lambda x: x["above"], lambda t: lib.limit_sector(ctx.sector(t)))
    return rows, chosen, skipped, bad


def _t(lang, pl, en):
    return en if lang == "en" else pl


def build_md(ctx, S, rows, chosen, skipped, bad, held, risk_on, prev, initial, lang):
    L = lambda pl, en: _t(lang, pl, en)
    p = lambda x, d=1: lib.pct(x, d, True, lang)
    names = ctx.names()
    cset = {c["tic"] for c in chosen}
    title = f"# {L('Pęd', 'Momentum')} — {L('sygnał po sesji', 'signal after the session of')} {lib.weekday(S, lang)} {lib.date_pl(S, lang)}"
    intro = L(
        f"Dane: notowania {len(ctx.tickers)} spółek z archiwum GPW ({len(ctx.sessions)} sesji, do {lib.date_pl(S, lang)}), ceny skorygowane o dywidendy "
        "(wypłaty z komunikatów spółek). Uniwersum: spółki z medianą obrotu z 60 sesji co najmniej 0,5 mln zł dziennie. Ranking 12-1: zwrot od 12 miesięcy do 1 miesiąca temu "
        "(ostatni miesiąc pomijamy). Sektory: uproszczona klasyfikacja własna; do limitu banki i pozostałe instytucje finansowe liczą się razem.",
        f"Data: quotes of {len(ctx.tickers)} stocks from the GPW archive ({len(ctx.sessions)} sessions, through {lib.date_pl(S, lang)}), prices adjusted for dividends "
        "(payouts from company announcements). Universe: stocks with a 60-session median turnover of at least PLN 0.5m a day. 12-1 ranking: return from 12 months to 1 month ago "
        "(the latest month is skipped). Sectors: a simplified in-house classification; banks and other financial institutions count together towards the limit.")
    if initial:
        intro += L(" **Raport startowy:** pierwszy skład portfela wirtualnego, poza cyklem miesięcznym (kolejne: ostatnia sesja każdego miesiąca).",
                   " **Starting report:** the first holdings of the virtual portfolio, outside the monthly cycle (next ones: the last session of each month).")
    new = [c for c in chosen if c["tic"] not in held]
    keep = [c for c in chosen if c["tic"] in held]
    out = [t for t in held if t not in cset]
    if risk_on is False:
        regime = L("**Reżim: ostrożnie.** Kompas pokazuje gotówkę, więc nowe pozycje mają połowę zwykłej wielkości.",
                   "**Regime: cautious.** Compass shows cash, so new positions are half the usual size.")
    elif risk_on is None:
        regime = L("Reżim: brak danych z Kompasu, nowe pozycje w pełnej wielkości.", "Regime: no Compass data, new positions at full size.")
    else:
        regime = L("Reżim: sprzyjający (Kompas jest w akcjach), nowe pozycje w pełnej wielkości.", "Regime: supportive (Compass is in equities), new positions at full size.")
    verdict = L(f"**Docelowy skład: {lib.count_stocks(len(chosen), 'pl')}** ({len(new)} nowych, {len(keep)} zostaje, {len(out)} wypada).",
                f"**Target holdings: {lib.count_stocks(len(chosen), 'en')}** ({len(new)} new, {len(keep)} kept, {len(out)} dropped).")
    head = ["#", "Tic", L("Spółka", "Company"), L("Sektor", "Sector"), L("Kurs", "Price"), L("Mom. 12-1", "Mom. 12-1"), "6M",
            L("Od maks. 52T", "From 52w high"), L("Kurs vs SMA200", "Price vs SMA200"), L("Obrót (mln zł)", "Turnover (PLN m)"), "Status"]
    def row(r, status):
        return [r["rank"], r["tic"], names.get(r["tic"], r["tic"]), lib.sector_name(ctx.sector(r["tic"]), lang), lib.px(r["close"], lang), p(r["mom"]),
                p(r["r6"]), p(r["dist"]), p(r["ser"].a[r["ser"].n(S) - 1] / r["sma200"] - 1 if r["sma200"] else None), lib.num(r["turn"] / 1e6, 1, lang), status]
    body = [row(c, L("nowa", "new") if c["tic"] not in held else L("zostaje", "kept")) for c in chosen]
    top = []
    for r in rows[:25]:
        if r["tic"] in cset:
            st = L("w portfelu", "in portfolio")
        elif skipped.get(r["tic"]) == "filter" or not r["above"]:
            st = L("poniżej SMA200", "below SMA200")
        elif skipped.get(r["tic"]) == "sector":
            st = L("limit sektora", "sector limit")
        else:
            st = L("poza portfelem", "not selected")
        top.append(row(r, st))
    drop_rows = []
    rk = {r["tic"]: r for r in rows}
    for t in out:
        r = rk.get(t)
        if r is None:
            why = L("poza uniwersum (płynność lub dane)", "outside the universe (liquidity or data)")
        elif not r["above"]:
            why = L("kurs poniżej SMA200", "price below SMA200")
        elif r["rank"] > KEEP_RANK:
            why = L(f"ranking spadł do {r['rank']}. miejsca (próg {KEEP_RANK})", f"rank fell to {r['rank']} (threshold {KEEP_RANK})")
        else:
            why = L("limit sektora", "sector limit")
        drop_rows.append([t, names.get(t, t), why])
    funnel = L(f"Lejek: {len(ctx.tickers)} spółek w uniwersum → {len(rows) + sum(1 for v in bad.values() if v == 'history')} z płynnością i danymi → "
               f"{len(rows)} z pełnym rankingiem 12-1 → {sum(1 for r in rows if r['above'])} nad SMA200 → {len(chosen)} w portfelu.",
               f"Funnel: {len(ctx.tickers)} stocks in the universe → {len(rows) + sum(1 for v in bad.values() if v == 'history')} with liquidity and data → "
               f"{len(rows)} with a full 12-1 ranking → {sum(1 for r in rows if r['above'])} above SMA200 → {len(chosen)} in the portfolio.")
    jumps = sorted(t for t, v in bad.items() if v == "jump")
    limits = [
        L("Momentum na GPW jest w badaniach słabo i niejednoznacznie udokumentowane (zob. metodologia). To sprawdzian prognoz od dnia startu, nie dowód skuteczności.",
          "Momentum on the GPW is weakly and ambiguously documented in research (see methodology). This is a forward check from the start date, not proof of effectiveness."),
        L("Uniwersum to dzisiejsza lista spółek (bez wycofanych z obrotu), więc nie nadaje się do testów wstecznych bez korekty o survivorship bias.",
          "The universe is today's list of stocks (without delisted ones), so it is unsuitable for backtests without a survivorship-bias correction."),
        L("Korekta o dywidendy opiera się na zebranych przez nas datach i kwotach wypłat; brakujące wpisy zaniżają zwrot spółek dywidendowych.",
          "The dividend adjustment relies on the payout dates and amounts we have collected; missing entries understate the return of dividend payers."),
    ]
    if jumps:
        limits.append(L(f"Pominięte z powodu dziennego skoku powyżej 30% w ostatnich 12 miesiącach (możliwy split): {', '.join(jumps)}.",
                        f"Skipped because of a daily jump above 30% in the last 12 months (possible split): {', '.join(jumps)}."))
    note = lib.rank_gap_note(chosen, lang)
    gap = [note, ""] if note else []
    disc = L("Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.", "Screening exercise under the given framework, not investment advice.")
    md = [title, "", intro, "", "## " + L("Sygnał", "Signal"), "", verdict, "", regime, "", funnel, "",
          "## " + L("Portfel docelowy", "Target portfolio"), "", lib.md_table(head, body), ""] + gap + ["<!-- chart -->", ""]
    if drop_rows:
        md += ["## " + L("Wypadają z portfela", "Dropped from the portfolio"), "", lib.md_table(["Tic", L("Spółka", "Company"), L("Powód", "Reason")], drop_rows), ""]
    md += ["## " + L("Ranking 12-1 (25 najlepszych)", "12-1 ranking (top 25)"), "", lib.md_table(head, top), "",
           "## " + L("Ograniczenia", "Limitations"), ""] + ["- " + x for x in limits] + ["", disc, ""]
    return "\n".join(md)


def signal(ctx, S, prev, initial=False, st=None):
    held = {t["tic"] for t in (prev or {}).get("targets", [])}
    rows, chosen, skipped, bad = evaluate(ctx, S, held)
    risk_on = kompas.regime(ctx, S)
    factor = 0.5 if risk_on is False else 1.0
    names = ctx.names()
    targets = [{"tic": c["tic"], "name": names.get(c["tic"], c["tic"]), "weight": 1.0, "sector": ctx.sector(c["tic"])} for c in chosen]
    cset = {c["tic"] for c in chosen}
    out = [t for t in held if t not in cset]
    return {
        "date": S, "initial": initial, "targets": targets, "size_factor": factor, "chips": [c["tic"] for c in chosen[:6]],
        "headline": {"pl": f"{lib.count_stocks(len(chosen), 'pl')}, najsilniejsze: {', '.join(c['tic'] for c in chosen[:3])}",
                     "en": f"{lib.count_stocks(len(chosen), 'en')}, strongest: {', '.join(c['tic'] for c in chosen[:3])}"},
        "why": {"pl": "Sygnał Pędu", "en": "Momentum signal"},
        "exit_reasons": {t: {"pl": "wypadła z rankingu Pędu", "en": "dropped from the Momentum ranking"} for t in out},
        "md": {lang: build_md(ctx, S, rows, chosen, skipped, bad, held, risk_on, prev, initial, lang) for lang in ("pl", "en")},
        "chart": {"unit": "%", "rows": [[c["tic"], round(c["mom"] * 100, 1)] for c in chosen],
                  "title": {"pl": "Momentum 12-1 spółek w portfelu", "en": "12-1 momentum of portfolio stocks"},
                  "sub": {"pl": "Zwrot od 12 do 1 miesiąca temu, ceny skorygowane o dywidendy.", "en": "Return from 12 to 1 month ago, dividend-adjusted prices."}},
        "data": {"ranked": len(rows), "eligible": len(rows)},
    }
