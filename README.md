# GPW Radar

Dzienny skaner swing GPW, publikowany na https://www.gpwradar.pl (GitHub Pages; gpwradar.pl przekierowuje na www w nazwa.pl; dawny adres romangpw.pl przekierowuje na nowy).

- `METHOD.md` — instrukcja i metodyka dla codziennego zaplanowanego zadania (ok. 4:00, dni robocze, Europe/Warsaw).
- `metodologia-swing.md` — strona „Swing Metodologia" (opis metody dla początkujących; aktualizuj razem z `METHOD.md`).
- `reports/YYYY-MM-DD.md` — raporty (archiwum, poprzedni raport służy do rozliczenia).
- `build.py` — generuje strony HTML (raporty, archiwa, newsy, portfel, metodologię) z Markdown (`pip install -r requirements.txt`) oraz `sitemap.xml`, `robots.txt`, `manifest.webmanifest`, `404.html` i kanały Atom z raportami swing (`feed.xml`, `en/feed.xml`); wykresy SVG (także wersje kompaktowe na telefon) liczy `charts.py`.
- `ranking.py` — ranking z raportu jako dane: tabelę parsuje w jednym miejscu, waliduje (powtórzenia, suma punktów, kolejność poziomów, R policzone z poziomów) i zapisuje `reports/YYYY-MM-DD.json` (schemat: `schemas/ranking.schema.json`); korzysta z niego `paper.py`, a `build.py` generuje pliki przy każdym buildzie. `python3 ranking.py check reports/YYYY-MM-DD.md` pokazuje problemy.
- `fetch_quotes.py` — pobiera notowania spółek i indeksów z oficjalnego archiwum GPW do `data/market/*.csv` (workflow `.github/workflows/quotes.yml`, nocą w dni robocze; `data/universe.json` — lista spółek; po dopisaniu symbolu uruchom workflow ręcznie z opcją `refetch`, która uzupełni jego historię); `quotes.py` — wspólny odczyt tych plików dla skanerów i portfela.
- `tests/` — testy jednostkowe (`pip install -r requirements-dev.txt`, potem `python -m pytest`), `tools/check_site.py` — statyczna kontrola strony; oba uruchamia CI (`.github/workflows/ci.yml`) po każdym pushu.
- `tools/make_assets.py` — jednorazowo generuje obrazy z logo: `favicon-32.png`, `favicon.ico`, `apple-touch-icon.png`, `icon-192/512.png`, `icon-maskable-512.png` oraz `og-pl.png` / `og-en.png` (podgląd linku). Uruchamiać ręcznie po zmianie logo (`pip install playwright pillow`).
- Wersja angielska: strony w `en/` (przełącznik PL/EN w lewym górnym rogu, domyślnie polski). Źródła tłumaczeń: `reports-en/`, `dywidendy-en/`, `metodologia-swing.en.md`; wykresy zawsze z polskich raportów. Brak tłumaczenia = polski tekst z informacją na stronie EN.
- `CNAME` — domena własna dla GitHub Pages.

Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.

## Menu w nagłówku
- Układ: **Newsy dnia** · **Swing ▾** · **Kompas ▾** · **Pęd ▾** · **Złoty Środek ▾** · **Przystań ▾** · **Dryf ▾** · **Dywidendy** · **Kontakt**. Każda strategia rozwija się w tej samej kolejności: Raport, Portfel, Metodologia, Archiwum. Definicja w `MENU` w `build.py`, nazwy grup w `UI[lang]["groups"]`, style i skrypt rozwijania w `CSS` i `NAV_JS` (klik, najechanie, klawiatura, telefon; bez JS działa `:hover`/`:focus-within`).
- Menu pięciu strategii uzupełniających powstaje z rejestru `strat/registry.py` (`STRATEGIES`: slug, nazwa PL/EN, opis), więc nowa strategia z rejestru dostaje zakładkę, strony i wpisy w mapie strony bez zmian w `MENU`. Pozycja Portfel pojawia się w menu tylko wtedy, gdy istnieje `paper/<slug>/state.json` (lista `build.PORTS`). Archiwum dywidend podświetla zakładkę Dywidendy (`NAV_ALIAS`). `tests/test_nav.py` pilnuje kolejności i aktywnej zakładki.
- Strategia swing (zakładka Swing) nie należy do rejestru: jej menu jest wpisane w `MENU` ręcznie.

## Zakładka Kontakt
- `kontakt.html` / `en/contact.html` — formularz do zadawania pytań i link do profilu LinkedIn (`build.contact_body`, stałe `LINKEDIN`, `WEB3FORMS_KEY` w `build.py`).
- Strona jest statyczna, więc pytania przekazuje usługa Web3Forms na skrzynkę przypisaną do klucza dostępu (klucz jest publiczny z założenia). Pusty `WEB3FORMS_KEY` = strona pokazuje sam link do LinkedIn, bez formularza.

## Zakładka Newsy dnia
- `NEWS-METHOD.md` — kryteria wyboru newsów (ocena istotności, język bez emocji, format); `newsy/sources.json` — źródła, progi i lista osób (edytowalne bez zmian w kodzie).
- `newsy/RRRR-MM-DD.md` (PL) i `newsy-en/` (EN) — wydania; w dni bez istotnych wiadomości wydanie nie powstaje. Strony: `newsy.html`, `en/news.html`.

## Zakładka Dywidendy
- `METHOD-DYWIDENDY.md` — instrukcja skanera „dywidenda przed ogłoszeniem"; uruchamiany tylko na wyraźną prośbę (bez zadania cyklicznego).
- `dywidendy/YYYY-MM-DD.md` — raporty; `dividends.py` (historia i kotwice sezonowe), `trendscan.py` (trend, płynność), `divrank.py` (punktacja i poziomy).
- `data/dividends/` — historia dywidend (raw_*.csv), `verify/*.json` (weryfikacja ESPI), `judgement.json` (oceny).

## Zakładka Portfel Swing
- `paper.py` — silnik wirtualnego portfela (sprawdzian prognoz ze skanera swing: stopy i cele), `portfel.py` — render strony, `paper/swing/state.json` — stan (notowania bierze z `data/market`). Opis kroków dziennych w `METHOD.md` (sekcja „Portfel wirtualny"). Portfele strategii uzupełniających: `paper/<slug>/state.json` (patrz niżej).

## Strategie uzupełniające: Kompas, Pęd, Złoty Środek, Przystań, Dryf
Pięć mechanicznych strategii na danych z `data/market`, każda z własnym raportem, portfelem wirtualnym (100 000 zł, prowizja 0,2% od transakcji, dywidendy w dniu ex, benchmark WIG20 w indeksie cenowym), metodologią i archiwum, po polsku i po angielsku. To testy w czasie rzeczywistym od dnia startu (6.11.2026), nie wyniki historyczne.

| Strategia (slug PL / EN) | Pomysł | Rytm |
|---|---|---|
| Kompas (`kompas` / `compass`) | rotacja WIG20, mWIG40, sWIG80 z filtrem trendu | miesięczny |
| Pęd (`ped` / `momentum`) | pęd 12-1 z filtrem średniej 200 sesji | miesięczny |
| Złoty Środek (`zloty-srodek` / `golden-mean`) | F-score Piotroskiego plus EV/EBIT | maj i październik |
| Przystań (`przystan` / `harbor`) | spółki o najniższej zmienności | kwartalny (3, 6, 9, 12) |
| Dryf (`dryf` / `drift`) | dryf po zaskakującym wzroście z dużym wolumenem | codziennie w oknach raportów |

- `strat/` — pakiet z logiką: `lib.py` (ceny skorygowane o dywidendy, wskaźniki, filtr płynności, wybór portfela z limitami sektorów, formatowanie), `engine.py` (silnik portfela: zlecenia na otwarciu następnej sesji, prowizja, dywidendy, krzywa kapitału; tryb „targets" dla portfeli docelowych i „events" dla Dryfu ze stopem i wyjściem czasowym), moduły reguł `kompas.py`, `ped.py`, `zloty.py`, `przystan.py`, `dryf.py`, `registry.py` (metadane: nazwy, slugi, opisy, rytm) i `run.py` (uruchomienie dzienne, nadrabianie brakujących sesji, raporty).
- Uruchomienie: `python3 -m strat daily` (wszystkie strategie), `--only kompas,ped` (wybrane), `--asof RRRR-MM-DD` (inna data), `--force` (przelicz sygnał mimo że termin nie wypada); `python3 -m strat status` pokazuje stan portfeli. Skrypt nie pobiera niczego z sieci: czyta `data/market`. Przy pokryciu notowań poniżej 80% spółek danego dnia raport się nie tworzy, żeby nie liczyć sygnałów z niepełnych danych.
- Wyniki: `strategie/<slug>/pl/RRRR-MM-DD.md` i `strategie/<slug>/en/RRRR-MM-DD.md` (raporty), `strategie/<slug>/RRRR-MM-DD.json` (sygnał jako dane), `paper/<slug>/state.json` (stan portfela). Metodologie: `strategie/<slug>/metodologia.md` i `metodologia.en.md` (ręcznie pisane, razem z hipotezą, dowodami z literatury i ograniczeniami; zmieniaj je razem z kodem reguł).
- Terminy: sygnał miesięczny i kwartalny powstaje na ostatniej sesji okresu, a raport dopiero po pierwszej sesji kolejnego okresu; zlecenia wykonują się na otwarciu drugiej sesji po sygnale. Pierwszy raport i skan dzienny Dryfu mają zlecenia na otwarciu najbliższej sesji.
- Dane pomocnicze: `data/sectors.json` (własny, przybliżony podział na sektory; służy tylko do limitów koncentracji), `data/fundamentals.csv` (sprawozdania roczne dla Złotego Środka, patrz `METHOD-ZLOTY-SRODEK.md`; dopóki plik ma sam nagłówek, Złoty Środek czeka na dane i stoi w gotówce), `strategie/wykluczenia.json` (ręczna lista spółek pomijanych przez strategie).
- Automat: `.github/workflows/strategies.yml` startuje po udanym workflow „Notowania GPW" (lub ręcznie z polami `only` i `force`), liczy sygnały, buduje stronę, commituje zmiany i prosi GitHub Pages o przebudowę. Testy: `tests/test_strat_*.py` (logika, silnik, strategie, Złoty Środek, uruchomienie i strona), `tests/test_nav.py` (menu).
- Zmiana reguł po starcie portfela psuje porównanie z dotychczasowym wynikiem. Jeśli trzeba ją wprowadzić, opisz w metodologii datę i powód, a portfel zacznij od nowa (usuń `paper/<slug>/`).
