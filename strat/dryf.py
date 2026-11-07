"""Dryf: zdarzenia cenowo-wolumenowe w sezonach raportowych (przybliżenie PEAD, czyli dryfu kursu po wynikach). Skan codziennie.

Reguła: w oknach publikacji raportów szukamy dnia, w którym płynna spółka (mediana obrotu z 60 sesji co najmniej 1 mln zł)
otwiera się luką co najmniej +2% względem poprzedniego zamknięcia, zamyka dzień co najmniej 4% wyżej (ruchy powyżej 30% odrzucamy
jako możliwe scalenia akcji), przy wolumenie co najmniej 2,5 raza wyższym niż mediana z poprzednich 20 sesji, a zamknięcie leży
w górnej połowie zakresu dnia. Kupno po otwarciu następnej sesji, stała kwota 10 tys. zł na spółkę (maksymalnie 10 pozycji), stop
na zamknięciu sprzed zdarzenia, wyjście po 40 sesjach. Lustrzane zdarzenia ujemne tworzą listę „nie kupuj” na 60 sesji.

Repozytorium nie ma danych o wynikach, konsensusie ani transakcjach insiderów, więc zdarzeniem jest ruch kursu i wolumenu,
a nie zaskoczenie wynikami. Progi ustawiono według częstotliwości zdarzeń w ostatnim roku (kilkanaście do kilkudziesięciu rocznie), nie według wyniku.
"""
import datetime as dt
import statistics

from . import lib

SLUG = "dryf"
KIND = "events"
MONTHS = None                       # skan codzienny, bez kalendarza rebalansu
CFG = {"position_value": 10000.0, "max_open": 10, "max_hold_sessions": 40}
GAP, RET, VOLX, CLOSE_POS, MIN_TURNOVER, MAX_RET = 0.02, 0.04, 2.5, 0.5, 1_000_000, 0.30
WINDOWS = (((2, 1), (4, 30)), ((5, 1), (5, 20)), ((8, 15), (9, 30)), ((11, 1), (11, 20)))
NOBUY = 60                          # sesji na liście „nie kupuj”
RECENT = 10                         # sesji wstecz w tabeli „ostatnie zdarzenia"


def in_window(day):
    m, d = int(day[5:7]), int(day[8:10])
    return any(a <= (m, d) <= b for a, b in WINDOWS)


def next_window_start(day):
    """Początek najbliższego okna raportowego po dniu `day` (data ISO)."""
    d0 = dt.date.fromisoformat(day)
    starts = sorted(dt.date(y, a[0], a[1]) for y in (d0.year, d0.year + 1) for a, _ in WINDOWS)
    return next(x for x in starts if x > d0).isoformat()


def day_stats(s, E, pos):
    """Metryki dnia E dla instrumentu s (Ser); pos = {data: numer sesji}. None, gdy nie da się ich policzyć."""
    k = s.index_of(E)
    if k is None or k < 21 or pos.get(s.d[k - 1]) != pos.get(E, -9) - 1:
        return None                           # brak historii albo poprzednia sesja bez notowania
    pc = s.c[k - 1]
    if pc <= 0 or s.a[k - 1] <= 0:
        return None
    vs = [x for x in s.v[k - 20:k] if x > 0]
    tv = lib.median_turnover(s, s.d[k - 1])
    if len(vs) < 10 or tv is None:
        return None
    rng = s.h[k] - s.l[k]
    return {"gap": (s.o[k] + s.ex.get(E, 0.0)) / pc - 1, "ret": s.a[k] / s.a[k - 1] - 1, "vr": s.v[k] / statistics.median(vs),
            "cp": (s.c[k] - s.l[k]) / rng if rng > 0 else 0.5, "tv": tv, "pc": pc, "open": s.o[k], "close": s.c[k]}


def classify(m):
    """'pos' (zdarzenie dodatnie), 'neg' (ujemne) albo None."""
    if m["tv"] < MIN_TURNOVER or m["vr"] < VOLX:
        return None
    if m["gap"] >= GAP and RET <= m["ret"] <= MAX_RET and m["cp"] >= CLOSE_POS:
        return "pos"
    if m["gap"] <= -GAP and -MAX_RET <= m["ret"] <= -RET and m["cp"] <= 1 - CLOSE_POS:
        return "neg"
    return None


def scan(ctx, days, windows_only=True):
    """Zdarzenia z podanych dni; wynik: lista słowników (najnowsze najpierw, w dniu wg siły ruchu)."""
    pos = {d: i for i, d in enumerate(ctx.sessions)}
    out = []
    for E in days:
        if windows_only and not in_window(E):
            continue
        for tic in ctx.tickers:
            if tic in ctx.exclude:
                continue
            s = ctx.stock(tic)
            m = day_stats(s, E, pos) if s else None
            kind = classify(m) if m else None
            if kind:
                out.append({"tic": tic, "date": E, "kind": kind, **m})
    out.sort(key=lambda e: (e["date"], abs(e["ret"])), reverse=True)
    return out


def _t(lang, pl, en):
    return en if lang == "en" else pl


def _status(e, st):
    """Co się stało ze zdarzeniem w portfelu wirtualnym (do tabeli ostatnich zdarzeń)."""
    if e["kind"] == "neg":
        return ("lista „nie kupuj”", "no-buy list")
    if any(o["tic"] == e["tic"] and o["event_date"] == e["date"] for o in st["orders"]):
        return ("zlecenie na następną sesję", "order for the next session")
    if any(p["tic"] == e["tic"] and p.get("event_date") == e["date"] for p in st["positions"]):
        return ("w portfelu", "in the portfolio")
    c = next((c for c in st["closed"] if c["tic"] == e["tic"] and c.get("event_date") == e["date"]), None)
    if c:
        return (f"zamknięta ({lib.pct(c['pnl_pct'] / 100, 1, True, 'pl')})", f"closed ({lib.pct(c['pnl_pct'] / 100, 1, True, 'en')})")
    if e["date"] < st["start_date"]:
        return ("przed startem portfela (bez zlecenia)", "before the portfolio start (no order)")
    return ("pominięta (limit pozycji lub otwarcie poniżej stopu)", "skipped (position limit or open below the stop)")


def build_md(ctx, S, today, recent, nobuy, st, initial, lang):
    L = lambda pl, en: _t(lang, pl, en)
    p = lambda x, d=1: lib.pct(x, d, True, lang)
    names = ctx.names()
    pos = {d: i for i, d in enumerate(ctx.sessions)}
    win = in_window(S)
    new_pos = [e for e in today if e["kind"] == "pos"]
    new_neg = [e for e in today if e["kind"] == "neg"]
    title = f"# {L('Dryf', 'Drift')} — {L('skan po sesji', 'scan after the session of')} {lib.weekday(S, lang)} {lib.date_pl(S, lang)}"
    vx = f"{VOLX:g}".replace(".", "," if lang == "pl" else ".")
    intro = L(
        f"Dane: notowania {len(ctx.tickers)} spółek z archiwum GPW ({len(ctx.sessions)} sesji, do {lib.date_pl(S, lang)}). Zdarzenie dodatnie: luka otwarcia co najmniej "
        f"+{GAP * 100:.0f}%, wzrost dnia od +{RET * 100:.0f}% do +{MAX_RET * 100:.0f}%, wolumen co najmniej {vx} raza wyższy niż mediana z 20 poprzednich sesji, zamknięcie w górnej połowie zakresu dnia, "
        f"mediana obrotu z 60 sesji co najmniej {MIN_TURNOVER / 1e6:g} mln zł. Zdarzenie ujemne to lustrzane odbicie. Skanujemy tylko w oknach publikacji raportów "
        "(1 lutego–30 kwietnia, 1–20 maja, 15 sierpnia–30 września, 1–20 listopada), bo bez ESPI traktujemy ruch w tych oknach jako przybliżenie reakcji na wyniki.",
        f"Data: quotes of {len(ctx.tickers)} stocks from the GPW archive ({len(ctx.sessions)} sessions, through {lib.date_pl(S, lang)}). A positive event: opening gap of at least "
        f"+{GAP * 100:.0f}%, a day gain from +{RET * 100:.0f}% to +{MAX_RET * 100:.0f}%, volume at least {vx} times the median of the previous 20 sessions, a close in the upper half of the day's range, "
        f"and a 60-session median turnover of at least PLN {MIN_TURNOVER / 1e6:g}m. A negative event is the mirror image. We scan only inside reporting windows "
        "(1 February–30 April, 1–20 May, 15 August–30 September, 1–20 November), because without ESPI data we treat a move in these windows as a proxy for the reaction to results.")
    if initial:
        intro += L(" **Raport startowy:** portfel wirtualny startuje bez pozycji; zlecenia powstają tylko po zdarzeniach z dnia sygnału.",
                   " **Starting report:** the virtual portfolio starts without positions; orders are created only after events on the signal day.")
    if win:
        window = L("Okno raportowe: **trwa** (skan aktywny).", "Reporting window: **open** (scan active).")
    else:
        window = L(f"Okno raportowe: **poza oknem**, skan wstrzymany; najbliższe okno zaczyna się {lib.date_pl(next_window_start(S), lang)}. "
                   "Otwarte pozycje są nadal prowadzone.",
                   f"Reporting window: **closed**, scan paused; the next window starts on {lib.date_pl(next_window_start(S), lang)}. Open positions are still managed.")
    if not win:
        verdict = L("**Brak skanu:** dziś poza oknem raportowym.", "**No scan:** outside a reporting window today.")
    elif new_pos or new_neg:
        verdict = L(f"**Nowe zdarzenia: {len(new_pos)} dodatnich, {len(new_neg)} ujemnych.**", f"**New events: {len(new_pos)} positive, {len(new_neg)} negative.**")
    else:
        verdict = L("**Brak nowych zdarzeń** spełniających wszystkie warunki.", "**No new events** meeting all conditions.")
    head_e = [L("Spółka", "Company"), "Tic", L("Sektor", "Sector"), L("Zmiana dnia", "Day change"), L("Luka otwarcia", "Opening gap"),
              L("Wolumen / mediana 20 sesji", "Volume / 20-session median"), L("Zamknięcie w zakresie dnia", "Close within day's range"),
              L("Obrót mediana (mln zł)", "Median turnover (PLN m)")]

    def erow(e):
        return [names.get(e["tic"], e["tic"]), e["tic"], lib.sector_name(ctx.sector(e["tic"]), lang), p(e["ret"]), p(e["gap"]),
                f"{e['vr']:.1f}×".replace(".", "," if lang == "pl" else "."), f"{e['cp'] * 100:.0f}%", lib.num(e["tv"] / 1e6, 1, lang)]

    md = [title, "", intro, "", "## " + L("Sygnał", "Signal"), "", verdict, "", window, ""]
    if new_pos:
        md += ["## " + L("Nowe zdarzenia dodatnie", "New positive events"), "",
               lib.md_table(head_e + [L("Zlecenie", "Order"), L("Stop (zamknięcie sprzed zdarzenia)", "Stop (close before the event)")],
                            [erow(e) + [L("kupno na otwarciu następnej sesji", "buy at the next session's open"), lib.px(e["pc"], lang)] for e in new_pos]), ""]
    if new_neg:
        md += ["## " + L("Nowe zdarzenia ujemne", "New negative events"), "",
               lib.md_table(head_e, [erow(e) for e in new_neg]), "",
               L("Spółki te trafiają na listę „nie kupuj” na 60 sesji (informacyjnie; skaner swing nie korzysta z tej listy automatycznie).",
                 "These stocks join the no-buy list for 60 sessions (for information; the swing scanner does not use this list automatically)."), ""]
    md += ["<!-- chart -->", ""]
    rec_rows = []
    for e in recent:
        stt = _status(e, st)
        rec_rows.append([lib.date_pl(e["date"], lang), e["tic"], names.get(e["tic"], e["tic"]), L("dodatnie", "positive") if e["kind"] == "pos" else L("ujemne", "negative"),
                         p(e["ret"]), p(e["gap"]), f"{e['vr']:.1f}×".replace(".", "," if lang == "pl" else "."), L(*stt)])
    if rec_rows:
        md += ["## " + L(f"Zdarzenia z ostatnich {RECENT} sesji", f"Events of the last {RECENT} sessions"), "",
               lib.md_table([L("Data", "Date"), "Tic", L("Spółka", "Company"), L("Rodzaj", "Type"), L("Zmiana dnia", "Day change"), L("Luka", "Gap"),
                             L("Wolumen / mediana", "Volume / median"), L("Status w portfelu", "Portfolio status")], rec_rows), ""]
    if st["positions"]:
        rows = []
        for q in sorted(st["positions"], key=lambda q: q["entry_date"]):
            held = pos.get(q["last_date"], 0) - pos.get(q["entry_date"], 0)
            rows.append([q["tic"], q["name"], lib.date_pl(q["entry_date"], lang), lib.px(q["entry"], lang), lib.px(q["stop"], lang) if q["stop"] else "—",
                         lib.px(q["last_close"], lang), p(q["last_close"] / q["entry"] - 1), f"{held} / {st['config']['max_hold_sessions']}"])
        md += ["## " + L("Otwarte pozycje", "Open positions"), "",
               lib.md_table(["Tic", L("Spółka", "Company"), L("Wejście", "Entry"), L("Kurs wejścia", "Entry price"), "Stop", L("Kurs", "Price"),
                             L("Wynik", "Result"), L("Sesje w pozycji", "Sessions held")], rows), ""]
    else:
        md += ["## " + L("Otwarte pozycje", "Open positions"), "", L("Brak otwartych pozycji.", "No open positions."), ""]
    if nobuy:
        last_idx = pos.get(S, 0)
        rows = [[e["tic"], names.get(e["tic"], e["tic"]), lib.date_pl(e["date"], lang), p(e["ret"]), p(e["gap"]),
                 f"{e['vr']:.1f}×".replace(".", "," if lang == "pl" else "."), max(0, NOBUY - (last_idx - pos.get(e["date"], 0)))] for e in nobuy]
        md += ["## " + L("Lista „nie kupuj” (zdarzenia ujemne z ostatnich 60 sesji)", "No-buy list (negative events of the last 60 sessions)"), "",
               lib.md_table(["Tic", L("Spółka", "Company"), L("Data zdarzenia", "Event date"), L("Zmiana dnia", "Day change"), L("Luka", "Gap"),
                             L("Wolumen / mediana", "Volume / median"), L("Sesji do końca listy", "Sessions left")], rows), ""]
    amt = lib.num(st["config"]["position_value"], 0, lang)
    how = [
        L("**Zdarzenie** to jeden dzień o silnym ruchu w górę na dużym wolumenie, w sezonie raportów. Nie wiemy z samych notowań, czy to wyniki; to przybliżenie.",
          "An **event** is a single day of a strong rise on heavy volume during the reporting season. Quotes alone do not tell us whether it was earnings; this is a proxy."),
        L(f"**Wejście:** kupno po otwarciu następnej sesji, stała kwota {amt} zł (maks. {st['config']['max_open']} pozycji). "
          "Zlecenie jest anulowane, gdy otwarcie leży na stopie lub poniżej niego.",
          f"**Entry:** buy at the next session's open, a fixed PLN {amt} (max {st['config']['max_open']} positions). "
          "The order is cancelled if the open is at or below the stop."),
        L(f"**Wyjście:** stop na zamknięciu sprzed zdarzenia (zamknięcie luki; gdy rynek otwiera się poniżej stopu, sprzedaż po otwarciu) albo po {st['config']['max_hold_sessions']} sesjach.",
          f"**Exit:** a stop at the close before the event (a gap fill; if the market opens below the stop, the sale is at the open) or after {st['config']['max_hold_sessions']} sessions."),
    ]
    limits = [
        L("To przybliżenie dryfu po wynikach: repozytorium nie ma danych o wynikach, konsensusie ani insiderach. Ruch w oknie raportowym może wynikać z innych wiadomości (przejęcia, plotki, zmiany indeksów).",
          "This is a proxy for post-earnings drift: the repository has no data on results, consensus or insiders. A move in a reporting window may come from other news (takeovers, rumours, index changes)."),
        L("Badania PEAD na GPW są niejednoznaczne co do strony długiej (zob. metodologia); lepiej udokumentowany jest dryf ujemny, stąd lista „nie kupuj”.",
          "PEAD research on the GPW is ambiguous about the long side (see methodology); negative drift is better documented, hence the no-buy list."),
        L("Progi ustawiono według liczby zdarzeń w ostatnim roku (około dwudziestu w oknach raportowych), nie według wyniku. Nie ma testu wstecznego.",
          "Thresholds were set by the number of events in the last year (about twenty inside reporting windows), not by results. There is no backtest."),
        L("Stop na zamknięciu sprzed zdarzenia jest odległy (równy ruchowi dnia zdarzenia), więc pojedyncza strata może być duża; stąd stała, niewielka kwota na pozycję.",
          "A stop at the close before the event is far away (equal to the event day's move), so a single loss can be large; hence the fixed, small amount per position."),
        L("Okna raportowe są przybliżeniem: kalendarza publikacji spółek nie ma w repozytorium.", "Reporting windows are an approximation: the repository has no company reporting calendar."),
    ]
    disc = L("Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.", "Screening exercise under the given framework, not investment advice.")
    md += ["## " + L("Jak czytać", "How to read"), ""] + ["- " + x for x in how]
    md += ["", "## " + L("Ograniczenia", "Limitations"), ""] + ["- " + x for x in limits] + ["", disc, ""]
    return "\n".join(md)


def signal(ctx, S, prev, initial=False, st=None):
    """Skan dnia S. `st` to stan portfela po przetworzeniu sesji S (pozycje i zlecenia do wyświetlenia)."""
    if st is None:
        from . import engine
        st = engine.new_state(KIND, S, None, CFG)
    idx = [d for d in ctx.sessions if d <= S]
    days = idx[-max(RECENT, NOBUY):]
    events = scan(ctx, days)
    today = [e for e in events if e["date"] == S]
    recent = [e for e in events if e["date"] >= (idx[-RECENT] if len(idx) >= RECENT else idx[0])]
    nobuy = [e for e in events if e["kind"] == "neg"]
    names = ctx.names()
    orders = [{"tic": e["tic"], "name": names.get(e["tic"], e["tic"]), "stop": e["pc"], "event_date": e["date"],
               "note": f"+{e['ret'] * 100:.1f}%, luka {e['gap'] * 100:+.1f}%, wolumen {e['vr']:.1f}×"} for e in today if e["kind"] == "pos"]
    n_pos = len(orders)
    n_neg = sum(1 for e in today if e["kind"] == "neg")
    if not in_window(S):
        head = {"pl": "Poza oknem raportowym, skan wstrzymany", "en": "Outside a reporting window, scan paused"}
    elif today:
        head = {"pl": f"Zdarzenia: {n_pos} dodatnich, {n_neg} ujemnych", "en": f"Events: {n_pos} positive, {n_neg} negative"}
    else:
        head = {"pl": "Brak nowych zdarzeń", "en": "No new events"}
    chips = [e["tic"] for e in today][:6] or [q["tic"] for q in st["positions"]][:6]
    chart_rows = [[f"{e['tic']} {e['date'][5:]}", round(e["ret"] * 100, 1)] for e in sorted(recent, key=lambda e: e["date"])]
    return {
        "date": S, "initial": initial, "targets": [], "orders": orders, "chips": chips, "headline": head,
        "why": {"pl": "Sygnał Dryfu", "en": "Drift signal"}, "exit_reasons": {},
        "md": {lang: build_md(ctx, S, today, recent, nobuy, st, initial, lang) for lang in ("pl", "en")},
        "chart": {"unit": "%", "rows": chart_rows, "title": {"pl": f"Zmiana dnia przy zdarzeniach z ostatnich {RECENT} sesji", "en": f"Day change on events of the last {RECENT} sessions"},
                  "sub": {"pl": "Dodatnie i ujemne zdarzenia w oknach raportowych (etykieta: ticker i data).", "en": "Positive and negative events inside reporting windows (label: ticker and date)."}},
        "data": {"in_window": in_window(S), "today": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in e.items()} for e in today],
                 "nobuy": [{"tic": e["tic"], "date": e["date"]} for e in nobuy]},
    }
