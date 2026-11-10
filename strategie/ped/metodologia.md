# Pęd — metodologia

Pęd kupuje siłę: co miesiąc wybiera 12 płynnych spółek, które rosły najmocniej w ostatnich 12 miesiącach (z pominięciem ostatniego), pod warunkiem że ich kurs leży nad średnią z 200 sesji. Swing kupuje korektę w trendzie, a Pęd kupuje spółki, które po prostu rosną, niezależnie od korekty.

Ta strona opisuje samą strategię. Jak działa wirtualny portfel (kapitał, koszty, terminy zleceń), wyjaśnia zakładka Portfel; jest to tylko sprawdzian prognoz od dnia startu.

## Hipoteza

Zwycięzcy ostatnich miesięcy częściej pozostają zwycięzcami, niż wynikałoby z przypadku (momentum przekrojowe). Jegadeesh i Titman (1993) znaleźli na rynku USA, że zwycięzcy z ostatnich 3–12 miesięcy biją przegranych o ok. 1% miesięcznie (liczba z opracowania wtórnego). George i Hwang (2004) pokazali, że bliskość 52-tygodniowego maksimum prognozuje stopy zwrotu lepiej niż same przeszłe zwroty. Dla GPW dowody są **mieszane** i to najsłabiej udokumentowana strategia z pięciu.

## Reguły

1. **Uniwersum.** Spółki z naszej listy obserwowanych spółek GPW, które w dniu sygnału spełniają wszystkie warunki: ostatnie notowanie nie starsze niż 10 dni; historia co najmniej 12 miesięcy; mediana dziennego obrotu z 60 sesji co najmniej 0,5 mln zł; świece w co najmniej 90% z ostatnich 120 sesji; brak dziennej zmiany ceny (skorygowanej o dywidendy) powyżej 30% w ostatnich ok. 260 notowaniach, co może oznaczać split lub szok. Spółki wykluczone ręcznie (np. w wezwaniu) odpadają od razu.
2. **Ranking 12-1.** Zwrot od 12 miesięcy do 1 miesiąca przed dniem sygnału, na cenach skorygowanych o dywidendy. Ostatni miesiąc pomijamy, zgodnie z klasyczną konstrukcją 12-1, bo bardzo krótkie zwroty bywają odwracane.
3. **Filtr trendu.** Kurs musi leżeć nad średnią z 200 sesji.
4. **Skład.** 12 spółek o równych wagach. Spółka dotychczas w portfelu zostaje, dopóki jest w czołowej 25 rankingu, nadal leży nad średnią z 200 sesji i mieści się w limicie sektora (histereza ogranicza obrót). Wolne miejsca zajmują najwyżej sklasyfikowane spółki, które spełniają filtr trendu i limit: maksymalnie 3 spółki z jednego sektora (uproszczona klasyfikacja własna; banki i pozostałe instytucje finansowe liczą się razem; sektor „inne” nie ma limitu).
5. **Reżim.** Gdy Kompas pokazuje gotówkę, nowe pozycje mają połowę zwykłej wielkości. Pozycji, które zostają, nie dokupujemy ani nie obcinamy.
6. **Rytm.** Sygnał liczymy na danych z ostatniej sesji każdego miesiąca, a raport ukazuje się po pierwszej sesji następnego miesiąca. Pierwszy skład powstał 6 listopada 2026, poza cyklem.

## Parametry

Liczba 12 spółek, próg 25 w histerezie, limit 3 na sektor, filtr 200 sesji i próg obrotu 0,5 mln zł to wartości startowe, nie wyniki badań ani optymalizacji na danych GPW. Okno 12-1 jest klasyczne, ale na GPW momentum bywa wykrywane tylko na krótszych horyzontach (zob. niżej). Nie testowaliśmy innych rankingów; zwrot 6M i odległość od 52-tygodniowego maksimum raport pokazuje tylko informacyjnie.

## Dowody i ich granice

- **Daniel i Moskowitz** (USA, 1927–2013, według opracowania Swedroe'a): momentum ma dodatnie średnie, ale zdarzają się rzadkie, długotrwałe serie strat. Występują w „stanach paniki”, po spadkach rynku przy wysokiej zmienności, równocześnie z odbiciami. Swedroe zauważa, że strategie wyłącznie długie nie mają tak głębokich załamań, bo największe straty powstają po stronie krótkiej.
- **GPW, wynik na plus:** badanie opisane w CEEOL znajduje „pewne dowody” momentum, ale tylko na krótkich horyzontach. Zysk wynika z mniejszych strat zwycięzców, a na dłuższych horyzontach pojawia się efekt kontrariański.
- **GPW, wynik na minus:** Zaremba i Konieczka (wszystkie spółki GPW, 2001–2013): premie z momentum, wartości i wielkości występują tylko częściowo, wzmacniają się razem, ale znikają po uwzględnieniu kosztów transakcyjnych i płynności.
- **Wniosek:** klasyczne 12-1 może na GPW nie działać. Ten portfel jest sprawdzianem na żywo, nie wdrożeniem sprawdzonej metody.
- **Haircut:** McLean i Pontiff (97 predyktorów, 80 publikacji): poza próbą, przed publikacją, zwroty były o 26% niższe, a po publikacji o 58% niższe. Zakładamy, że realna przewaga to najwyżej połowa tej z backtestu.

Nie sprawdzaliśmy ponownie kilku badań z wcześniejszego przeglądu (m.in. Applied Financial Economics 2013, Sekula, FIQF 2016), dlatego nie opieramy na nich żadnych wniosków.

## Wzorzec porównania

Portfel porównujemy z WIG20, bo na pytanie „czy strategia bije WIG20” ma odpowiedzieć ten sprawdzian. WIG20 jest jednak indeksem cenowym, bez dywidend. Według Parkietu (7 maja 2024) od końca 2004 r. WIG20 zyskał ok. 25%, a WIG20TR ok. 155%, czyli w przeliczeniu ok. 1,2% wobec ok. 5,0% rocznie (własny rachunek z tych wartości, ok. 19,4 roku). Porównanie z indeksem cenowym zawyża więc wynik portfela, który zbiera dywidendy. Poprzeczka jest też niska z przyczyn strukturalnych: w latach 2013–2022 WIG20TR dał ok. −4%, mWIG40TR +114%, a sWIG80TR +119%. Sam brak WIG20 w portfelu może więc dawać przewagę, która nie jest zasługą momentum. Portfela równych wag z całego uniwersum, który pozwoliłby odróżnić selekcję od omijania WIG20, nie prowadzimy, więc wynik względem WIG20 trzeba czytać z tą świadomością.

## Dane i znane ograniczenia

- Mamy ok. roku historii notowań, więc nie ma testu wstecznego, a pełny ranking 12-1 jest dostępny dopiero od końca października 2026.
- Uniwersum to dzisiejsza lista spółek, bez wycofanych z obrotu, więc nie nadaje się do testów wstecznych bez korekty o survivorship bias.
- Korekta o dywidendy opiera się na zebranych przez nas datach i kwotach wypłat; brakujące wpisy zaniżają zwrot spółek dywidendowych.
- Klasyfikacja sektorów jest robocza, więc limit 3 spółek na sektor działa tylko w przybliżeniu.
- Momentum ma ryzyko załamań na odbiciach po spadkach rynku i wymaga częstych transakcji (koszty rotacji, podatek 19% przy realizacji poza IKE i IKZE).
- Te same spółki mogą trafić do Pędu i do skanera swing; nakładania się portfeli nie mierzymy.

## Rola obok swingu

„Kupuj siłę” niezależnie od korekty, podczas gdy swing kupuje korektę w trendzie. Filtr reżimu bierze z Kompasu.

## Historia zmian reguł

- 7 listopada 2026: pierwsza wersja reguł i pierwszy skład (6 listopada 2026).
- 7 listopada 2026 (przegląd przed pierwszą transakcją): banki i pozostałe instytucje finansowe liczą się razem do limitu 3 spółek z sektora. Wcześniej były to dwie osobne etykiety z osobnymi limitami, więc finanse mogły zająć do 6 z 12 miejsc. Pierwszy skład przeliczyliśmy według tej reguły, zanim portfel wirtualny złożył pierwsze zlecenia (otwarcie 9 listopada 2026).

## Źródła

- [NBER: Momentum Crashes (Daniel, Moskowitz)](https://www.nber.org/papers/w20439)
- [etf.com, Swedroe: The Downside of Momentum](https://www.etf.com/sections/index-investor-corner/swedroe-downside-momentum)
- [George, Hwang: The 52-Week High and Momentum Investing](https://typeset.io/pdf/the-52-week-high-and-momentum-investing-4u9j16d52p.pdf)
- [CEEOL: momentum na GPW](https://www.ceeol.com/search/article-detail?id=762235)
- [Zaremba, Konieczka (FIQF 2017)](https://reference-global.com/article/10.1515/fiqf-2016-0119)
- [Jegadeesh, Titman (opracowanie wtórne CBS)](https://research.cbs.dk/en/studentProjects/88a3aa5c-bc3e-4141-8f23-4d678e9db4c1/)
- [Parkiet: Czemu wyniki WIG20 były w ostatnich latach tak słabe](https://www.parkiet.com/analizy-rynkowe/art38741821-czemu-wyniki-wig20-byly-w-ostatnich-latach-takie-slabe-3)
- [McLean, Pontiff: Does Academic Research Destroy Stock Return Predictability?](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.
