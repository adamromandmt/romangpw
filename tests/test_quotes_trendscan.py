"""Testy wspólnego odczytu notowań (quotes.py) i skanera trendu dywidend (trendscan.py)."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import quotes  # noqa: E402
import trendscan  # noqa: E402


def write_csv(path, rows, header=("date", "open", "high", "low", "close", "volume")):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def series(n, start=100.0, step=1.0):
    """n rosnących sesji roboczych o kolejnych datach (od 2026-01-05)."""
    import datetime as dt
    out, d, price = [], dt.date(2026, 1, 5), start
    while len(out) < n:
        if d.weekday() < 5:
            out.append((d.isoformat(), price - 0.5, price + 1.0, price - 1.0, price, 1000 + len(out)))
            price += step
        d += dt.timedelta(days=1)
    return out


class QuotesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        patcher = mock.patch.object(quotes, "MARKET", self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_read_sorts_and_skips_malformed_rows(self):
        write_csv(self.dir / "AAA.csv", [("2026-11-10", 2, 3, 1, 2.5, 10), ("2026-11-09", 1, 2, 0.5, "x", 10), ("2026-11-06", 1, 2, 0.5, 1.5, 10)])
        rows = quotes.load("AAA")
        self.assertEqual([r["date"] for r in rows], ["2026-11-06", "2026-11-10"])
        self.assertEqual(rows[0], {"date": "2026-11-06", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10.0})

    def test_missing_or_empty_file_gives_none(self):
        self.assertIsNone(quotes.load("NOPE"))
        write_csv(self.dir / "EMPTY.csv", [])
        self.assertIsNone(quotes.load("EMPTY"))

    def test_status_reads_json_or_empty(self):
        self.assertEqual(quotes.status(), {})
        (self.dir / "_status.json").write_text(json.dumps({"latest_session": "2026-11-06"}), encoding="utf-8")
        self.assertEqual(quotes.status()["latest_session"], "2026-11-06")


class TrendscanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "market").mkdir()
        (self.root / "dividends").mkdir()
        for p in (mock.patch.object(quotes, "MARKET", self.root / "market"), mock.patch.object(trendscan, "D", self.root / "dividends")):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_load_uses_only_the_last_50_sessions(self):
        rows = series(260)
        write_csv(self.root / "market" / "AAA.csv", rows)
        got = trendscan.load("AAA")
        self.assertEqual(len(got), 50)
        self.assertEqual(got[0]["date"], rows[-50][0])
        self.assertEqual(got[-1]["close"], rows[-1][4])

    def test_metrics_on_trend_window(self):
        write_csv(self.root / "market" / "AAA.csv", series(260, start=100.0, step=1.0))
        m = trendscan.metrics(trendscan.load("AAA"))
        self.assertEqual(m["n"], 50)
        self.assertTrue(m["above_base"])
        self.assertTrue(m["ema20_gt_sma50"])
        self.assertAlmostEqual(m["ret_all"], (m["close"] / (m["close"] - 49) - 1) * 100, places=6)   # okno 50 sesji, nie rok
        self.assertEqual(m["hi_n"], m["close"] + 1.0)
        self.assertGreater(m["rsi"], 90)

    def test_main_writes_trend_json_and_reports_missing(self):
        write_csv(self.root / "market" / "AAA.csv", series(80))
        write_csv(self.root / "market" / "SHORT.csv", series(10))
        pool = [{"tic": t, "name": t, "win0": "2026-12-01", "win1": "2026-12-10", "next_agm": "2026-12-05"} for t in ("AAA", "SHORT", "NOPE")]
        (self.root / "dividends" / "pool_list.json").write_text(json.dumps(pool), encoding="utf-8")
        with mock.patch("sys.stdout"):
            self.assertEqual(trendscan.main([]), 0)
        res = json.loads((self.root / "dividends" / "trend.json").read_text(encoding="utf-8"))
        self.assertEqual(list(res), ["AAA"])                     # krótsze niż 15 sesji i brakujące są pomijane
        self.assertEqual(res["AAA"]["n"], 50)
        self.assertEqual(res["AAA"]["win0"], "2026-12-01")


if __name__ == "__main__":
    unittest.main()
