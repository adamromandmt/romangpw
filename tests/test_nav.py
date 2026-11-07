"""Testy menu w nagłówku (build.nav_html): kolejność pozycji w rozwijanym menu Swing, aktywna zakładka, brak portfela.

Uruchomienie: python3 -m unittest discover -s tests -v   (wymaga pakietu markdown, zob. requirements.txt)
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build  # noqa: E402


def links(nav):
    return re.findall(r'<a href="([^"]+)"', nav)


class NavTests(unittest.TestCase):
    def setUp(self):
        self._ports = list(build.PORTS)
        build.PORTS[:] = ["swing"]

    def tearDown(self):
        build.PORTS[:] = self._ports

    def test_order_news_then_swing_menu_then_dividends(self):
        nav = build.nav_html("swing", "pl", "")
        self.assertEqual(links(nav), ["newsy.html", "index.html", "portfel-swing.html", "metodologia-swing.html", "archiwum.html",
                                      "dywidendy.html"])
        # jedno rozwijane menu o nazwie Swing, a pozycje leżą wewnątrz niego
        self.assertEqual(nav.count('<div class="dd'), 1)
        menu = re.search(r'<ul class="dd-m".*?</ul>', nav).group(0)
        self.assertEqual(links(menu), ["index.html", "portfel-swing.html", "metodologia-swing.html", "archiwum.html"])

    def test_english_labels(self):
        nav = build.nav_html("swing", "en", "")
        menu = re.search(r'<ul class="dd-m".*?</ul>', nav).group(0)
        self.assertEqual(re.findall(r">([^<]+)</a>", menu), ["Swing Report", "Swing Portfolio", "Swing Methodology", "Archive"])
        self.assertEqual(links(nav)[1], "index.html")
        self.assertIn("portfolio-swing.html", links(nav))

    def test_group_active_on_every_swing_page(self):
        for key in ("swing", "port-swing", "meth", "arch"):
            nav = build.nav_html(key, "pl", "../")
            self.assertIn('<div class="dd on">', nav, key)
            self.assertEqual(nav.count('aria-current="page"'), 1, key)
            self.assertIn(f'href="../{build.fname(key, "pl")}" aria-current="page"', nav, key)
            self.assertIn('href="../newsy.html">', nav)  # ścieżki względne dla stron w podkatalogach

    def test_other_tabs_do_not_activate_group(self):
        for key, name in (("news", "newsy.html"), ("div", "dywidendy.html"), ("darch", "dywidendy.html"), (None, None)):
            nav = build.nav_html(key, "pl", "")
            self.assertIn('<div class="dd">', nav, key)
            self.assertEqual(nav.count('aria-current="page"'), 1 if name else 0, key)
            if name:
                self.assertIn(f'href="{name}" class="on" aria-current="page"', nav, key)  # archiwum dywidend podświetla Dywidendy

    def test_portfolio_item_skipped_without_state(self):
        build.PORTS[:] = []
        self.assertNotIn("portfel-swing.html", links(build.nav_html("swing", "pl", "")))


if __name__ == "__main__":
    unittest.main()
