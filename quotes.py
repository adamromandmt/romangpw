"""Wspólny odczyt notowań dziennych: jedno źródło dla skanera trendu, portfela wirtualnego i dywidend.

Podstawą jest data/market/<TIC>.csv, który co noc pobiera fetch_quotes.py z archiwum GPW (workflow „Notowania GPW").
Wiersze: date,open,high,low,close,volume. Ceny są surowe (bez korekt o dywidendy i splity), a dni bez obrotu nie mają
świecy. Plik data/market/_status.json opisuje aktualność i braki.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKET = ROOT / "data" / "market"
COLUMNS = ("open", "high", "low", "close", "volume")


def read_csv(path):
    """Świece z pliku CSV posortowane rosnąco po dacie albo None, gdy pliku nie ma. Wiersze z błędnymi liczbami są pomijane."""
    path = Path(path)
    if not path.exists():
        return None
    rows = []
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                rows.append({"date": r["date"], **{k: float(r[k]) for k in COLUMNS}})
            except (KeyError, ValueError, TypeError):
                continue
    rows.sort(key=lambda r: r["date"])
    return rows


def load(tic):
    """Świece spółki (lista słowników date/open/high/low/close/volume) albo None, gdy brak danych."""
    return read_csv(MARKET / f"{tic}.csv") or None


def status():
    """Zawartość data/market/_status.json albo pusty słownik."""
    p = MARKET / "_status.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
