# Złoty Środek — metodologia

Złoty Środek szuka dobrych firm w rozsądnej cenie. Dwa razy w roku wybiera 20 niefinansowych spółek, które łączą wysoką jakość (wskaźnik Piotroskiego, zyskowność brutto do aktywów) z niską wyceną EV/EBIT. To powolny rdzeń portfela o innym źródle zysku niż swing: ma zarabiać na wzroście zysków i na rewaluacji spółek, a nie na korektach cen.

Ta strona opisuje samą strategię. Jak działa wirtualny portfel (kapitał, koszty, terminy zleceń), wyjaśnia zakładka Portfel; jest to tylko sprawdzian prognoz od dnia startu.

## Hipoteza

Zyskowność brutto (zysk brutto do aktywów) przewiduje stopy zwrotu mniej więcej tak dobrze jak klasyczne wskaźniki wyceny, a jest z nimi silnie ujemnie skorelowana, więc połączenie obu sygnałów poprawia wynik względem samej wyceny (Novy-Marx). Proste testy rentowności, dźwigni i efektywności (F-score Piotroskiego) pomagają odsiać spółki tanie z powodu pogarszającej się kondycji. Podobne połączenie jakości z ceną stoi za Magic Formula Greenblatta i za czynnikiem „jakość minus śmieci” (Asness, Frazzini i Pedersen). Na GPW dodajemy ograniczenie ryzyka politycznego: limit spółek z sektorów wrażliwych regulacyjnie.

## Reguły (tak liczy je kod)

1. **Dane.** Roczne sprawozdania spółek niefinansowych z pliku data/fundamentals.csv (kwoty w tys. zł, liczba akcji w sztukach). Plik wypełnia się osobno z publicznych sprawozdań; kolumny i zasady opisuje METHOD-ZLOTY-SRODEK.md w repozytorium. Sprawozdanie liczy się dopiero od dnia publikacji (gdy brak daty: koniec okresu plus 120 dni), żeby nie wyprzedzać faktów. Dopóki plik jest pusty, strategia nie wskazuje spółek, a portfel wirtualny stoi w gotówce.
2. **Uniwersum.** Spółki z naszej listy (data/universe.json) poza bankami i spółkami finansowymi, które w dniu sygnału spełniają warunki: ostatnie notowanie nie starsze niż 10 dni; historia co najmniej 12 miesięcy; mediana dziennego obrotu z 60 sesji co najmniej 0,3 mln zł; świece w co najmniej 90% z ostatnich 120 sesji; brak dziennej zmiany ceny powyżej 30% w ostatnich ok. 260 notowaniach. Potrzebne są sprawozdania z dwóch kolejnych lat. Banki i ubezpieczyciele wymagają innych mierników (P/B, ROE, bufory kapitałowe) i są poza zakresem tej wersji.
3. **Wskaźniki.** Dla każdej spółki liczymy F-score (uproszczony Piotroski), wolny przepływ pieniężny, dług netto do EBITDA, EV/EBIT i zyskowność brutto do aktywów. Definicje są w sekcji „Wskaźniki” poniżej.
4. **Progi wejścia** (dla spółek spoza portfela): F-score co najmniej 7, dodatni FCF, dług netto do EBITDA do 3.
5. **Ranking.** Suma pozycji w rankingu EV/EBIT (im taniej, tym lepiej) i w rankingu zyskowności brutto (im wyżej, tym lepiej); niższa suma oznacza wyższe miejsce. Remisy rozstrzyga wyższy F-score, potem niższe EV/EBIT.
6. **Skład.** 20 spółek o równych wagach. Spółka dotychczas w portfelu zostaje, dopóki ma F-score co najmniej 5, dług netto do EBITDA do 4 i miejsce w czołowych 30 rankingu. Maksymalnie 4 spółki z jednego sektora (robocza klasyfikacja własna w data/sectors.json; sektor „inne” nie ma limitu) i 8 łącznie z sektorów wrażliwych regulacyjnie (energetyka, paliwa), czyli 40% portfela.
7. **Rytm.** Sygnał liczymy na danych z ostatniej sesji maja i października, a raport ukazuje się po pierwszej sesji następnego miesiąca. Pierwszy sygnał powstał 6 listopada 2026, poza cyklem.

## Wskaźniki

- **F-score** (uproszczona wersja Piotroskiego, 9 testów po 1 punkcie): dodatnia ROA; dodatni przepływ operacyjny; wzrost ROA rok do roku; przepływ operacyjny do aktywów wyższy niż ROA; spadek zadłużenia do aktywów; wzrost wskaźnika bieżącej płynności; liczba akcji nie wzrosła o więcej niż 0,5%; wzrost marży brutto; wzrost rotacji aktywów.
- **Wolny przepływ pieniężny** (FCF): przepływ operacyjny minus nakłady inwestycyjne.
- **Dług netto do EBITDA**: dług minus gotówka, podzielone przez EBITDA. Spółka z gotówką netto ma 0, a spółka z długiem netto i niedodatnią EBITDA nie przechodzi.
- **EV/EBIT**: wartość przedsiębiorstwa (kapitalizacja z ostatniego kursu zamknięcia plus dług netto) do EBIT. Wymaga dodatniego EBIT, dodatniego EV i dodatniego kapitału własnego.
- **Zyskowność brutto**: zysk brutto do aktywów.

## Parametry

Progi F-score (7 przy wejściu, 5 przy utrzymaniu), dług netto do EBITDA (3 i 4), liczba 20 spółek, miejsce 30 w histerezie, limity 4 i 8 oraz próg obrotu 0,3 mln zł to wartości startowe z naszego opracowania, nie wyniki badań ani optymalizacji na danych GPW. Zamiast Magic Formula w pełnej postaci (zwrot z kapitału) użyliśmy zyskowności brutto do aktywów Novy-Marxa. Nie testowaliśmy innych wag między wyceną a jakością: oba rankingi liczą się po równo.

## Dowody i ich granice

- **Novy-Marx** (dane USA): zyskowność brutto przewiduje stopy zwrotu mniej więcej tak samo dobrze jak klasyczne wskaźniki wyceny i jest z nimi silnie ujemnie skorelowana (korelacja stóp zwrotu strategii długich i krótkich pozycji z book-to-price: −0,71 dla dużych i −0,24 dla małych spółek). Połączenie obu sygnałów wyraźnie poprawia wynik względem samej wartości: dla dużych spółek ok. 3,1% rocznie ponad benchmark netto (information ratio 0,66), a dla Magic Formula ok. 1,9% (information ratio 0,37).
- **Jakość minus śmieci** (CXO Advisory o pracy Asnessa, Frazziniego i Pedersena): 24 rynki rozwinięte; w próbie globalnej (czerwiec 1989 – grudzień 2016) średnio 0,36% miesięcznie brutto; dodatnie w 21 z 24 krajów, a dodatnia alfa czteroczynnikowa w 23 z 24. Wyniki brutto, bez kosztów krótkiej sprzedaży; w streszczeniu CXO nie ma wyniku dla samej GPW.
- **GPW:** Zaremba i Konieczka (wszystkie spółki GPW, 2001–2013): premia za wartość występuje częściowo, ale znika po uwzględnieniu kosztów transakcyjnych i płynności. Według streszczenia, którego nie sprawdzaliśmy ponownie, Pilch (2021) potwierdził F-score na GPW dla branż IT i gamingu w latach 2017–2019, na wąskiej próbie.
- **Ryzyko polityczne:** Parkiet wskazuje je jako jedną z przyczyn słabych wyników WIG20TR, a sektor finansowy stanowi ponad 40% tego indeksu. Limit spółek z sektorów wrażliwych regulacyjnie jest tylko częściową ochroną.
- **Haircut:** McLean i Pontiff (97 predyktorów, 80 publikacji): poza próbą, przed publikacją, zwroty były o 26% niższe, a po publikacji o 58% niższe. Zakładamy, że realna przewaga to najwyżej połowa tej z backtestu.

## Wzorzec porównania

Portfel porównujemy z WIG20, ale WIG20 jest indeksem cenowym, bez dywidend. Według Parkietu (7 maja 2024) od końca 2004 r. WIG20 zyskał ok. 25%, a WIG20TR ok. 155%, czyli w przeliczeniu ok. 1,2% wobec ok. 5,0% rocznie (własny rachunek z tych wartości, ok. 19,4 roku). Porównanie z indeksem cenowym zawyża więc wynik portfela, który zbiera dywidendy. W latach 2013–2022 WIG20TR dał ok. −4%, mWIG40TR +114%, a sWIG80TR +119%, więc poprzeczka jest niska. Złoty Środek nie zawiera banków i spółek finansowych, które według Parkietu stanowią ponad 40% WIG20, więc jego wynik względem WIG20 zależy także od tego, jak radził sobie sektor finansowy.

## Dane i znane ograniczenia

- To najtrudniejsza z pięciu strategii do zautomatyzowania: wymaga danych fundamentalnych, które wprowadza się osobno i które trzeba sprawdzać ręcznie.
- Dane wejściowe to sprawozdania roczne. Sygnał październikowy odświeża więc głównie wycenę (kurs), a nie jakość; wyniki półroczne nie wchodzą do ocen.
- Tanie spółki bywają tanie z powodów politycznych lub regulacyjnych (pułapki wartości).
- Bonus za zwrot dla akcjonariuszy (dywidendy i skupy), który opisuje opracowanie, nie wchodzi do rankingu; dywidenda z ostatnich 12 miesięcy jest w raporcie tylko informacją.
- Rzadki rebalans (dwa razy w roku) oznacza długie trwanie w złym reżimie. Repozytorium ma ok. roku notowań, więc nie ma testu wstecznego tej reguły na danych GPW.
- Uniwersum to dzisiejsza lista spółek, bez wycofanych z obrotu (survivorship bias), a klasyfikacja sektorów jest robocza.
- Zmiana składu oznacza realizację zysku i podatek 19% poza IKE i IKZE.

## Rola obok swingu

Powolny rdzeń z decyzjami dwa razy w roku. Źródło zysku (rewaluacja i wzrost zysków) różni się od swingu, więc korelacja powinna być niższa; to wymaga sprawdzenia.

## Historia zmian reguł

- 7 listopada 2026: pierwsza wersja reguł i pierwszy sygnał (6 listopada 2026).

## Źródła

- [Novy-Marx: The Other Side of Value](https://www.ivey.uwo.ca/media/3775548/novy-marx.pdf)
- [CXO Advisory: Quality Minus Junk](https://www.cxoadvisory.com/fundamental-valuation/stock-quality-and-future-returns/)
- [Zaremba, Konieczka (FIQF 2017)](https://reference-global.com/article/10.1515/fiqf-2016-0119)
- [Pilch: F-score na GPW (streszczenie, niesprawdzone ponownie)](https://journals.umcs.pl/h/article/view/11872)
- [Parkiet: Czemu wyniki WIG20 były w ostatnich latach tak słabe](https://www.parkiet.com/analizy-rynkowe/art38741821-czemu-wyniki-wig20-byly-w-ostatnich-latach-takie-slabe-3)
- [McLean, Pontiff: Does Academic Research Destroy Stock Return Predictability?](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.
