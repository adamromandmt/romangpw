# GPW Radar

Dzienny skaner swing GPW, publikowany na https://www.gpwradar.pl (GitHub Pages; gpwradar.pl przekierowuje na www w nazwa.pl; dawny adres romangpw.pl przekierowuje na nowy).

- `METHOD.md` — instrukcja i metodyka dla codziennego zaplanowanego zadania (ok. 4:00, dni robocze, Europe/Warsaw).
- `metodologia-swing.md` — strona „Swing Metodologia" (opis metody dla początkujących; aktualizuj razem z `METHOD.md`).
- `reports/YYYY-MM-DD.md` — raporty (archiwum, poprzedni raport służy do rozliczenia).
- `build.py` — generuje strony HTML (raporty, archiwa, newsy, portfel, metodologię) z Markdown (`pip install -r requirements.txt`) oraz `sitemap.xml`, `robots.txt`, `manifest.webmanifest`, `404.html` i kanały Atom z raportami swing (`feed.xml`, `en/feed.xml`); wykresy SVG (także wersje kompaktowe na telefon) liczy `charts.py`.
- `ranking.py` — ranking z raportu jako dane: tabelę parsuje w jednym miejscu, waliduje (powtórzenia, suma punktów, kolejność poziomów, R policzone z poziomów) i zapisuje `reports/YYYY-MM-DD.json` (schemat: `schemas/ranking.schema.json`); korzysta z niego `paper.py`, a `build.py` generuje pliki przy każdym buildzie. `python3 ranking.py check reports/YYYY-MM-DD.md` pokazuje problemy.
- `fetch_quotes.py` — pobiera notowania spółek i indeksów z oficjalnego archiwum GPW do `data/market/*.csv` (workflow `.github/workflows/quotes.yml`, nocą w dni robocze; `data/universe.json` — lista spółek); `quotes.py` — wspólny odczyt tych plików dla skanerów i portfela.
- `tests/` — testy jednostkowe (`pip install -r requirements-dev.txt`, potem `python -m pytest`), `tools/check_site.py` — statyczna kontrola strony; oba uruchamia CI (`.github/workflows/ci.yml`) po każdym pushu.
- `tools/make_assets.py` — jednorazowo generuje obrazy z logo: `favicon-32.png`, `favicon.ico`, `apple-touch-icon.png`, `icon-192/512.png`, `icon-maskable-512.png` oraz `og-pl.png` / `og-en.png` (podgląd linku). Uruchamiać ręcznie po zmianie logo (`pip install playwright pillow`).
- Wersja angielska: strony w `en/` (przełącznik PL/EN w lewym górnym rogu, domyślnie polski). Źródła tłumaczeń: `reports-en/`, `dywidendy-en/`, `metodologia-swing.en.md`; wykresy zawsze z polskich raportów. Brak tłumaczenia = polski tekst z informacją na stronie EN.
- `CNAME` — domena własna dla GitHub Pages.

Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.

## Menu w nagłówku
- Układ: **Newsy dnia** · **Swing ▾** (rozwijane: Swing Raport, Portfel Swing, Swing Metodologia, Archiwum, w tej kolejności) · **Dywidendy**. Definicja w `MENU` w `build.py`, nazwy grup w `UI[lang]["groups"]`, style i skrypt rozwijania w `CSS` i `NAV_JS` (klik, najechanie, klawiatura, telefon; bez JS działa `:hover`/`:focus-within`).
- Kolejna strategia: dopisz do `MENU` wpis `("menu", "<klucz>", [raport, "port-<nazwa>", metodologia, archiwum])`, nazwę grupy do `UI["pl"]["groups"]` i `UI["en"]["groups"]`, a strony do `FILES` i `UI[lang]["tabs"]`. Archiwum dywidend podświetla zakładkę Dywidendy (`NAV_ALIAS`). `tests/test_nav.py` pilnuje kolejności i aktywnej zakładki.

## Zakładka Newsy dnia
- `NEWS-METHOD.md` — kryteria wyboru newsów (ocena istotności, język bez emocji, format); `newsy/sources.json` — źródła, progi i lista osób (edytowalne bez zmian w kodzie).
- `newsy/RRRR-MM-DD.md` (PL) i `newsy-en/` (EN) — wydania; w dni bez istotnych wiadomości wydanie nie powstaje. Strony: `newsy.html`, `en/news.html`.

## Zakładka Dywidendy
- `METHOD-DYWIDENDY.md` — instrukcja skanera „dywidenda przed ogłoszeniem"; uruchamiany tylko na wyraźną prośbę (bez zadania cyklicznego).
- `dywidendy/YYYY-MM-DD.md` — raporty; `dividends.py` (historia i kotwice sezonowe), `trendscan.py` (trend, płynność), `divrank.py` (punktacja i poziomy).
- `data/dividends/` — historia dywidend (raw_*.csv), `verify/*.json` (weryfikacja ESPI), `judgement.json` (oceny).

## Zakładka Portfel Swing
- `paper.py` — silnik wirtualnego portfela (sprawdzian prognoz ze skanera swing: stopy i cele), `portfel.py` — render strony, `paper/swing/state.json` — stan (notowania bierze z `data/market`). Kolejne strategie: `paper/<nazwa>/`. Opis kroków dziennych w `METHOD.md` (sekcja „Portfel wirtualny").
