"""Testy Złotego Środka (strat/zloty.py): wskaźniki z dwóch lat sprawozdań, ochrona przed wyprzedzaniem (data publikacji),
wczytywanie data/fundamentals.csv, ranking, progi wejścia i utrzymania, limity sektorów oraz zachowanie bez danych.
Kwoty w tys. zł, akcje w sztukach (jak w pliku CSV)."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import strat_fixture as fx
from strat import zloty

PREV = dict(revenue=1_000_000, gross_profit=300_000, ebit=100_000, ebitda=150_000, net_income=60_000, cfo=80_000, capex=30_000,
            total_assets=1_000_000, equity=500_000, current_assets=400_000, current_liabilities=300_000, debt=200_000, cash=50_000,
            shares=10_000_000)
CUR = dict(revenue=1_200_000, gross_profit=400_000, ebit=160_000, ebitda=220_000, net_income=100_000, cfo=150_000, capex=40_000,
           total_assets=1_100_000, equity=600_000, current_assets=500_000, current_liabilities=300_000, debt=180_000, cash=80_000,
           shares=10_000_000)                    # wszystkie 9 testów Piotroskiego zdane, kurs 100 zł daje kapitalizację 1 mld zł


def row(tic, fy, base, published, **over):
    r = {"tic": tic, "fy": fy, "period_end": f"{fy}-12-31", "published": published, "source": "test", **base}
    r.update(over)
    return r


def company(tic, published="2026-03-31", **over):
    """Sprawozdania za 2024 i 2025; `over` zmienia wartości roku 2025."""
    return {2024: row(tic, 2024, PREV, "2025-03-31"), 2025: row(tic, 2025, CUR, published, **over)}


class MetricsTests(unittest.TestCase):
    def m(self, price=100.0, **over):
        return zloty.metrics({**CUR, **over, "fy": 2025}, {**PREV, "fy": 2024}, price)

    def test_full_score_and_valuation(self):
        m = self.m()
        self.assertEqual(m["f"], 9)
        self.assertTrue(all(m["tests"].values()))
        self.assertAlmostEqual(m["nd_ebitda"], 100_000 / 220_000)         # dług 180 mln − gotówka 80 mln = 100 mln
        self.assertEqual(m["mcap"], 1_000_000)                            # 100 zł × 10 mln akcji, w tys. zł
        self.assertEqual(m["ev"], 1_100_000)
        self.assertAlmostEqual(m["ev_ebit"], 1_100_000 / 160_000)
        self.assertEqual(m["fcf"], 110_000)
        self.assertAlmostEqual(m["gpa"], 400_000 / 1_100_000)
        self.assertEqual((m["equity"], m["fy"]), (600_000, 2025))

    def test_each_piotroski_test_can_fail_on_its_own(self):
        cases = {
            "droa": dict(net_income=50_000),                              # ROA 4,5% < 6%
            "accrual": dict(cfo=80_000),                                  # CFO/aktywa 7,3% < ROA 9,1%
            "lever": dict(debt=300_000),                                  # dług/aktywa 27% > 20%
            "liquid": dict(current_assets=300_000),                       # płynność bieżąca 1,0 < 1,33
            "shares": dict(shares=11_000_000),                            # emisja akcji +10%
            "margin": dict(gross_profit=300_000),                         # marża brutto 25% < 30%
            "turn": dict(revenue=1_000_000),                              # obrót aktywów 0,91 < 1,0
        }
        for key, over in cases.items():
            with self.subTest(key):
                m = self.m(**over)
                self.assertFalse(m["tests"][key])
                self.assertEqual(m["f"], 8)
        self.assertTrue(self.m(shares=10_040_000)["tests"]["shares"])      # tolerancja +0,5% na zaokrąglenia liczby akcji
        self.assertFalse(self.m(net_income=-10_000)["tests"]["roa"])
        self.assertFalse(self.m(cfo=-1.0)["tests"]["cfo"])

    def test_leverage_test_passes_when_debt_ratio_does_not_rise(self):
        debt_free = zloty.metrics({**CUR, "debt": 0, "fy": 2025}, {**PREV, "debt": 0, "fy": 2024}, 100.0)
        self.assertTrue(debt_free["tests"]["lever"])                       # spółka bez długu nie traci punktu
        self.assertEqual(debt_free["f"], 9)
        same = zloty.metrics({**CUR, "debt": 220_000, "fy": 2025}, {**PREV, "fy": 2024}, 100.0)   # 220/1100 = 200/1000
        self.assertTrue(same["tests"]["lever"])
        self.assertFalse(self.m(debt=221_000)["tests"]["lever"])           # wzrost zadłużenia do aktywów: test niezaliczony

    def test_net_cash_and_unrankable_cases(self):
        self.assertEqual(self.m(debt=50_000, cash=80_000)["nd_ebitda"], 0.0)               # gotówka netto
        self.assertIsNone(self.m(ebitda=-5_000)["nd_ebitda"])                              # dług przy ujemnym EBITDA: bez wskaźnika
        self.assertEqual(self.m(ebitda=-5_000, debt=50_000, cash=80_000)["nd_ebitda"], 0.0)
        self.assertIsNone(self.m(ebit=-1.0)["ev_ebit"])
        self.assertIsNone(self.m(ebit=0.0)["ev_ebit"])

    def test_missing_or_invalid_inputs_give_none(self):
        self.assertIsNone(self.m(cfo=None))
        self.assertIsNone(self.m(total_assets=0.0))
        self.assertIsNone(self.m(shares=0.0))
        self.assertIsNone(zloty.metrics({**CUR, "fy": 2025}, {**PREV, "cash": None, "fy": 2024}, 100.0))


class DataFileTests(unittest.TestCase):
    def test_available_from_prefers_publication_date(self):
        self.assertEqual(zloty.available_from({"fy": 2025, "published": "2026-04-20", "period_end": "2025-12-31"}), "2026-04-20")
        self.assertEqual(zloty.available_from({"fy": 2025, "published": "", "period_end": "2025-12-31"}), "2026-04-30")      # koniec okresu + 120 dni
        self.assertEqual(zloty.available_from({"fy": 2025, "published": "", "period_end": ""}), "2026-04-30")
        self.assertEqual(zloty.available_from({"fy": 2025, "published": "", "period_end": "nie-data"}), "2026-05-01")
        self.assertEqual(zloty.available_from({"fy": 2024, "published": "", "period_end": "2024-06-30"}), "2024-10-28")       # rok obrotowy do czerwca

    def write(self, path, rows):
        with Path(path).open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=zloty.FIELDS)
            w.writeheader()
            w.writerows(rows)

    def test_load_fundamentals_parses_numbers_and_skips_bad_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "fund.csv"
            self.write(p, [
                row("AAA", 2025, CUR, "2026-03-31"),
                row("AAA", 2024, PREV, "2025-03-31", revenue="1 234,5", cash="", ebit="abc"),     # spacja i przecinek dziesiętny, puste, tekst
                row("", 2025, CUR, "2026-03-31"),                                                  # bez tickera
                row("BBB", "n/a", CUR, "2026-03-31"),                                              # rok nie jest liczbą
            ])
            out = zloty.load_fundamentals(p)
        self.assertEqual(list(out), ["AAA"])
        self.assertEqual(sorted(out["AAA"]), [2024, 2025])
        old = out["AAA"][2024]
        self.assertEqual(old["revenue"], 1234.5)
        self.assertIsNone(old["cash"])
        self.assertIsNone(old["ebit"])
        self.assertEqual(old["period_end"], "2024-12-31")
        self.assertEqual(out["AAA"][2025]["shares"], 10_000_000.0)

    def test_missing_file_is_empty_not_an_error(self):
        self.assertEqual(zloty.load_fundamentals(Path("/nonexistent/fundamentals.csv")), {})


class ZlotyTests(fx.MarketCase):
    def universe(self, extra=()):
        """A, B, C: komplet danych i progi zdane; LOWF (F-score 6), NEGFCF (ujemny FCF), HIGHDEBT (dług netto/EBITDA 3,7), WEAK (F-score 4),
        BANK (poza zakresem), LATE (sprawozdanie opublikowane po dniu sygnału), ILLIQ (za mały obrót)."""
        self.three_indices()
        fund = {}

        def add(tic, sector=None, volume=100000.0, **over):
            self.add_stock(tic, fx.path(self.days, 100.0), sector=sector, volume=volume)
            fund[tic] = company(tic, **over)

        add("A", ebit=200_000)
        add("B", ebit=160_000, gross_profit=440_000)
        add("C", ebit=120_000)
        add("LOWF", ebit=220_000, shares=11_500_000, gross_profit=300_000, revenue=1_000_000)
        add("NEGFCF", capex=200_000)
        add("HIGHDEBT", debt=900_000)
        add("WEAK", shares=11_500_000, gross_profit=300_000, revenue=1_000_000, debt=900_000, current_assets=300_000)
        add("BANK", sector="banki")
        add("LATE", published="2026-12-01")
        add("ILLIQ", volume=1000.0)
        for tic, sector, over in extra:
            add(tic, sector, **over)
        return self.ctx(), fund

    def test_ranking_funnel_and_entry_thresholds(self):
        ctx, fund = self.universe()
        rows, chosen, skipped, info = zloty.evaluate(ctx, fx.LAST, set(), fund)
        by = {r["tic"]: r for r in rows}
        self.assertEqual(set(by), {"A", "B", "C", "LOWF", "NEGFCF", "HIGHDEBT", "WEAK"})          # bank, spóźnione sprawozdanie i niepłynna spółka poza rankingiem
        self.assertEqual((by["LOWF"]["f"], by["WEAK"]["f"], by["A"]["f"]), (6, 4, 9))
        self.assertLess(by["NEGFCF"]["fcf"], 0)
        self.assertAlmostEqual(by["HIGHDEBT"]["nd_ebitda"], 820_000 / 220_000)
        # A najtańsza (EV/EBIT 5,5) i druga wg zyskowności; B najwyższa zyskowność; remis punktów A–B rozstrzyga niższe EV/EBIT
        self.assertEqual([r["tic"] for r in rows[:2]], ["A", "B"])
        self.assertEqual([r["rank"] for r in rows], list(range(1, len(rows) + 1)))
        self.assertEqual(by["A"]["score"], 3)
        self.assertEqual(by["B"]["score"], 4)
        self.assertEqual([c["tic"] for c in chosen], ["A", "B", "C"])                             # progi wejścia: F>=7, FCF>0, dług netto/EBITDA<=3
        self.assertEqual(skipped, {"NEGFCF": "filter", "LOWF": "filter", "HIGHDEBT": "filter", "WEAK": "filter"})
        self.assertEqual(info["universe"], 10)
        self.assertEqual(info["with_data"], 10)                   # każda spółka ma jakieś dostępne sprawozdanie (LATE: tylko za 2024)
        self.assertEqual(info["financial"], 1)                    # BANK
        self.assertEqual(info["liquid"], 8)                       # bez BANK i ILLIQ
        self.assertEqual(info["complete"], 7)                     # bez LATE: za 2025 jeszcze nie opublikowano, więc nie ma pary lat
        self.assertEqual(info["rankable"], 7)
        self.assertEqual(info["pass_entry"], 3)

    def test_hysteresis_uses_looser_thresholds_for_held_names(self):
        ctx, fund = self.universe()
        rows, chosen, skipped, info = zloty.evaluate(ctx, fx.LAST, {"LOWF", "HIGHDEBT", "WEAK"}, fund)
        tics = [c["tic"] for c in chosen]
        self.assertEqual(tics, ["A", "B", "C", "LOWF", "HIGHDEBT"])        # F-score 6 i dług 3,7x mieszczą się w progach utrzymania (5 i 4x)
        self.assertEqual(skipped, {"NEGFCF": "filter", "WEAK": "filter"})  # WEAK ma F-score 4 < 5: wypada mimo że była w portfelu

    def test_regulated_sectors_share_one_cap(self):
        ctx, fund = self.universe([("E1", "energia", dict(ebit=300_000)), ("E2", "energia", dict(ebit=290_000)), ("E3", "energia", dict(ebit=280_000)),
                                   ("P1", "paliwa", dict(ebit=285_000))])
        with mock.patch.object(zloty, "REG_CAP", 2):
            rows, chosen, skipped, info = zloty.evaluate(self.ctx(), fx.LAST, set(), fund)
        reg = [c["tic"] for c in chosen if c["tic"] in {"E1", "E2", "E3", "P1"}]
        self.assertEqual(len(reg), 2)
        self.assertEqual(sum(1 for v in skipped.values() if v == "sector"), 2)

    def test_per_sector_cap(self):
        ctx, fund = self.universe([("M1", "przemysl", dict(ebit=300_000)), ("M2", "przemysl", dict(ebit=290_000)), ("M3", "przemysl", dict(ebit=280_000))])
        with mock.patch.object(zloty, "SECTOR_CAP", 2):
            rows, chosen, skipped, info = zloty.evaluate(self.ctx(), fx.LAST, set(), fund)
        self.assertEqual(sum(1 for c in chosen if c["tic"] in {"M1", "M2", "M3"}), 2)
        self.assertEqual(sum(1 for v in skipped.values() if v == "sector"), 1)

    def test_statement_is_used_only_after_publication(self):
        ctx, fund = self.universe([("SAMEDAY", None, dict(published=fx.LAST)), ("NEXTDAY", None, dict(published="2026-11-09"))])
        rows, *_ = zloty.evaluate(self.ctx(), fx.LAST, set(), fund)
        tics = {r["tic"] for r in rows}
        self.assertIn("SAMEDAY", tics)                                      # w dniu publikacji sprawozdanie już obowiązuje
        self.assertNotIn("NEXTDAY", tics)                                   # dzień później: jeszcze nieznane
        self.assertNotIn("LATE", tics)
        rows, *_ = zloty.evaluate(self.ctx("2026-12-02"), "2026-12-02", set(), fund)
        tics = {r["tic"] for r in rows}
        self.assertTrue({"NEXTDAY", "LATE"} <= tics)                        # po publikacji trafiają do rankingu

    def test_signal_without_data_stays_in_cash(self):
        ctx, _ = self.universe()
        sig = zloty.signal(ctx, fx.LAST, None, initial=True, fund={})
        self.assertEqual(sig["targets"], [])
        self.assertEqual(sig["chips"], ["GOTÓWKA"])
        self.assertEqual(sig["headline"], {"pl": "Czeka na dane fundamentalne", "en": "Waiting for fundamental data"})
        self.assertEqual(sig["data"]["status"], "no_data")
        self.assertIn("Czeka na dane fundamentalne", sig["md"]["pl"])
        self.assertNotIn("METHOD-ZLOTY-SRODEK.md", sig["md"]["pl"])                 # instrukcja dla opiekuna nie trafia do raportu
        self.assertIn("Waiting for fundamental data", sig["md"]["en"])
        for text in ("Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.",):
            self.assertIn(text, sig["md"]["pl"])
        self.assertIn("Screening exercise under the given framework, not investment advice.", sig["md"]["en"])

    def test_signal_without_data_but_with_holdings_carries_them(self):
        ctx, _ = self.universe()
        prev = {"date": "2026-05-29", "targets": [{"tic": "A", "name": "A SA", "weight": 1.0}]}
        sig = zloty.signal(ctx, fx.LAST, prev, fund={})
        self.assertEqual(sig["targets"], prev["targets"])
        self.assertEqual(sig["exit_reasons"], {})
        self.assertEqual(sig["data"]["status"], "carried")
        self.assertEqual(sig["headline"]["pl"], "Brak świeżych danych, skład bez zmian")
        self.assertEqual(sig["chart"]["rows"], [])

    def test_signal_with_data(self):
        ctx, fund = self.universe()
        prev = {"date": "2026-05-29", "targets": [{"tic": "WEAK", "name": "WEAK SA"}, {"tic": "A", "name": "A SA"}]}
        sig = zloty.signal(ctx, fx.LAST, prev, fund=fund)
        self.assertEqual([t["tic"] for t in sig["targets"]], ["A", "B", "C"])
        self.assertEqual(list(sig["exit_reasons"]), ["WEAK"])
        self.assertEqual(sig["data"]["status"], "ok")
        self.assertEqual(sig["headline"]["pl"], "3 spółki: A, B, C…")
        self.assertEqual([r[0] for r in sig["chart"]["rows"]], ["A", "B", "C"])
        self.assertAlmostEqual(sig["chart"]["rows"][0][1], 5.5)
        self.assertIn("Złoty Środek", sig["md"]["pl"].splitlines()[0])
        self.assertIn("Golden Mean", sig["md"]["en"].splitlines()[0])
        self.assertIn("Lejek:", sig["md"]["pl"])
        self.assertIn("Funnel:", sig["md"]["en"])

    def test_signal_reads_the_default_csv_file(self):
        ctx, fund = self.universe()
        path = self.data / "fundamentals.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=zloty.FIELDS)
            w.writeheader()
            for years in fund.values():
                w.writerows(years.values())
        sig = zloty.signal(self.ctx(), fx.LAST, None, initial=True)
        self.assertEqual([t["tic"] for t in sig["targets"]], ["A", "B", "C"])
        self.assertEqual(sig["data"]["fund_rows"], 20)


if __name__ == "__main__":
    unittest.main()
