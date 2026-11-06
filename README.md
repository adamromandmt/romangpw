# GPW Radar

Dzienny skaner swing GPW, publikowany na https://www.gpwradar.pl (GitHub Pages; gpwradar.pl przekierowuje na www w nazwa.pl; dawny adres romangpw.pl przekierowuje na nowy).

- `METHOD.md` — instrukcja i metodyka dla codziennego zaplanowanego zadania (ok. 4:00, dni robocze, Europe/Warsaw).
- `metodologia-swing.md` — strona „Swing Metodologia" (opis metody dla początkujących; aktualizuj razem z `METHOD.md`).
- `reports/YYYY-MM-DD.md` — raporty (archiwum, poprzedni raport służy do rozliczenia).
- `build.py` — generuje strony HTML (raporty, archiwa, newsy, portfel, metodologię) z Markdown (`pip install markdown`) oraz `sitemap.xml`, `robots.txt`, `manifest.webmanifest` i `404.html`; wykresy SVG (także wersje kompaktowe na telefon) liczy `charts.py`.
- `tools/make_assets.py` — jednorazowo generuje obrazy z logo: `favicon-32.png`, `favicon.ico`, `apple-touch-icon.png`, `icon-192/512.png`, `icon-maskable-512.png` oraz `og-pl.png` / `og-en.png` (podgląd linku). Uruchamiać ręcznie po zmianie logo (`pip install playwright pillow`).
- Wersja angielska: strony w `en/` (przełącznik PL/EN w lewym górnym rogu, domyślnie polski). Źródła tłumaczeń: `reports-en/`, `dywidendy-en/`, `metodologia-swing.en.md`; wykresy zawsze z polskich raportów. Brak tłumaczenia = polski tekst z informacją na stronie EN.
- `CNAME` — domena własna dla GitHub Pages.

Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.

## Zakładka Newsy dnia
- `NEWS-METHOD.md` — kryteria wyboru newsów (ocena istotności, język bez emocji, format); `newsy/sources.json` — źródła, progi i lista osób (edytowalne bez zmian w kodzie).
- `newsy/RRRR-MM-DD.md` (PL) i `newsy-en/` (EN) — wydania; w dni bez istotnych wiadomości wydanie nie powstaje. Strony: `newsy.html`, `en/news.html`.

## Zakładka Dywidendy
- `METHOD-DYWIDENDY.md` — instrukcja skanera „dywidenda przed ogłoszeniem"; uruchamiany tylko na wyraźną prośbę (bez zadania cyklicznego).
- `dywidendy/YYYY-MM-DD.md` — raporty; `dividends.py` (historia i kotwice sezonowe), `trendscan.py` (trend, płynność), `divrank.py` (punktacja i poziomy).
- `data/dividends/` — historia dywidend (raw_*.csv), `verify/*.json` (weryfikacja ESPI), `judgement.json` (oceny), `data/quotes/` — notowania.

## Zakładka Portfel Swing
- `paper.py` — silnik wirtualnego portfela (sprawdzian prognoz ze skanera swing: stopy i cele), `portfel.py` — render strony, `paper/swing/state.json` — stan, `paper/swing/quotes/` — notowania pozycji. Kolejne strategie: `paper/<nazwa>/`. Opis kroków dziennych w `METHOD.md` (sekcja „Portfel wirtualny").
