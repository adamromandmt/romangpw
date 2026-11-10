# Dryf — metodologia

Dryf wyłapuje w sezonach raportowych spółki, które otwierają się wyraźną luką w górę na dużym wolumenie, i trzyma je do 40 sesji. To przybliżenie dryfu kursu po wynikach (PEAD), liczone z cen i wolumenu, bo repozytorium nie ma danych o wynikach, konsensusie ani komunikatach spółek.

Ta strona opisuje samą strategię. Jak działa wirtualny portfel (kapitał, koszty, terminy zleceń), wyjaśnia zakładka Portfel; jest to tylko sprawdzian prognoz od dnia startu.

## Hipoteza

Kursy dryfują w kierunku zaskoczenia wynikami przez tygodnie, a nawet miesiące po ogłoszeniu (Ball i Brown 1968, Bernard i Thomas 1989). Jeśli rynek reaguje na dobre wyniki stopniowo, kupno po pierwszej reakcji może jeszcze coś zarobić. Dla GPW dowody są **mieszane**, a próby małe.

## Reguły (tak liczy je kod)

1. **Okna skanu.** Szukamy zdarzeń tylko w oknach publikacji raportów: 1 lutego – 30 kwietnia, 1–20 maja, 15 sierpnia – 30 września i 1–20 listopada. Bez danych ESPI traktujemy ruch w tych oknach jako przybliżenie reakcji na wyniki. Poza oknami nie szukamy nowych zdarzeń, ale otwarte pozycje są nadal prowadzone.
2. **Zdarzenie dodatnie** (dzień E): spółka z medianą dziennego obrotu z 60 sesji co najmniej 1 mln zł, której luka otwarcia względem poprzedniego zamknięcia wynosi co najmniej +2% (z korektą o odcięcie dywidendy), wzrost dnia (cena skorygowana o dywidendy) mieści się między +4% a +30%, wolumen jest co najmniej 2,5 raza wyższy niż mediana z 20 poprzednich sesji, a zamknięcie leży w górnej połowie zakresu dnia. Ruchy powyżej 30% odrzucamy jako możliwe scalenia akcji. Poprzednia sesja musi mieć notowanie.
3. **Zdarzenie ujemne.** Lustrzane odbicie: luka co najmniej −2%, spadek dnia od −4% do −30%, ten sam próg wolumenu i obrotu, zamknięcie w dolnej połowie zakresu dnia. Spółka ze zdarzeniem ujemnym trafia na 60 sesji na listę „nie kupuj”. Lista jest informacją dla własnych decyzji; skaner swing nie korzysta z niej automatycznie.
4. **Wejście.** Kupno po otwarciu następnej sesji po zdarzeniu dodatnim, za stałą kwotę 10 tys. zł na spółkę, maksymalnie 10 pozycji naraz. Zlecenie jest anulowane, gdy otwarcie leży na poziomie stopu lub poniżej niego.
5. **Stop.** Zamknięcie z dnia przed zdarzeniem (czyli domknięcie luki). Stop działa śróddziennie: jeśli kurs dotknie tego poziomu, wychodzimy po cenie stopu, a jeśli sesja otwiera się poniżej niego, po cenie otwarcia.
6. **Wyjście w czasie.** Po 40 sesjach, na zamknięciu.
7. **Rytm.** Skan po każdej sesji.

## Parametry

Wszystkie progi (luka 2%, wzrost 4%, wolumen 2,5 raza, obrót 1 mln zł, okna, 40 sesji, 10 tys. zł na pozycję, 10 pozycji) to wartości startowe, nie wyniki badań ani optymalizacji. Opracowanie, na którym oparliśmy strategię, zakładało trzymanie 40–60 sesji i wejście przy zaskoczeniu w górnym kwintylu; my wybraliśmy 40 sesji i zdarzenie cenowo-wolumenowe.

Progi ustawiliśmy według liczby zdarzeń, nie według tego, jak kursy zachowały się po nich. W historii notowań z repozytorium (od 23 października 2025 do 6 listopada 2026) takie warunki spełniło 35 zdarzeń dodatnich (20 w oknach raportowych) i 20 ujemnych (10 w oknach).

## Dowody i ich granice

- **Sojka** (Bank i Kredyt 52(2), 2021; dane 2004–2018): strategia oparta na PEAD dawała na polskim rynku średnio 5,4% w ciągu 90 dni od utworzenia portfela. Cytujemy streszczenie; pełnego tekstu roboczej wersji (SSRN) nie udało się pobrać.
- **Jagliński** (Financial Sciences 2020; zdarzenia z lat 2017–2019; zaskoczenie liczone względem prognoz analityków, podczas gdy wcześniejsze badanie Sojki używało modeli autoregresyjnych): brak PEAD dla spółek powyżej oczekiwań, dryf tylko w grupie poniżej oczekiwań. Autor wiąże to z ograniczoną dostępnością krótkiej sprzedaży w Polsce.
- **Szyszka** (2001), według streszczenia z wyszukiwarki: najwyraźniejszy wynik to istotny dryf ujemny po wyraźnie rozczarowujących wynikach.
- **Wniosek:** najlepiej udokumentowane na GPW jest ujemne zaskoczenie, stąd lista „nie kupuj”. Strona długa ma poparcie u Sojki, ale nie u Jaglińskiego, więc wynik zależy od miary zaskoczenia i okresu.
- **Haircut:** McLean i Pontiff (97 predyktorów, 80 publikacji): poza próbą, przed publikacją, zwroty były o 26% niższe, a po publikacji o 58% niższe. Zakładamy, że realna przewaga to najwyżej połowa tej z backtestu.

Opracowanie opisuje też wzmocnienia, których ta wersja nie ma: zaskoczenie liczone z danych finansowych lub konsensusu, zakupy insiderów (zawiadomienia MAR) i ogłoszenia skupu akcji własnych. Brakuje do nich danych w repozytorium.

## Przykład zdarzenia (ilustracja, nie dowód)

LPP, 18 września 2026 (w oknie raportowym): poprzednie zamknięcie 22 380 zł, otwarcie 23 200 zł (luka +3,7%), zamknięcie 24 160 zł (+8,0%), wolumen 10,0 razy wyższy niż mediana z 20 poprzednich sesji, zamknięcie w górnej części zakresu dnia. Spełnione były wszystkie warunki zdarzenia dodatniego. Najwyższe zamknięcie po zdarzeniu (28 080 zł, 5 listopada 2026) było o ok. 16% wyższe niż zamknięcie w dniu zdarzenia, a ostatnie (27 480 zł, 6 listopada 2026) o ok. 14%.

To jeden przykład, który znaliśmy z wcześniejszych skanów, a nie próba reprezentatywna: pokazuje, jak wygląda zdarzenie, a nie że strategia działa. Przy stałej kwocie 10 tys. zł na pozycję spółek o cenie akcji powyżej tej kwoty, jak LPP, w ogóle nie da się kupić.

## Wzorzec porównania

Portfel porównujemy z WIG20, ale WIG20 jest indeksem cenowym, bez dywidend. Według Parkietu (7 maja 2024) od końca 2004 r. WIG20 zyskał ok. 25%, a WIG20TR ok. 155%, czyli w przeliczeniu ok. 1,2% wobec ok. 5,0% rocznie (własny rachunek z tych wartości, ok. 19,4 roku). W latach 2013–2022 WIG20TR dał ok. −4%, mWIG40TR +114%, a sWIG80TR +119%, więc poprzeczka jest niska. Dryf trzyma gotówkę, dopóki nie pojawią się zdarzenia, więc porównanie z WIG20 trzeba czytać z uwzględnieniem tego, jaka część kapitału jest zainwestowana (zob. zakładka Portfel).

## Dane i znane ograniczenia

- Zdarzenie cenowo-wolumenowe to nie to samo co zaskoczenie wynikami: ruch w oknie raportowym może mieć inną przyczynę, a spółki publikują raporty w różnych dniach, także poza naszymi oknami.
- Informacja może być wyceniona już w dniu raportu, a kupujemy dopiero po luce. Luki cenowe i płynność zwiększają ryzyko poślizgu.
- Próby są małe, a wyniki badań sprzeczne (Sojka i Jagliński). Repozytorium ma ok. roku notowań, więc nie ma testu wstecznego.
- Uniwersum to dzisiejsza lista spółek, bez wycofanych z obrotu (survivorship bias).
- Częste transakcje na zwykłym rachunku oznaczają podatek 19% przy każdej realizacji zysku, co zjada przewagę; pasowałyby tu raczej konta IKE i IKZE.

## Rola obok swingu

Komplementarna w kalendarzu: skaner swing traktuje raport w ciągu najbliższych 14 dni jako ryzyko, a Dryf handluje tuż po raporcie. Rozszerza też podejście oparte na zdarzeniach z samych dywidend na wyniki.

## Historia zmian reguł

- 7 listopada 2026: pierwsza wersja reguł i pierwszy skan (6 listopada 2026).

## Źródła

- [Sojka: PEAD na polskim rynku akcji (Bank i Kredyt 2021)](https://bankandcredit.nbp.pl/content/2021/02/BIK_02_2021_03.pdf)
- [Jagliński: The Impact of Quarterly Earnings Announcements on Stock Prices](https://journals.ue.wroc.pl/fins/article/view/233)
- [Szyszka (2001), SSRN](https://ssrn.com/abstract=295299)
- [Parkiet: Czemu wyniki WIG20 były w ostatnich latach tak słabe](https://www.parkiet.com/analizy-rynkowe/art38741821-czemu-wyniki-wig20-byly-w-ostatnich-latach-takie-slabe-3)
- [McLean, Pontiff: Does Academic Research Destroy Stock Return Predictability?](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.
