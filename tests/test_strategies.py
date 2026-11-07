"""Testy selektorów i silnika strategii (strategies.py) na danych syntetycznych."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import strategies as S  # noqa: E402


def series(n, start=100.0, step=0.5, vol=1000, first="2025-01-01"):
    import datetime as dt
    d0 = dt.date.fromisoformat(first)
    out, p = [], start
    for i in range(n):
        d = d0 + dt.timedelta(days=i)
        o = p
        p = p + step
        out.append({"date": d.isoformat(), "open": o, "high": p + 1, "low": o - 1, "close": p, "volume": vol})
    return out


class Selectors(unittest.TestCase):
    def test_kompas_needs_13_months(self):
        idx = {n: series(100) for n in S.INDEX_KEYS}
        pick, rows, short = S.kompas_pick(idx)
        self.assertTrue(short)
        self.assertIsNone(pick)

    def test_kompas_picks_strongest_above_average(self):
        idx = {"WIG20": series(500, step=0.1), "mWIG40": series(500, step=0.5), "sWIG80": series(500, step=0.2)}
        pick, rows, short = S.kompas_pick(idx)
        self.assertFalse(short)
        self.assertEqual(pick, "mWIG40")

    def test_kompas_cash_when_below_average(self):
        c = series(500, step=0.5)
        for x in c[-20:]:
            x["close"] = 1.0
        idx = {n: c for n in S.INDEX_KEYS}
        self.assertEqual(S.kompas_pick(idx)[0], "CASH")

    def test_ped_sector_cap_and_sma(self):
        st = {f"T{i}": series(300, step=0.1 * (i + 1)) for i in range(8)}
        sec = {t: "a" for t in st}
        chosen, _ = S.ped_rank(st, sec, n=12, per_sector=3)
        self.assertEqual(len(chosen), 3)
        self.assertEqual(chosen[0]["tic"], "T7")

    def test_ped_needs_history(self):
        self.assertEqual(S.ped_rank({"A": series(100)}, {})[1], [])

    def test_zloty_srodek_filters(self):
        f = [
            {"tic": "A", "sector": "x", "f_score": "8", "fcf": "10", "net_debt_ebitda": "1", "ev_ebit": "5", "gross_profit_assets": "0.5", "is_financial": "0", "is_energy": "0"},
            {"tic": "B", "sector": "x", "f_score": "6", "fcf": "10", "net_debt_ebitda": "1", "ev_ebit": "4", "gross_profit_assets": "0.6", "is_financial": "0", "is_energy": "0"},
            {"tic": "C", "sector": "bank", "f_score": "9", "fcf": "10", "net_debt_ebitda": "1", "ev_ebit": "3", "gross_profit_assets": "0.7", "is_financial": "1", "is_energy": "0"},
            {"tic": "D", "sector": "x", "f_score": "9", "fcf": "-1", "net_debt_ebitda": "1", "ev_ebit": "3", "gross_profit_assets": "0.7", "is_financial": "0", "is_energy": "0"},
        ]
        chosen, _ = S.zs_rank(f)
        self.assertEqual([r["tic"] for r in chosen], ["A"])

    def test_przystan_drawdown_filter(self):
        calm = series(300, step=0.01)
        crash = series(300, step=0.01)
        for x in crash[-100:-50]:
            x["close"] = 50.0
        st = {f"C{i}": series(300, step=0.01 * (i + 1)) for i in range(9)}
        st["X"] = crash
        chosen, rows = S.przystan_rank(st, {})
        self.assertNotIn("X", [r["tic"] for r in chosen])

    def test_dryf_gap_in_window(self):
        cs = series(40, step=0.0)
        cs[30].update(open=cs[29]["close"] * 1.05, volume=10000)
        sess = [c["date"] for c in cs]
        ev = S.dryf_events("A", cs, {cs[30]["date"]}, sess)
        self.assertEqual([(e[0], e[1]) for e in ev], [(cs[30]["date"], "up")])
        self.assertEqual(S.dryf_events("A", cs, set(), sess), [])

    def test_rebalance_calendar(self):
        self.assertTrue(S.is_rebalance("kompas", "2026-12-01", "2026-11-30"))
        self.assertFalse(S.is_rebalance("kompas", "2026-12-02", "2026-12-01"))
        self.assertTrue(S.is_rebalance("zloty-srodek", "2027-05-04", "2027-04-30"))
        self.assertFalse(S.is_rebalance("zloty-srodek", "2027-06-01", "2027-05-31"))
        self.assertTrue(S.is_rebalance("przystan", "2027-03-01", "2027-02-26"))


class Engine(unittest.TestCase):
    def test_waiting_strategy_stays_in_cash(self):
        d = S.Data(stocks={"A": series(60, first="2026-09-01")})
        st = S.build_state("ped", d)
        self.assertEqual(st["status"], "waiting")
        self.assertEqual(st["cash"], S.CAPITAL)
        self.assertEqual(st["positions"], [])


if __name__ == "__main__":
    unittest.main()
