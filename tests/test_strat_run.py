"""Testy uruchamiania strategii uzupełniających (strat/run.py, wiersz poleceń): pierwszy przebieg, idempotencja, nadrabianie
zaległych sygnałów, kalendarze (miesiąc, kwartał, maj i październik), ochrona przed niepełnymi notowaniami, wymuszenie oraz
pełna ścieżka zdarzenia Dryfu od skanu do wyjścia po 40 sesjach."""
import contextlib
import io
import json
import unittest
from unittest import mock

import strat_fixture as fx
from strat import __main__ as cli
from strat import engine, lib, registry, run

SLUGS = registry.SLUGS


RunCase = fx.RunCase


class FirstRunTests(RunCase):
    def test_every_strategy_gets_reports_and_a_portfolio(self):
        res = run.run_all(asof=fx.LAST)
        self.assertEqual(res, {slug: [fx.LAST] for slug in SLUGS})
        for slug in SLUGS:
            for lang in ("pl", "en"):
                self.assertTrue((self.strat_dir / slug / lang / f"{fx.LAST}.md").is_file(), (slug, lang))
            sig = self.signal(slug, fx.LAST)
            self.assertTrue(sig["initial"], slug)
            self.assertNotIn("md", sig)                                    # tekst raportu leży w plikach .md, nie w .json
            st = self.state(slug)
            self.assertEqual((st["start_date"], st["processed_through"]), (fx.LAST, fx.LAST), slug)
            self.assertEqual(st["cash"], 100000.0)                         # w dniu startu nic jeszcze nie kupiono
            self.assertEqual(st["positions"], [])
            self.assertEqual(st["equity"][0]["bench"], lib.Ctx(fx.LAST).indices["WIG20"].at(fx.LAST, "c"))     # punkt startowy z zamknięciem WIG20
        self.assertEqual(self.state("kompas")["config"]["fractional"], True)
        self.assertEqual(self.state("ped")["config"]["fractional"], False)
        self.assertEqual(self.state("dryf")["kind"], "events")
        self.assertEqual(self.state("dryf")["config"]["position_value"], 10000.0)

    def test_signals_of_the_first_day(self):
        run.run_all(asof=fx.LAST)
        self.assertEqual([t["tic"] for t in self.signal("kompas", fx.LAST)["targets"]], ["MWIG40"])
        self.assertEqual(len(self.signal("ped", fx.LAST)["targets"]), 12)
        self.assertEqual(self.signal("zloty-srodek", fx.LAST)["headline"]["pl"], "Czeka na dane fundamentalne")
        self.assertEqual(self.signal("zloty-srodek", fx.LAST)["targets"], [])
        self.assertGreater(len(self.signal("przystan", fx.LAST)["targets"]), 0)
        self.assertEqual(self.signal("dryf", fx.LAST)["orders"], [])
        # zlecenie czeka na otwarcie najbliższej sesji po dniu sygnału
        self.assertEqual(self.state("kompas")["pending"]["signal_date"], fx.LAST)

    def test_second_run_changes_nothing(self):
        run.run_all(asof=fx.LAST)
        before = {slug: (self.paper_dir / slug / "state.json").read_text(encoding="utf-8") for slug in SLUGS}
        reports = sorted(p.name for p in self.strat_dir.rglob("*.md"))
        again = run.run_all(asof=fx.LAST)
        self.assertEqual(again, {slug: [] for slug in SLUGS})
        self.assertEqual({slug: (self.paper_dir / slug / "state.json").read_text(encoding="utf-8") for slug in SLUGS}, before)
        self.assertEqual(sorted(p.name for p in self.strat_dir.rglob("*.md")), reports)

    def test_orders_execute_at_the_open_of_the_next_session(self):
        run.run_all(asof=fx.LAST)
        res = run.run_all(asof="2026-11-09")                                # poniedziałek: pierwsza sesja po 6 XI
        self.assertEqual(res["dryf"], ["2026-11-09"])                       # Dryf skanuje każdą nową sesję
        self.assertEqual(res["kompas"], [])                                 # listopad jeszcze trwa: bez nowego sygnału miesięcznego
        kompas = self.state("kompas")
        pos = kompas["positions"][0]
        self.assertEqual((pos["tic"], pos["entry_date"]), ("MWIG40", "2026-11-09"))
        self.assertLess(kompas["cash"], 1.0)                                # jednostki ułamkowe: prawie cały kapitał w indeksie
        self.assertAlmostEqual(pos["shares"] * pos["entry"] * 1.002 + kompas["cash"], 100000.0, places=2)
        ped = self.state("ped")
        self.assertEqual({p["entry_date"] for p in ped["positions"]}, {"2026-11-09"})
        self.assertEqual(len(ped["positions"]), 12)
        self.assertEqual(self.state("zloty-srodek")["positions"], [])
        self.assertEqual(self.state("zloty-srodek")["cash"], 100000.0)

    def test_force_recomputes_the_signal_for_the_last_session(self):
        run.run_all(asof=fx.LAST)
        res = run.run_all(asof=fx.LAST, only=["kompas"], force=True)
        self.assertEqual(res, {"kompas": [fx.LAST]})
        st = self.state("kompas")
        self.assertEqual(st["pending"]["signal_date"], fx.LAST)
        self.assertTrue(any("zastępuje" in e["pl"] for e in st["log"]))
        self.assertEqual(len([e for e in st["log"] if e["pl"].startswith("Sygnał:")]), 2)
        self.assertEqual(st["positions"], [])


class CatchUpTests(RunCase):
    def test_monthly_signals_wait_for_the_new_month_and_daily_scan_runs_every_session(self):
        run.run_all(asof=fx.LAST)
        res = run.run_all(asof="2026-12-03")
        newer = [d for d in fx.SESSIONS if fx.LAST < d <= "2026-12-03"]
        self.assertEqual(res["kompas"], ["2026-11-30"])                       # ostatnia sesja listopada, raport po pierwszej sesji grudnia
        self.assertEqual(res["ped"], ["2026-11-30"])
        self.assertEqual(res["przystan"], [])                                  # kwartał kończy się w grudniu, a grudzień trwa
        self.assertEqual(res["zloty-srodek"], [])                              # maj i październik
        self.assertEqual(res["dryf"], newer)
        self.assertEqual(len(newer), 19)
        kompas = self.state("kompas")
        self.assertEqual(kompas["processed_through"], "2026-12-03")
        self.assertEqual([p["entry_date"] for p in kompas["positions"]], ["2026-11-09"])    # kupno na otwarciu drugiej sesji po sygnale startowym
        self.assertEqual(kompas["closed"], [])                                              # ten sam indeks: bez transakcji
        self.assertIn("Bez zmian względem sygnału z 6 listopada 2026", self.report("kompas", "2026-11-30"))
        self.assertFalse(self.signal("kompas", "2026-11-30")["initial"])

    def test_calendars_for_quarterly_and_semiannual_strategies(self):
        run.run_all(asof="2026-09-15")
        res = run.run_all(asof="2026-10-05")
        self.assertEqual((res["kompas"], res["ped"], res["przystan"], res["zloty-srodek"]),
                         (["2026-09-30"], ["2026-09-30"], ["2026-09-30"], []))
        res = run.run_all(asof="2026-11-04")
        self.assertEqual((res["kompas"], res["ped"], res["przystan"], res["zloty-srodek"]),
                         (["2026-10-30"], ["2026-10-30"], [], ["2026-10-30"]))
        self.assertTrue(self.report("zloty-srodek", "2026-10-30").startswith("# Złoty Środek"))

    def test_catch_up_is_limited_to_the_newest_dates(self):
        run.run_all(asof=fx.LAST)
        with mock.patch.object(run, "MAX_CATCHUP", 3):
            res = run.run_all(asof="2026-11-20", only=["dryf"])
        self.assertEqual(res["dryf"], ["2026-11-18", "2026-11-19", "2026-11-20"])

    def test_report_for_each_missed_month_end_in_order(self):
        run.run_all(asof="2026-08-14")
        res = run.run_all(asof="2026-11-04", only=["kompas", "ped"])
        self.assertEqual(res["kompas"], ["2026-08-31", "2026-09-30", "2026-10-30"])
        self.assertEqual(res["ped"], ["2026-08-31", "2026-09-30", "2026-10-30"])
        # raport porównuje się z poprzednim sygnałem (wtedy brakowało 12 miesięcy historii, więc była gotówka)
        self.assertIn("Zmiana względem sygnału z 30 września 2026: gotówka → mWIG40", self.report("kompas", "2026-10-30"))
        self.assertIn("Change versus the signal of 30 September 2026: cash → mWIG40", self.report("kompas", "2026-10-30", "en"))


class GuardTests(RunCase):
    def test_incomplete_download_skips_all_strategies(self):
        (self.market / "_status.json").write_text(json.dumps({"coverage": 0.5}), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            res = run.run_all(asof=fx.LAST)
        self.assertEqual(res, {})
        self.assertIn("niepełne notowania", out.getvalue())
        self.assertEqual(list(self.paper_dir.iterdir()), [])
        self.assertEqual(list(self.strat_dir.iterdir()), [])

    def test_coverage_at_the_threshold_or_missing_is_fine(self):
        self.assertTrue(run.coverage_ok())                                                # brak pliku
        (self.market / "_status.json").write_text(json.dumps({"coverage": 0.8}), encoding="utf-8")
        self.assertTrue(run.coverage_ok())
        (self.market / "_status.json").write_text(json.dumps({"note": "bez pokrycia"}), encoding="utf-8")
        self.assertTrue(run.coverage_ok())
        (self.market / "_status.json").write_text(json.dumps({"coverage": 0.79}), encoding="utf-8")
        self.assertFalse(run.coverage_ok())

    def test_no_market_data_creates_nothing(self):
        for p in self.market.glob("*.csv"):
            p.unlink()
        res = run.run_all()
        self.assertEqual(res, {slug: [] for slug in SLUGS})
        self.assertEqual(list(self.paper_dir.iterdir()), [])

    def test_history_shorter_than_a_year_gives_empty_but_valid_reports(self):
        # 23 X 2025 - 6 XI 2026 to mniej niż 12 miesięcy przed wcześniejszymi datami: Pęd i Przystań nie mają kogo wybrać
        res = run.run_all(asof="2026-03-02")
        self.assertEqual(res, {slug: ["2026-03-02"] for slug in SLUGS})
        for slug in ("ped", "przystan", "zloty-srodek"):
            self.assertEqual(self.signal(slug, "2026-03-02")["targets"], [], slug)
        self.assertEqual(self.signal("kompas", "2026-03-02")["targets"], [])               # Kompas bez 12 miesięcy: brak sygnału, gotówka
        for slug in SLUGS:
            self.assertTrue(self.report(slug, "2026-03-02", "en").startswith("# "), slug)


class CommandLineTests(RunCase):
    def call(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_daily_and_status(self):
        code, out, _ = self.call("daily", "--asof", fx.LAST, "--only", "kompas,ped")
        self.assertEqual(code, 0)
        self.assertIn(f"kompas: raporty {fx.LAST}", out)
        self.assertIn(f"ped: raporty {fx.LAST}", out)
        self.assertNotIn("dryf", out)
        code, out, _ = self.call("daily", "--asof", fx.LAST, "--only", "kompas")
        self.assertIn("kompas: bez nowych sygnałów", out)
        code, out, _ = self.call("status")
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[0].startswith("kompas") and "raportów   1" in lines[0] and "kapitał 100,000" in lines[0])
        self.assertIn("raportów   0", lines[2])                                           # Złoty Środek: jeszcze nie uruchomiony

    def test_unknown_strategy_is_rejected(self):
        code, out, err = self.call("daily", "--only", "kompas,nie-ma-takiej")
        self.assertEqual(code, 2)
        self.assertIn("Nieznana strategia: nie-ma-takiej", err)
        self.assertEqual(list(self.paper_dir.iterdir()), [])


class DryfEndToEndTests(fx.MarketCase):
    """Zdarzenie dodatnie 10 III 2026 -> zlecenie -> kupno po otwarciu 11 III -> wyjście po 40 sesjach (koniec okna)."""

    def test_event_to_time_exit(self):
        self.three_indices()
        for i in range(1, 6):
            self.add_stock(f"S{i:02d}", fx.path(self.days, 100.0, 0.1, 0.004 + 0.001 * i))
        up = {"2026-03-10": {"open": 103.0, "low": 102.5, "high": 106.5, "volume": 500000.0}}
        self.add_stock("EVT", [106.0 if d >= "2026-03-10" else 100.0 for d in self.days], edit=up)
        self.finish()
        run.run_all(asof="2026-03-09", only=["dryf"])
        res = run.run_all(asof="2026-05-15", only=["dryf"])
        sessions = fx.SESSIONS
        self.assertEqual(res["dryf"][0], "2026-03-10")
        self.assertEqual(len(res["dryf"]), len([d for d in sessions if "2026-03-09" < d <= "2026-05-15"]))
        event = run.read_signal("dryf", "2026-03-10")
        self.assertEqual([(o["tic"], o["stop"], o["event_date"]) for o in event["orders"]], [("EVT", 100.0, "2026-03-10")])
        st = engine.load("dryf")
        self.assertEqual(st["positions"], [])
        row = st["closed"][0]
        entry_idx = sessions.index("2026-03-11")
        self.assertEqual((row["tic"], row["entry_date"], row["entry"], row["event_date"]), ("EVT", "2026-03-11", 106.0, "2026-03-10"))
        self.assertEqual((row["exit_date"], row["exit"], row["why_pl"]), (sessions[entry_idx + 40], 106.0, "koniec okna (40 sesji)"))
        self.assertEqual(row["shares"], 94)                                  # 10 000 zł / (106 zł · 1,002), w dół
        self.assertAlmostEqual(row["pnl"], 94 * 106 * 0.998 - 94 * 106 * 1.002, places=2)
        # raport z dnia po zdarzeniu pokazuje pozycję w portfelu; po wyjściu (40 sesji później) zdarzenie nie mieści się już w tabeli
        # ostatnich 10 sesji, a zamknięta transakcja jest na stronie portfela
        after = (self.strat_dir / "dryf" / "pl" / "2026-03-11.md").read_text(encoding="utf-8")
        self.assertIn("w portfelu", after)
        self.assertIn("Otwarte pozycje", after)
        self.assertIn("EVT", after)
        shortly = (self.strat_dir / "dryf" / "pl" / "2026-03-12.md").read_text(encoding="utf-8")
        self.assertRegex(shortly, r"\| EVT \| EVT \| 11 marca 2026 \| 106,00 \| 100,00 \| 106,00 \| 0,0% \| 1 / 40 \|")   # otwarte pozycje: wejście, stop, sesje
        late = (self.strat_dir / "dryf" / "pl" / f"{sessions[entry_idx + 40]}.md").read_text(encoding="utf-8")
        self.assertIn("Brak otwartych pozycji.", late)
        self.assertNotIn("EVT", late)


if __name__ == "__main__":
    unittest.main()
