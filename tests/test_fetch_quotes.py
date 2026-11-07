"""Testy offline fetch_quotes.py: sztuczne pliki .xls i migawka GPW, bez dostępu do sieci.

Uruchomienie: python3 -m unittest discover -s tests -v   (wymaga xlrd i xlwt, zob. requirements*.txt)
"""
import csv
import io
import json
import re
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import xlwt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fetch_quotes as fq  # noqa: E402

HEADER = ["Data", "Nazwa", "ISIN", "Waluta", "Kurs otwarcia", "Kurs max", "Kurs min", "Kurs zamknięcia", "Zmiana", "Wolumen",
          "Liczba Transakcji", "Obrót", "Liczba otwartych pozycji", "Wartość otwartych pozycji", "Cena nominalna"]
HTML_PAGE = b"<!DOCTYPE html><html lang='pl'><body>brak notowan</body></html>"
ISIN_OF = {"AAA": "PLAAA0000011", "BBB": "PLBBB0000012", "ZZZ": "PLZZZ0000013", "KRVITAMIN": "PLKRVIT00019"}


def make_xls(rows):
    wb = xlwt.Workbook()
    ws = wb.add_sheet("Worksheet")
    for c, h in enumerate(HEADER):
        ws.write(0, c, h)
    for r, row in enumerate(rows, 1):
        for c, v in enumerate(row):
            ws.write(r, c, v)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def stock(d, name, isin, o, h, l, c, vol):
    return [d, name, isin, "PLN", o, h, l, c, 0.0, vol, 7, round(c * vol, 2), "", "", ""]


def index(d, name, o, h, l, c, turnover):
    return [d, name, "PL9999999999", "", o, h, l, c, 0.1, 0.0, 0.0, turnover, 0.0, 0.0, 0.0]


def fillers(d, n=60):
    """Dodatkowe instrumenty, by plik miał realistyczną liczbę wierszy (>= MIN_ROWS)."""
    return [stock(d, f"FILL{i:03d}", f"PLFILL{i:05d}0", 1.0, 1.1, 0.9, 1.0, 100) for i in range(n)]


def snapshot_html(pairs):
    head = "<tr><th></th><th>Op. na pap.</th><th>Nazwa</th><th>ISIN</th><th>Skrót</th><th>Waluta</th></tr>"
    body = "".join(f"<tr><td></td><td></td><td>{n}</td><td>{i}</td><td>{t}</td><td>PLN</td></tr>" for n, i, t in pairs)
    return f"<table><thead>{head}</thead><tbody>{body}</tbody></table>".encode()


def day_rows(d, variant):
    """Zawartość pliku akcji dla dnia d. AAA nie handluje 2026-11-05 (wolumen 0), BBB ma max poniżej zamknięcia."""
    k = int(d[-2:])
    rows = [
        stock(d, "AAA", ISIN_OF["AAA"], 10 + k / 10, 11 + k / 10, 9.9 + k / 10, 10.5 + k / 10, 0 if d == "2026-11-05" else 1000 + k),
        stock(d, "BBB", ISIN_OF["BBB"], 20.0, 20.5, 19.8, 20.6, 500),
        stock(d, "KRVITAMIN", ISIN_OF["KRVITAMIN"], 12.0, 12.6, 11.9, 12.4, 5),
        stock(d, "OTHERDAY", "PLOTHER00018", 1.0, 1.0, 1.0, 1.0, 10),
    ]
    if variant == "zzz":        # ZZZ jest w migawce, ale nigdy nie handluje
        rows.append(stock(d, "ZZZ", ISIN_OF["ZZZ"], 3.0, 3.0, 3.0, 3.0, 0))
    if variant == "stops":      # ZZZ handlował tylko do 2026-11-03
        rows.append(stock(d, "ZZZ", ISIN_OF["ZZZ"], 3.0, 3.1, 2.9, 3.0, 100 if d <= "2026-11-03" else 0))
    return make_xls(rows + fillers(d))


def day_indices(d):
    k = int(d[-2:])
    return make_xls([index(d, "WIG20", 4100 + k, 4180 + k, 4090 + k, 4150 + k, 2400167.18), index(d, "MWIG40", 10400.5, 10600.25, 10390.0, 10594.92, 373157.49),
                     index(d, "WIG20TR", 9000.0, 9100.0, 8990.0, 9050.0, 1.0)])


class FakeSite:
    SESSIONS = ["2026-11-02", "2026-11-03", "2026-11-05", "2026-11-06"]       # 2026-11-04 to dzień wolny

    def __init__(self, variant="base", fail=False):
        self.variant, self.fail, self.calls = variant, fail, []
        pairs = [("AAA", ISIN_OF["AAA"], "AAA"), ("BBB", ISIN_OF["BBB"], "BBB"), ("ZZZ", ISIN_OF["ZZZ"], "ZZZ")]
        pairs += [(f"FILL{i:03d}", f"PLFILL{i:05d}0", f"F{i:03d}") for i in range(110)]
        self.snapshot = snapshot_html(pairs)

    def __call__(self, url, timeout=40, tries=3):
        self.calls.append(url)
        if url == fq.SNAPSHOT:
            return self.snapshot
        if self.fail:
            raise urllib.error.URLError("sieć niedostępna")
        m = re.search(r"type=(\d+)&instrument=&date=(\d\d)-(\d\d)-(\d{4})", url)
        typ, d = int(m[1]), f"{m[4]}-{m[3]}-{m[2]}"
        if d not in self.SESSIONS:
            return HTML_PAGE
        return day_rows(d, self.variant) if typ == fq.STOCKS else day_indices(d)


class Env:
    """Tymczasowy katalog projektu z data/universe.json i podmienionymi ROOT/OUT/http_get."""

    def __init__(self, stocks, site):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "market").mkdir(parents=True)
        uni = {"stocks": stocks, "gpw_alias": {"KVT": "KRVITAMIN"}, "indices": ["WIG20", "MWIG40"]}
        (self.root / "data" / "universe.json").write_text(json.dumps(uni), encoding="utf-8")
        self.out = self.root / "data" / "market"
        self.patches = [mock.patch.object(fq, "ROOT", self.root), mock.patch.object(fq, "OUT", self.out),
                        mock.patch.object(fq, "http_get", site), mock.patch.object(fq, "CONFIRM_DELAY", 0)]

    def __enter__(self):
        for p in self.patches:
            p.start()
        return self

    def __exit__(self, *exc):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def run(self, *args, today="2026-11-09"):
        return fq.main(["fetch_quotes.py", "--days", "10", "--pause", "0", "--today", today, *args])

    def csv(self, name):
        with (self.out / name).open(encoding="utf-8", newline="") as fh:
            return {r["date"]: r for r in csv.DictReader(fh)}

    def json(self, name):
        return json.loads((self.out / name).read_text(encoding="utf-8"))


class ParsingTests(unittest.TestCase):
    def test_parse_snapshot_maps_by_header_and_ignores_junk(self):
        text = (b"<table><tr><th>x</th></tr>" b"<tr><th></th><th>Nazwa</th><th>ISIN</th><th>Skr\xc3\xb3t</th></tr>"
                b"<tr><td></td><td>PKOBP</td><td>PLPKO0000016</td><td>PKO</td></tr>"
                b"<tr><td></td><td>BRAK ISIN</td><td>-</td><td>XXX</td></tr>"
                b"<tr><td></td><td>LPP</td><td>PLLPP0000011</td><td>LPP</td></tr></table>").decode()
        by_isin, by_name = fq.parse_snapshot(text)
        self.assertEqual(by_isin, {"PLPKO0000016": "PKO", "PLLPP0000011": "LPP"})
        self.assertEqual(by_name, {"PKOBP": "PKO", "LPP": "LPP"})

    def test_parse_xls_reads_by_header_name_and_blank_cells(self):
        rows = fq.parse_xls(make_xls([stock("2026-11-06", "AAA", "PLAAA0000011", 1.0, 2.0, 0.5, 1.5, 10),
                                      ["2026-11-06", "CEEplus", "PL9999998948", "PLN", "", "", "", 2404.29, -1.08, "", "", "", "", "", ""]]))
        self.assertEqual(rows[0]["name"], "AAA")
        self.assertEqual((rows[0]["open"], rows[0]["close"], rows[0]["volume"]), (1.0, 1.5, 10.0))
        self.assertIsNone(rows[1]["open"])
        self.assertIsNone(fq.bar(rows[1], index=True))

    def test_parse_xls_rejects_unknown_layout(self):
        wb = xlwt.Workbook()
        wb.add_sheet("S").write(0, 0, "Cokolwiek")
        buf = io.BytesIO()
        wb.save(buf)
        with self.assertRaises(ValueError):
            fq.parse_xls(buf.getvalue())

    def test_bar_rules(self):
        base = {"open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "volume": 100.0, "turnover": 1050.0}
        self.assertEqual(fq.bar(base), ((10.0, 11.0, 9.0, 10.5, 100.0), False))
        self.assertIsNone(fq.bar({**base, "volume": 0.0}))                          # brak obrotu = brak świecy
        self.assertIsNone(fq.bar({**base, "open": None}))
        self.assertIsNone(fq.bar({**base, "close": 0.0}))
        self.assertEqual(fq.bar({**base, "high": 10.2}), ((10.0, 10.5, 9.0, 10.5, 100.0), True))   # max poniżej zamknięcia
        self.assertEqual(fq.bar({**base, "volume": 0.0, "turnover": 5.0}, index=True)[0][4], 5.0)  # indeks: obrót w polu volume
        self.assertEqual(fq.bar({**base, "volume": 0.0, "turnover": 0.0}, index=True)[0][4], 0.0)

    def test_fnum_keeps_precision_and_never_uses_exponent(self):
        self.assertEqual(fq.fnum(156000.97), "156000.97")
        self.assertEqual(fq.fnum(5647131.0), "5647131")
        self.assertEqual(fq.fnum(0.0), "0")
        self.assertEqual(fq.fnum(3.515), "3.515")
        self.assertEqual(fq.fnum(100.0), "100")

    def test_weekdays_skips_weekends(self):
        import datetime as dt
        days = [d.isoformat() for d in fq.weekdays(dt.date(2026, 11, 6), dt.date(2026, 11, 10))]
        self.assertEqual(days, ["2026-11-06", "2026-11-09", "2026-11-10"])


class EndToEndTests(unittest.TestCase):
    def test_full_run_writes_stocks_indices_calendar_and_status(self):
        site = FakeSite()
        with Env(["AAA", "BBB", "KVT", "CCC"], site) as env:
            self.assertEqual(env.run(), 0)
            aaa = env.csv("AAA.csv")
            self.assertEqual(sorted(aaa), ["2026-11-02", "2026-11-03", "2026-11-06"])   # 11-05 bez obrotu, 11-04 święto
            self.assertAlmostEqual(float(aaa["2026-11-06"]["close"]), 11.1, places=6)
            self.assertEqual(aaa["2026-11-06"]["volume"], "1006")
            bbb = env.csv("BBB.csv")["2026-11-06"]
            self.assertEqual((bbb["high"], bbb["close"]), ("20.6", "20.6"))               # max poprawione do zamknięcia
            kvt = env.csv("KVT.csv")                                                     # rozpoznane po nazwie (alias)
            self.assertEqual(sorted(kvt), ["2026-11-02", "2026-11-03", "2026-11-05", "2026-11-06"])
            self.assertFalse((env.out / "CCC.csv").exists())
            wig = env.csv("_WIG20.csv")["2026-11-06"]
            self.assertEqual((wig["close"], wig["volume"]), ("4156", "2400167.18"))        # obrót w tys. zł jako wolumen
            self.assertTrue((env.out / "_MWIG40.csv").exists())
            self.assertFalse((env.out / "_WIG20TR.csv").exists())
            cal = env.json("_calendar.json")
            self.assertEqual(cal["sessions"], FakeSite.SESSIONS)
            self.assertEqual(cal["closed"], ["2026-10-30", "2026-11-04"])                  # 11-09 jeszcze bez pliku: nie jest świętem
            st = env.json("_status.json")
            self.assertEqual((st["latest_session"], st["ok"], st["resolvable"], st["universe"]), ("2026-11-06", 3, 3, 4))
            self.assertIn("nierozpoznana", st["failed"]["CCC"])
            self.assertEqual(st["repaired_bars"], 4)                                       # BBB w czterech sesjach
            self.assertEqual(st["indices_last_date"], {"WIG20": "2026-11-06", "MWIG40": "2026-11-06"})
            self.assertEqual(env.json("_names.json")["isin"][ISIN_OF["KRVITAMIN"]], "KVT")  # ISIN zapamiętany po dopasowaniu nazwy

    def test_second_run_is_idempotent_and_refetches_only_latest_and_recent_gaps(self):
        site = FakeSite()
        with Env(["AAA", "BBB", "KVT"], site) as env:
            self.assertEqual(env.run(), 0)
            before = {p.name: p.read_text(encoding="utf-8") for p in env.out.iterdir() if p.name != "_status.json"}
            first_calls = len(site.calls)
            self.assertEqual(env.run(), 0)
            after = {p.name: p.read_text(encoding="utf-8") for p in env.out.iterdir() if p.name != "_status.json"}
            self.assertEqual(before, after)
            self.assertLess(len(site.calls) - first_calls, first_calls)       # sesje 02/03/05 nie są pobierane drugi raz

    def test_low_coverage_gives_nonzero_exit_and_reason(self):
        site = FakeSite(variant="zzz")
        with Env(["AAA", "BBB", "KVT", "ZZZ"], site) as env:
            self.assertEqual(env.run(), 1)                                   # ZZZ nigdy nie handluje: 3/4 < 85%
            st = env.json("_status.json")
            self.assertEqual(st["coverage"], 0.75)
            self.assertEqual(st["failed"], {"ZZZ": "brak danych w archiwum"})

    def test_ticker_that_stopped_trading_is_reported_as_behind(self):
        site = FakeSite(variant="stops")
        with Env(["AAA", "BBB", "KVT", "ZZZ"], site) as env:
            env.run()
            st = env.json("_status.json")
            self.assertEqual(st["behind_latest_session"], ["ZZZ"])
            self.assertEqual(st["failed"], {"ZZZ": "bez obrotu w najnowszej sesji (ostatni wiersz 2026-11-03)"})
            self.assertEqual(st["last_date"]["ZZZ"], "2026-11-03")

    def test_stale_data_gives_nonzero_exit(self):
        site = FakeSite()
        with Env(["AAA", "BBB", "KVT"], site) as env:
            self.assertEqual(env.run(), 0)
            self.assertEqual(env.run(today="2026-11-30"), 1)                 # ostatnia sesja sprzed 3 tygodni
            self.assertEqual(env.json("_status.json")["latest_session"], "2026-11-06")

    def test_circuit_breaker_stops_after_repeated_errors(self):
        site = FakeSite(fail=True)
        with Env(["AAA", "BBB", "KVT"], site) as env:
            self.assertEqual(env.run(), 1)
            self.assertEqual(len(site.calls), 1 + fq.MAX_CONSECUTIVE_ERRORS)   # migawka + 5 nieudanych sesji, reszta czeka
            st = env.json("_status.json")
            self.assertEqual(len(st["errors"]), fq.MAX_CONSECUTIVE_ERRORS)
            self.assertEqual(st["sessions_pending"], 2)

    def test_only_dates_does_not_write_status(self):
        site = FakeSite()
        with Env(["AAA", "BBB", "KVT"], site) as env:
            self.assertEqual(env.run("--only-dates", "2026-11-06"), 0)
            self.assertEqual(sorted(env.csv("AAA.csv")), ["2026-11-06"])
            self.assertFalse((env.out / "_status.json").exists())


if __name__ == "__main__":
    unittest.main()
