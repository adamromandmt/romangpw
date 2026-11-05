# METHOD-DYWIDENDY — skaner „dywidenda przed ogłoszeniem" (GPW)

Instrukcja dla cyklicznego zadania, które aktualizuje zakładkę **Dywidendy** na romangpw.pl. Raport jest po polsku, plik `dywidendy/YYYY-MM-DD.md`. Zadanie działa niezależnie od codziennego skanera swing (`METHOD.md`) — nie zmieniaj plików `reports/`.

## Cel

Wskazać spółki z GPW, które:

1. **regularnie wypłacają dywidendę** (dywidenda za co najmniej 4 z ostatnich 5 lat obrotowych, bez dużych dziur),
2. **jeszcze nie ogłosiły dywidendy za bieżący cykl** (brak rekomendacji zarządu ani uchwały WZA w ostatnich 12 miesiącach dla tego cyklu) — czyli informacja dopiero nadejdzie,
3. są w **trendzie wzrostowym** i **płynne**,
4. mają **szacowane okno ogłoszenia** (rekomendacji zarządu) w najbliższych tygodniach/miesiącach.

Hipoteza: informacja o dywidendzie zgodnej z historią lub wyższej bywa katalizatorem wzrostu kursu przed lub w dniu ogłoszenia. To hipoteza, nie reguła — raport ma ją testować, a nie zakładać (patrz „Rozliczenie").

## Dane (powtarzalna procedura)

Powłoka nie ma dostępu do portali finansowych. Dane pobieraj WebFetch (równolegle, przez podagentów przy dużych listach).

1. **Historia dywidend**: `https://www.biznesradar.pl/dywidendy/akcje_gpw,<rok>,3,1` dla lat bieżący−5 … bieżący+1 → `data/dividends/raw_<rok>.csv` (nagłówek `ticker,company,fiscal_year,agm_date,last_cum_date,pay_date,dps_pln,status`). Odśwież co najmniej lata bieżący i bieżący−1; starsze tylko, gdy brakuje. Uzupełnienia: `strefainwestorow.pl/dane/dywidendy/<rok>`, bankier.pl.
2. `python3 dividends.py pool` → `data/dividends/pool.json` (kotwice sezonowe WZA, szacowane okno rekomendacji, status sezonu). Reguły: seria ≥ 4 z 5 lat; okno rekomendacji ≈ data WZA − 50 dni (WZA maj–lip) lub − 25 dni (pozostałe), z rozstępem historycznym; ustawowe zwołanie WZA ≥ 26 dni przed terminem.
3. **Notowania** (ok. 50 sesji) z `https://www.biznesradar.pl/notowania-historyczne/<SYMBOL>?r=<losowa>` → `data/quotes/<TIC>.csv` (`date,open,high,low,close,volume`); aliasy symboli jak w `METHOD.md`. Sprawdź datę ostatniej świecy.
4. `python3 trendscan.py` → `data/dividends/trend.json`: EMA20, SMA50, RSI14, odległość od maksimum, obrót 20 sesji w PLN, stosunek wolumenu dni wzrostowych do spadkowych.
5. **Weryfikacja „czy już ogłosili"** dla krótkiej listy (obowiązkowa przed publikacją): ESPI/komunikaty (bankier.pl `/komunikaty`, strona IR, wyszukiwanie „rekomendacja zarządu dywidenda <spółka> 2026"), strefainwestorow.pl. Jeśli rekomendacja lub uchwała już padła — wyklucz z listy głównej i wpisz do „Odrzucone: już ogłoszone". Daty historycznych rekomendacji (2024–2026) ze ESPI zastępują szacunki z WZA, gdy są dostępne.

## Filtry i punktacja (0–100)

Filtry twarde: seria ≥ 4/5, brak ogłoszenia dla bieżącego cyklu, obrót 20 sesji ≥ ok. 200 tys. PLN (preferuj ≥ 500 tys.), brak wezwania/arbitrażu, kurs powyżej SMA50 lub EMA20 przy EMA20 > SMA50 (trend wzrostowy; korekta do 15% od maksimum jest dopuszczalna).

**Dyw/50** — jakość i timing dywidendy: regularność serii (0–15), stabilność/wzrost DPS (0–10), pewność okna (zbieżność historycznych dat, 0–10), bliskość okna (0–10), kondycja finansowa i zdolność do wypłaty (zysk, gotówka, polityka dywidendowa, ograniczenia nadzorcze dla banków; 0–5).
**Tech/50** — trend (0–15), pozycja względem EMA20/SMA50 i RSI (0–10), wolumen/akumulacja (0–10), płynność (0–10), R:R (0–5).
**Suma** = Dyw/50 + Tech/50. Klasy: **A** (≥ 75, okno ≤ 6 tygodni, bez czerwonych flag), **B** (60–74 lub okno dalsze), **C** (spekulacyjne/niepłynne lub niepewny timing).

## Poziomy handlowe

Wejście, stop (logiczna inwalidacja techniczna — poniżej niedawnego dołka/SMA50), C1, C2 (opory, ostatnie szczyty), R:R od środka strefy wejścia. Pamiętaj: **dywidenda kupiona przed dniem ex-dividend spada z kursem** — plan wyjścia ma być przed „dniem dywidendy" albo musi to uwzględniać (poziomy w raporcie są bez korekty o przyszłą dywidendę). Raport wskazuje ostatni dzień z prawem i szacowany dzień ex.

## Format raportu (`dywidendy/YYYY-MM-DD.md`)

Nagłówek: `# GPW dywidendy — <dzień tygodnia> <D miesiąc RRRR>`, linia o danych (data ostatnich notowań, źródła, stan historii dywidend).

1. **Metoda w skrócie** (3–4 zdania) i **Wniosek** (ile spółek przeszło, czy sezon sprzyja).
2. **Ranking** — tabela: `# | Tic | Spółka | Sektor | Kurs | Trend | Od maks. | RSI | Seria (lata) | Ost. DPS | Oczek. DPS | Okno od | Okno do | Dni do okna | Dyw/50 | Tech/50 | Suma | Klasa | Wejście | Stop | C1 | C2 | R (C1 / C2) | Raport`. **Nie zmieniaj nazw kolumn** (na ich podstawie powstają wykresy: kalendarz okien ogłoszeń, ranking, R:R). `Okno od`/`Okno do` jako daty ISO (`2026-12-01`). Liczby jak w `METHOD.md` (`26 220`, `5,40`).
3. **TOP 5 — analiza**: dlaczego interesująca, historia wypłat (tabela DPS za 5 lat, daty WZA/rekomendacji), polityka dywidendowa i zdolność do wypłaty, techniczna struktura, szacowane okno i jego wiarygodność, plan wejścia/wyjścia (przed/po ex-dividend), ryzyka (3–5), werdykt: STRONG SETUP / GOOD SETUP / WATCH / WAIT / AVOID (w sensie ramy skanera).
4. **Kalendarz dalszych okien** (kolejne 3–9 miesięcy): spółki z dobrym trendem, których okno jest dalej — tabela krótka.
5. **Odrzucone** — „już ogłoszone", „bez trendu", „niepłynne", „dziura w serii", z powodem.
6. **Rozliczenie poprzedniego skanu** — dla spółek z poprzedniego raportu: czy ogłosiły dywidendę (data, DPS vs oczekiwany), jak zareagował kurs w dniu ogłoszenia i w 5/10 sesji po (liczby). Zbieraj to konsekwentnie: to jedyny sposób, żeby sprawdzić, czy strategia w ogóle działa.
7. **Zastrzeżenia**: daty okien są szacunkiem z historycznych WZA, nie z komunikatów; co nie zostało zweryfikowane; ograniczenia danych.
8. Ostatnia linia: `Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.`

## Publikacja

1. Zapisz `dywidendy/YYYY-MM-DD.md` (nie nadpisuj starszych), zaktualizuj `data/`.
2. `pip install --break-system-packages markdown` (jeśli brak), `python3 build.py` → `dywidendy.html`, `dywidendy-archiwum.html`, `dywidendy/YYYY-MM-DD.html`.
3. Sprawdź, że `dywidendy.html` zawiera tabelę rankingu.
4. `git pull --rebase origin main`, potem `git add -A && git commit -m "Dywidendy GPW YYYY-MM-DD" && git push origin main` (trailery jak w sesji). Zadanie swing pushuje o 7:15 — nie uruchamiaj publikacji w tym samym czasie; przy konflikcie push `git pull --rebase` i ponów raz.
5. Jeśli push się nie uda, nie obchodź błędu; zakończ z opisem.

## Procedura cotygodniowa (zadanie cykliczne, poniedziałek rano)

Pełny przesiew 118 spółek już wykonano (5.11.2026). Co tydzień aktualizujesz tylko to, co mogło się zmienić; pełny przesiew powtarzaj w pierwszym przebiegu każdego kwartału (styczeń, kwiecień, lipiec, październik).

1. **Zakres.** Lista śledzona = spółki z tabeli rankingu ostatniego raportu + pliki `data/dividends/verify/*.json` + spółki z `data/dividends/pool_list.json`, których okno zaczyna się w ciągu 120 dni od dziś. Wyniki poprzedniego raportu przeczytaj w `dywidendy/` (najnowszy plik).
2. **Nowe ogłoszenia (najważniejszy krok).** Dla każdej spółki z listy śledzonej sprawdź w ESPI/IR/bankier/strefainwestorow, czy od poprzedniego raportu padła rekomendacja, zaliczka lub zapowiedź. Zaktualizuj `verify/<TIC>.json` (`announced_current_cycle`, `announcement_note`, historia). Spółkę z ogłoszeniem przenieś do „Rozliczenia" (nie do rankingu).
3. **Rozliczenie.** Dla każdego ogłoszenia: data, kwota vs oczekiwana (`exp_dps` w `judgement.json`), kurs zamknięcia w dniu ogłoszenia vs sesja wcześniej oraz po 5 sesjach (z `data/quotes/<TIC>.csv`; pobierz świeże notowania). Dopisz wiersz do tabeli „Wyniki hipotezy" na końcu raportu (kumulatywna, przenoś z poprzednich raportów) — to jedyny sposób sprawdzenia, czy strategia działa.
4. **Notowania.** Pobierz świeże notowania dla listy śledzonej (po jednej stronie biznesradaru naraz; podagenci ≤ 3 równoległe WebFetch, bo przy większej liczbie jest `RATE_LIMIT_EXCEEDED`). Zachowaj aliasy symboli (np. KGH→KGHM, PKN→ORLEN, ASB→ASBISC, MBR→MOBRUK, CBF→CYBER-FOLKS po wyszukaniu, EBP→ERSTEPL). Spółki z niewielkim obrotem mają luki w sesjach — to normalne. Odpowiedź WebFetch nie zawiera symbolu: po pobraniu sprawdź cenę i nazwę względem poprzedniego pliku (w pierwszym przebiegu zdarzyła się pomyłka PEO/ELT).
5. **Przeliczenie.** `python3 trendscan.py`, potem uzupełnij `data/dividends/judgement.json` dla nowych tickerów (sektor, `stab` 0–10, `health` 0–5, `exp_dps`, `last_dps`, `years`, `report`), `python3 divrank.py --today <dziś>` i do raportu wklej tabelę (kolumny dokładnie jak wyżej). Spółki bez trendu wzrostowego `divrank.py` pomija (komunikat na stderr) — wpisz je pod tabelą.
6. **Odświeżenie weryfikacji.** Pełne ponowne sprawdzenie (`verify/*.json`) tylko dla spółek, których plik ma więcej niż 45 dni, albo których okno zaczyna się w ciągu 45 dni, albo po publikacji raportu kwartalnego (zmiana wyników/polityki). Format `verify/<TIC>.json`: `{"tic","announced_current_cycle":"tak|nie|niejasne","announcement_note","history":[{"fy","rec_date","rec_dps","agm_date","final_dps","cum_date","source"}],"policy","next_reports":[{"what","date","source"}],"expected_rec_window":{"from","to","basis"},"results_note","flags":[],"confidence":"wysoka|średnia|niska","sources":[]}`. Daty rekomendacji bierz z komunikatów, nie z dat WZA; luki wpisuj jako null.
7. **Raport.** Zapisz `dywidendy/RRRR-MM-DD.md` w formacie z sekcji wyżej (data dzisiejsza, Europe/Warsaw), zbuduj (`python3 build.py`) i opublikuj (sekcja „Publikacja"). Zakończ krótkim podsumowaniem: co się zmieniło (nowe ogłoszenia, nowe wejścia/wyjścia z rankingu), czy push się udał.

**Znane pułapki danych (z pierwszego przebiegu):** biznesradar bywa błędny w datach (jesienne „agm_date" to czasem data komunikatu zarządu o zaliczce, nie WZA; MOL w forintach; LPP ma rok obrotowy luty–styczeń); dla banków i spółek z rekomendacją razem z raportem rocznym okno to marzec–maj, nie „WZA − 50 dni"; bankier.pl i PAP bywają niedostępne (nie obchodź blokad, użyj parkiet.com, strefainwestorow.pl, stron IR); terminarze raportów rocznych na kolejny rok pojawiają się zwykle w grudniu–styczniu.
