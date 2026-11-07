"""Testy ranking.py: wyciąganie tabeli rankingu z raportu, walidacja i zgodność ze schematem JSON."""
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import ranking  # noqa: E402

SCHEMA = json.loads((ROOT / "schemas" / "ranking.schema.json").read_text(encoding="utf-8"))
HEAD = "| # | Tic | Spółka | Sektor | Kurs | Od maks. 50s | Trend | Wsparcie | RSI | Fund/30 | Tech/70 | Suma | Klasa | Wejście | Stop | C1 | C2 | R (C1 / C2) | Raport |"
SEP = "|" + "---|" * 19
DAY = dt.date(2026, 11, 6)


def row(rank, tic, price="100", off="−3,5%", fund=20, tech=40, score=None, cls="B (retest)", entry="95–99", stop="92", c1="107", c2="117",
        r="2,0 / 4,0", earn="12.12"):
    """Domyślne poziomy dają R = 2,0 / 4,0 od środka strefy 95–99 (ryzyko 5, zyski 10 i 20); suma = Fund + Tech."""
    score = fund + tech if score is None else score
    return f"| {rank} | {tic} | Firma {tic} | banki | {price} | {off} | wzrostowy | {entry} | 55 | {fund} | {tech} | {score} | {cls} | {entry} | {stop} | {c1} | {c2} | {r} | {earn} |"


def report(*rows):
    return "# Raport\n\nWstęp.\n\n" + "\n".join([HEAD, SEP, *rows]) + "\n\nReszta.\n"


class ExtractTests(unittest.TestCase):
    def test_extracts_typed_fields(self):
        md = report(row(1, "AAA", price="1 610 (3.11)", off="−3,5% (korekta)", entry="95–99", r="2,0 / 4,0", earn="**12.11 (6 dni!)**"))
        data = ranking.extract(md, DAY)
        c = data["candidates"][0]
        self.assertEqual((data["schema"], data["date"], len(data["candidates"])), (1, "2026-11-06", 1))
        self.assertEqual((c["rank"], c["tic"], c["name"], c["sector"]), (1, "AAA", "Firma AAA", "banki"))
        self.assertEqual((c["price"], c["price_asof"], c["off_high_pct"], c["rsi"]), (1610.0, "2026-11-03", -3.5, 55.0))
        self.assertEqual((c["fund"], c["tech"], c["score"], c["class"], c["class_note"]), (20.0, 40.0, 60.0, "B", "(retest)"))
        self.assertEqual(c["entry"], {"lo": 95.0, "hi": 99.0, "breakout": False})
        self.assertEqual((c["stop"], c["t1"], c["t2"], c["r1"], c["r2"], c["r_basis"]), (92.0, 107.0, 117.0, 2.0, 4.0, "entry"))
        self.assertEqual(c["earnings"], {"text": "12.11 (6 dni!)", "date": "2026-11-12", "days": 6})
        jsonschema.validate(data, SCHEMA)

    def test_breakout_entry_and_price_basis(self):
        data = ranking.extract(report(row(1, "AAA", entry=">241 (zamknięcie)", stop="226", c1="250", c2="258", r="1,3 / 2,0 (od kursu)", price="236,60")), DAY)
        c = data["candidates"][0]
        self.assertEqual(c["entry"], {"lo": 241.0, "hi": 241.0, "breakout": True})
        self.assertEqual(c["r_basis"], "price")
        self.assertEqual(ranking.check(data), [])               # R od kursu 236,6: (250−236,6)/(236,6−226) = 1,26 ≈ 1,3

    def test_year_rolls_for_dates_around_new_year(self):
        data = ranking.extract(report(row(1, "AAA", earn="9.01 (64 dni)", price="100 (30.12)")), dt.date(2026, 12, 31))
        c = data["candidates"][0]
        self.assertEqual((c["earnings"]["date"], c["earnings"]["days"], c["price_asof"]), ("2027-01-09", 9, "2026-12-30"))

    def test_no_table_gives_error(self):
        data = ranking.extract("# Raport\n\nBez tabeli.\n", DAY)
        self.assertEqual(data["candidates"], [])
        self.assertEqual([p["level"] for p in ranking.check(data)], ["error"])

    def test_older_layout_without_name_and_sector_columns(self):
        md = ("| # | Tic | Kurs 12.10 | Od maks. | RSI | Fund/30 | Tech/70 | Suma | Klasa | Wejście | Stop | C1 | C2 | R | Raport |\n" + "|---|" * 15 + "\n"
              "| 1 | ALE | 54,0 | −2% | 60 | 20 | 40 | 60 | B | 52–54 | 50 | 57 | 60 | 1,6 / 3,5 | 12.11 |\n")
        c = ranking.extract(md, DAY)["candidates"][0]
        self.assertEqual((c["tic"], c["name"], c["sector"], c["price"], c["entry"]["lo"]), ("ALE", None, None, 54.0, 52.0))


class CheckTests(unittest.TestCase):
    def problems(self, *rows):
        return [(p["level"], p["tic"], p["msg"]) for p in ranking.check(ranking.extract(report(*rows), DAY))]

    def test_clean_report_has_no_problems(self):
        self.assertEqual(self.problems(row(1, "AAA", fund=22), row(2, "BBB")), [])

    def test_detects_duplicates_score_sum_and_order(self):
        got = self.problems(row(1, "AAA"), row(2, "AAA", fund=25), row(3, "CCC", score=70))
        levels = {(lvl, tic) for lvl, tic, _ in got}
        self.assertIn(("error", "AAA"), levels)
        self.assertIn(("warning", "AAA"), levels)           # 65 po 60: zła kolejność
        self.assertIn(("warning", "CCC"), levels)           # 20 + 40 ≠ 70 (i zła kolejność)

    def test_detects_wrong_r_and_level_order(self):
        got = self.problems(row(1, "AAA", r="3,5 / 6,0"), row(2, "BBB", stop="97"))
        self.assertTrue(any(t == "AAA" and "R w tabeli 3,5 / 6,0" in m and "2,0 / 4,0" in m for _, t, m in got), got)
        self.assertTrue(any(t == "BBB" and "poziomy nie rosną" in m for _, t, m in got), got)

    def test_missing_levels_and_class(self):
        got = self.problems(row(1, "AAA", stop="—", cls="—"))
        self.assertTrue(any("niekompletne poziomy" in m for _, _, m in got))
        self.assertTrue(any("brak klasy" in m for _, _, m in got))


class SidecarTests(unittest.TestCase):
    def test_write_sidecar_is_idempotent_and_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "2026-11-06.md"
            md.write_text(report(row(1, "AAA")), encoding="utf-8")
            data = ranking.write_sidecar(md)
            out = ranking.sidecar_path(md)
            first = out.stat().st_mtime_ns
            ranking.write_sidecar(md)
            self.assertEqual(out.stat().st_mtime_ns, first)          # bez zmian treści nie przepisujemy pliku
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), data)
            jsonschema.validate(data, SCHEMA)

    def test_all_repository_reports_have_a_valid_ranking(self):
        files = sorted((ROOT / "reports").glob("20??-??-??.md"))
        self.assertTrue(files)
        for f in files:
            data = ranking.build(f)
            jsonschema.validate(data, SCHEMA)
            errors = [p for p in ranking.check(data) if p["level"] == "error"]
            self.assertEqual(errors, [], f"{f.name}: {errors}")


if __name__ == "__main__":
    unittest.main()
