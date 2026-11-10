"""Testy reguł Kompasu, Pędu, Przystani i Dryfu na sztucznym rynku (tests/strat_fixture.py). Każdy test ustawia notowania tak,
żeby poprawny wynik wynikał wprost z reguły opisanej w metodologii, a nie z liczb zapisanych po obejrzeniu wyniku."""
import datetime as dt
import unittest

import strat_fixture as fx
from strat import dryf, kompas, lib, ped, przystan

DISCLAIMER_PL = "Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna."
DISCLAIMER_EN = "Screening exercise under the given framework, not investment advice."


def rise_then_fall(days, up_until, yearly, daily_fall):
    """Wzrost wykładniczy do dnia up_until, potem spadek o daily_fall na sesję (bez wahań)."""
    out, peak, n_fall = [], 1000.0, 0
    for t, d in enumerate(days):
        if d <= up_until:
            peak = 1000.0 * (1 + yearly) ** (t / 252.0)
            out.append(round(peak, 4))
        else:
            n_fall += 1
            out.append(round(peak * (1 - daily_fall) ** n_fall, 4))
    return out


class KompasTests(fx.MarketCase):
    def test_holds_the_strongest_index_when_its_trend_is_up(self):
        self.three_indices(wig20=0.10, mwig40=0.40, swig80=0.20)
        ctx = self.ctx()
        rows, best, hold = kompas.evaluate(ctx, fx.LAST)
        self.assertEqual({r["key"] for r in rows}, {"WIG20", "MWIG40", "SWIG80"})
        self.assertEqual((best["key"], hold["key"]), ("MWIG40", "MWIG40"))
        by = {r["key"]: r for r in rows}
        self.assertTrue(all(r["trend_ok"] for r in rows))                   # wszystkie rosną, więc wszystkie nad średnią
        self.assertAlmostEqual(by["MWIG40"]["mom"], (by["MWIG40"]["r6"] + by["MWIG40"]["r12"]) / 2)
        self.assertGreater(by["MWIG40"]["r12"], by["SWIG80"]["r12"])
        self.assertTrue(kompas.regime(ctx, fx.LAST))
        sig = kompas.signal(ctx, fx.LAST, None, initial=True)
        self.assertEqual(sig["targets"], [{"tic": "MWIG40", "name": "mWIG40", "weight": 1.0}])
        self.assertEqual(sig["headline"], {"pl": "Pozycja: mWIG40", "en": "Position: mWIG40"})
        self.assertTrue(sig["initial"])
        self.assertIn("Raport startowy", sig["md"]["pl"])
        self.assertIn("Starting report", sig["md"]["en"])
        self.assertIn("Kompas", sig["md"]["pl"].splitlines()[0])
        self.assertIn("Compass", sig["md"]["en"].splitlines()[0])
        for lang, text in (("pl", DISCLAIMER_PL), ("en", DISCLAIMER_EN)):
            self.assertIn(text, sig["md"][lang])
        self.assertRegex(sig["md"]["pl"], r"kurs leży \d+,\d% nad średnią z 10 zamknięć miesięcznych, czyli filtr trendu jest spełniony")
        self.assertRegex(sig["md"]["en"], r"the index sits \d+\.\d% above its 10-month average of month-end closes, so the trend filter is met")

    def test_cash_when_every_index_is_falling(self):
        self.three_indices(wig20=-0.20, mwig40=-0.10, swig80=-0.30)
        ctx = self.ctx()
        rows, best, hold = kompas.evaluate(ctx, fx.LAST)
        self.assertEqual(best["key"], "MWIG40")                              # najmniej spada, ale to nadal spadek
        self.assertIsNone(hold)
        self.assertFalse(any(r["trend_ok"] for r in rows))
        self.assertIs(kompas.regime(ctx, fx.LAST), False)
        sig = kompas.signal(ctx, fx.LAST, None)
        self.assertEqual(sig["targets"], [])
        self.assertEqual(sig["chips"], ["GOTÓWKA"])
        self.assertEqual(sig["headline"]["pl"], "Pozycja: gotówka")
        self.assertRegex(sig["md"]["pl"], r"nie przechodzi filtra trendu: kurs leży \d+,\d% pod średnią z 10 zamknięć miesięcznych\.")
        self.assertRegex(sig["md"]["en"], r"fails the trend filter: the index sits \d+\.\d% below its 10-month average of month-end closes\.")
        self.assertNotIn("względem średniej", sig["md"]["pl"])                 # bez znaku „+/−" w zdaniu: kierunek mówią słowa nad/pod

    def test_missing_average_is_explained_in_words(self):
        self.three_indices(wig20=-0.20, mwig40=-0.10, swig80=-0.30)
        ctx = self.ctx()
        rows, best, _ = kompas.evaluate(ctx, fx.LAST)
        best["vs_sma"] = None                                                # gałąź obronna: za mało zamknięć miesięcznych na średnią
        pl = kompas.build_md(ctx, fx.LAST, rows, best, None, None, False, "pl")
        en = kompas.build_md(ctx, fx.LAST, rows, best, None, None, False, "en")
        self.assertIn("nie przechodzi filtra trendu: za krótka historia na średnią z 10 zamknięć miesięcznych.", pl)
        self.assertIn("fails the trend filter: too little history for the 10-month average of month-end closes.", en)

    def test_strongest_index_below_its_average_means_cash_even_if_others_pass(self):
        self.add_index("WIG20", fx.path(self.days, 1000.0, 0.10, 0.004))
        self.add_index("MWIG40", fx.path(self.days, 1000.0, 0.20, 0.004))
        self.add_index("SWIG80", rise_then_fall(self.days, "2026-09-30", 3.0, 0.03))      # ostry wzrost, potem załamanie w ostatnich tygodniach
        ctx = self.ctx()
        rows, best, hold = kompas.evaluate(ctx, fx.LAST)
        by = {r["key"]: r for r in rows}
        self.assertEqual(best["key"], "SWIG80")                              # najwyższe średnie momentum 6M i 12M
        self.assertLess(by["SWIG80"]["vs_sma"], 0)                           # ale kurs leży pod średnią z 10 zamknięć miesięcznych
        self.assertTrue(by["WIG20"]["trend_ok"] and by["MWIG40"]["trend_ok"])
        self.assertIsNone(hold)                                              # reguła: gotówka, a nie „drugi w kolejności"
        self.assertIs(kompas.regime(ctx, fx.LAST), False)
        self.assertIn("najsilniejszy, ale filtr nie przeszedł", kompas.signal(ctx, fx.LAST, None)["md"]["pl"])

    def test_change_versus_previous_signal_is_described(self):
        self.three_indices(wig20=0.10, mwig40=0.40, swig80=0.20)
        ctx = self.ctx()
        same = kompas.signal(ctx, fx.LAST, {"date": "2026-10-30", "targets": [{"tic": "MWIG40", "name": "mWIG40"}]})
        self.assertIn("Bez zmian względem sygnału z 30 października 2026", same["md"]["pl"])
        changed = kompas.signal(ctx, fx.LAST, {"date": "2026-10-30", "targets": [{"tic": "WIG20", "name": "WIG20"}]})
        self.assertIn("WIG20 → mWIG40", changed["md"]["pl"])
        self.assertIn("WIG20 → mWIG40", changed["md"]["en"])

    def test_too_little_history_gives_no_signal(self):
        self.three_indices(wig20=0.10, mwig40=0.40, swig80=0.20)
        ctx = self.ctx("2026-03-02")                                         # ok. 90 sesji: brak 12 miesięcy historii
        rows, best, hold = kompas.evaluate(ctx, "2026-03-02")
        self.assertIsNone(best)
        self.assertIsNone(hold)
        self.assertIsNone(kompas.regime(ctx, "2026-03-02"))
        sig = kompas.signal(ctx, "2026-03-02", None)
        self.assertEqual(sig["targets"], [])
        self.assertIn("Brak sygnału", sig["md"]["pl"])


def crash_path(days, up_until, yearly, daily_fall):
    """Silny wzrost do dnia up_until, potem seria spadków po daily_fall dziennie (bez skoku powyżej 30% w jednym dniu)."""
    return rise_then_fall(days, up_until, yearly, daily_fall)


class PedTests(fx.MarketCase):
    def universe(self, wig20=0.10, mwig40=0.20, swig80=0.05):
        """CRASH (najwyższe momentum 12-1, ale po załamaniu w ostatnim miesiącu) i P01..P40 o malejącym momentum; P01-P05 to banki."""
        self.three_indices(wig20, mwig40, swig80)
        self.add_stock("CRASH", crash_path(self.days, "2026-10-06", 4.0, 0.07))
        for i in range(1, 41):
            self.add_stock(f"P{i:02d}", fx.path(self.days, 100.0, 2.0 - 0.045 * (i - 1)), sector="banki" if i <= 5 else None)
        return self.ctx()

    def test_ranking_filter_sector_cap_and_size(self):
        ctx = self.universe()
        rows, chosen, skipped, bad = ped.evaluate(ctx, fx.LAST, set())
        self.assertEqual(bad, {})
        self.assertEqual(len(rows), 41)
        self.assertEqual([r["tic"] for r in rows[:3]], ["CRASH", "P01", "P02"])           # 12-1 omija ostatni miesiąc, więc CRASH jest pierwszy
        self.assertEqual([r["rank"] for r in rows[:3]], [1, 2, 3])
        crash = rows[0]
        self.assertFalse(crash["above"])                                                  # ale kurs jest pod SMA200
        self.assertEqual(skipped["CRASH"], "filter")
        self.assertEqual(skipped["P04"], "sector")                                        # limit 3 spółek z sektora banki
        self.assertEqual(skipped["P05"], "sector")
        self.assertEqual([c["tic"] for c in chosen], ["P01", "P02", "P03"] + [f"P{i:02d}" for i in range(6, 15)])
        self.assertEqual(len(chosen), ped.N)

    def test_hysteresis_keeps_held_names_inside_rank_25(self):
        ctx = self.universe()
        rows, chosen, skipped, bad = ped.evaluate(ctx, fx.LAST, {"P20", "P30"})
        tics = [c["tic"] for c in chosen]
        self.assertIn("P20", tics)                                                        # miejsce 21 <= 25: zostaje mimo że nie weszłaby z rankingu
        self.assertNotIn("P30", tics)                                                     # miejsce 31 > 25: wypada
        self.assertEqual(len(tics), 12)
        self.assertEqual(tics, ["P01", "P02", "P03"] + [f"P{i:02d}" for i in range(6, 14)] + ["P20"])

    def test_signal_sizes_new_positions_by_compass_regime(self):
        ctx = self.universe()
        prev = {"date": "2026-09-30", "targets": [{"tic": "P30", "name": "P30"}, {"tic": "P01", "name": "P01"}]}
        sig = ped.signal(ctx, fx.LAST, prev)
        self.assertEqual(sig["size_factor"], 1.0)                                         # indeksy rosną: Kompas w akcjach
        self.assertEqual(len(sig["targets"]), 12)
        self.assertEqual(sig["targets"][0], {"tic": "P01", "name": "P01", "weight": 1.0, "sector": "banki"})
        self.assertEqual(list(sig["exit_reasons"]), ["P30"])
        self.assertIn("12 spółek", sig["headline"]["pl"])
        self.assertIn("Reżim: sprzyjający", sig["md"]["pl"])
        self.assertIn("poniżej SMA200", sig["md"]["pl"])                        # CRASH w tabeli rankingu
        self.assertIn("sector limit", sig["md"]["en"])
        for lang, text in (("pl", DISCLAIMER_PL), ("en", DISCLAIMER_EN)):
            self.assertIn(text, sig["md"][lang])

    def test_half_size_when_compass_is_in_cash(self):
        ctx = self.universe(wig20=-0.20, mwig40=-0.10, swig80=-0.30)
        sig = ped.signal(ctx, fx.LAST, None)
        self.assertEqual(sig["size_factor"], 0.5)
        self.assertIn("Reżim: ostrożnie", sig["md"]["pl"])
        self.assertIn("Regime: cautious", sig["md"]["en"])


class PrzystanTests(fx.MarketCase):
    def universe(self):
        """H01..H30 o rosnącej zmienności (H01-H05 to banki) i BAD: najspokojniejsza, ale z obsunięciem 45% w roku."""
        self.three_indices()
        for i in range(1, 31):
            self.add_stock(f"H{i:02d}", fx.path(self.days, 100.0, 0.05, 0.004 + 0.002 * (i - 1)), sector="banki" if i <= 5 else None)
        self.add_stock("BAD", fx.path(self.days, 100.0, -0.45, 0.001))
        return self.ctx()

    def test_lowest_quintile_with_drawdown_filter_and_sector_cap(self):
        ctx = self.universe()
        rows, chosen, skipped, bad, quint, keep = przystan.evaluate(ctx, fx.LAST, set())
        self.assertEqual(bad, {"BAD": "drawdown"})                                        # najniższa zmienność, ale obsunięcie głębsze niż 30%
        self.assertEqual([r["tic"] for r in rows], [f"H{i:02d}" for i in range(1, 31)])     # rosnąca zmienność
        self.assertTrue(all(a["vol"] < b["vol"] for a, b in zip(rows, rows[1:])))
        self.assertEqual((quint, keep), (6, 12))                                          # 20% i 40% z 30 spółek
        self.assertEqual([c["tic"] for c in chosen], ["H01", "H02", "H03", "H04", "H06"])  # tylko dolny kwintyl, w tym max 4 banki
        self.assertEqual(skipped, {"H05": "sector"})
        self.assertAlmostEqual(rows[0]["vol"], 0.004 * 9.77, delta=0.01)                   # σ dziennych zwrotów × √252 dla wahania 0,4%

    def test_hysteresis_keeps_names_in_calmest_40_percent(self):
        ctx = self.universe()
        rows, chosen, skipped, bad, quint, keep = przystan.evaluate(ctx, fx.LAST, {"H10", "H15"})
        self.assertEqual([c["tic"] for c in chosen], ["H01", "H02", "H03", "H04", "H06", "H10"])   # H10 (miejsce 10 <= 12) zostaje, H15 wypada

    def test_signal_payload(self):
        ctx = self.universe()
        prev = {"date": "2026-09-30", "targets": [{"tic": "H10", "name": "H10"}, {"tic": "H15", "name": "H15"}]}
        sig = przystan.signal(ctx, fx.LAST, prev)
        self.assertEqual([t["tic"] for t in sig["targets"]], ["H01", "H02", "H03", "H04", "H06", "H10"])
        self.assertEqual(list(sig["exit_reasons"]), ["H15"])
        self.assertEqual(sig["data"], {"eligible": 30, "quintile": 6})
        self.assertIn("6 spółek o najniższej zmienności", sig["headline"]["pl"])
        self.assertIn("Przystań", sig["md"]["pl"].splitlines()[0])
        self.assertIn("Harbor", sig["md"]["en"].splitlines()[0])
        self.assertIn("maksymalne obsunięcie z 12 miesięcy nie głębsze niż 30%", sig["md"]["pl"])
        for lang, text in (("pl", DISCLAIMER_PL), ("en", DISCLAIMER_EN)):
            self.assertIn(text, sig["md"][lang])


class DryfTests(fx.MarketCase):
    UP, DOWN = "2026-03-10", "2026-03-12"

    def flat_with(self, changes):
        """Zamknięcia 100 zł; changes = {data: cena} zmienia cenę od tego dnia."""
        out, cur = [], 100.0
        for d in self.days:
            cur = changes.get(d, cur)
            out.append(cur)
        return out

    def up(self, **over):
        """Zdarzenie dodatnie 10 III 2026: luka +3%, dzień +6%, zamknięcie blisko maksimum, wolumen 5× normy."""
        e = {"open": 103.0, "low": 102.5, "high": 106.5, "volume": 500000.0}
        e.update(over)
        return {self.UP: e}

    def universe(self):
        self.three_indices()
        self.add_stock("UP", self.flat_with({self.UP: 106.0}), edit=self.up())
        self.add_stock("DOWN", self.flat_with({self.DOWN: 94.0}), edit={self.DOWN: {"open": 97.0, "low": 93.5, "high": 97.5, "volume": 500000.0}})
        self.add_stock("OFF", self.flat_with({"2026-06-10": 106.0}), edit={"2026-06-10": {"open": 103.0, "low": 102.5, "high": 106.5, "volume": 500000.0}})
        self.add_stock("LOWVOL", self.flat_with({self.UP: 106.0}), edit=self.up(volume=200000.0))               # tylko 2× mediany
        self.add_stock("SMALLGAP", self.flat_with({self.UP: 106.0}), edit=self.up(open=101.0, low=100.5))        # luka +1%
        self.add_stock("MERGER", self.flat_with({self.UP: 140.0}), edit=self.up(open=130.0, low=129.0, high=140.5))  # +40%: możliwe scalenie
        self.add_stock("ILLIQ", self.flat_with({self.UP: 106.0}), edit=self.up(volume=25000.0), volume=5000.0)   # obrót ok. 0,5 mln zł
        self.add_stock("WEAKCLOSE", self.flat_with({self.UP: 106.0}), edit=self.up(high=112.0))                  # zamknięcie w dolnej połowie zakresu
        return self.ctx("2026-06-12")

    def test_positive_and_negative_events_are_detected_only_inside_windows(self):
        ctx = self.universe()
        found = dryf.scan(ctx, [self.UP, self.DOWN, "2026-06-10"])
        self.assertEqual([(e["tic"], e["date"], e["kind"]) for e in found], [("DOWN", self.DOWN, "neg"), ("UP", self.UP, "pos")])
        up = next(e for e in found if e["tic"] == "UP")
        self.assertAlmostEqual(up["gap"], 0.03)
        self.assertAlmostEqual(up["ret"], 0.06)
        self.assertAlmostEqual(up["vr"], 5.0)
        self.assertAlmostEqual(up["cp"], 0.875)
        self.assertEqual((up["pc"], up["open"], up["close"]), (100.0, 103.0, 106.0))
        both = dryf.scan(ctx, ["2026-06-10"], windows_only=False)                         # poza oknem zdarzenie istnieje, ale nie jest skanowane
        self.assertEqual([e["tic"] for e in both], ["OFF"])

    def test_every_condition_matters(self):
        ctx = self.universe()
        pos = {d: i for i, d in enumerate(ctx.sessions)}
        classified = {t: dryf.classify(dryf.day_stats(ctx.stock(t), self.UP, pos)) for t in
                      ("UP", "LOWVOL", "SMALLGAP", "MERGER", "ILLIQ", "WEAKCLOSE")}
        self.assertEqual(classified, {"UP": "pos", "LOWVOL": None, "SMALLGAP": None, "MERGER": None, "ILLIQ": None, "WEAKCLOSE": None})

    def test_ex_dividend_drop_is_not_an_opening_gap(self):
        self.three_indices()
        self.add_stock("DIV", self.flat_with({self.UP: 93.0}), edit={self.UP: {"open": 96.0, "low": 92.8, "high": 96.2, "volume": 500000.0}})
        self.div_events.append({"tic": "DIV", "cum": dt.date(2026, 3, 9), "dps": 3.0, "status": "wypłacona"})
        ctx = self.ctx("2026-03-12")
        pos = {d: i for i, d in enumerate(ctx.sessions)}
        m = dryf.day_stats(ctx.stock("DIV"), self.UP, pos)
        self.assertAlmostEqual(m["gap"], -0.01)                                           # (96 + 3) / 100 - 1, a nie −4%
        self.assertIsNone(dryf.classify(m))
        self.div_events.clear()
        plain = self.ctx("2026-03-12")
        self.assertEqual(dryf.classify(dryf.day_stats(plain.stock("DIV"), self.UP, pos)), "neg")      # bez korekty o dywidendę byłoby „zdarzenie ujemne"

    def test_previous_session_must_exist(self):
        self.three_indices()
        days = [d for d in self.days if d != "2026-03-09"]                                  # brak notowania dzień przed zdarzeniem
        closes = [106.0 if d >= self.UP else 100.0 for d in days]
        self.add_stock("GAPDAY", closes, days=days, edit=self.up())
        ctx = self.ctx("2026-03-12")
        pos = {d: i for i, d in enumerate(ctx.sessions)}
        self.assertIsNone(dryf.day_stats(ctx.stock("GAPDAY"), self.UP, pos))

    def test_window_edges(self):
        inside = ["2026-02-01", "2026-04-30", "2026-05-01", "2026-05-20", "2026-08-15", "2026-09-30", "2026-11-01", "2026-11-20"]
        outside = ["2026-01-31", "2026-05-21", "2026-08-14", "2026-10-01", "2026-11-21", "2026-12-31"]
        self.assertTrue(all(dryf.in_window(d) for d in inside))
        self.assertFalse(any(dryf.in_window(d) for d in outside))
        self.assertEqual(dryf.next_window_start("2026-11-06"), "2027-02-01")
        self.assertEqual(dryf.next_window_start("2026-11-20"), "2027-02-01")
        self.assertEqual(dryf.next_window_start("2026-05-01"), "2026-08-15")
        self.assertEqual(dryf.next_window_start("2026-01-15"), "2026-02-01")
        self.assertEqual(dryf.next_window_start("2026-12-31"), "2027-02-01")

    def test_signal_creates_orders_with_stop_at_previous_close(self):
        ctx = self.universe()
        ctx = self.ctx(self.UP)
        sig = dryf.signal(ctx, self.UP, None)
        self.assertEqual(sig["targets"], [])
        self.assertEqual([(o["tic"], o["stop"], o["event_date"]) for o in sig["orders"]], [("UP", 100.0, self.UP)])
        self.assertEqual(sig["headline"], {"pl": "Zdarzenia: 1 dodatnich, 0 ujemnych", "en": "Events: 1 positive, 0 negative"})
        self.assertEqual(sig["chips"], ["UP"])
        self.assertIn("Dryf", sig["md"]["pl"].splitlines()[0])
        self.assertIn("Drift", sig["md"]["en"].splitlines()[0])
        self.assertIn("Okno raportowe: **trwa**", sig["md"]["pl"])
        for lang, text in (("pl", DISCLAIMER_PL), ("en", DISCLAIMER_EN)):
            self.assertIn(text, sig["md"][lang])

    def test_negative_event_goes_to_no_buy_list_without_order(self):
        self.universe()
        ctx = self.ctx(self.DOWN)
        sig = dryf.signal(ctx, self.DOWN, None)
        self.assertEqual(sig["orders"], [])
        self.assertEqual(sig["data"]["nobuy"], [{"tic": "DOWN", "date": self.DOWN}])
        self.assertEqual([e["tic"] for e in sig["data"]["today"]], ["DOWN"])
        self.assertIn("nie kupuj", sig["md"]["pl"])
        self.assertIn("UP", sig["md"]["pl"])                                               # zdarzenie sprzed dwóch sesji w tabeli ostatnich zdarzeń
        self.assertIn("lista „nie kupuj”", sig["md"]["pl"])

    def test_outside_window_the_scan_is_paused(self):
        self.universe()
        ctx = self.ctx("2026-06-10")
        sig = dryf.signal(ctx, "2026-06-10", None)
        self.assertEqual(sig["orders"], [])
        self.assertFalse(sig["data"]["in_window"])
        self.assertEqual(sig["headline"]["pl"], "Poza oknem raportowym, skan wstrzymany")
        self.assertIn("najbliższe okno zaczyna się 15 sierpnia 2026", sig["md"]["pl"])
        self.assertIn("the next window starts on 15 August 2026", sig["md"]["en"])


if __name__ == "__main__":
    unittest.main()


class FinanceGroupTests(fx.MarketCase):
    """Banki i pozostałe instytucje finansowe liczą się razem do limitu sektora (Pęd: 3, Przystań: 4)."""

    def test_momentum_counts_banks_and_financials_together(self):
        self.three_indices()
        for i in range(1, 21):                                  # P01-P02 banki, P03-P05 finanse, reszta bez sektora; momentum maleje z numerem
            self.add_stock(f"P{i:02d}", fx.path(self.days, 100.0, 2.0 - 0.045 * (i - 1)), sector="banki" if i <= 2 else "fin" if i <= 5 else None)
        rows, chosen, skipped, bad = ped.evaluate(self.ctx(), fx.LAST, set())
        names = [c["tic"] for c in chosen]
        self.assertEqual(names[:3], ["P01", "P02", "P03"])       # dwa banki i jedna spółka finansowa wyczerpują limit 3
        self.assertEqual({t: skipped.get(t) for t in ("P04", "P05")}, {"P04": "sector", "P05": "sector"})
        self.assertEqual(len(chosen), ped.N)

    def test_harbor_counts_banks_and_financials_together(self):
        self.three_indices()
        for i in range(1, 31):                                  # H01-H03 banki, H04-H06 finanse; zmienność rośnie z numerem
            self.add_stock(f"H{i:02d}", fx.path(self.days, 100.0, 0.05, 0.004 + 0.002 * (i - 1)), sector="banki" if i <= 3 else "fin" if i <= 6 else None)
        rows, chosen, skipped, bad, quint, keep = przystan.evaluate(self.ctx(), fx.LAST, set())
        self.assertEqual([c["tic"] for c in chosen], ["H01", "H02", "H03", "H04"])   # kwintyl to 6 spółek, wszystkie z finansów: limit 4
        self.assertEqual(skipped, {"H05": "sector", "H06": "sector"})

    def test_limit_sector_keeps_other_sectors_apart(self):
        self.assertEqual(lib.limit_sector("banki"), lib.limit_sector("fin"))
        self.assertEqual((lib.limit_sector("it"), lib.limit_sector("inne")), ("it", "inne"))


class RankGapNoteTests(unittest.TestCase):
    def test_note_only_when_ranks_skip(self):
        self.assertEqual(lib.rank_gap_note([{"rank": 1}, {"rank": 2}], "pl"), "")
        self.assertEqual(lib.rank_gap_note([], "pl"), "")
        self.assertIn("Przeskoki", lib.rank_gap_note([{"rank": 1}, {"rank": 3}], "pl"))
        self.assertIn("Gaps", lib.rank_gap_note([{"rank": 2}], "en"))
