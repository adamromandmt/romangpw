"""Kompas: rotacja między segmentami GPW (WIG20 / mWIG40 / sWIG80) z filtrem trendu. Sygnał raz w miesiącu.

Reguła (dual momentum + filtr Fabera): spośród trzech indeksów wybieramy ten o najwyższym średnim zwrocie z 6 i 12 miesięcy
(momentum względne). Trzymamy go tylko wtedy, gdy jego kurs leży powyżej średniej z 10 ostatnich zamknięć miesięcznych
(momentum bezwzględne, filtr trendu). W przeciwnym razie gotówka. Sygnały liczymy na wskaźnikach cenowych (bez dywidend).
"""
import datetime as dt

from . import lib

SLUG = "kompas"
KIND = "targets"
MONTHS = set(range(1, 13))
CFG = {"fractional": True}          # jednostki indeksu bywają warte tysiące punktów (sWIG80 ok. 25 tys.), więc model dopuszcza ułamki
INDICES = [("WIG20", "WIG20", "ETFBW20TR"), ("MWIG40", "mWIG40", "ETFBM40TR"), ("SWIG80", "sWIG80", "ETFBS80TR")]


def evaluate(ctx, S):
    """Tabela indeksów z metrykami na dzień S i wybrana pozycja. Zwraca (rows, winner_row_or_None)."""
    rows = []
    for key, name, etf in INDICES:
        s = ctx.indices.get(key)
        if not s or s.n(S) == 0:
            continue
        d = dt.date.fromisoformat(S)
        r6 = lib.price_ret(s, lib.iso(lib.add_months(d, -6)), S, "c")
        r12 = lib.price_ret(s, lib.iso(lib.add_months(d, -12)), S, "c")
        me = lib.month_end_closes(s, S, 10)
        sma10 = sum(me) / 10 if len(me) == 10 else None
        close = s.at(S, "c")
        mom = (r6 + r12) / 2 if r6 is not None and r12 is not None else None
        rows.append({"key": key, "name": name, "etf": etf, "close": close, "r6": r6, "r12": r12, "mom": mom, "sma10": sma10,
                     "vs_sma": close / sma10 - 1 if sma10 else None, "trend_ok": bool(sma10 and close > sma10)})
    rank = sorted([r for r in rows if r["mom"] is not None], key=lambda r: -r["mom"])
    best = rank[0] if rank else None
    hold = best if best and best["trend_ok"] else None
    return rows, best, hold


def regime(ctx, S):
    """Czy Kompas jest dziś w akcjach (True) czy w gotówce (False); None, gdy brak danych. Używane jako filtr reżimu przez Pęd."""
    rows, best, hold = evaluate(ctx, S)
    if best is None:
        return None
    return hold is not None


def _t(lang, pl, en):
    return en if lang == "en" else pl


def build_md(ctx, S, rows, best, hold, prev, initial, lang):
    L = lambda pl, en: _t(lang, pl, en)
    p = lambda x: lib.pct(x, 1, True, lang)

    def rel(x):
        """Położenie kursu względem średniej z 10 zamknięć miesięcznych, słowami ('8,8% nad średnią', '5,1% pod średnią')."""
        if x is None:
            return L("za krótka historia na średnią z 10 zamknięć miesięcznych", "too little history for the 10-month average of month-end closes")
        a = lib.pct(abs(x), 1, False, lang)
        if x >= 0:
            return L(f"kurs leży {a} nad średnią z 10 zamknięć miesięcznych", f"the index sits {a} above its 10-month average of month-end closes")
        return L(f"kurs leży {a} pod średnią z 10 zamknięć miesięcznych", f"the index sits {a} below its 10-month average of month-end closes")
    title = f"# {L('Kompas', 'Compass')} — {L('sygnał po sesji', 'signal after the session of')} {lib.weekday(S, lang)} {lib.date_pl(S, lang)}"
    n = ctx.indices["WIG20"].n(S) if "WIG20" in ctx.indices else 0
    intro = L(
        f"Dane: zamknięcia wskaźników cenowych WIG20, mWIG40 i sWIG80 z archiwum GPW ({n} sesji, do {lib.date_pl(S, lang)}). "
        "Wskaźniki cenowe nie zawierają dywidend, a ETF-y na indeksy TR (np. ETFBW20TR, ETFBM40TR, ETFBS80TR) nie mają tu notowań, "
        "więc sygnał jest przybliżeniem. Gotówka w modelu nie przynosi odsetek.",
        f"Data: closing levels of the WIG20, mWIG40 and sWIG80 price indices from the GPW archive ({n} sessions, through {lib.date_pl(S, lang)}). "
        "Price indices exclude dividends, and ETFs on the TR indices (e.g. ETFBW20TR, ETFBM40TR, ETFBS80TR) have no quotes here, "
        "so the signal is an approximation. Cash earns no interest in the model.")
    if initial:
        intro += L(" **Raport startowy:** pierwszy sygnał portfela wirtualnego, poza cyklem miesięcznym (kolejne: ostatnia sesja każdego miesiąca).",
                   " **Starting report:** the first signal of the virtual portfolio, outside the monthly cycle (next ones: the last session of each month).")
    if best is None:
        verdict = L("**Brak sygnału:** za mało danych do policzenia momentum (potrzebne 12 miesięcy).",
                    "**No signal:** not enough data to compute momentum (12 months needed).")
    elif hold:
        verdict = L(f"**Pozycja: {hold['name']}.** Najwyższe średnie momentum z 6 i 12 miesięcy ({p(hold['mom'])}), {rel(hold['vs_sma'])}, "
                    f"czyli filtr trendu jest spełniony. Odpowiednik ETF (do sprawdzenia u brokera): {hold['etf']}.",
                    f"**Position: {hold['name']}.** Highest average 6- and 12-month momentum ({p(hold['mom'])}), {rel(hold['vs_sma'])}, "
                    f"so the trend filter is met. ETF counterpart (check with your broker): {hold['etf']}.")
    else:
        verdict = L(f"**Pozycja: gotówka.** Najsilniejszy indeks ({best['name']}, momentum {p(best['mom'])}) nie przechodzi filtra trendu: {rel(best['vs_sma'])}.",
                    f"**Position: cash.** The strongest index ({best['name']}, momentum {p(best['mom'])}) fails the trend filter: {rel(best['vs_sma'])}.")
    cur = hold["name"] if hold else L("gotówka", "cash")
    if prev is None:
        change = L(f"Pierwszy sygnał: {cur}. Transakcja na otwarciu najbliższej sesji.", f"First signal: {cur}. The trade is made at the next session's open.")
    else:
        was = (prev["targets"][0]["name"] if prev.get("targets") else L("gotówka", "cash"))
        if was == cur:
            change = L(f"Bez zmian względem sygnału z {lib.date_pl(prev['date'], lang)} ({cur}). Brak transakcji.",
                       f"No change versus the signal of {lib.date_pl(prev['date'], lang)} ({cur}). No trade.")
        else:
            change = L(f"Zmiana względem sygnału z {lib.date_pl(prev['date'], lang)}: {was} → {cur}. Transakcja na otwarciu najbliższej sesji.",
                       f"Change versus the signal of {lib.date_pl(prev['date'], lang)}: {was} → {cur}. The trade is made at the next session's open.")
    head = [L("Indeks", "Index"), L("Zamknięcie", "Close"), "6M", "12M", L("Momentum (śr. 6M i 12M)", "Momentum (avg 6M and 12M)"),
            L("Średnia 10 zamknięć mies.", "10-month average"), L("Kurs vs średnia", "Price vs average"), L("Filtr trendu", "Trend filter"),
            L("Decyzja", "Decision")]
    body = []
    for r in sorted(rows, key=lambda r: -(r["mom"] if r["mom"] is not None else -9)):
        dec = L("**trzymamy**", "**hold**") if hold and r["key"] == hold["key"] else (L("najsilniejszy, ale filtr nie przeszedł", "strongest, but filter failed")
                                                                                        if best and r["key"] == best["key"] else "—")
        body.append([r["name"], lib.px(r["close"], lang), p(r["r6"]), p(r["r12"]), p(r["mom"]), lib.px(r["sma10"], lang) if r["sma10"] else "—",
                     p(r["vs_sma"]), L("tak", "yes") if r["trend_ok"] else L("nie", "no"), dec])
    above = [r["name"] for r in rows if r["trend_ok"]]
    variant = L(f"Wariant Fabera (informacyjnie): powyżej 10-miesięcznej średniej są: {', '.join(above) if above else 'żaden indeks'}.",
                f"Faber variant (for information): above the 10-month average: {', '.join(above) if above else 'no index'}.")
    how = [
        L("**Momentum** to średni zwrot z ostatnich 6 i 12 miesięcy. Wygrywa segment, który rośnie najmocniej.",
          "**Momentum** is the average return over the last 6 and 12 months. The segment rising the most wins."),
        L("**Filtr trendu**: kurs musi leżeć nad średnią z 10 ostatnich zamknięć miesięcznych. Jeśli nie, zamiast akcji jest gotówka.",
          "**Trend filter**: the price must sit above the average of the last 10 month-end closes. If not, cash replaces equities."),
        L("Sygnał zmienia się rzadko i może zawieść w trendzie bocznym (kolejne fałszywe przełączenia).",
          "The signal changes rarely and can fail in a sideways market (repeated false switches)."),
    ]
    limits = [
        L("Brak notowań ETF-ów i indeksów TR w repozytorium: wynik portfela wirtualnego pomija dywidendy, a ich udział w zwrocie bywa różny w różnych segmentach, więc ranking oparty na indeksach TR mógłby wyglądać inaczej.",
          "No ETF or TR-index quotes in the repository: the virtual portfolio result omits dividends, and their share of the return can differ across segments, so a ranking based on TR indices could look different."),
        L("Historia w repozytorium to ok. roku, więc nie ma testu wstecznego tej reguły na danych GPW. To sprawdzian prognoz od dnia startu, nie dowód skuteczności.",
          "The repository holds about a year of history, so this rule has no backtest on GPW data. This is a forward check from the start date, not proof of effectiveness."),
        L("Gotówka nie przynosi odsetek (w praktyce: fundusz pieniężny lub ETF krótkoterminowych obligacji).",
          "Cash earns no interest (in practice a money-market fund or a short-term bond ETF)."),
    ]
    disc = L("Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.", "Screening exercise under the given framework, not investment advice.")
    md = [title, "", intro, "", "## " + L("Sygnał", "Signal"), "", verdict, "", change, "", "## " + L("Indeksy", "Indices"), "",
          lib.md_table(head, body), "", variant, "", "<!-- chart -->", "", "## " + L("Jak czytać", "How to read"), ""]
    md += ["- " + x for x in how] + ["", "## " + L("Ograniczenia danych", "Data limitations"), ""] + ["- " + x for x in limits] + ["", disc, ""]
    return "\n".join(md)


def signal(ctx, S, prev, initial=False, st=None):
    rows, best, hold = evaluate(ctx, S)
    targets = [{"tic": hold["key"], "name": hold["name"], "weight": 1.0}] if hold else []
    cur = {"pl": hold["name"] if hold else "gotówka", "en": hold["name"] if hold else "cash"}
    chips = [cur["pl"] if hold else "GOTÓWKA"]
    chart_rows = [[r["name"], round(r["mom"] * 100, 1)] for r in rows if r["mom"] is not None]
    return {
        "date": S, "initial": initial, "targets": targets, "chips": chips,
        "headline": {"pl": f"Pozycja: {cur['pl']}", "en": f"Position: {cur['en']}"},
        "why": {"pl": "Sygnał Kompasu", "en": "Compass signal"},
        "exit_reasons": {r["key"]: {"pl": "zmiana sygnału Kompasu", "en": "Compass signal change"} for r in rows},
        "md": {lang: build_md(ctx, S, rows, best, hold, prev, initial, lang) for lang in ("pl", "en")},
        "chart": {"unit": "%", "rows": chart_rows, "title": {"pl": "Momentum indeksów (śr. 6M i 12M)", "en": "Index momentum (avg 6M and 12M)"},
                  "sub": {"pl": "Im wyżej, tym silniejszy segment rynku.", "en": "The higher the bar, the stronger the market segment."}},
        "data": {"rows": rows},
    }
