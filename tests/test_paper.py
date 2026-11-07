"""Testy silnika portfela wirtualnego (paper.py) na sztucznych świecach w tymczasowym data/market."""
import csv
import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import paper  # noqa: E402
import quotes  # noqa: E402


class PaperEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.market = Path(self.tmp.name)
        patcher = mock.patch.object(quotes, "MARKET", self.market)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def write(self, tic, rows):
        with (self.market / f"{tic}.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["date", "open", "high", "low", "close", "volume"])
            for r in rows:
                w.writerow([*r, 1000])

    @staticmethod
    def order(st, tic, limit=100, stop=95, c1=110, c2=120, valid_from="2026-11-09", shares=10):
        st["orders"].append({
            "id": st["next_id"], "tic": tic, "name": tic, "shares": shares, "limit": limit, "zone_lo": limit - 2, "stop": stop,
            "c1": c1, "c2": c2, "score": 70, "cls": "B", "report": "2026-11-06", "valid_from": valid_from,
            "expires": (dt.date.fromisoformat(valid_from) + dt.timedelta(days=6)).isoformat(), "checked_through": None})
        st["next_id"] += 1

    def test_reads_bars_from_market_directory(self):
        self.write("AAA", [("2026-11-10", 2, 3, 1, 2.5), ("2026-11-09", 1, 2, 0.5, 1.5)])
        self.assertEqual(paper.bars("AAA"), [("2026-11-09", 1.0, 2.0, 0.5, 1.5), ("2026-11-10", 2.0, 3.0, 1.0, 2.5)])
        self.assertIsNone(paper.bars("NOPE"))

    def test_fill_then_target_one_then_target_two(self):
        st = paper.new_state("2026-11-06")
        self.order(st, "AAA")
        self.write("AAA", [("2026-11-09", 101, 102, 99, 100.5), ("2026-11-10", 100, 112, 99, 111), ("2026-11-11", 111, 121, 110, 120)])
        self.assertEqual(paper.update(st, "2026-11-11"), [])
        c = st["closed"][0]
        self.assertEqual((c["entry"], c["pnl"], c["r"]), (100, 145.7, 2.91))
        self.assertEqual([(l["reason"], l["qty"], l["price"]) for l in c["legs"]], [("cel 1", 5, 110), ("cel 2", 5, 120)])
        self.assertAlmostEqual(st["cash"], 100145.7, places=2)

    def test_stop_wins_when_candle_touches_stop_and_target(self):
        st = paper.new_state()
        self.order(st, "BBB")
        self.write("BBB", [("2026-11-09", 100, 101, 98, 99.5), ("2026-11-10", 99, 115, 94, 96)])
        paper.update(st, "2026-11-10")
        c = st["closed"][0]
        self.assertEqual((c["exit_reason"], c["pnl"]), ("stop", -53.9))

    def test_gap_below_stop_exits_at_open(self):
        st = paper.new_state()
        self.order(st, "CCC")
        self.write("CCC", [("2026-11-09", 99, 101, 98, 100), ("2026-11-10", 90, 92, 88, 89)])
        paper.update(st, "2026-11-10")
        c = st["closed"][0]
        self.assertEqual((c["exit_reason"], c["legs"][0]["price"]), ("stop (luka)", 90.0))

    def test_open_below_stop_cancels_order(self):
        st = paper.new_state()
        self.order(st, "DDD")
        self.write("DDD", [("2026-11-09", 92, 94, 90, 93)])
        paper.update(st, "2026-11-09")
        self.assertEqual((st["positions"], st["orders"]), ([], []))
        self.assertEqual(st["log"][-1]["text"], "Anulowano zlecenie DDD: otwarcie 92 poniżej stopu 95")

    def test_unfilled_order_expires(self):
        st = paper.new_state()
        self.order(st, "EEE")
        self.write("EEE", [("2026-11-09", 110, 112, 108, 111), ("2026-11-12", 111, 113, 109, 112)])
        paper.update(st, "2026-11-16")
        self.assertEqual(st["orders"], [])
        self.assertEqual(st["log"][-1]["text"], "Zlecenie EEE wygasło bez realizacji (limit 100)")

    def test_stop_moves_to_entry_after_target_one(self):
        st = paper.new_state()
        self.order(st, "FFF")
        self.write("FFF", [("2026-11-09", 100, 101, 99, 100), ("2026-11-10", 100, 111, 99, 108), ("2026-11-11", 108, 109, 99, 101),
                           ("2026-11-12", 101, 102, 99, 100)])
        paper.update(st, "2026-11-12")
        c = st["closed"][0]
        self.assertEqual([(l["reason"], l["qty"], l["price"]) for l in c["legs"]], [("cel 1", 5, 110), ("stop na wejściu", 5, 100.0)])
        self.assertEqual(c["pnl"], 45.9)

    def test_exit_after_max_hold_days(self):
        st = paper.new_state()
        self.order(st, "GGG")
        rows, d = [("2026-11-09", 100, 101, 99, 100)], dt.date(2026, 11, 10)
        while d <= dt.date(2026, 12, 12):
            if d.weekday() < 5:
                rows.append((d.isoformat(), 101, 104, 100, 102))
            d += dt.timedelta(days=1)
        self.write("GGG", rows)
        paper.update(st, "2026-12-12")
        c = st["closed"][0]
        self.assertEqual((c["exit_reason"], c["exit_date"], c["days"]), ("czas (30 dni)", "2026-12-09", 30))

    def test_update_is_idempotent_and_mark_records_equity(self):
        st = paper.new_state()
        self.order(st, "HHH")
        self.write("HHH", [("2026-11-09", 100, 101, 99, 100.5), ("2026-11-10", 100.5, 105, 100, 104)])
        paper.update(st, "2026-11-10")
        first = (st["cash"], [dict(p) for p in st["positions"]])
        paper.update(st, "2026-11-10")
        self.assertEqual((st["cash"], st["positions"]), first)
        self.assertEqual(paper.mark(st, "2026-11-10"), {"date": "2026-11-10", "equity": 100038.0, "cash": 98998.0, "invested": 1040.0})

    def test_missing_quotes_are_reported(self):
        st = paper.new_state()
        self.order(st, "ZZZ")
        self.assertIn("brak notowań ZZZ", paper.update(st, "2026-11-10"))


if __name__ == "__main__":
    unittest.main()
