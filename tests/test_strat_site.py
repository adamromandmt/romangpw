"""Testy warstwy stron strategii uzupełniających: wykres słupkowy raportu (charts.strategy_chart), strona portfela
(portfel.render_strategy), treść raportu (build.strategy_body) oraz komplet podstron jednej strategii (build.build_strategy)."""
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import strat_fixture as fx
import build
import charts
import portfel
from strat import engine, lib, registry, run

REPO = Path(build.__file__).resolve().parent


def spec(rows, unit="%"):
    return {"unit": unit, "rows": rows, "title": {"pl": "Tytuł wykresu", "en": "Chart title"}, "sub": {"pl": "Podtytuł", "en": "Subtitle"}}


class ChartTests(unittest.TestCase):
    ROWS = [["AAA", 12.3], ["BBB", -4.5], ["CCC", 0.0]]

    def test_bars_colour_sign_and_format_by_language(self):
        pl = charts.strategy_chart(spec(self.ROWS), "pl")
        en = charts.strategy_chart(spec(self.ROWS), "en")
        for html_, title, sub in ((pl, "Tytuł wykresu", "Podtytuł"), (en, "Chart title", "Subtitle")):
            self.assertTrue(html_.startswith('<div class="chart-card">'))
            self.assertIn(f'<h2 class="ch">{title}</h2>', html_)
            self.assertIn(f'<p class="sub">{sub}</p>', html_)
            self.assertEqual(html_.count("<svg"), 2)                              # wariant szeroki i kompaktowy
            self.assertEqual(html_.count("<rect"), 6)                              # po trzy słupki w każdym wariancie
            self.assertIn("fill:var(--up)", html_)
            self.assertIn("fill:var(--down)", html_)
        self.assertIn("+12,3%", pl)
        self.assertIn("−4,5%", pl)                                                 # minus typograficzny
        self.assertIn("+12.3%", en)
        self.assertIn("−4.5%", en)
        self.assertNotIn("+12.3%", pl)

    def test_empty_or_broken_spec_gives_nothing(self):
        self.assertEqual(charts.strategy_chart(spec([]), "pl"), "")
        self.assertEqual(charts.strategy_chart(spec([["A", None]]), "pl"), "")
        self.assertEqual(charts.strategy_chart({"unit": "%", "rows": [["A", 1.0]]}, "pl"), "")          # brak tytułu
        self.assertEqual(charts.strategy_chart({"unit": "%", "rows": [["A", 1.0]], "title": {"pl": "x"}, "sub": {"pl": "y"}}, "en"), "")

    def test_language_is_restored_and_labels_are_escaped(self):
        charts.LANG = "pl"
        charts.strategy_chart(spec([["<b>X</b>", 1.0]]), "en")
        self.assertEqual(charts.LANG, "pl")
        out = charts.strategy_chart(spec([["<b>X</b>", 1.0]]), "pl")
        self.assertNotIn("<b>X</b>", out)
        self.assertIn("&lt;b&gt;X&lt;/b&gt;", out)

    def test_large_values_are_drawn_without_decimals(self):
        out = charts.strategy_chart(spec([["A", 250.0], ["B", -120.0]], "×"), "pl")
        self.assertIn("+250×", out)
        self.assertIn("−120×", out)


class ReportBodyTests(unittest.TestCase):
    TEXT = ("# Raport\n\nWstęp.\n\n## Sygnał\n\nTreść.\n\n## Indeksy\n\n| A | B |\n|---|---|\n| 1 | +5,0% |\n\n<!-- chart -->\n\n"
            "## Jak czytać\n\nTreść.\n\n## Ograniczenia\n\nTreść.\n")

    def test_chart_replaces_marker_and_toc_precedes_first_section(self):
        sig = {"chart": spec([["A", 5.0]])}
        out = build.strategy_body(self.TEXT, sig, "pl")
        self.assertNotIn("<!-- chart -->", out)
        self.assertIn('<div class="chart-card">', out)
        self.assertLess(out.index('<nav class="toc"'), out.index("<h2"))
        self.assertLess(out.index("Indeksy"), out.index("chart-card"))              # wykres stoi w miejscu znacznika, po nagłówku sekcji
        self.assertIn('<td class="up">+5,0%</td>', out)

    def test_report_without_chart_data_still_renders(self):
        out = build.strategy_body(self.TEXT, {"chart": spec([])}, "pl")
        self.assertNotIn("chart-card", out)
        self.assertNotIn("<!-- chart -->", out)
        self.assertIn("<h2", out)
        self.assertNotIn("chart-card", build.strategy_body(self.TEXT, {}, "en"))


class PortfolioPageTests(fx.RunCase):
    def test_pages_of_a_portfolio_with_positions(self):
        run.run_all(asof=fx.LAST)
        run.run_all(asof="2026-11-12")
        kompas = registry.BY_SLUG["kompas"]
        st = engine.load("kompas")
        pl = portfel.render_strategy(st, kompas, "pl", run.last_signal("kompas"))
        en = portfel.render_strategy(st, registry.BY_SLUG["kompas"], "en", run.last_signal("kompas"))
        self.assertIn("<h1>Portfel Kompas</h1>", pl)
        self.assertIn("<h1>Compass Portfolio</h1>", en)
        self.assertIn("nie porada inwestycyjna", pl)
        self.assertIn("not investment advice", en)
        for needle in ("Wartość portfela", "Zamknięte transakcje", "Plan transakcji", "Zasady portfela", "Wzorzec porównania", "Kapitał:"):
            self.assertIn(needle, pl, needle)
        for needle in ("Portfolio value", "Closed trades", "Planned trades", "Portfolio rules", "Benchmark:", "Capital:"):
            self.assertIn(needle, en, needle)
        self.assertIn("<strong>MWIG40</strong>", pl)                                # otwarta pozycja
        self.assertIn("<strong>Co trzymamy:</strong>", pl)                          # zasady z rejestru, pogrubienia zamienione na HTML
        self.assertNotIn("**", pl)
        self.assertIn("Portfel działa od krótkiego czasu", pl)                       # mniej niż 60 sesji
        self.assertIn("has been running only briefly", en)
        self.assertEqual(pl.count('<div class="chart-card">'), 1)
        self.assertIn("<polyline", pl)                                              # krzywa kapitału
        self.assertIn("polyline class=\"bm\"", pl)                                  # i WIG20 do porównania

    def test_portfolio_without_trades_and_golden_mean_note(self):
        run.run_all(asof=fx.LAST)
        zloty = registry.BY_SLUG["zloty-srodek"]
        st = engine.load("zloty-srodek")
        pl = portfel.render_strategy(st, zloty, "pl", run.last_signal("zloty-srodek"))
        en = portfel.render_strategy(st, zloty, "en", run.last_signal("zloty-srodek"))
        self.assertIn("Złoty Środek czeka na dane fundamentalne", pl)
        self.assertIn("Golden Mean is waiting for fundamental data", en)
        self.assertIn("Brak otwartych pozycji.", pl)
        self.assertIn("No open positions.", en)
        self.assertIn("Pojawi się po kilku sesjach", pl)                            # jeden punkt kapitału: jeszcze bez krzywej
        self.assertIn("<h1>Golden Mean Portfolio</h1>", en)

    def test_events_portfolio_shows_stop_column(self):
        self.add_stock("EVT", [106.0 if d >= "2026-11-09" else 100.0 for d in self.days],
                       edit={"2026-11-09": {"open": 103.0, "low": 102.5, "high": 106.5, "volume": 500000.0}})
        self.finish()
        run.run_all(asof=fx.LAST, only=["dryf"])
        run.run_all(asof="2026-11-12", only=["dryf"])
        st = engine.load("dryf")
        self.assertEqual([(p["tic"], p["entry_date"], p["stop"]) for p in st["positions"]], [("EVT", "2026-11-10", 100.0)])
        pl = portfel.render_strategy(st, registry.BY_SLUG["dryf"], "pl", run.last_signal("dryf"))
        self.assertIn("<th>Stop</th>", pl)
        self.assertIn("100,00", pl)
        self.assertIn("<h1>Portfel Dryf</h1>", pl)
        self.assertIn("Kupno EVT: 94 szt. po 106", pl)                                # dziennik
        en = portfel.render_strategy(st, registry.BY_SLUG["dryf"], "en", run.last_signal("dryf"))
        self.assertIn("<h1>Drift Portfolio</h1>", en)
        self.assertIn("Bought EVT: 94 units at 106", en)


class BuildStrategyTests(fx.RunCase):
    def setUp(self):
        super().setUp()
        self.site = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.site, True)
        for patcher in (mock.patch.object(build, "ROOT", self.site), mock.patch.object(build, "PAGES", []),
                        mock.patch.object(build, "PORTS", list(registry.SLUGS))):
            patcher.start()
            self.addCleanup(patcher.stop)

    def copy_methodology(self, slug):
        """Prawdziwe pliki metodologii z repozytorium (sprawdza też, że się budują)."""
        (self.strat_dir / slug).mkdir(parents=True, exist_ok=True)
        for name in ("metodologia.md", "metodologia.en.md"):
            shutil.copy(REPO / "strategie" / slug / name, self.strat_dir / slug / name)

    def test_all_pages_of_a_strategy_in_both_languages(self):
        run.run_all(asof=fx.LAST, only=["kompas"])
        run.run_all(asof="2026-12-03", only=["kompas"])
        self.copy_methodology("kompas")
        strat = registry.BY_SLUG["kompas"]
        self.assertEqual(build.build_strategy("pl", strat), "2026-11-30")
        self.assertEqual(build.build_strategy("en", strat), "2026-11-30")
        pl = {p.relative_to(self.site).as_posix() for p in self.site.rglob("*.html") if "en/" not in p.relative_to(self.site).as_posix()}
        self.assertEqual(pl, {"kompas.html", "kompas-archiwum.html", "metodologia-kompas.html", "portfel-kompas.html",
                              "kompas/2026-11-06.html", "kompas/2026-11-30.html"})
        en = {p.relative_to(self.site / "en").as_posix() for p in (self.site / "en").rglob("*.html")}
        self.assertEqual(en, {"compass.html", "compass-archive.html", "methodology-compass.html", "portfolio-compass.html",
                              "compass/2026-11-06.html", "compass/2026-11-30.html"})
        latest = (self.site / "kompas.html").read_text(encoding="utf-8")
        self.assertEqual(latest.count("<h1"), 1)
        self.assertIn("<title>Kompas Raport 30.11.2026 · GPW Radar</title>", latest)
        self.assertIn('<link rel="canonical" href="https://', latest)
        self.assertIn('hreflang="en"', latest)
        self.assertIn('href="portfel-kompas.html"', latest)                          # w menu i w pasku nad raportem
        self.assertIn('<div class="dd on">', latest)                                  # aktywna grupa Kompas
        self.assertIn("Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.", latest)
        self.assertIn('<div class="chart-card">', latest)
        daily = (self.site / "kompas" / "2026-11-06.html").read_text(encoding="utf-8")
        self.assertIn('href="../kompas-archiwum.html"', daily)                       # linki względne w podkatalogu
        archive = (self.site / "kompas-archiwum.html").read_text(encoding="utf-8")
        self.assertLess(archive.index("30.11.2026"), archive.index("6.11.2026"))        # od najnowszego
        self.assertIn('href="strategie/kompas/pl/2026-11-30.md"', archive)
        en_archive = (self.site / "en" / "compass-archive.html").read_text(encoding="utf-8")
        self.assertIn('href="../strategie/kompas/en/2026-11-30.md"', en_archive)       # źródła .md leżą pod polskim slugiem
        method = (self.site / "metodologia-kompas.html").read_text(encoding="utf-8")
        self.assertEqual(method.count("<h1"), 1)
        self.assertIn("Kompas", method)
        port = (self.site / "portfel-kompas.html").read_text(encoding="utf-8")
        self.assertIn("<h1>Portfel Kompas</h1>", port)
        self.assertIn("Portfolio value", (self.site / "en" / "portfolio-compass.html").read_text(encoding="utf-8"))

    def test_sitemap_registry_gets_a_pair_for_every_page(self):
        run.run_all(asof=fx.LAST, only=["ped"])
        self.copy_methodology("ped")
        strat = registry.BY_SLUG["ped"]
        build.build_strategy("pl", strat)
        build.build_strategy("en", strat)
        urls = {p["url"] for p in build.PAGES}
        self.assertEqual(len(build.PAGES), 10)                                         # raport, dzienny, archiwum, metodologia, portfel x 2 języki
        for page in build.PAGES:
            self.assertTrue(page["pl"].startswith("https://") and "/en/" in page["en"], page)
            self.assertIn(page["url"], (page["pl"], page["en"]))
        self.assertEqual(len(urls), 10)
        self.assertTrue(any(u.endswith("/en/momentum.html") for u in urls))
        self.assertTrue(any(u.endswith("/ped/2026-11-06.html") for u in urls))

    def test_strategy_without_reports_shows_a_placeholder(self):
        strat = registry.BY_SLUG["dryf"]
        self.assertIsNone(build.build_strategy("pl", strat))
        page = (self.site / "dryf.html").read_text(encoding="utf-8")
        self.assertIn("Pierwszy raport tej strategii jest w przygotowaniu.", page)
        self.assertEqual(page.count("<h1"), 1)
        arch = (self.site / "dryf-archiwum.html").read_text(encoding="utf-8")
        self.assertIn("Pierwszy raport tej strategii jest w przygotowaniu.", arch)
        self.assertFalse((self.site / "portfel-dryf.html").exists())                  # bez stanu portfela nie ma strony portfela
        self.assertFalse((self.site / "metodologia-dryf.html").exists())               # ani metodologii bez pliku

    def test_english_falls_back_to_polish_methodology_with_a_notice(self):
        run.run_all(asof=fx.LAST, only=["przystan"])
        shutil.copy(REPO / "strategie" / "przystan" / "metodologia.md", self.strat_dir / "przystan" / "metodologia.md")      # bez wersji EN
        build.build_strategy("en", registry.BY_SLUG["przystan"])
        page = (self.site / "en" / "methodology-harbor.html").read_text(encoding="utf-8")
        self.assertIn('<div class="banner">', page)
        self.assertEqual(page.count("<h1"), 1)


if __name__ == "__main__":
    unittest.main()
