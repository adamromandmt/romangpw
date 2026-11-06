# romangpw

Dzienny skaner swing GPW, publikowany na https://www.romangpw.pl (GitHub Pages; romangpw.pl przekierowuje na www w nazwa.pl).

- `METHOD.md` — instrukcja i metodyka dla codziennego zaplanowanego zadania (7:15, dni robocze, Europe/Warsaw).
- `metodologia-swing.md` — strona „Swing Metodologia" (opis metody dla początkujących; aktualizuj razem z `METHOD.md`).
- `reports/YYYY-MM-DD.md` — raporty (archiwum, poprzedni raport służy do rozliczenia).
- `build.py` — generuje `index.html`, `archiwum.html` i `reports/*.html` z Markdown (`pip install markdown`).
- `CNAME` — domena własna dla GitHub Pages.

Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.

## Zakładka Dywidendy
- `METHOD-DYWIDENDY.md` — instrukcja dla cyklicznego skanera „dywidenda przed ogłoszeniem".
- `dywidendy/YYYY-MM-DD.md` — raporty; `dividends.py` (historia i kotwice sezonowe), `trendscan.py` (trend, płynność), `divrank.py` (punktacja i poziomy).
- `data/dividends/` — historia dywidend (raw_*.csv), `verify/*.json` (weryfikacja ESPI), `judgement.json` (oceny), `data/quotes/` — notowania.
