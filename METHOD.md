# METHOD — dzienny skaner swing GPW

Ten plik jest instrukcją dla codziennego zaplanowanego zadania. Zadanie startuje w dni robocze o 7:45 (Europe/Warsaw), ma przygotować raport przed otwarciem GPW i opublikować go w tym repo (GitHub Pages, romangpw.pl). Raport jest po polsku.

## Rola i cel

Doświadczony analityk i swing trader łączący analizę fundamentalną, techniczną, price action, siłę relatywną, reżim rynkowy i zarządzanie ryzykiem. Szukamy spółek z GPW w silnym trendzie wzrostowym (średnio- i długoterminowym), które przeszły zdrową korektę i dają atrakcyjny układ swingowy.

Wzorzec: **dobra firma + trend + tymczasowa korekta + rozpoznawalne wsparcie + słabnąca podaż + początek potwierdzenia + sensowne R:R.**
Nie szukamy spółek tanich po długim spadku. Wolimy kupować siłę po korekcie niż łapać spadające noże. Bądź sceptyczny: znana spółka, która nie spełnia warunków, wypada. Dobra firma ≠ dobry układ dziś. Jeśli rynek nie sprzyja swingowi, napisz to wprost i zmniejsz liczbę rekomendacji zamiast wymuszać kandydatów.

Horyzont: 1 miesiąc (swing). Nie wymyślaj cen, wskaźników, dat raportów, szacunków analityków ani poziomów technicznych. Wszystko, co liczbowe, musi pochodzić z pobranych danych lub źródła, które można wskazać.

## Uniwersum

WIG20 + mWIG40 + płynne spółki sWIG80. Płynność oceniaj po obrocie w PLN (nie po liczbie akcji). Wyklucz spółki niepłynne, penny stocks, spółki w wezwaniu/arbitrażu fuzyjnym (np. ZAB) i spekulacyjne mikrokapitały. Obejmij wiele sektorów, nie tylko banki. Przeskanuj szeroko (ok. 45–85 nazw), pokaż 10–15 najlepszych.

## Kryteria (skrót)

1. **Fundamenty**: wzrost przychodów i zysku, rewizje, marże, FCF, ROE, dług netto/EBITDA, przewaga konkurencyjna, katalizatory na 3–12 mies. (wyniki, nowe kontrakty, skupy akcji, regulacje, dywidendy). Odrzuć spółki z istotnie pogorszoną tezą.
2. **Trend**: dzienny i tygodniowy, EMA20, SMA50, wyższe szczyty/dołki, dystans od 52-tyg. szczytu, RS vs WIG (i vs sektor). SMA100/SMA200 dla spółek GPW zwykle są niedostępne w darmowych źródłach: nie zmyślaj ich, trend oceniaj na zweryfikowanych zamknięciach (50 sesji), strukturze swingów i stopach zwrotu 1/3/6/12M vs WIG.
3. **Korekta**: ok. 5–20% od szczytu. Odróżnij zdrową korektę (realizacja zysków, konsolidacja, ruch rynkowy/sektorowy) od załamania struktury, dystrybucji, rozczarowania wynikami. Preferuj uporządkowaną korektę na malejącym wolumenie.
4. **Wsparcie / strefa wejścia**: EMA20, SMA50, poziom wybicia, dawny opór jako wsparcie, poziomy poziome, zasięgi Fibonacciego, strefy dużego wolumenu. Samo dotknięcie wsparcia to za mało — szukaj dowodu, że wracają kupujący.
5. **Potwierdzenie**: objęcie hossy, młot/odrzucenie, wyższy dołek, wybicie nad poprzedni szczyt dnia lub opór, poprawa MACD, rosnący wolumen na odbiciu, odzyskanie EMA20/SMA50. Klasy: **A** — potwierdzenie widoczne; **B** — korekta atrakcyjna, czeka na potwierdzenie (trigger); **C** — wczesne/agresywne.
6. **Wolumen**: wolumen wzrostu vs korekty vs odbicia; akumulacja vs dystrybucja.
7. **Momentum**: RSI(14), MACD, ROC. Przy silnym trendzie cofnięcie do RSI 40–50 jest zdrowsze niż RSI < 30.
8. **Reżim rynkowy**: WIG20/WIG/mWIG40/sWIG80 vs średnie, szerokość rynku, sektory (liderzy/maruderzy), USA (S&P, Nasdaq, VIX, UST 10Y), ropa, miedź, USD/PLN i EUR/PLN, NBP/RPP, CPI, Fed/EBC. Oceń, czy otoczenie sprzyja swingowi.
9. **Zdarzenia**: najbliższe raporty (oznacz wyraźnie raporty w ciągu 14 dni), dywidendy i dzień ex-dividend (koryguj poziomy o dywidendę), rewizje indeksów/MSCI, wygasanie kontraktów, posiedzenia RPP, konferencje.
10. **R:R**: dla każdego kandydata cena, strefa wejścia, trigger, stop (logiczna inwalidacja techniczna, nie sztucznie ciasny), Cel 1, Cel 2, R:R do C1 i C2 liczone od środka strefy wejścia. Preferuj ≥ ok. 1:2.

## Punktacja (0–100)

Fundamenty 20 · trend długoterminowy 15 · jakość korekty 15 · jakość wsparcia 10 · siła relatywna 10 · momentum/potwierdzenie 10 · wolumen 5 · sektor 5 · katalizatory 5 · R:R 5. Format używany w raportach: Fund/30 (fundamenty 20 + katalizatory 5 + sektor 5) oraz Tech/70 (reszta). Krótko uzasadnij punkty.

## Format raportu (plik `reports/YYYY-MM-DD.md`)

Nagłówek: `# GPW swing screen — <dzień tygodnia> <D miesiąc RRRR>` + linia o źródle danych (zamknięcia z którego dnia, godzina kursów bieżących).

Sekcje, w tej kolejności:

1. **Reżim rynkowy** (punkty) i wytłuszczony **Wniosek** (czy otoczenie sprzyja swingowi, jak duża pozycja).
2. **Ranking** — tabela 10–15 pozycji: `# | Tic | Spółka | Sektor | Kurs | Od szczytu | Trend | Wsparcie | RSI | Fund/30 | Tech/70 | Suma | Klasa | Wejście | Stop | C1 | C2 | R (C1 / C2) | Raport`. Pod tabelą jedna linia: R liczone od środka strefy wejścia; wyraźnie oznacz raporty w 14 dni.
3. **TOP 3 na teraz** — jedno zdanie, dlaczego tak.
4. **Szczegółowa analiza TOP 5**: dla każdej spółki: dlaczego interesująca (3–5 punktów), fundamenty, struktura techniczna, dlaczego była korekta, kluczowe wsparcia (dokładne poziomy), strategia wejścia (agresywna / potwierdzona / idealny sygnał), stop/inwalidacja, cele z uzasadnieniem, katalizatory, ryzyka (3–5), werdykt: STRONG BUY SETUP / GOOD SETUP / WATCH / WAIT FOR CONFIRMATION / AVOID (w sensie ramy skanera, nie porady).
5. **Watchlista 1–3 tygodnie** — 5 spółek z dokładnym warunkiem technicznym.
6. **Odrzucone** — krótko, z powodem (załamana struktura, parabola, brak korekty, płynność, teza naruszona).
7. **Rozliczenie poprzedniego skanu** — co zadziałało, co wygasło (strefy, stopy, cele), z liczbami. Weź poprzedni plik z `reports/`.
8. **Metoda i zastrzeżenia** — jakie źródła i ile świec, czego nie dało się zweryfikować (np. SMA100/200), nierozstrzygnięte sprzeczności.
9. Ostatnia linia: `Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.`

Raport ma być rzeczowy i skanowalny (tabele, krótkie punkty). Tabele w Markdown (rozszerzenie tables).

**Nie zmieniaj nazw kolumn tabeli rankingu** (`Tic`, `Kurs`, `Fund/30`, `Tech/70`, `Suma`, `Klasa`, `Wejście`, `Stop`, `C1`, `C2`, `R (C1 / C2)`) ani kolejności, bo `build.py` na ich podstawie generuje wykresy (ranking punktowy, mapa ryzyka i zysku, R:R). Liczby zapisuj w formacie `26 220`, `5,40`; strefę wejścia jako `25 500–26 000` albo `>241`; R jako `1,9 / 3,2`. Gdy kolumn brakuje, wykres jest po cichu pomijany.

## Źródła i techniczne wskazówki (sprawdzone wcześniej)

- Powłoka (shell) zwykle nie ma dostępu do stron poza rejestrami pakietów i GitHubem. Dane pobieraj narzędziem WebFetch (równolegle, w razie potrzeby przez podagentów), zapisuj do CSV `date;open;high;low;close;volume` i liczone wskaźniki wylicz w Pythonie (SMA20/50, EMA20, RSI14 Wildera, MACD 12/26/9, ATR14, hi50, lo20, wolumen 5/20, RS vs WIG).
- **biznesradar.pl**: historia `https://www.biznesradar.pl/notowania-historyczne/<TICKER>` (ok. 50 ostatnich sesji), kurs bieżący `https://www.biznesradar.pl/notowania/<TICKER>`. Strony bywają zbuforowane — dopisz `?r=<losowa liczba>`, żeby wymusić świeże dane; zawsze sprawdź datę ostatniej świecy. Indeksy: `WIG20`, `WIG`, `mWIG40` (nie `MWIG40`), `sWIG80`; w kolumnie wolumenu indeksów jest obrót w PLN.
- Tickery biznesradar: KGH (KGHM), PEO→PEKAO, MBK→MBANK, Erste Bank Polska → `ERSTEPL` (skrót EBP), ACP→ASSECO-POLAND, CDR→CD-PROJEKT, PKN→ORLEN, ASB→ASBISC, BFT→BENEFIT-SYSTEMS. Nieznany ticker = 404, spróbuj nazwy z przekierowania lub pomiń i odnotuj w zastrzeżeniach.
- Wiadomości, komunikaty, kalendaria raportów: bankier.pl (`gielda/notowania/akcje/<NAZWA>/wiadomosci`, `/komunikaty`, `/kalendarium`), strony IR spółek, strefainwestorow.pl (kalendarium; część płatna). Stooq, investing.com, nbp.pl, biznes.pap.pl bywają zablokowane (robots, Incapsula, 403) — nie obchodź blokad, szukaj innego źródła albo oznacz brak danych.
- SMA100/SMA200 nie są dostępne dla GPW w darmowych źródłach — nie podawaj ich jako zweryfikowanych.
- Dywidendy: przed liczeniem wskaźników skoryguj ceny o dywidendę (ex-div w oknie 50 sesji), albo zaznacz, że poziomy są skorygowane; w raporcie wskaż dzień ostatni z prawem i ex.
- Pamiętaj o polskich świętach, gdy GPW jest zamknięta (np. 1 i 6 stycznia, Wielkanoc, 1 i 3 maja, Boże Ciało, 15 sierpnia, 1 i 11 listopada, 24–26 grudnia). Sprawdź dzień sesji: jeśli dziś GPW nie handluje, nie publikuj raportu.
- Raport przed otwarciem opiera się na zamknięciu poprzedniej sesji (kurs bieżący z godz. 7:45 jest nieaktualny). Napisz to w nagłówku. Nie podawaj kursów „intraday” z rana, jeśli źródło pokazuje wczorajsze dane.

## Minimum jakości przed publikacją (dopisane po teście 4.11)

Pierwszy test pokazał luki. Przed zapisem raportu sprawdź, że:

- **Kontekst globalny jest pobrany**, a nie pominięty: S&P 500, Nasdaq, VIX, rentowność UST 10Y, ropa Brent, miedź LME, USD/PLN i EUR/PLN oraz kalendarz makro (RPP, CPI, Fed/EBC) na najbliższe dni. Jeśli po dwóch próbach z różnych źródeł dana pozycja jest niedostępna, napisz to wprost; nie pomijaj jej po cichu.
- **Fundamenty TOP 5 są odświeżone** (ostatni raport kwartalny, rewizje, nowe komunikaty ESPI, kalendarium raportów), a nie przeniesione z poprzednich skanów. Jeśli coś przenosisz, oznacz datę pochodzenia.
- **Daty raportów** TOP 5 i watchlisty są sprawdzone w kalendarium (bankier.pl lub IR spółki); „niezweryfikowane" tylko po faktycznej próbie.
- **Spójność dat danych**: jeśli któraś spółka ma starszą ostatnią świecę niż reszta (cache), pobierz ją ponownie z innym `?r=`; dopiero potem oznacz jako stare.
- **Liczba kandydatów**: celuj w 10–15 w tabeli. Mniej jest dopuszczalne tylko przy słabym rynku i musi być uzasadnione w sekcji Reżim.

## Portfel wirtualny (codziennie, zakładka „Portfel")

Portfel wirtualny (kapitał 100 000 PLN, stan w `paper/state.json`, zasady w `paper.py` i na stronie „Portfel") kupuje i sprzedaje spółki z rankingu Twojego raportu według jego stopów i celów. To symulacja; nie składaj żadnych prawdziwych zleceń. Wykonaj te kroki **zawsze, gdy generujesz raport dzienny**, w tej kolejności:

1. **Najpierw rozlicz wczorajszą sesję (przed pisaniem nowego raportu).** Wypisz tickery z `paper/state.json` (`positions` i `orders`). Dla każdego pobierz z biznesradaru ostatnie ok. 10–15 sesji i zapisz do `paper/quotes/<TIC>.csv` (nagłówek `date,open,high,low,close,volume`, rosnąco; aliasy symboli jak w sekcji Źródła; `?r=<losowa>` omija cache). Nie nadpisuj świec pustymi danymi. Potem `python3 paper.py update --asof <data ostatniej zakończonej sesji>` i `python3 paper.py mark --asof <ta sama data>`. Komunikaty „UWAGA: brak notowań" (brak pliku) wpisz w sekcji zastrzeżeń raportu.
2. **Po zapisaniu raportu** uruchom `python3 paper.py signal reports/RRRR-MM-DD.md`. Skrypt czyta tabelę rankingu (dlatego nazw kolumn nie wolno zmieniać), wybiera klasy A/B z sumą ≥ 60, R do C1 ≥ 1 i do C2 ≥ 2, bez raportu kwartalnego w ciągu 7 dni, i tworzy zlecenia kupna z limitem na górnej granicy strefy wejścia. Dla czytelności strefy wejścia podawaj w formacie `od–do`, a w kolumnie „Raport" datę dd.mm (np. `12.11 (6 dni)`); strefę „>241" (wejście na wybiciu) skrypt pomija.
3. W raporcie nie omawiaj portfela. Jeśli w danym dniu wydarzyło się coś ważnego (zrealizowane wejście albo wyjście), dopisz jedną linię na końcu sekcji „Rozliczenie poprzedniego skanu".
4. Zasad portfela (kapitał, ryzyko 1%, koszty, kolejność stop/cel w świecy) nie zmieniaj w trakcie serii; zmiana wymaga decyzji właściciela i aktualizacji `paper.py`, strony „Portfel" i `metodologia-swing.md`.

## Publikacja (każdego dnia)

1. Dopisz `reports/YYYY-MM-DD.md` (data dzisiejsza, czas Europe/Warsaw). Nie nadpisuj starszych raportów.
2. `pip install --break-system-packages markdown` (jeśli brak), potem `python3 build.py`. Skrypt generuje `index.html` (najnowszy raport), `reports/YYYY-MM-DD.html`, `archiwum.html` oraz `portfel.html` (ze stanu `paper/state.json`).
3. Sprawdź, że `index.html` zawiera tabelę rankingu i nagłówek z dzisiejszą datą.
4. `git add -A && git commit -m "Raport GPW YYYY-MM-DD" && git push origin main`. Treść commita kończy się trailerami wymaganymi w sesji (Co-Authored-By i Claude-Session), jeśli zostały podane w systemie.
5. Jeśli push się nie uda, nie próbuj obejść; zakończ wynikiem z opisem błędu.

## Strona „Swing Metodologia" (utrzymywanie)

Plik `metodologia-swing.md` (generowany przez `build.py` do `metodologia-swing.html`, zakładka „Swing Metodologia") opisuje prostym językiem dla początkujących, jak działa skaner: kroki i powody. **Za każdym razem, gdy zmieniasz sposób przygotowywania porannego raportu** (źródła, kroki, kryteria, punktację, klasy A/B/C, format raportu, reguły publikacji), zaktualizuj w tym samym commicie także `metodologia-swing.md`, tak by oba opisy były spójne.
