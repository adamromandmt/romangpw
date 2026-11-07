# METHOD — dzienny skaner swing GPW

Ten plik jest instrukcją dla codziennego zaplanowanego zadania. Zadanie startuje w dni robocze ok. 4:00 (Europe/Warsaw, 3:53), ma przygotować raport przed otwarciem GPW i opublikować go w tym repo (GitHub Pages, gpwradar.pl). Raport jest po polsku.

## Rola i cel

Doświadczony analityk i swing trader łączący analizę fundamentalną, techniczną, price action, siłę relatywną, reżim rynkowy i zarządzanie ryzykiem. Szukamy spółek z GPW w silnym trendzie wzrostowym (średnio- i długoterminowym), które przeszły zdrową korektę i dają atrakcyjny układ swingowy.

Wzorzec: **dobra firma + trend + tymczasowa korekta + rozpoznawalne wsparcie + słabnąca podaż + początek potwierdzenia + sensowne R:R.**
Nie szukamy spółek tanich po długim spadku. Wolimy kupować siłę po korekcie niż łapać spadające noże. Bądź sceptyczny: znana spółka, która nie spełnia warunków, wypada. Dobra firma ≠ dobry układ dziś. Jeśli rynek nie sprzyja swingowi, napisz to wprost i zmniejsz liczbę rekomendacji zamiast wymuszać kandydatów.

Horyzont: 1 miesiąc (swing). Nie wymyślaj cen, wskaźników, dat raportów, szacunków analityków ani poziomów technicznych. Wszystko, co liczbowe, musi pochodzić z pobranych danych lub źródła, które można wskazać.

## Uniwersum

WIG20 + mWIG40 + płynne spółki sWIG80. Płynność oceniaj po obrocie w PLN (nie po liczbie akcji). Wyklucz spółki niepłynne, penny stocks, spółki w wezwaniu/arbitrażu fuzyjnym (np. ZAB) i spekulacyjne mikrokapitały. Obejmij wiele sektorów, nie tylko banki. Przeskanuj szeroko (ok. 45–85 nazw), pokaż 10–15 najlepszych.

## Kryteria (skrót)

1. **Fundamenty**: wzrost przychodów i zysku, rewizje, marże, FCF, ROE, dług netto/EBITDA, przewaga konkurencyjna, katalizatory na 3–12 mies. (wyniki, nowe kontrakty, skupy akcji, regulacje, dywidendy). Odrzuć spółki z istotnie pogorszoną tezą.
2. **Trend**: dzienny i tygodniowy, EMA20, SMA50, SMA100 i SMA200 (liczone z `data/market`, gdy spółka ma ≥ 200 sesji; inaczej ich nie podawaj), wyższe szczyty/dołki, dystans od 52-tyg. szczytu (też z `data/market`), RS vs WIG (i vs sektor), stopy zwrotu 1/3/6/12M vs WIG. Dla symboli pobranych tylko przez WebFetch (ok. 50 sesji) nie zmyślaj SMA100/200 ani 52-tyg. szczytu: trend oceniaj na zweryfikowanych zamknięciach, strukturze swingów i stopach zwrotu.
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
3. **TOP 3 na teraz** — jedno zdanie, dlaczego tak. Format: lista numerowana `1. **LPP** — …`, w pogrubieniu ticker albo nazwa spółki dokładnie jak w kolumnach `Tic` / `Spółka` rankingu, w kolejności 1–3. `build.py` buduje z niej karty TOP 3 na górze raportu i chipy w archiwum; gdy nazwy nie pasują do wierszy rankingu, karty są po cichu pomijane. Nagłówki `##` trafiają jako chipy do paska sekcji u góry raportu, więc trzymaj je krótkie.
4. **Szczegółowa analiza TOP 5**: dla każdej spółki: dlaczego interesująca (3–5 punktów), fundamenty, struktura techniczna, dlaczego była korekta, kluczowe wsparcia (dokładne poziomy), strategia wejścia (agresywna / potwierdzona / idealny sygnał), stop/inwalidacja, cele z uzasadnieniem, katalizatory, ryzyka (3–5), werdykt: STRONG BUY SETUP / GOOD SETUP / WATCH / WAIT FOR CONFIRMATION / AVOID (w sensie ramy skanera, nie porady).
5. **Watchlista 1–3 tygodnie** — 5 spółek z dokładnym warunkiem technicznym.
6. **Odrzucone** — krótko, z powodem (załamana struktura, parabola, brak korekty, płynność, teza naruszona).
7. **Rozliczenie poprzedniego skanu** — co zadziałało, co wygasło (strefy, stopy, cele), z liczbami. Weź poprzedni plik z `reports/`.
8. **Metoda i zastrzeżenia** — jakie źródła i ile świec, czego nie dało się zweryfikować (np. symbole spoza `data/market` bez SMA100/200), nierozstrzygnięte sprzeczności.
9. Ostatnia linia: `Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.`

Raport ma być rzeczowy i skanowalny (tabele, krótkie punkty). Tabele w Markdown (rozszerzenie tables).

**Nie zmieniaj nazw kolumn tabeli rankingu** (`Tic`, `Kurs`, `Fund/30`, `Tech/70`, `Suma`, `Klasa`, `Wejście`, `Stop`, `C1`, `C2`, `R (C1 / C2)`) ani kolejności, bo `build.py` na ich podstawie generuje wykresy (ranking punktowy, mapa ryzyka i zysku, R:R). Liczby zapisuj w formacie `26 220`, `5,40`; strefę wejścia jako `25 500–26 000` albo `>241`; R jako `1,9 / 3,2`. Gdy kolumn brakuje, wykres jest po cichu pomijany.

**Po zapisaniu raportu sprawdź ranking:** `python3 ranking.py check reports/RRRR-MM-DD.md`. Skrypt wyciąga tabelę do danych (`reports/RRRR-MM-DD.json`, schemat w `schemas/ranking.schema.json`; plik zapisuje też `build.py`) i wypisuje błędy oraz uwagi: powtórzony ticker, suma różna od Fund + Tech, wiersze nieposortowane po sumie, poziomy niezgodne z regułą stop < wejście < C1 < C2 oraz **R niezgodne z poziomami**. R liczymy od środka strefy wejścia, a przy wejściu na wybiciu (`>241`) od poziomu wybicia; jeśli celowo liczysz od kursu, dopisz w komórce R „(od kursu)". Popraw tabelę i uruchom skrypt ponownie; uwagi, których nie da się usunąć, wyjaśnij w zastrzeżeniach raportu.

## Notowania z repozytorium (najpierw tu)

Workflow GitHub Actions `.github/workflows/quotes.yml` (codziennie ok. 2:15–3:15 czasu warszawskiego) uruchamia `fetch_quotes.py`, który pobiera dzienne OHLCV spółek i indeksów **z oficjalnego archiwum notowań GPW** (jeden plik .xls z całą sesją; lista spółek w `data/universe.json`) do `data/market/<TIC>.csv` (indeksy: `_WIG.csv`, `_WIG20.csv`, `_MWIG40.csv`, `_SWIG80.csv`, w kolumnie wolumenu jest obrót w tys. zł; ok. 260 sesji) i commituje je do repo. Ceny są **surowe** (bez korekt o dywidendy i splity), a wolumen to pełny wolumen sesji, więc bywa wyższy niż na biznesradarze (obejmuje transakcje pakietowe). Dzień bez obrotu nie daje świecy, więc słabo płynne spółki mają luki.

Podsumowanie przebiegu jest w `data/market/_status.json`: `latest_session`, `ok` i `coverage` (spółki z notowaniem w najnowszej sesji), `failed` (symbol → przyczyna: „nierozpoznana" = brak w GPW, prawdopodobnie wycofana lub zmieniony ticker; „bez obrotu w najnowszej sesji"), `behind_latest_session`, `last_date`, `short_history_under_200`, `suspect_jumps_over_30pct` (możliwy split), `calendar_gaps`. Pliki `_calendar.json` (sesje i dni wolne) oraz `_names.json` (mapa ISIN i nazw na tickery) są pomocnicze. **Ta sekcja ma pierwszeństwo przed ogólnym poleceniem z promptu zadania („dane pobieraj WebFetch"): WebFetch służy tylko do luk w notowaniach, wiadomości, kalendarzy raportów i kursów bieżących.**

Przed skanem: (1) `git pull`, odczytaj `data/market/_status.json` i sprawdź `run_utc` oraz `latest_session` — dane są użyteczne, jeśli `latest_session` to ostatnia zakończona sesja GPW. (2) Dla symboli z tego pliku licz wskaźniki w Pythonie bezpośrednio z CSV (pełna historia, także SMA100/200 i 52-tyg. szczyt — nie trzeba już ich pomijać, o ile liczba wierszy ≥ 200; symbole z `short_history_under_200` oznacz jako niepełne). Wokół dnia ex-dywidendy i splitu (`suspect_jumps_over_30pct`) seria jest nieskorygowana, więc odnotuj to przy poziomach. (3) WebFetch z biznesradaru używaj tylko dla luk: symboli spoza `data/market`, symboli z `failed` lub `behind_latest_session`, oraz do kursów bieżących i wiadomości. Jeśli plik statusu jest stary (> 1 dzień roboczy) albo go nie ma, wróć do pobierania przez WebFetch jak niżej i odnotuj to w sekcji „Metoda i zastrzeżenia". (4) Portfel wirtualny: `paper.py` czyta świece bezpośrednio z `data/market/<TIC>.csv` — nie kopiuj ani nie pobieraj ich osobno.

## Źródła i techniczne wskazówki (sprawdzone wcześniej)

- Powłoka (shell) zwykle nie ma dostępu do stron poza rejestrami pakietów i GitHubem. Dane pobieraj narzędziem WebFetch (równolegle, w razie potrzeby przez podagentów), zapisuj do CSV `date;open;high;low;close;volume` i liczone wskaźniki wylicz w Pythonie (SMA20/50, EMA20, RSI14 Wildera, MACD 12/26/9, ATR14, hi50, lo20, wolumen 5/20, RS vs WIG).
- **biznesradar.pl**: historia `https://www.biznesradar.pl/notowania-historyczne/<TICKER>` (ok. 50 ostatnich sesji), kurs bieżący `https://www.biznesradar.pl/notowania/<TICKER>`. Strony bywają zbuforowane — dopisz `?r=<losowa liczba>`, żeby wymusić świeże dane; zawsze sprawdź datę ostatniej świecy. Indeksy: `WIG20`, `WIG`, `mWIG40` (nie `MWIG40`), `sWIG80`; w kolumnie wolumenu indeksów jest obrót w PLN.
- Tickery biznesradar: KGH (KGHM), PEO→PEKAO, MBK→MBANK, Erste Bank Polska → `ERSTEPL` (skrót EBP), ACP→ASSECO-POLAND, CDR→CD-PROJEKT, PKN→ORLEN, ASB→ASBISC, BFT→BENEFIT-SYSTEMS. Nieznany ticker = 404, spróbuj nazwy z przekierowania lub pomiń i odnotuj w zastrzeżeniach.
- Wiadomości, komunikaty, kalendaria raportów: bankier.pl (`gielda/notowania/akcje/<NAZWA>/wiadomosci`, `/komunikaty`, `/kalendarium`), strony IR spółek, strefainwestorow.pl (kalendarium; część płatna). Stooq, investing.com, nbp.pl, biznes.pap.pl bywają zablokowane (robots, Incapsula, 403) — nie obchodź blokad, szukaj innego źródła albo oznacz brak danych.
- SMA100/SMA200 licz z `data/market` (≥ 200 sesji). Dla symboli pobranych tylko przez WebFetch (ok. 50 sesji) nie podawaj ich jako zweryfikowanych.
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

## Portfel Swing (codziennie, zakładka „Portfel Swing")

Portfel Swing (wirtualny sprawdzian prognoz: kapitał 100 000 PLN, pozycja do 5 000 PLN, stan w `paper/swing/state.json`, zasady w `paper.py` i na stronie „Portfel Swing") kupuje i sprzedaje spółki z rankingu Twojego raportu według jego stopów i celów. To symulacja; nie składaj żadnych prawdziwych zleceń. Wykonaj te kroki **zawsze, gdy generujesz raport dzienny**, w tej kolejności:

1. **Najpierw rozlicz wczorajszą sesję (przed pisaniem nowego raportu).** Wypisz tickery z `paper/swing/state.json` (`positions` i `orders`). `paper.py` czyta ich świece bezpośrednio z `data/market/<TIC>.csv` — nic nie kopiuj. Jeśli `latest_session` w `_status.json` jest starsza niż ostatnia zakończona sesja GPW albo ticker jest w `failed` lub `behind_latest_session`, dopisz brakujące sesje z biznesradaru do `data/market/<TIC>.csv` (nagłówek `date,open,high,low,close,volume`, rosnąco; aliasy symboli jak w sekcji Źródła; `?r=<losowa>` omija cache; nie nadpisuj świec pustymi danymi). Workflow przy następnym przebiegu zastąpi te wiersze danymi z GPW. Potem `python3 paper.py update --asof <data ostatniej zakończonej sesji>` i `python3 paper.py mark --asof <ta sama data>`. Komunikaty „UWAGA: brak notowań" (brak pliku) wpisz w sekcji zastrzeżeń raportu.
2. **Po zapisaniu raportu** uruchom `python3 paper.py signal reports/RRRR-MM-DD.md`. Skrypt czyta tabelę rankingu (dlatego nazw kolumn nie wolno zmieniać), wybiera klasy A/B z sumą ≥ 60, R do C1 ≥ 1 i do C2 ≥ 2, bez raportu kwartalnego w ciągu 7 dni, i tworzy zlecenia kupna z limitem na górnej granicy strefy wejścia. Dla czytelności strefy wejścia podawaj w formacie `od–do`, a w kolumnie „Raport" datę dd.mm (np. `12.11 (6 dni)`); strefę „>241" (wejście na wybiciu) skrypt pomija.
3. W raporcie nie omawiaj portfela. Jeśli w danym dniu wydarzyło się coś ważnego (zrealizowane wejście albo wyjście), dopisz jedną linię na końcu sekcji „Rozliczenie poprzedniego skanu".
4. Zasad portfela (kapitał, limit 5 000 PLN na pozycję, koszty, kolejność stop/cel w świecy) nie zmieniaj w trakcie serii; zmiana wymaga decyzji właściciela i aktualizacji `paper.py`. Portfel nie jest częścią metodologii: strona „Swing Metodologia" opisuje wyłącznie mechanizm wyszukiwania akcji, więc jej z tego powodu nie zmieniaj. Kolejne strategie dostaną własne katalogi `paper/<nazwa>/` i własną zakładkę z rozwijanym menu w nagłówku (wpis w `MENU` w `build.py`, jak Swing: Raport, „Portfel <nazwa>", „<Nazwa> Metodologia", Archiwum).

## Publikacja (każdego dnia)

1. Dopisz `reports/YYYY-MM-DD.md` (data dzisiejsza, czas Europe/Warsaw). Nie nadpisuj starszych raportów.
2. `pip install --break-system-packages -r requirements.txt` (jeśli brak), potem `python3 ranking.py check reports/YYYY-MM-DD.md` (popraw tabelę, jeśli są błędy lub uwagi o R i poziomach) i `python3 build.py`. Skrypt generuje `index.html` (najnowszy raport), `reports/YYYY-MM-DD.html` i `reports/YYYY-MM-DD.json` (dane rankingu), `archiwum.html` oraz `portfel-swing.html` (ze stanu `paper/swing/state.json`). Generuje też `sitemap.xml`, `robots.txt`, `manifest.webmanifest`, `404.html`, kanały Atom `feed.xml` i `en/feed.xml`, `favicon.svg` i `logo.svg` (nie edytuj ich ręcznie; `git add -A` zabierze je do commita). Obrazy (`og-pl.png`, `og-en.png`, `apple-touch-icon.png`, `icon-*.png`, `favicon-32.png`, `favicon.ico`) powstają osobno z `tools/make_assets.py` po zmianie logo i nie wymagają regeneracji w codziennym przebiegu.
3. **Wersja angielska.** Przed `python3 build.py` przetłumacz dzisiejszy raport na angielski i zapisz jako `reports-en/YYYY-MM-DD.md` (ta sama struktura: te same sekcje, wiersze i kolumny tabel). Tabela rankingu ma angielskie nagłówki dokładnie w tej kolejności: `# | Tic | Company | Sector | Price | From high | Trend | Support | RSI | Fund/30 | Tech/70 | Total | Class | Entry | Stop | T1 | T2 | R (T1 / T2) | Earnings`. Liczby w formacie angielskim (`26,220`, `5.40`, `25,500–26,000`, `1.9 / 3.2`), daty typu `3 Dec`, etykiety werdyktów bez zmian (STRONG BUY SETUP itd.), tytuł `# GPW swing screen — Friday 6 November 2026`, ostatnia linia `Screening exercise under the given framework, not investment advice.` Wykresy zawsze powstają z polskiego raportu, więc liczby w tabeli PL zostają w formacie polskim. Brak pliku EN nie psuje budowy: strona `en/` pokaże wtedy polski tekst z informacją o braku tłumaczenia. Następnie uruchom build (krok 2).
4. Sprawdź, że `index.html` i `en/index.html` zawierają tabelę rankingu i nagłówek z dzisiejszą datą.
5. `git add -A && git commit -m "Raport GPW YYYY-MM-DD" && git push origin main`. Treść commita kończy się trailerami wymaganymi w sesji (Co-Authored-By i Claude-Session), jeśli zostały podane w systemie.
6. Jeśli push się nie uda, nie próbuj obejść; zakończ wynikiem z opisem błędu.

## Newsy dnia (po opublikowaniu raportu swing)

Po tym, jak raport swing jest już opublikowany (push zakończony), wykonaj osobny krok „Newsy dnia" według `NEWS-METHOD.md` (kryteria, język bez emocji, format) i `newsy/sources.json` (źródła, progi). Zakładka nie ma stałego terminu wydań: **jeżeli żadna wiadomość nie przekracza progu `min_score`, nie twórz pliku ani commita** i napisz o tym w podsumowaniu. Gdy są istotne wiadomości: zapisz `newsy/RRRR-MM-DD.md`, przetłumacz na `newsy-en/RRRR-MM-DD.md`, `python3 build.py`, sprawdź `newsy.html` i `en/news.html`, osobny commit „Newsy dnia RRRR-MM-DD" i push (po `git pull --rebase origin main`). Błąd lub brak źródeł w tym kroku nie może blokować ani cofać raportu swing.

## Strona „Swing Metodologia" (utrzymywanie)

Plik `metodologia-swing.md` (generowany przez `build.py` do `metodologia-swing.html`, zakładka „Swing Metodologia") opisuje prostym językiem dla początkujących, jak działa skaner: kroki i powody. **Za każdym razem, gdy zmieniasz sposób przygotowywania porannego raportu** (źródła, kroki, kryteria, punktację, klasy A/B/C, format raportu, reguły publikacji), zaktualizuj w tym samym commicie także `metodologia-swing.md` oraz jej angielską wersję `metodologia-swing.en.md` (strona `en/methodology-swing.html`), tak by wszystkie opisy były spójne.
