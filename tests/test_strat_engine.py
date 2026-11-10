"""Testy silnika wirtualnych portfeli strategii uzupełniających (strat/engine.py) na krótkich, ręcznie ułożonych notowaniach.

Wszystkie ceny są dobrane tak, żeby wynik dało się policzyć w głowie: koszt 0,2% od transakcji, kupno po otwarciu sesji
następującej po sygnale, sprzedaż po otwarciu, stop po cenie sprzed zdarzenia."""
import datetime as dt
import unittest

import strat_fixture as fx
from strat import engine, lib

DAYS = fx.business_days("2026-03-02", "2026-04-30")        # 43 sesje: 2 III (poniedziałek) ... 30 IV


def bars(tic, spec, start=0, div=()):
    """Seria z krotek (otwarcie, minimum, zamknięcie) od DAYS[start]; maksimum = większe z otwarcia i zamknięcia."""
    rows = [{"date": DAYS[start + i], "open": o, "high": max(o, c), "low": min(lo, o, c), "close": c, "volume": 100000.0}
            for i, (o, lo, c) in enumerate(spec)]
    return lib.Ser(tic, rows, div)


def closes(tic, values, start=0, div=()):
    """Seria bez luk: otwarcie = poprzednie zamknięcie, minimum = mniejsze z otwarcia i zamknięcia."""
    spec, prev = [], values[0]
    for c in values:
        spec.append((prev, min(prev, c), c))
        prev = c
    return bars(tic, spec, start, div)


class FakeCtx:
    """Minimalny odpowiednik strat.lib.Ctx dla silnika: kalendarz sesji, akcje, indeksy."""

    def __init__(self, series, n_sessions, bench=None):
        self.sessions = DAYS[:n_sessions]
        self.series = {s.tic: s for s in series}
        self.indices = {"WIG20": bench} if bench else {}

    def stock(self, tic):
        return self.series.get(tic)

    ser = stock


def bench_series(n, start=1000.0, step=10.0):
    return closes("WIG20", [start + step * i for i in range(n)])


def target(tic, **kw):
    return {"tic": tic, "name": tic + " SA", **kw}


WHY = {"pl": "test", "en": "test"}


class TargetsTests(unittest.TestCase):
    def setUp(self):
        # AAA: 10 zł, potem rośnie; BBB: 20 zł; CCC: 50 zł
        self.aaa = closes("AAA", [10, 10, 10, 11, 12, 12, 12, 12, 12, 12])
        self.bbb = closes("BBB", [20, 20, 20, 22, 22, 22, 22, 22, 22, 22])
        self.ccc = closes("CCC", [50] * 10)
        self.ctx = FakeCtx([self.aaa, self.bbb, self.ccc], 10, bench_series(10))

    def new(self, **cfg):
        return engine.new_state("targets", DAYS[0], 1000.0, cfg)

    def test_buys_at_next_open_with_fee_and_equal_split(self):
        st = self.new()
        engine.queue_targets(st, DAYS[1], [target("AAA"), target("BBB")], WHY)
        engine.advance(st, DAYS[1], self.ctx)
        self.assertEqual(st["positions"], [])                          # w dniu sygnału nic się nie dzieje
        engine.advance(st, DAYS[2], self.ctx)
        pos = {p["tic"]: p for p in st["positions"]}
        self.assertEqual({k: v["shares"] for k, v in pos.items()}, {"AAA": 4990, "BBB": 2495})   # 50 000 / (cena · 1,002), w dół
        self.assertEqual(pos["AAA"]["entry"], 10.0)
        self.assertEqual(pos["AAA"]["entry_date"], DAYS[2])
        self.assertAlmostEqual(st["cash"], 100000 - 4990 * 10.02 - 2495 * 20.04)
        self.assertIsNone(st["pending"])
        self.assertAlmostEqual(engine.equity(st), st["cash"] + 4990 * 10 + 2495 * 20)

    def test_weight_and_size_factor(self):
        st = self.new()
        engine.queue_targets(st, DAYS[1], [target("AAA"), target("BBB", weight=0.5)], WHY, size_factor=0.5)
        engine.advance(st, DAYS[2], self.ctx)
        pos = {p["tic"]: p["shares"] for p in st["positions"]}
        # pozycja docelowa = equity / liczba pozycji · waga · współczynnik: 50 000·0,5 = 25 000 oraz 50 000·0,5·0,5 = 12 500
        self.assertEqual(pos, {"AAA": 2495, "BBB": 623})

    def test_kept_names_are_not_topped_up_and_dropped_are_sold_at_open(self):
        st = self.new()
        engine.queue_targets(st, DAYS[1], [target("AAA"), target("BBB")], WHY)
        engine.advance(st, DAYS[3], self.ctx)
        engine.queue_targets(st, DAYS[4], [target("AAA"), target("CCC")], WHY,
                             exit_reasons={"BBB": {"pl": "słaby ranking", "en": "weak rank"}})
        engine.advance(st, DAYS[5], self.ctx)
        pos = {p["tic"]: p for p in st["positions"]}
        self.assertEqual(sorted(pos), ["AAA", "CCC"])
        self.assertEqual(pos["AAA"]["shares"], 4990)                  # AAA zostaje bez dokupienia i bez obcięcia
        sold = st["closed"][0]
        self.assertEqual((sold["tic"], sold["exit"], sold["exit_date"], sold["why_pl"], sold["why_en"]),
                         ("BBB", 22.0, DAYS[5], "słaby ranking", "weak rank"))
        proceeds = 2495 * 22 * 0.998
        self.assertAlmostEqual(sold["pnl"], proceeds - 2495 * 20.04, places=2)
        # nowa spółka dostaje tyle, ile pozwala gotówka po sprzedaży (equity/2 byłoby więcej niż gotówka, a AAA nie jest obcinana)
        cash_before = 100000 - 4990 * 10.02 - 2495 * 20.04 + proceeds
        self.assertEqual(pos["CCC"]["shares"], int(cash_before / (50 * 1.002)))

    def test_dividend_is_credited_on_ex_date_and_counts_in_pnl(self):
        aaa = closes("AAA", [10, 10, 10, 11, 12, 12, 12, 12, 12, 12], div=[(dt.date.fromisoformat(DAYS[3]), 0.5)])
        self.assertEqual(aaa.ex, {DAYS[4]: 0.5})
        ctx = FakeCtx([aaa, self.bbb], 10, bench_series(10))
        st = self.new()
        engine.queue_targets(st, DAYS[1], [target("AAA")], WHY)
        engine.advance(st, DAYS[3], ctx)
        self.assertEqual(st["positions"][0]["divs"], 0.0)
        engine.advance(st, DAYS[4], ctx)
        shares = st["positions"][0]["shares"]
        self.assertAlmostEqual(st["positions"][0]["divs"], shares * 0.5)
        engine.queue_targets(st, DAYS[5], [target("BBB")], WHY)
        engine.advance(st, DAYS[6], ctx)
        row = st["closed"][0]
        self.assertAlmostEqual(row["divs"], shares * 0.5, places=2)
        self.assertAlmostEqual(row["pnl"], shares * 12 * 0.998 + shares * 0.5 - shares * 10.02, places=2)

    def test_dividend_on_the_buy_day_is_not_credited(self):
        aaa = closes("AAA", [10, 10, 10, 11, 12, 12, 12, 12, 12, 12], div=[(dt.date.fromisoformat(DAYS[1]), 0.5)])
        self.assertEqual(aaa.ex, {DAYS[2]: 0.5})                       # odcięcie w dniu kupna po otwarciu: kupujący dywidendy nie dostaje
        st = self.new()
        engine.queue_targets(st, DAYS[1], [target("AAA")], WHY)
        engine.advance(st, DAYS[3], FakeCtx([aaa], 10))
        self.assertEqual(st["positions"][0]["divs"], 0.0)

    def test_new_signal_replaces_unexecuted_orders(self):
        st = self.new()
        engine.queue_targets(st, DAYS[1], [target("AAA")], WHY)
        engine.queue_targets(st, DAYS[1], [target("BBB")], WHY)
        self.assertEqual([t["tic"] for t in st["pending"]["targets"]], ["BBB"])
        self.assertTrue(any("zastępuje" in e["pl"] for e in st["log"]))

    def test_missing_quotes_expire_after_max_wait(self):
        late = closes("LATE", [30] * 3, start=7)                      # notowania dopiero od ósmej sesji
        ctx = FakeCtx([self.aaa, late], 10)
        st = self.new(max_wait_sessions=3)
        engine.queue_targets(st, DAYS[1], [target("AAA"), target("LATE")], WHY)
        engine.advance(st, DAYS[3], ctx)
        self.assertIsNotNone(st["pending"])                           # LATE czeka, AAA kupiona
        self.assertEqual([p["tic"] for p in st["positions"]], ["AAA"])
        engine.advance(st, DAYS[4], ctx)
        self.assertIsNone(st["pending"])                               # po trzech sesjach bez notowań zlecenie wygasa
        self.assertTrue(any("Niewykonane" in e["pl"] and "LATE" in e["pl"] for e in st["log"]))
        self.assertEqual([p["tic"] for p in st["positions"]], ["AAA"])

    def test_cash_signal_sells_everything(self):
        st = self.new()
        engine.queue_targets(st, DAYS[1], [target("AAA"), target("BBB")], WHY)
        engine.advance(st, DAYS[3], self.ctx)
        engine.queue_targets(st, DAYS[3], [], WHY)
        engine.advance(st, DAYS[4], self.ctx)
        self.assertEqual(st["positions"], [])
        self.assertEqual(len(st["closed"]), 2)
        self.assertIsNone(st["pending"])
        self.assertAlmostEqual(engine.equity(st), st["cash"])

    def test_fractional_units_for_index_strategy(self):
        st = self.new(fractional=True)
        engine.queue_targets(st, DAYS[1], [target("AAA")], WHY)
        engine.advance(st, DAYS[2], self.ctx)
        self.assertAlmostEqual(st["positions"][0]["shares"], int(100000 / 10.02 * 10000) / 10000)

    def test_equity_curve_and_benchmark_are_stored_per_session(self):
        st = self.new()
        engine.queue_targets(st, DAYS[1], [target("AAA"), target("BBB")], WHY)
        engine.advance(st, DAYS[5], self.ctx)
        self.assertEqual([e["date"] for e in st["equity"]], DAYS[:6])
        self.assertEqual(st["equity"][0]["bench"], 1000.0)             # punkt startowy
        self.assertEqual(st["equity"][5]["bench"], 1050.0)             # zamknięcie WIG20 z tego dnia
        self.assertEqual(st["processed_through"], DAYS[5])
        last = st["equity"][5]
        self.assertAlmostEqual(last["equity"], last["cash"] + last["invested"], places=2)
        engine.advance(st, DAYS[5], self.ctx)                          # ponowny przebieg niczego nie zmienia
        self.assertEqual([e["date"] for e in st["equity"]], DAYS[:6])

    def test_stats(self):
        st = self.new()
        engine.queue_targets(st, DAYS[1], [target("AAA"), target("BBB")], WHY)
        engine.advance(st, DAYS[3], self.ctx)
        engine.queue_targets(st, DAYS[3], [target("AAA")], WHY)
        engine.advance(st, DAYS[5], self.ctx)
        s = engine.stats(st)
        self.assertEqual(s["closed"], 1)
        self.assertEqual(s["win_rate"], 100.0)
        self.assertAlmostEqual(s["bench_ret"], 5.0)                    # 1000 -> 1050
        self.assertAlmostEqual(s["vs_bench"], s["ret"] - 5.0)
        self.assertAlmostEqual(s["ret"], (engine.equity(st) / 100000 - 1) * 100)
        self.assertGreaterEqual(s["max_dd"], -100.0)
        self.assertLessEqual(s["max_dd"], 0.0)
        self.assertTrue(0.0 < s["exposure"] < 100.0)
        self.assertAlmostEqual(s["cash_pct"], st["cash"] / engine.equity(st) * 100)
        self.assertAlmostEqual(s["realized"], st["closed"][0]["pnl"])

    def test_stats_of_empty_portfolio(self):
        st = self.new()
        s = engine.stats(st)
        self.assertEqual((s["ret"], s["closed"], s["win_rate"], s["exposure"], s["cash_pct"]), (0.0, 0, None, 0.0, 100.0))

    def test_warns_about_stale_position(self):
        gone = closes("GONE", [10] * 4)                                 # notowania urywają się po czterech sesjach
        ctx = FakeCtx([gone, self.aaa], 20)
        st = self.new()
        engine.queue_targets(st, DAYS[1], [target("GONE")], WHY)
        warns = engine.advance(st, DAYS[19], ctx)
        self.assertEqual(len(warns), 1)
        self.assertIn("GONE", warns[0])


class EventsTests(unittest.TestCase):
    CFG = {"position_value": 10000.0, "max_open": 10, "max_hold_sessions": 3}

    def new(self, **cfg):
        return engine.new_state("events", DAYS[0], 1000.0, {**self.CFG, **cfg})

    def order(self, st, tic="EVT", stop=9.0, day=1):
        return engine.queue_order(st, DAYS[day], tic, tic + " SA", stop, DAYS[day], "test")

    def test_buy_at_next_open_and_hold(self):
        evt = bars("EVT", [(10, 10, 10), (10, 10, 10), (10, 9.5, 11), (11, 10.5, 12), (12, 11, 12)])
        ctx = FakeCtx([evt], 5, bench_series(5))
        st = self.new()
        self.assertTrue(self.order(st))
        engine.advance(st, DAYS[1], ctx)
        self.assertEqual(st["positions"], [])
        self.assertEqual(len(st["orders"]), 1)                         # zlecenie złożone w dniu sygnału czeka na następną sesję
        engine.advance(st, DAYS[2], ctx)
        pos = st["positions"][0]
        self.assertEqual((pos["tic"], pos["shares"], pos["entry"], pos["entry_date"], pos["stop"], pos["event_date"]),
                         ("EVT", 998, 10.0, DAYS[2], 9.0, DAYS[1]))   # 10 000 / 10,02 = 998,0
        self.assertEqual(st["orders"], [])
        self.assertAlmostEqual(st["cash"], 100000 - 998 * 10.02)

    def test_intraday_stop_exits_at_stop_price(self):
        evt = bars("EVT", [(10, 10, 10), (10, 10, 10), (10, 9.5, 10), (9.6, 8.8, 9.2), (9, 9, 9)])
        st = self.new()
        self.order(st)
        engine.advance(st, DAYS[3], FakeCtx([evt], 5))
        row = st["closed"][0]
        self.assertEqual((row["exit"], row["exit_date"], row["why_pl"]), (9.0, DAYS[3], "stop (zamknięcie luki)"))
        self.assertAlmostEqual(row["pnl"], 998 * 9 * 0.998 - 998 * 10.02, places=2)
        self.assertEqual(st["positions"], [])

    def test_gap_below_stop_exits_at_open(self):
        evt = bars("EVT", [(10, 10, 10), (10, 10, 10), (10, 9.5, 10), (8.5, 8.2, 8.7), (9, 9, 9)])
        st = self.new()
        self.order(st)
        engine.advance(st, DAYS[3], FakeCtx([evt], 5))
        row = st["closed"][0]
        self.assertEqual((row["exit"], row["why_pl"], row["why_en"]), (8.5, "stop (luka)", "stop (gap)"))

    def test_order_is_cancelled_when_open_is_not_above_stop(self):
        evt = bars("EVT", [(10, 10, 10), (10, 10, 10), (8.9, 8.5, 9.4), (9.4, 9.2, 9.6)])
        st = self.new()
        self.order(st)
        engine.advance(st, DAYS[3], FakeCtx([evt], 4))
        self.assertEqual((st["positions"], st["orders"], st["closed"]), ([], [], []))
        self.assertTrue(any("anulowane" in e["pl"] for e in st["log"]))

    def test_stop_hit_on_entry_day_closes_the_same_day(self):
        evt = bars("EVT", [(10, 10, 10), (10, 10, 10), (10, 8.9, 9.5), (9.5, 9.4, 9.6)])
        st = self.new()
        self.order(st)
        engine.advance(st, DAYS[2], FakeCtx([evt], 4))
        self.assertEqual(st["positions"], [])
        row = st["closed"][0]
        self.assertEqual((row["entry_date"], row["exit_date"], row["exit"]), (DAYS[2], DAYS[2], 9.0))

    def test_time_exit_after_max_hold_sessions(self):
        evt = bars("EVT", [(10, 10, 10), (10, 10, 10), (10, 9.8, 10.5), (10.5, 10.2, 10.8), (10.8, 10.4, 11), (11, 10.9, 11.5),
                           (11.5, 11, 11.6)])
        st = self.new()
        self.order(st)
        ctx = FakeCtx([evt], 7)
        engine.advance(st, DAYS[4], ctx)
        self.assertEqual(len(st["positions"]), 1)                       # po dwóch sesjach od kupna pozycja trwa
        engine.advance(st, DAYS[5], ctx)
        self.assertEqual(st["positions"], [])
        row = st["closed"][0]
        self.assertEqual((row["exit_date"], row["exit"], row["why_pl"]), (DAYS[5], 11.5, "koniec okna (3 sesji)"))

    def test_max_open_and_duplicates(self):
        a = bars("AAA", [(10, 10, 10)] * 5)
        b = bars("BBB", [(10, 10, 10)] * 5)
        st = self.new(max_open=1)
        self.assertTrue(self.order(st, "AAA"))
        self.assertTrue(self.order(st, "BBB"))
        self.assertFalse(self.order(st, "AAA"))                       # to samo zlecenie drugi raz
        engine.advance(st, DAYS[2], FakeCtx([a, b], 5))
        self.assertEqual([p["tic"] for p in st["positions"]], ["AAA"])
        self.assertTrue(any("limit 1" in e["pl"] and "BBB" in e["pl"] for e in st["log"]))
        self.assertFalse(self.order(st, "AAA", day=3))               # spółka jest już w portfelu

    def test_share_price_above_position_value_is_not_bought(self):
        big = bars("BIG", [(20000, 20000, 20000)] * 4)
        st = self.new()
        self.order(st, "BIG", stop=18000.0)
        engine.advance(st, DAYS[2], FakeCtx([big], 4))
        self.assertEqual((st["positions"], st["orders"]), ([], []))
        self.assertTrue(any("Nie kupiono BIG" in e["pl"] for e in st["log"]))


if __name__ == "__main__":
    unittest.main()
