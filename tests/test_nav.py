"""Testy menu w nagłówku (build.nav_html): kolejność zakładek, rozwijane menu Swing i pięciu strategii uzupełniających
(Raport, Portfel, Metodologia, Archiwum), aktywna zakładka, brak portfela bez stanu.

Uruchomienie: python3 -m unittest discover -s tests -v   (wymaga pakietu markdown, zob. requirements.txt)
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build  # noqa: E402

SLUGS = ["kompas", "ped", "zloty-srodek", "przystan", "dryf"]
SLUGS_EN = ["compass", "momentum", "golden-mean", "harbor", "drift"]
NAMES_PL = ["Kompas", "Pęd", "Złoty Środek", "Przystań", "Dryf"]
NAMES_EN = ["Compass", "Momentum", "Golden Mean", "Harbor", "Drift"]


def links(nav):
    return re.findall(r'<a href="([^"]+)"', nav)


def menu_of(nav, group):
    """Fragment <ul> rozwijanego menu jednej grupy."""
    return re.search(rf'<ul class="dd-m" id="dd-{re.escape(group)}".*?</ul>', nav).group(0)


def strategy_links(slugs, lang):
    out = []
    for pl, en in zip(SLUGS, SLUGS_EN):
        if pl not in slugs:
            continue
        out += ([f"{pl}.html", f"portfel-{pl}.html", f"metodologia-{pl}.html", f"{pl}-archiwum.html"] if lang == "pl"
                else [f"{en}.html", f"portfolio-{en}.html", f"methodology-{en}.html", f"{en}-archive.html"])
    return out


class NavTests(unittest.TestCase):
    def setUp(self):
        self._ports = list(build.PORTS)
        build.PORTS[:] = ["swing"] + SLUGS

    def tearDown(self):
        build.PORTS[:] = self._ports

    def test_strategy_registry_matches_expectations(self):
        self.assertEqual([s["slug"] for s in build.STRATS], SLUGS)
        self.assertEqual([s["slug_en"] for s in build.STRATS], SLUGS_EN)
        self.assertEqual([s["name"]["pl"] for s in build.STRATS], NAMES_PL)
        self.assertEqual([s["name"]["en"] for s in build.STRATS], NAMES_EN)

    def test_order_news_then_swing_then_strategies_then_dividends(self):
        nav = build.nav_html("swing", "pl", "")
        self.assertEqual(links(nav), ["newsy.html", "index.html", "portfel-swing.html", "metodologia-swing.html", "archiwum.html",
                                      *strategy_links(SLUGS, "pl"), "dywidendy.html"])
        # sześć rozwijanych menu (Swing i pięć strategii), pozycje leżą wewnątrz nich
        self.assertEqual(nav.count('<div class="dd'), 6)
        self.assertEqual(links(menu_of(nav, "swing")), ["index.html", "portfel-swing.html", "metodologia-swing.html", "archiwum.html"])
        for slug in SLUGS:
            self.assertEqual(links(menu_of(nav, slug)), strategy_links([slug], "pl"), slug)

    def test_each_strategy_menu_is_report_portfolio_methodology_archive(self):
        for lang, names, slugs in (("pl", NAMES_PL, SLUGS), ("en", NAMES_EN, SLUGS_EN)):
            nav = build.nav_html("swing", lang, "")
            for slug, name, en_slug in zip(SLUGS, names, SLUGS_EN):
                labels = re.findall(r">([^<]+)</a>", menu_of(nav, slug))
                expected = ([f"{name} Raport", f"Portfel {name}", f"{name} Metodologia", f"{name} Archiwum"] if lang == "pl"
                            else [f"{name} Report", f"{name} Portfolio", f"{name} Methodology", f"{name} Archive"])
                self.assertEqual(labels, expected, (lang, slug))
                # przycisk grupy ma nazwę strategii
                self.assertRegex(nav, rf'aria-controls="dd-{re.escape(slug)}">{re.escape(name)}<svg')

    def test_english_labels_and_files(self):
        nav = build.nav_html("swing", "en", "")
        menu = menu_of(nav, "swing")
        self.assertEqual(re.findall(r">([^<]+)</a>", menu), ["Swing Report", "Swing Portfolio", "Swing Methodology", "Archive"])
        self.assertEqual(links(nav)[1], "index.html")
        self.assertIn("portfolio-swing.html", links(nav))
        self.assertEqual(links(nav)[5:-1], strategy_links(SLUGS, "en"))

    def test_group_active_on_every_swing_page(self):
        for key in ("swing", "port-swing", "meth", "arch"):
            nav = build.nav_html(key, "pl", "../")
            self.assertIn('<div class="dd on">', nav, key)
            self.assertEqual(nav.count('<div class="dd on">'), 1, key)
            self.assertEqual(nav.count('aria-current="page"'), 1, key)
            self.assertIn(f'href="../{build.fname(key, "pl")}" aria-current="page"', nav, key)
            self.assertIn('href="../newsy.html">', nav)  # ścieżki względne dla stron w podkatalogach

    def test_group_active_on_every_strategy_page(self):
        for slug in SLUGS:
            for prefix in ("rep", "port", "meth", "arch"):
                key = f"{prefix}-{slug}"
                for lang in ("pl", "en"):
                    nav = build.nav_html(key, lang, "../")
                    self.assertEqual(nav.count('<div class="dd on">'), 1, (key, lang))
                    self.assertEqual(nav.count('aria-current="page"'), 1, (key, lang))
                    self.assertIn(f'href="../{build.fname(key, lang)}" aria-current="page"', nav, (key, lang))
                    # podświetlona jest grupa tej strategii, nie inna
                    on = re.search(r'<div class="dd on">.*?<ul class="dd-m" id="dd-([^"]+)"', nav).group(1)
                    self.assertEqual(on, slug, (key, lang))

    def test_other_tabs_do_not_activate_group(self):
        for key, name in (("news", "newsy.html"), ("div", "dywidendy.html"), ("darch", "dywidendy.html"), (None, None)):
            nav = build.nav_html(key, "pl", "")
            self.assertNotIn('<div class="dd on">', nav, key)
            self.assertEqual(nav.count('<div class="dd">'), 6, key)
            self.assertEqual(nav.count('aria-current="page"'), 1 if name else 0, key)
            if name:
                self.assertIn(f'href="{name}" class="on" aria-current="page"', nav, key)  # archiwum dywidend podświetla Dywidendy

    def test_portfolio_item_skipped_without_state(self):
        build.PORTS[:] = []
        nav = build.nav_html("swing", "pl", "")
        self.assertFalse([x for x in links(nav) if x.startswith("portfel-")])
        build.PORTS[:] = ["kompas"]
        nav = build.nav_html("swing", "pl", "")
        self.assertEqual([x for x in links(nav) if x.startswith("portfel-")], ["portfel-kompas.html"])
        self.assertEqual(links(menu_of(nav, "kompas")), strategy_links(["kompas"], "pl"))
        self.assertEqual(links(menu_of(nav, "ped")), ["ped.html", "metodologia-ped.html", "ped-archiwum.html"])


if __name__ == "__main__":
    unittest.main()
