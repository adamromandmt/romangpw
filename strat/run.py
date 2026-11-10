"""Uruchamianie strategii uzupełniających: raporty Markdown (strategie/<slug>/pl|en/<data>.md), dane sygnałów
(strategie/<slug>/<data>.json) i wirtualne portfele (paper/<slug>/state.json).

Kolejność dla każdej daty sygnału S: portfel przetwarzany jest do dnia publikacji, moduł strategii liczy sygnał z danych do dnia S,
raport trafia do plików, a zlecenia czekają na otwarcie następnej sesji po publikacji. Sygnały miesięczne i kwartalne liczymy po
ostatniej sesji okresu, ale raport powstaje dopiero po pierwszej sesji nowego okresu (wtedy dane potwierdzają zmianę miesiąca),
więc zlecenia wykonują się na otwarciu drugiej sesji po S. Sygnał startowy (pierwsze uruchomienie) i skan dzienny Dryfu:
zlecenia na otwarciu sesji po S.
"""
import json

import quotes

from . import engine, lib, registry

MIN_COVERAGE = 0.8       # poniżej tego udziału spółek z notowaniem z ostatniej sesji nie liczymy sygnałów
MAX_CATCHUP = 60         # tyle zaległych dat sygnału nadrabiamy po przerwie (Dryf: sesji)


def report_dir(slug):
    return lib.STRAT_DIR / slug


def report_dates(slug):
    d = report_dir(slug) / "pl"
    return sorted(p.stem for p in d.glob("20??-??-??.md")) if d.exists() else []


def read_signal(slug, day):
    p = report_dir(slug) / f"{day}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def last_signal(slug):
    ds = report_dates(slug)
    return read_signal(slug, ds[-1]) if ds else None


def write_report(slug, sig):
    base = report_dir(slug)
    for lang in ("pl", "en"):
        (base / lang).mkdir(parents=True, exist_ok=True)
        (base / lang / f"{sig['date']}.md").write_text(sig["md"][lang], encoding="utf-8")
    meta = {k: v for k, v in sig.items() if k != "md"}
    (base / f"{sig['date']}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def coverage_ok():
    """Czy ostatnie pobranie notowań było kompletne (data/market/_status.json)."""
    cov = lib.load_json(quotes.MARKET / "_status.json", {}).get("coverage")
    return cov is None or cov >= MIN_COVERAGE


def _due(mod, full, prev):
    """Lista (data sygnału S, data publikacji Q, czy startowy)."""
    if mod.MONTHS is None:                                   # skan dzienny: każda sesja po ostatnim raporcie
        ds = [d for d in full.sessions if d > prev["date"]][-MAX_CATCHUP:]
        return [(d, d, False) for d in ds]
    out = []
    for S in lib.due_signal_dates(full.sessions, mod.MONTHS, prev["date"])[-MAX_CATCHUP:]:
        out.append((S, next(d for d in full.sessions if d > S), False))
    return out


def run_one(slug, asof=None, force=False, full=None):
    """Jedna strategia. Zwraca listę dat zapisanych raportów (pusta, gdy nic nie było do zrobienia)."""
    mod = registry.module(slug)
    full = full or lib.Ctx(asof)
    if not full.asof:
        return []
    st, prev = engine.load(slug), last_signal(slug)
    if st is None or prev is None:
        bench = full.indices.get(lib.BENCH)
        st = engine.new_state(mod.KIND, full.asof, bench.at(full.asof, "c") if bench else None, getattr(mod, "CFG", None))
        due = [(full.asof, full.asof, True)]
        prev = None
    elif force:
        due = [(full.asof, full.asof, False)]
        prev = next((read_signal(slug, d) for d in reversed(report_dates(slug)) if d < full.asof), None)
    else:
        due = _due(mod, full, prev)
    written = []
    for S, Q, initial in due:
        ctx = full if S == full.asof else lib.Ctx(S)
        engine.advance(st, Q, full)
        sig = mod.signal(ctx, S, prev, initial, st)
        write_report(slug, sig)
        if mod.KIND == "targets":
            engine.queue_targets(st, Q, sig["targets"], sig["why"], sig.get("size_factor", 1.0), sig.get("exit_reasons"))
        else:
            for o in sig.get("orders", []):
                engine.queue_order(st, Q, o["tic"], o["name"], o["stop"], o["event_date"], o["note"])
        prev = sig
        written.append(S)
    warns = engine.advance(st, full.asof, full)
    engine.save(slug, st)
    for w in warns:
        print(f"UWAGA {slug}: {w}")
    return written


def run_all(asof=None, only=None, force=False):
    """Wszystkie strategie (albo wskazane). Zwraca słownik slug -> daty zapisanych raportów."""
    full = lib.Ctx(asof)
    if not coverage_ok():
        print("UWAGA: niepełne notowania z ostatniej sesji (pokrycie poniżej progu), strategie pominięte.")
        return {}
    out = {}
    for slug in (only or registry.SLUGS):
        out[slug] = run_one(slug, asof, force, full)
    return out
