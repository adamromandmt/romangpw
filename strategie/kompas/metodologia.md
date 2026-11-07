# Kompas — metodologia

Kompas odpowiada na jedno pytanie: który segment GPW jest dziś najsilniejszy (duże spółki z WIG20, średnie z mWIG40 czy małe z sWIG80) i czy w ogóle warto być w akcjach. To rotacja między trzema indeksami z filtrem trendu, liczona raz w miesiącu.

Ta strona opisuje samą strategię. Jak działa wirtualny portfel (kapitał, koszty, terminy zleceń), wyjaśnia zakładka Portfel; jest to tylko sprawdzian prognoz od dnia startu.

## Hipoteza

Trendy w cenach utrzymują się przez miesiące, a prosty filtr trendu ogranicza straty w długich spadkach. Rotacja między segmentami dodaje drugą korzyść: nie siedzimy w najsłabszym z nich. Na GPW ma to lokalne uzasadnienie. W latach 2013–2022 WIG20TR dał według Parkietu ok. −4%, mWIG40TR +114%, a sWIG80TR +119%.

## Reguły (tak liczy je kod)

1. Po ostatniej sesji miesiąca liczymy dla WIG20, mWIG40 i sWIG80 zwrot z 6 i z 12 miesięcy (zamknięcia wskaźników cenowych). **Momentum** to średnia tych dwóch zwrotów.
2. Wybieramy indeks o najwyższym momentum.
3. **Filtr trendu:** trzymamy go tylko wtedy, gdy jego zamknięcie leży powyżej średniej z 10 ostatnich zamknięć miesięcznych (bieżący miesiąc liczy się jako zamknięcie z dnia sygnału). W przeciwnym razie jest gotówka. Nie przechodzimy wtedy do drugiego indeksu: gdy najsilniejszy nie przechodzi filtra, całość stoi w gotówce.
4. Pierwszy sygnał powstał 6 listopada 2026, poza cyklem. Kolejne liczymy na danych z ostatniej sesji każdego miesiąca. Miesiąc uznajemy za zamknięty dopiero wtedy, gdy w danych pojawi się sesja następnego, więc raport z takim sygnałem ukazuje się po pierwszej sesji nowego miesiąca.

Raport pokazuje też informacyjnie wariant Fabera: które z trzech indeksów leżą powyżej 10-miesięcznej średniej.

## Parametry

Okna 6, 12 i 10 miesięcy są klasyczne (10 miesięcy pochodzi od Fabera), ale to wartości startowe, nie wynik optymalizacji na danych GPW. Nie testowaliśmy innych okien. CXO Advisory ostrzega, że wybór dokładnie 10 miesięcy może być efektem data snoopingu, choć okna 3, 6, 9 i 12 miesięcy też biły kup-i-trzymaj pod względem wskaźnika Sharpe'a (brutto).

Reguła jest hybrydą dwóch wariantów z naszego opracowania: wybór indeksu jak w dual momentum, a test bezwzględny jak u Fabera (średnia 10-miesięczna). Wersji z porównaniem zwrotu 12M z zwrotem gotówki nie użyliśmy, bo w repozytorium nie ma stopy gotówki.

## Dowody i ich granice

- **Faber** (w ujęciu CXO Advisory): lata 1973–2012, pięć klas aktywów w równych wagach, rebalans miesięczny. Timing według średniej 10-miesięcznej wobec kup-i-trzymaj: roczna stopa zwrotu 10,5% wobec 9,9%, wskaźnik Sharpe'a 0,73 wobec 0,44, maksymalny roczny spadek −9,5% wobec −46,0%, wszystko przed kosztami. Główna korzyść to ograniczenie spadków, a nie wyższy zwrot.
- **Hurst, Ooi i Pedersen** oraz **Moskowitz, Ooi i Pedersen** opisują trend-following na bardzo długich próbach. Użyliśmy ich tylko jako wskazania kierunku, nie sprawdzaliśmy szczegółów.
- **GPW:** nie znaleźliśmy rygorystycznego badania dual momentum ani reguły Fabera na indeksach TR. Znaleziony test blogowy (357 testów średnich ruchomych) wskazywał miesięczny interwał jako najlepszy dla indeksów, ale w płaskim, sześcioletnim oknie średnia nie biła benchmarku w ok. połowie przypadków. To blog, nie praca naukowa, i nie sprawdzaliśmy go ponownie.
- **Haircut:** McLean i Pontiff zbadali 97 predyktorów stóp zwrotu z 80 publikacji: poza próbą, przed publikacją, zwroty były o 26% niższe, a po publikacji o 58% niższe. Zakładamy, że realna przewaga to najwyżej połowa tej z backtestu.

## Wzorzec porównania

Portfel porównujemy z WIG20, bo na pytanie „czy strategia bije WIG20” ma odpowiedzieć ten sprawdzian. Kompas trzyma w modelu jednostki indeksów cenowych, które tak jak WIG20 nie zbierają dywidend, więc samo porównanie jest spójne. Jest jednak zaniżone względem ETF-ów na indeksy TR i względem właściwego wzorca, czyli WIG20TR. Według Parkietu (7 maja 2024) od końca 2004 r. WIG20 zyskał ok. 25%, a WIG20TR ok. 155%; w przeliczeniu na stopę roczną (własny rachunek z tych wartości, ok. 19,4 roku) to ok. 1,2% wobec ok. 5,0% rocznie. W repozytorium nie ma notowań indeksów TR ani ETF-ów, więc porównania z WIG20TR nie liczymy.

## Dane i znane ograniczenia

- Sygnał liczymy na wskaźnikach cenowych z archiwum GPW, bez dywidend. Ich udział w zwrocie bywa różny w różnych segmentach, więc ranking oparty na indeksach TR mógłby wyglądać inaczej.
- Repozytorium ma ok. roku notowań, więc nie ma testu wstecznego tej reguły na danych GPW. To sprawdzian prognoz od dnia startu, nie dowód skuteczności.
- Rotacja bywa zawodna w trendzie bocznym (kolejne fałszywe przełączenia). Zmiana pozycji oznacza w praktyce realizację zysku i podatek 19% poza IKE i IKZE.
- ETF-y na indeksy TR (np. ETFBW20TR, ETFBM40TR, ETFBS80TR) są tu tylko wskazówką do sprawdzenia u brokera. Ich płynność, opłaty i możliwość kupna w IKE i IKZE trzeba zweryfikować samodzielnie.
- Pominęliśmy nakładkę sezonową (półrocze zimowe XI–IV wobec letniego V–X). Analiza Strefy Inwestorów z 2019 r. opiera się na małych próbach (9–14 półroczy), kończy się w 2019 r., nie uwzględnia kosztów ani podatków, a przyczyna zjawiska jest nieznana.

## Rola obok swingu

Kompas jest przełącznikiem reżimu. Pęd używa go jako filtra: gdy Kompas pokazuje gotówkę, nowe pozycje Pędu mają połowę zwykłej wielkości. Skaner swing nie korzysta z Kompasu automatycznie.

## Historia zmian reguł

- 7 listopada 2026: pierwsza wersja reguł i pierwszy sygnał (6 listopada 2026).

## Źródła

- [CXO Advisory: Long-term outperformance from trends defined by moving averages (Faber)](https://www.cxoadvisory.com/technical-trading/long-term-outperformance-from-trends-defined-by-moving-averages)
- [Hurst, Ooi, Pedersen: A Century of Evidence on Trend-Following Investing](https://fairmodel.econ.yale.edu/ec439/hurst.pdf)
- [stockbroker.pl: Średnia krocząca (test blogowy)](https://stockbroker.pl/srednia-kroczaca/)
- [Strefa Inwestorów: Najlepszy okres inwestowania](https://strefainwestorow.pl/artykuly/analizy/20191106/najlepszy-okres-inwestowania)
- [Parkiet: Czemu wyniki WIG20 były w ostatnich latach tak słabe](https://www.parkiet.com/analizy-rynkowe/art38741821-czemu-wyniki-wig20-byly-w-ostatnich-latach-takie-slabe-3)
- [Parkiet: 30 lat z WIG20](https://www.parkiet.com/felietony/art40303951-30-lat-z-wig20)
- [McLean, Pontiff: Does Academic Research Destroy Stock Return Predictability?](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.
