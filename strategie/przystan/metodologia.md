# Przystań — metodologia

Przystań wybiera raz na kwartał do 16 płynnych spółek o najniższej zmienności z ostatniego roku. To portfel defensywny: ma ograniczać wahania i obsunięcia, a nie gonić hossę.

Ta strona opisuje samą strategię. Jak działa wirtualny portfel (kapitał, koszty, terminy zleceń), wyjaśnia zakładka Portfel; jest to tylko sprawdzian prognoz od dnia startu.

## Hipoteza

Spółki o niskiej zmienności dają w długim okresie zwroty skorygowane o ryzyko lepsze niż spółki bardzo zmienne (efekt niskiej zmienności, opisany m.in. przez Blitza i van Vlieta oraz przez Frazziniego i Pedersena). Dla inwestora wyłącznie długiego główna korzyść to niższe ryzyko, a nie pewna nadwyżka nad WIG20TR. W silnych hossach strategia może zostawać w tyle.

## Reguły (tak liczy je kod)

1. **Uniwersum.** Spółki z naszej listy (data/universe.json), które w dniu sygnału spełniają wszystkie warunki: ostatnie notowanie nie starsze niż 10 dni; historia co najmniej 12 miesięcy; mediana dziennego obrotu z 60 sesji co najmniej 0,3 mln zł; świece w co najmniej 90% z ostatnich 120 sesji (spółki rzadko notowane mają sztucznie niską zmienność); brak dziennej zmiany ceny (skorygowanej o dywidendy) powyżej 30% w ostatnich ok. 260 notowaniach; maksymalne obsunięcie z ostatnich 252 sesji nie głębsze niż 30%. Spółki z listy ręcznych wykluczeń (strategie/wykluczenia.json) odpadają od razu.
2. **Zmienność.** Odchylenie standardowe dziennych logarytmicznych zwrotów z ostatnich ok. 250 sesji (cena skorygowana o dywidendy, co najmniej 200 zwrotów między kolejnymi sesjami giełdowymi), pomnożone przez pierwiastek z 252.
3. **Wybór.** Do portfela wchodzą spółki z dolnego kwintyla zmienności spośród spółek uniwersum, czyli najspokojniejsza piąta część.
4. **Skład.** Do 16 spółek o równych wagach. Spółka dotychczas w portfelu zostaje, dopóki mieści się w najspokojniejszych 40% uniwersum i limit sektora na to pozwala (histereza ogranicza obrót). Maksymalnie 4 spółki z jednego sektora (robocza klasyfikacja własna w data/sectors.json; sektor „inne” nie ma limitu). Portfel może mieć mniej niż 16 spółek, jeśli dolny kwintyl po limitach sektorowych jest mniejszy.
5. **Rytm.** Sygnał liczymy na danych z ostatniej sesji marca, czerwca, września i grudnia, a raport ukazuje się po pierwszej sesji następnego miesiąca. Pierwszy skład powstał 6 listopada 2026, poza cyklem.

## Parametry

Dolny kwintyl, próg 40% w histerezie, limit 16 spółek i 4 na sektor, próg obrotu 0,3 mln zł oraz próg obecności 90% to wartości startowe, nie wyniki badań ani optymalizacji na danych GPW.

**Filtr obsunięcia 30% dodaliśmy po obejrzeniu pierwszego przebiegu na danych próbnych**, jeszcze przed pierwszym składem. Bez niego w dolnym kwintylu zmienności znalazłaby się AMC, która w ciągu roku straciła od szczytu 31,1%, a tuż za nim KRU (−31,7%). Niska zmienność dziennych zwrotów może ukrywać powolne, ale głębokie osuwanie się kursu, a to nie jest portfel, który chcemy nazywać defensywnym. Opracowanie, na którym oparliśmy strategię, proponowało filtr jakości z danych finansowych (dodatni zysk netto i ROE, F-score co najmniej 5, brak ujemnego kapitału własnego). Takich danych nie ma w repozytorium, więc filtr obsunięcia jest tylko zastępczym bezpiecznikiem opartym na cenie. To jedyny parametr, który zmieniliśmy po obejrzeniu danych.

## Dowody i ich granice

- **Blitz, Pang i van Vliet** (w ujęciu CXO Advisory): 30 rynków wschodzących, grudzień 1988 – grudzień 2010, ok. 1 000 spółek rocznie. Kwintyl o najniższej zmienności bił kwintyl o najwyższej o 4,4% rocznie (geometrycznie; 2,1% arytmetycznie), a wskaźnik Sharpe'a wynosił 0,64 wobec 0,29. Portfel hedge (długie spółki o niskiej zmienności, krótkie o wysokiej) bił indeks rynków wschodzących o 8,8% rocznie, głównie dzięki stronie krótkiej. Alfa trzyczynnikowa wynosiła 5,7%, a po dodaniu momentum 3,1% i była statystycznie nieistotna. Wszystko przed kosztami.
- **Polska 1989–2010** (z tego samego badania): portfel długich spółek o wysokiej zmienności i krótkich o niskiej dał −9,5% (t = −1,23). Kierunek jest zgodny z efektem niskiej zmienności, ale samodzielnie nieistotny statystycznie. Blog Falkenblog odczytał z tabeli badania, że w 17 z 19 krajów spółki o niskiej zmienności biły te o wysokiej (wyjątki: Meksyk i Rosja); tego odczytu nie sprawdzaliśmy ponownie.
- **Wniosek:** dla inwestora wyłącznie długiego główna korzyść to niższe ryzyko, nie pewna nadwyżka nad WIG20TR. W silnych hossach strategia może zostawać w tyle.
- **Haircut:** McLean i Pontiff (97 predyktorów, 80 publikacji): poza próbą, przed publikacją, zwroty były o 26% niższe, a po publikacji o 58% niższe. Zakładamy, że realna przewaga to najwyżej połowa tej z backtestu.

## Wzorzec porównania

Portfel porównujemy z WIG20, ale WIG20 jest indeksem cenowym, bez dywidend. Według Parkietu (7 maja 2024) od końca 2004 r. WIG20 zyskał ok. 25%, a WIG20TR ok. 155%, czyli w przeliczeniu ok. 1,2% wobec ok. 5,0% rocznie (własny rachunek z tych wartości, ok. 19,4 roku). Porównanie z indeksem cenowym zawyża więc wynik portfela, który zbiera dywidendy. W latach 2013–2022 WIG20TR dał ok. −4%, mWIG40TR +114%, a sWIG80TR +119%, więc poprzeczka jest niska. Przystań nie powinna być oceniana samym wynikiem: jej celem są mniejsze wahania, dlatego warto patrzeć także na maksymalne obsunięcie, które pokazuje zakładka Portfel. W silnej hossie spodziewamy się, że zostanie w tyle.

## Dane i znane ograniczenia

- Zmienność liczymy z ok. roku notowań (to cała historia w repozytorium), więc nie ma testu wstecznego tej reguły na danych GPW.
- Uniwersum to dzisiejsza lista spółek, bez wycofanych z obrotu, więc nie nadaje się do testów wstecznych bez korekty o survivorship bias.
- Brak filtra jakości z danych fundamentalnych (zob. wyżej) oraz brak oceny wyceny: spółki defensywne bywają drogie.
- Portfel może się skupiać w sektorach defensywnych, a klasyfikacja sektorów jest robocza, więc limit 4 spółek na sektor działa tylko w przybliżeniu.
- Część spółek ma niską płynność, a zmiana składu oznacza realizację zysku i podatek 19% poza IKE i IKZE.

## Rola obok swingu

Defensywny filar i kandydat na alternatywę dla gotówki w Kompasie, gdy ten pokazuje risk-off. Taki wariant wymaga osobnego sprawdzenia i dziś nie jest wdrożony: w Kompasie gotówka nie przynosi odsetek.

## Historia zmian reguł

- 7 listopada 2026: pierwsza wersja reguł. Przed pierwszym składem (6 listopada 2026) dodano filtr obsunięcia 30% (zob. Parametry).

## Źródła

- [CXO Advisory: The Volatility Effect in Emerging Markets](https://www.cxoadvisory.com/?p=20977)
- [Falkenblog: Low volatility effect in emerging markets](https://falkenblog.blogspot.com/2012/05/low-volatility-effect-in-emerging.html)
- [Blitz, Pang, van Vliet (EconPapers)](https://econpapers.repec.org/RePEc:eee:ememar:v:16:y:2013:i:c:p:31-45)
- [Parkiet: Czemu wyniki WIG20 były w ostatnich latach tak słabe](https://www.parkiet.com/analizy-rynkowe/art38741821-czemu-wyniki-wig20-byly-w-ostatnich-latach-takie-slabe-3)
- [McLean, Pontiff: Does Academic Research Destroy Stock Return Predictability?](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.
