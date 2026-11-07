"""Testy wspólnych narzędzi strategii uzupełniających (strat/lib.py): formatowanie, kalendarz sygnałów, korekta o dywidendy,
wybór składu z histerezą i limitami oraz przesiew uniwersum."""
import datetime as dt
import unittest

import strat_fixture as fx
from strat import lib


def rows(closes, start="2026-01-05"):
    """Świece z samych zamknięć na kolejnych dniach roboczych."""
    days = fx.business_days(start, "2027-12-31")[:len(closes)]
    return fx.candles(days, closes)


class FormatTests(unittest.TestCase):
    def test_pct_signs_and_zero(self):
        self.assertEqual(lib.pct(0.1234), "+12,3%")
        self.assertEqual(lib.pct(-0.05), "−5,0%")                       # minus typograficzny
        self.assertEqual(lib.pct(0.0), "0,0%")
        self.assertEqual(lib.pct(-0.00001), "0,0%")                     # bez „−0,0%"
        self.assertEqual(lib.pct(0.1234, 1, False), "12,3%")
        self.assertEqual(lib.pct(0.1234, 1, True, "en"), "+12.3%")
        self.assertEqual(lib.pct(None), "—")

    def test_count_stocks_polish_plurals(self):
        pl = {0: "0 spółek", 1: "1 spółka", 2: "2 spółki", 4: "4 spółki", 5: "5 spółek", 11: "11 spółek", 12: "12 spółek",
              14: "14 spółek", 22: "22 spółki", 25: "25 spółek", 112: "112 spółek"}
        for n, text in pl.items():
            self.assertEqual(lib.count_stocks(n, "pl"), text)
        self.assertEqual([lib.count_stocks(n, "en") for n in (0, 1, 3)], ["0 stocks", "1 stock", "3 stocks"])

    def test_number_and_price_formats(self):
        self.assertEqual(lib.num(1234567.891, 1), "1 234 567,9")
        self.assertEqual(lib.num(1234567.891, 1, "en"), "1,234,567.9")
        self.assertEqual(lib.px(24160.0), "24 160")
        self.assertEqual(lib.px(12.3456), "12,35")

    def test_dates(self):
        self.assertEqual(lib.date_pl("2026-11-06"), "6 listopada 2026")
        self.assertEqual(lib.date_pl("2026-11-06", "en"), "6 November 2026")
        self.assertEqual(lib.weekday("2026-11-06"), "piątek")

    def test_md_table_escapes_pipes(self):
        self.assertEqual(lib.md_table(["A", "B"], [["x|y", 1]]), "| A | B |\n|---|---|\n| x/y | 1 |")


class CalendarTests(unittest.TestCase):
    def test_add_months_clamps_day(self):
        self.assertEqual(lib.add_months(dt.date(2026, 1, 31), 1), dt.date(2026, 2, 28))
        self.assertEqual(lib.add_months(dt.date(2026, 3, 31), -1), dt.date(2026, 2, 28))
        self.assertEqual(lib.add_months(dt.date(2026, 11, 6), -12), dt.date(2025, 11, 6))

    def test_due_signal_dates_use_closed_months_only(self):
        sessions = ["2026-09-29", "2026-09-30", "2026-10-01", "2026-10-30", "2026-11-02", "2026-11-03"]
        # listopad jest jeszcze otwarty (ostatni miesiąc w danych), więc listopadowego sygnału nie ma; wrzesień i październik są zamknięte
        self.assertEqual(lib.due_signal_dates(sessions, set(range(1, 13)), None), ["2026-09-30", "2026-10-30"])
        self.assertEqual(lib.due_signal_dates(sessions, set(range(1, 13)), "2026-09-30"), ["2026-10-30"])   # tylko późniejsze niż ostatni raport
        self.assertEqual(lib.due_signal_dates(sessions, {9}, None), ["2026-09-30"])                       # kwartały / półrocza
        self.assertEqual(lib.due_signal_dates(sessions, {5, 10}, "2026-10-30"), [])


class SeriesTests(unittest.TestCase):
    def test_dividend_adjustment_makes_return_total(self):
        r = rows([100.0, 100.0, 98.0, 98.0])
        cum = dt.date.fromisoformat(r[1]["date"])                         # dzień z prawem; odcięcie w kolejnej sesji
        s = lib.Ser("AAA", r, [(cum, 2.0)])
        self.assertEqual(s.ex, {r[2]["date"]: 2.0})
        self.assertAlmostEqual(s.a[0], 98.0)                              # ceny sprzed odcięcia pomniejszone o 2%
        self.assertAlmostEqual(s.a[3], 98.0)
        self.assertAlmostEqual(lib.price_ret(s, r[0]["date"], r[3]["date"]), 0.0)         # po korekcie spadek o dywidendę znika
        self.assertAlmostEqual(lib.price_ret(s, r[0]["date"], r[3]["date"], "c"), -0.02)  # w cenach surowych zostaje −2%

    def test_dividend_not_below_price_is_ignored_when_absurd(self):
        r = rows([10.0, 10.0, 10.0])
        s = lib.Ser("AAA", r, [(dt.date.fromisoformat(r[0]["date"]), 15.0), (dt.date.fromisoformat(r[0]["date"]), 0.0)])
        self.assertEqual(s.ex, {})
        self.assertEqual(s.a, s.c)

    def test_price_ret_needs_history(self):
        s = lib.Ser("AAA", rows([100.0, 110.0, 121.0], "2026-03-02"))
        self.assertIsNone(lib.price_ret(s, "2025-01-01", "2026-03-04"))
        self.assertAlmostEqual(lib.price_ret(s, "2026-03-02", "2026-03-04"), 0.21)

    def test_sma_drawdown_and_month_end_closes(self):
        s = lib.Ser("AAA", rows([10.0, 20.0, 10.0, 15.0, 12.0], "2026-01-28"))      # 28.01, 29.01, 30.01, 02.02, 03.02
        self.assertIsNone(lib.sma(s, "2026-02-03", 6))
        self.assertAlmostEqual(lib.sma(s, "2026-02-03", 5), 13.4)
        self.assertAlmostEqual(lib.max_drawdown(s, "2026-02-03"), -0.5)
        self.assertEqual(lib.month_end_closes(s, "2026-02-03", 2), [10.0, 12.0])      # styczeń: ostatnie zamknięcie; luty: cena z dnia
        self.assertEqual(lib.month_end_closes(s, "2026-02-03", 1), [12.0])

    def test_median_turnover_needs_enough_bars(self):
        s = lib.Ser("AAA", rows([10.0] * 8))
        self.assertIsNone(lib.median_turnover(s, s.d[-1]))
        s = lib.Ser("AAA", rows([10.0] * 40))
        self.assertAlmostEqual(lib.median_turnover(s, s.d[-1]), 10.0 * 100000.0)


class PickTests(unittest.TestCase):
    SECTOR = {"A": "banki", "B": "banki", "C": "it", "D": "inne", "E": "inne", "F": "inne"}

    def ranked(self, tics="ABCDEF"):
        return [{"tic": t, "rank": i} for i, t in enumerate(tics, 1)]

    def pick(self, held=(), n=3, entry=None, keep=5, cap=1, ok=lambda x: True, **kw):
        sector = lambda t: self.SECTOR.get(t, "inne")
        chosen, skipped = lib.pick(self.ranked(), set(held), n, entry, keep, cap, ok, sector, **kw)
        return [c["tic"] for c in chosen], skipped

    def test_sector_cap_does_not_apply_to_other(self):
        chosen, skipped = self.pick()
        self.assertEqual(chosen, ["A", "C", "D"])                  # B pominięty (limit sektora banki), „inne" bez limitu
        self.assertEqual(skipped, {"B": "sector"})
        self.assertEqual(self.pick(n=5)[0], ["A", "C", "D", "E", "F"])

    def test_hysteresis_keeps_held_inside_keep_rank(self):
        self.assertEqual(self.pick(held={"E"})[0], ["A", "C", "E"])      # E (miejsce 5 <= 5) zostaje i zajmuje miejsce
        self.assertEqual(self.pick(held={"F"})[0], ["A", "C", "D"])      # F (miejsce 6 > 5) wypada
        self.assertEqual(self.pick(held={"E"}, keep=4)[0], ["A", "C", "D"])

    def test_held_must_still_pass_filter_and_sector_room(self):
        self.assertEqual(self.pick(held={"E"}, ok=lambda x: x["tic"] != "E")[0], ["A", "C", "D"])
        chosen, _ = self.pick(held={"B", "A"}, cap=1)                    # obie z sektora banki: zostaje wyższa
        self.assertEqual(chosen, ["A", "C", "D"])

    def test_entry_rank_limits_new_names(self):
        chosen, skipped = self.pick(entry=2)
        self.assertEqual(chosen, ["A"])                                  # B odpada przez limit sektora, reszta jest za daleko
        self.assertEqual(skipped, {"B": "sector"})

    def test_filter_reason(self):
        chosen, skipped = self.pick(ok=lambda x: x["tic"] not in ("A", "D"))
        self.assertEqual(chosen, ["B", "C", "E"])
        self.assertEqual(skipped, {"A": "filter", "D": "filter"})

    def test_group_cap_for_regulated_sectors(self):
        group = lambda t: "reg" if t in ("A", "C", "D") else None
        chosen, skipped = self.pick(n=4, group_of=group, group_cap=2)
        self.assertEqual(chosen, ["A", "C", "E", "F"])                   # A i C zajmują oba miejsca grupy, D (też z grupy) odpada
        self.assertEqual(skipped, {"B": "sector", "D": "sector"})


class ScreenTests(fx.MarketCase):
    def test_reasons_for_rejection(self):
        days = self.days
        self.three_indices()
        self.add_stock("GOOD", fx.path(days, 100, 0.1, 0.01))
        self.add_stock("THIN", fx.path(days, 100, 0.1, 0.01), volume=100.0)                     # obrót ok. 10 tys. zł: za mały
        self.add_stock("SHORT", fx.path(days[150:], 100, 0.1, 0.01), days=days[150:])           # historia krótsza niż 12 miesięcy
        sparse_days = [d for i, d in enumerate(days) if i % 4 != 0]                              # świece tylko w 75% sesji
        self.add_stock("SPARSE", fx.path(sparse_days, 100, 0.1, 0.01), days=sparse_days)
        jump = fx.path(days, 100, 0.0, 0.0)
        jump = jump[:150] + [v * 1.5 for v in jump[150:]]                                       # skok o 50% w jeden dzień (np. split)
        self.add_stock("JUMP", jump)
        stale_days = days[:days.index("2026-10-01") + 1]
        self.add_stock("STALE", fx.path(stale_days, 100, 0.1, 0.01), days=stale_days)           # ostatnie notowanie sprzed ponad 10 dni
        self.add_stock("MANUAL", fx.path(days, 100, 0.1, 0.01))
        (self.strat_dir / "wykluczenia.json").write_text('{"tickers": ["MANUAL"]}', encoding="utf-8")
        ctx = self.ctx()
        ok, bad = lib.screen(ctx, fx.LAST, 500_000)
        self.assertEqual(list(ok), ["GOOD"])
        self.assertEqual(bad, {"THIN": "illiquid", "SHORT": "history", "SPARSE": "sparse", "JUMP": "jump", "STALE": "no_data",
                               "MANUAL": "manual"})
        for code in bad.values():
            self.assertIn(code, lib.REASONS)


if __name__ == "__main__":
    unittest.main()
