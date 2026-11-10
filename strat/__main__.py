"""Wiersz poleceń: python3 -m strat daily [--asof RRRR-MM-DD] [--only slug,slug] [--force]  |  python3 -m strat status"""
import argparse
import sys

from . import engine, registry, run


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m strat", description="Strategie uzupełniające GPW Radar: raporty i portfele wirtualne.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("daily", help="policz zaległe sygnały, zapisz raporty i przesuń portfele do ostatniej sesji")
    d.add_argument("--asof", help="przytnij dane do tej daty (domyślnie ostatnia sesja)")
    d.add_argument("--only", help="tylko te strategie (slugi po przecinku)")
    d.add_argument("--force", action="store_true", help="policz sygnał na dzień asof mimo że nie przypada w kalendarzu (np. po uzupełnieniu danych)")
    sub.add_parser("status", help="pokaż ostatnie raporty i stan portfeli")
    a = ap.parse_args(argv)
    if a.cmd == "daily":
        only = [s.strip() for s in a.only.split(",")] if a.only else None
        bad = [s for s in (only or []) if s not in registry.BY_SLUG]
        if bad:
            print(f"Nieznana strategia: {', '.join(bad)}. Dostępne: {', '.join(registry.SLUGS)}", file=sys.stderr)
            return 2
        res = run.run_all(a.asof, only, a.force)
        for slug, days in res.items():
            print(f"{slug}: " + (f"raporty {', '.join(days)}" if days else "bez nowych sygnałów"))
        return 0
    for s in registry.STRATEGIES:
        ds = run.report_dates(s["slug"])
        st = engine.load(s["slug"])
        line = f"{s['slug']:13} raportów {len(ds):3}  ostatni {ds[-1] if ds else '—'}"
        if st:
            x = engine.stats(st)
            line += f"  kapitał {x['equity']:,.0f}  wynik {x['ret']:+.2f}%  WIG20 {x['bench_ret'] if x['bench_ret'] is not None else 0:+.2f}%"
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
