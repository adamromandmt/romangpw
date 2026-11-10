"""Wspólne narzędzia strategii uzupełniających (Kompas, Pęd, Złoty Środek, Przystań, Dryf).

Źródłem są te same notowania co w skanerze swing: data/market/<TIC>.csv (surowe ceny z archiwum GPW) i wskaźniki cenowe
data/market/_<INDEKS>.csv. Dywidendy z data/dividends/raw_*.csv służą do korekty cen (stopa zwrotu z dywidendami)
oraz do księgowania dywidend w portfelach wirtualnych. Nic tu nie sięga do sieci.
"""
import bisect
import calendar
import datetime as dt
import json
import math
import statistics
from pathlib import Path

import dividends
import quotes

ROOT = Path(__file__).resolve().parent.parent
STRAT_DIR = ROOT / "strategie"          # raporty i dane strategii: strategie/<slug>/...
PAPER_DIR = ROOT / "paper"               # stan portfeli: paper/<slug>/state.json
DATA = ROOT / "data"

# Wskaźniki cenowe z archiwum GPW; benchmark portfeli to WIG20 (cenowy, bez dywidend).
BENCH = "WIG20"
PRICE_STATUSES = {"wypłacona", "uchwalona"}   # dywidendy faktycznie uchwalone lub wypłacone

# Robocza, uproszczona klasyfikacja sektorów (data/sectors.json): kod -> (polska nazwa, angielska nazwa).
SECTORS = {
    "banki": ("Banki", "Banks"),
    "fin": ("Finanse i ubezpieczenia", "Financials and insurance"),
    "energia": ("Energetyka", "Power utilities"),
    "paliwa": ("Paliwa", "Oil and fuels"),
    "chemia": ("Chemia", "Chemicals"),
    "surowce": ("Surowce i górnictwo", "Mining and metals"),
    "budownictwo": ("Budownictwo i materiały", "Construction and materials"),
    "deweloperzy": ("Deweloperzy i nieruchomości", "Real estate and developers"),
    "handel": ("Handel i e-commerce", "Retail and e-commerce"),
    "konsumpcyjne": ("Dobra konsumpcyjne i żywność", "Consumer goods and food"),
    "it": ("IT i oprogramowanie", "IT and software"),
    "gry": ("Gry", "Gaming"),
    "medyczne": ("Farmacja i medycyna", "Healthcare and pharma"),
    "media": ("Media i telekomunikacja", "Media and telecom"),
    "przemysl": ("Przemysł", "Industrials"),
    "motoryzacja": ("Motoryzacja", "Automotive"),
    "transport": ("Transport i turystyka", "Transport and travel"),
    "uslugi": ("Usługi", "Services"),
    "inne": ("Inne / bez klasyfikacji", "Other / unclassified"),
}
# Sektory wrażliwe regulacyjnie (limit ekspozycji w Złotym Środku).
REGULATED = {"banki", "fin", "energia", "paliwa"}


def sector_name(code, lang="pl"):
    return SECTORS.get(code, SECTORS["inne"])[0 if lang == "pl" else 1]


# ------------------------------------------------------------------ drobne narzędzia

def load_json(path, default):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def add_months(d, k):
    """Data przesunięta o k miesięcy (k może być ujemne); dzień obcięty do długości miesiąca."""
    m = d.month - 1 + k
    y, m = d.year + m // 12, m % 12 + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def iso(d):
    return d.isoformat() if isinstance(d, dt.date) else d


def due_signal_dates(sessions, months, last_done):
    """Daty sygnałów: ostatnie sesje miesięcy z `months`, które są już zamknięte (w danych jest późniejszy miesiąc),
    późniejsze niż `last_done`. `sessions` kończy się na bieżącej sesji."""
    last_of_month = {}
    for d in sessions:
        last_of_month[d[:7]] = d
    keys = sorted(last_of_month)[:-1]            # ostatni miesiąc w danych jest jeszcze otwarty
    return [last_of_month[k] for k in keys if int(k[5:7]) in months and (last_done is None or last_of_month[k] > last_done)]


# ------------------------------------------------------------------ serie notowań

class Ser:
    """Notowania jednego instrumentu: surowe świece oraz zamknięcie skorygowane o dywidendy (a)."""

    def __init__(self, tic, rows, div_events=()):
        self.tic = tic
        self.d = [r["date"] for r in rows]
        self.o = [r["open"] for r in rows]
        self.h = [r["high"] for r in rows]
        self.l = [r["low"] for r in rows]
        self.c = [r["close"] for r in rows]
        self.v = [r["volume"] for r in rows]
        self.a = list(self.c)
        self.ex = {}                              # data odcięcia (pierwsza sesja po dniu z prawem) -> dywidenda na akcję
        for cum, dps in div_events:
            i = bisect.bisect_right(self.d, cum.isoformat())      # pierwszy wiersz po dniu z prawem do dywidendy
            if i <= 0 or i >= len(self.d) or not dps or dps <= 0:
                continue
            ref = self.c[i - 1]
            if ref <= 0 or dps >= ref:
                continue
            self.ex[self.d[i]] = self.ex.get(self.d[i], 0.0) + dps
            f = 1 - dps / ref
            for j in range(i):
                self.a[j] *= f

    def __len__(self):
        return len(self.d)

    def n(self, day):
        """Liczba świec o dacie <= day."""
        return bisect.bisect_right(self.d, day)

    def i(self, day):
        """Indeks ostatniej świecy <= day albo None."""
        k = bisect.bisect_right(self.d, day) - 1
        return k if k >= 0 else None

    def at(self, day, field="a"):
        k = self.i(day)
        return getattr(self, field)[k] if k is not None else None

    def index_of(self, day):
        """Indeks świecy dokładnie z tą datą albo None."""
        k = bisect.bisect_left(self.d, day)
        return k if k < len(self.d) and self.d[k] == day else None


class Ctx:
    """Zestaw danych dla jednego przebiegu: kalendarz sesji, akcje, indeksy, dywidendy i sektory (przycięte do `asof`)."""

    def __init__(self, asof=None, tickers=None):
        self.indices = {}
        for name in ("WIG20", "MWIG40", "SWIG80", "WIG"):
            rows = quotes.read_csv(quotes.MARKET / f"_{name}.csv")
            if rows:
                self.indices[name] = Ser(name, rows)
        dates = sorted({d for s in self.indices.values() for d in s.d})
        if asof:
            dates = [d for d in dates if d <= asof]
        self.sessions = dates
        self.asof = dates[-1] if dates else None
        self.div = {}
        try:
            for ev in dividends.load_events():
                if ev["cum"] and ev["dps"] and ev["status"] in PRICE_STATUSES:
                    self.div.setdefault(ev["tic"], []).append((ev["cum"], ev["dps"]))
        except OSError:
            pass
        if tickers is None:
            tickers = load_json(DATA / "universe.json", {}).get("stocks", [])
        self.tickers = list(tickers)
        self.sectors = load_json(DATA / "sectors.json", {})
        self.exclude = set(load_json(STRAT_DIR / "wykluczenia.json", {}).get("tickers", []))
        self._stocks = {}

    def stock(self, tic):
        if tic not in self._stocks:
            rows = quotes.load(tic)
            if rows and self.asof:
                rows = [r for r in rows if r["date"] <= self.asof]
            self._stocks[tic] = Ser(tic, rows, self.div.get(tic, ())) if rows else None
        return self._stocks[tic]

    def ser(self, tic):
        """Akcja albo indeks (np. WIG20) po symbolu."""
        return self.indices.get(tic) or self.stock(tic)

    def sector(self, tic):
        return self.sectors.get(tic, "inne")

    def names(self):
        """Ticker -> nazwa GPW (z _names.json), do czytelnych tabel."""
        if not hasattr(self, "_names"):
            raw = load_json(quotes.MARKET / "_names.json", {"name": {}})["name"]
            self._names = {}
            for nm, tic in raw.items():
                self._names.setdefault(tic, nm)
        return self._names


# ------------------------------------------------------------------ metryki

def price_ret(s, day0, day1, field="a", tol_days=10):
    """Stopa zwrotu między ostatnimi cenami z dni <= day0 i <= day1. None, gdy historia nie sięga day0 (z tolerancją)."""
    if not s or not s.d:
        return None
    first = dt.date.fromisoformat(s.d[0])
    if first > dt.date.fromisoformat(day0) + dt.timedelta(days=tol_days):
        return None
    p0, p1 = s.at(day0, field), s.at(day1, field)
    if not p0 or not p1 or p0 <= 0:
        return None
    return p1 / p0 - 1


def sma(s, day, n, field="a"):
    k = s.n(day)
    if k < n:
        return None
    vals = getattr(s, field)[k - n:k]
    return sum(vals) / n


def month_end_closes(s, day, months):
    """Zamknięcia z ostatnich sesji `months` miesięcy kalendarzowych kończących się na `day` (bieżący miesiąc = cena z `day`)."""
    k = s.n(day)
    last = {}
    for j in range(k):
        last[s.d[j][:7]] = s.c[j]
    keys = sorted(last)[-months:]
    return [last[x] for x in keys]


def vol_annual(s, day, master, nret=250, min_ret=200):
    """Roczna zmienność (odchylenie standardowe dziennych logarytmicznych zwrotów × √252) z ostatnich `nret` sesji.
    Liczymy tylko zwroty między kolejnymi sesjami giełdowymi (dzień bez obrotu przerywa serię, nie daje zerowego zwrotu)."""
    k = s.n(day)
    pos = {d: j for j, d in enumerate(master)}
    rets = []
    for j in range(max(1, k - nret), k):
        pj, pp = pos.get(s.d[j]), pos.get(s.d[j - 1])
        if pj is None or pp is None or pj - pp != 1 or s.a[j - 1] <= 0 or s.a[j] <= 0:
            continue
        rets.append(math.log(s.a[j] / s.a[j - 1]))
    if len(rets) < min_ret:
        return None
    return statistics.stdev(rets) * math.sqrt(252)


def median_turnover(s, day, n=60):
    k = s.n(day)
    if k < max(10, n // 2):
        return None
    xs = [s.c[j] * s.v[j] for j in range(max(0, k - n), k)]
    return statistics.median(xs)


def presence(s, day, master, n=120):
    """Udział sesji z ostatnich n sesji kalendarza, w których instrument miał świecę (miara płynności i „nieskostniałych" cen)."""
    ms = [d for d in master if d <= day][-n:]
    if not ms:
        return 0.0
    have = set(s.d[max(0, s.n(day) - n - 5):s.n(day)])
    return sum(1 for d in ms if d in have) / len(ms)


def max_jump(s, day, nbars=260):
    """Największa dzienna zmiana skorygowanego zamknięcia (wartość bezwzględna) w ostatnich nbars świecach: wykrywa splity i szoki."""
    k = s.n(day)
    best = 0.0
    for j in range(max(1, k - nbars), k):
        if s.a[j - 1] > 0:
            best = max(best, abs(s.a[j] / s.a[j - 1] - 1))
    return best


def pct(x, d=1, sign=True, lang="pl"):
    """Procent z minusem typograficznym: 0.1234 -> '+12,3%'."""
    if x is None:
        return "—"
    v = round(x * 100, d) + 0.0                # +0.0 zamienia −0,0 na 0,0
    s = f"{v:.{d}f}" if v == 0 else (f"{v:+.{d}f}" if sign else f"{v:.{d}f}")    # zero bez znaku (bez „−0,0%")
    s = s.replace("-", "−")
    return (s if lang == "en" else s.replace(".", ",")) + "%"


def num(x, d=2, lang="pl"):
    """Liczba z separatorem tysięcy i przecinkiem (PL) albo kropką (EN)."""
    if x is None:
        return "—"
    s = f"{x:,.{d}f}"
    return s if lang == "en" else s.replace(",", " ").replace(".", ",")


def px(x, lang="pl"):
    if x is None:
        return "—"
    return num(x, 0 if abs(x) >= 1000 else 2, lang)


def date_pl(day, lang="pl"):
    """6 listopada 2026 / 6 November 2026."""
    d = dt.date.fromisoformat(day)
    if lang == "en":
        mn = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        return f"{d.day} {mn[d.month - 1]} {d.year}"
    mn = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "września", "października", "listopada", "grudnia"]
    return f"{d.day} {mn[d.month - 1]} {d.year}"


def weekday(day, lang="pl"):
    d = dt.date.fromisoformat(day)
    return (["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] if lang == "en"
            else ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"])[d.weekday()]


def count_stocks(n, lang="pl"):
    """„1 spółka", „2 spółki", „5 spółek" / „1 stock", „2 stocks"."""
    if lang == "en":
        return f"{n} stock" + ("" if n == 1 else "s")
    if n == 1:
        return "1 spółka"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} spółki"
    return f"{n} spółek"


def md_table(head, rows):
    """Tabela Markdown; znaki | w komórkach są zastępowane."""
    esc = lambda x: str(x).replace("|", "/")
    out = ["| " + " | ".join(esc(h) for h in head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def max_drawdown(s, day, nbars=252):
    """Największy spadek od szczytu (liczba ujemna) skorygowanego zamknięcia w ostatnich nbars świecach."""
    k = s.n(day)
    peak, dd = 0.0, 0.0
    for v in s.a[max(0, k - nbars):k]:
        peak = max(peak, v)
        if peak > 0:
            dd = min(dd, v / peak - 1)
    return dd


# ------------------------------------------------------------------ przesiew uniwersum (wspólny dla Pędu i Przystani)

REASONS = {
    "manual": ("wykluczona ręcznie (strategie/wykluczenia.json)", "excluded manually (strategie/wykluczenia.json)"),
    "no_data": ("brak notowań w ostatnich 10 dniach", "no quotes in the last 10 days"),
    "history": ("za krótka historia notowań", "history too short"),
    "illiquid": ("zbyt niski obrót", "turnover too low"),
    "sparse": ("rzadkie notowania (mało sesji z obrotem)", "sparse trading (few sessions with turnover)"),
    "jump": ("skok dzienny powyżej 30% w oknie (split lub szok)", "daily jump above 30% in the window (split or shock)"),
    "drawdown": ("maksymalne obsunięcie z 12 miesięcy głębsze niż 30%", "12-month maximum drawdown deeper than 30%"),
}


def screen(ctx, S, min_turnover, months=12, min_presence=0.9, max_jump_pct=0.30):
    """Przesiew płynności i jakości danych. Zwraca (ok, bad): ok = {tic: {"ser", "turn"}}, bad = {tic: kod powodu z REASONS}."""
    master = [d for d in ctx.sessions if d <= S]
    t0 = iso(add_months(dt.date.fromisoformat(S), -months))
    cutoff = iso(dt.date.fromisoformat(S) - dt.timedelta(days=10))
    ok, bad = {}, {}
    for tic in ctx.tickers:
        if tic in ctx.exclude:
            bad[tic] = "manual"
            continue
        s = ctx.stock(tic)
        k = s.n(S) if s else 0
        if not s or k == 0 or s.d[k - 1] < cutoff:
            bad[tic] = "no_data"
            continue
        if dt.date.fromisoformat(s.d[0]) > dt.date.fromisoformat(t0) + dt.timedelta(days=10):
            bad[tic] = "history"
            continue
        turn = median_turnover(s, S)
        if turn is None or turn < min_turnover:
            bad[tic] = "illiquid"
            continue
        if presence(s, S, master) < min_presence:
            bad[tic] = "sparse"
            continue
        if max_jump(s, S) > max_jump_pct:
            bad[tic] = "jump"
            continue
        ok[tic] = {"ser": s, "turn": turn}
    return ok, bad


def pick(ranked, held, n, entry_rank, keep_rank, cap, ok_fn, sector_of, group_of=None, group_cap=None):
    """Wybór składu z rankingu (lista słowników z kluczami tic i rank): najpierw zostają dotychczasowe pozycje, które nadal
    są w czołowych `keep_rank` i spełniają ok_fn (histereza), potem uzupełniamy najlepszymi z rankingu do `n`.
    Limit `cap` spółek na sektor (sektor „inne" bez limitu); opcjonalnie limit `group_cap` spółek łącznie w grupie
    (group_of(tic) zwraca nazwę grupy albo None, np. sektory wrażliwe regulacyjnie). Zwraca (wybrane wg rankingu, powody pominięcia {tic: kod})."""
    chosen, count, gcount, skipped = [], {}, {}, {}

    def room(x):
        sec = sector_of(x["tic"])
        if sec != "inne" and count.get(sec, 0) >= cap:
            return False
        g = group_of(x["tic"]) if group_of else None
        return not (g and group_cap is not None and gcount.get(g, 0) >= group_cap)

    def add(x):
        chosen.append(x)
        sec = sector_of(x["tic"])
        count[sec] = count.get(sec, 0) + 1
        g = group_of(x["tic"]) if group_of else None
        if g:
            gcount[g] = gcount.get(g, 0) + 1

    for x in ranked:
        if len(chosen) < n and x["tic"] in held and x["rank"] <= keep_rank and ok_fn(x) and room(x):
            add(x)
    names = {x["tic"] for x in chosen}
    for x in ranked:
        if len(chosen) >= n:
            break
        if x["tic"] in names or (entry_rank is not None and x["rank"] > entry_rank):
            continue
        if not ok_fn(x):
            skipped[x["tic"]] = "filter"
        elif not room(x):
            skipped[x["tic"]] = "sector"
        else:
            add(x)
            names.add(x["tic"])
    chosen.sort(key=lambda x: x["rank"])
    return chosen, skipped
