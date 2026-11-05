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
