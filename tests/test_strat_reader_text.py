"""Teksty dla czytelnika (metodologie, raporty strategii, opisy w rejestrze) tłumaczą logikę na danych publicznych
i nie odsyłają do plików, skryptów, poleceń ani repozytorium. Instrukcje dla opiekuna są w README i w plikach METHOD*.md."""
import pathlib
import re
import unittest

import strat_fixture as fx
from strat import dryf, kompas, ped, przystan, registry, zloty

ROOT = pathlib.Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(
    r"data/|strategie/|paper/|\.json|\.csv|\.py\b|\.md\b|(?-i:METHOD)|python3?|repozytori|repositor|github|gitlab|workflow|"
    r"\bplik(u|i|iem|ach|ów)?\b|\bfiles?\b|skrypt|\bscripts?\b|`", re.IGNORECASE)


def offences(text):
    return sorted({m.group(0) for m in FORBIDDEN.finditer(text)})


class MethodologyTextTests(unittest.TestCase):
    def test_methodologies_have_no_maintainer_references(self):
        files = sorted((ROOT / "strategie").glob("*/metodologia*.md")) + [ROOT / "metodologia-swing.md", ROOT / "metodologia-swing.en.md"]
        self.assertEqual(len(files), 12)
        for f in files:
            with self.subTest(f.relative_to(ROOT).as_posix()):
                self.assertEqual(offences(f.read_text(encoding="utf-8")), [])

    def test_each_strategy_methodology_has_rule_history(self):
        for f in sorted((ROOT / "strategie").glob("*/metodologia*.md")):
            with self.subTest(f.relative_to(ROOT).as_posix()):
                text = f.read_text(encoding="utf-8")
                self.assertRegex(text, r"## (Historia zmian reguł|Rule change history)")
                self.assertRegex(text, r"(przegląd przed pierwszą transakcją|review before the first trade)")

    def test_registry_descriptions(self):
        for slug in registry.SLUGS:
            with self.subTest(slug):
                entry = next(x for x in registry.STRATEGIES if x["slug"] == slug)
                self.assertEqual(offences(repr({k: entry[k] for k in ("tagline", "cadence", "rules")})), [])


class ReportTextTests(fx.MarketCase):
    def make_market(self):
        self.three_indices()
        for i in range(1, 31):
            self.add_stock(f"S{i:02d}", fx.path(self.days, 100.0, 1.5 - 0.04 * (i - 1), 0.004 + 0.002 * (i - 1)), sector="banki" if i <= 5 else None)
        return self.ctx()

    def check(self, sig):
        for lang in ("pl", "en"):
            with self.subTest(lang):
                self.assertEqual(offences(sig["md"][lang]), [])

    def test_momentum_and_harbor_reports(self):
        ctx = self.make_market()
        self.check(ped.signal(ctx, fx.LAST, None, initial=True))
        self.check(przystan.signal(ctx, fx.LAST, None, initial=True))

    def test_compass_report(self):
        self.check(kompas.signal(self.make_market(), fx.LAST, None, initial=True))

    def test_golden_mean_waiting_report(self):
        sig = zloty.signal(self.make_market(), fx.LAST, None, initial=True, fund={})
        self.assertEqual(sig["headline"]["pl"], "Czeka na dane fundamentalne")
        self.check(sig)


if __name__ == "__main__":
    unittest.main()
