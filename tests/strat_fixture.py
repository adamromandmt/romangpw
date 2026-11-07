"""Sztuczny rynek GPW dla testów strategii uzupełniających (pakiet strat/).

Notowania to deterministyczne wzory (trend wykładniczy z drobnymi wahaniami sinusoidalnymi), bez losowości, więc wyniki są
powtarzalne. MarketCase tworzy katalog tymczasowy i podmienia ścieżki w modułach (quotes.MARKET, lib.DATA, lib.STRAT_DIR,
lib.PAPER_DIR, zloty.FUND_PATH oraz dividends.load_events), więc testy nie dotykają prawdziwych danych w repozytorium.
"""
import csv
import datetime as dt
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import dividends  # noqa: E402
import quotes  # noqa: E402
from strat import engine, lib, run, zloty  # noqa: E402


def business_days(start, end):
    """Dni od poniedziałku do piątku (bez świąt) między datami włącznie."""
    d, stop, out = dt.date.fromisoformat(start), dt.date.fromisoformat(end), []
    while d <= stop:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


SESSIONS = business_days("2025-10-23", "2026-12-03")    # 2025-10-23 jak w prawdziwym archiwum; ostatnia sesja danych 2026-12-03
LAST = "2026-11-06"                                     # ostatnia sesja pierwszego przebiegu w testach


def path(days, start=100.0, yearly=0.0, wiggle=0.0, freq=0.9, phase=0.0):
    """Zamknięcia: trend wykładniczy (yearly = zmiana na 252 sesje, np. 0,3 = +30%) razy wahania sinusoidalne (wiggle = amplituda)."""
    out = []
    for t in range(len(days)):
        trend = start * math.exp(math.log1p(yearly) * t / 252.0)
        out.append(round(trend * (1 + wiggle * math.sin(freq * t + phase)), 4))
    return out


def candles(days, closes, volume=100000.0):
    """Świece z szeregu zamknięć: otwarcie = poprzednie zamknięcie (bez luk), zakres o 0,3% szerszy niż otwarcie-zamknięcie."""
    rows, prev = [], closes[0]
    for d, c in zip(days, closes):
        rows.append({"date": d, "open": prev, "high": max(prev, c) * 1.003, "low": min(prev, c) * 0.997, "close": c, "volume": volume})
        prev = c
    return rows


def write_csv(p, rows):
    with Path(p).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "open", "high", "low", "close", "volume"])
        for r in rows:
            w.writerow([r["date"], r["open"], r["high"], r["low"], r["close"], r["volume"]])


class MarketCase(unittest.TestCase):
    """Baza testów: tymczasowy data/market z indeksami i spółkami; add_stock / add_index dopisują pliki, finish() zapisuje uniwersum."""
    days = SESSIONS

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.data, self.market = root / "data", root / "data" / "market"
        self.strat_dir, self.paper_dir = root / "strategie", root / "paper"
        for d in (self.market, self.strat_dir, self.paper_dir):
            d.mkdir(parents=True)
        self.tickers, self.sectors, self.div_events = [], {}, []
        for target, name, value in ((quotes, "MARKET", self.market), (lib, "DATA", self.data), (lib, "STRAT_DIR", self.strat_dir),
                                    (lib, "PAPER_DIR", self.paper_dir), (zloty, "FUND_PATH", self.data / "fundamentals.csv")):
            patcher = mock.patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(dividends, "load_events", side_effect=lambda: list(self.div_events))
        patcher.start()
        self.addCleanup(patcher.stop)

    def add_index(self, name, closes, days=None):
        write_csv(self.market / f"_{name}.csv", candles(days or self.days, closes, 1_000_000.0))

    def add_stock(self, tic, closes, sector=None, volume=100000.0, days=None, edit=None):
        """Dopisuje spółkę. edit = {data: {pole: wartość}} podmienia pola wybranych świec (np. luka i wolumen w dniu zdarzenia)."""
        rows = candles(days or self.days, closes, volume)
        for r in rows:
            r.update((edit or {}).get(r["date"], {}))
        write_csv(self.market / f"{tic}.csv", rows)
        self.tickers.append(tic)
        if sector:
            self.sectors[tic] = sector
        return rows

    def finish(self):
        """Zapisuje uniwersum i sektory (wywołaj po dodaniu wszystkich spółek)."""
        (self.data / "universe.json").write_text(json.dumps({"stocks": self.tickers}), encoding="utf-8")
        (self.data / "sectors.json").write_text(json.dumps(self.sectors), encoding="utf-8")

    def ctx(self, asof=LAST):
        self.finish()
        return lib.Ctx(asof)

    def three_indices(self, wig20=0.0, mwig40=0.0, swig80=0.0):
        """Trzy indeksy cenowe o podanych rocznych zmianach (trend wykładniczy z drobnymi wahaniami)."""
        for name, yearly in (("WIG20", wig20), ("MWIG40", mwig40), ("SWIG80", swig80)):
            self.add_index(name, path(self.days, 1000.0, yearly, 0.004))


class RunCase(MarketCase):
    """Rynek do testów przebiegów: trzy rosnące indeksy i 30 spółek S01..S30 (różne trendy i zmienności), 23 X 2025 - 3 XII 2026."""

    def setUp(self):
        super().setUp()
        self.three_indices(0.10, 0.20, 0.05)
        for i in range(1, 31):
            self.add_stock(f"S{i:02d}", path(self.days, 100.0, 1.0 - 0.02 * i, 0.004 + 0.001 * i))
        self.finish()

    def state(self, slug):
        return engine.load(slug)

    def report(self, slug, day, lang="pl"):
        return (self.strat_dir / slug / lang / f"{day}.md").read_text(encoding="utf-8")

    def signal(self, slug, day):
        return run.read_signal(slug, day)
