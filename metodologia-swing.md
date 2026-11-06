# Swing Metodologia — jak działa monitor

*Opis dla osób, które dopiero zaczynają. Ta strona wyjaśnia, co robi codzienny skaner swing GPW, krok po kroku i dlaczego. Szczegółowa instrukcja techniczna (dla automatu) jest w pliku `METHOD.md` w repozytorium. Gdy zmienia się sposób przygotowywania porannego raportu, ta strona jest aktualizowana razem z nim.*

## Po co to wszystko

**Swing trading** to kupowanie akcji na kilka dni lub tygodni (u nas horyzont to ok. 1 miesiąc), żeby złapać jeden „zamach" ceny w górę. Nie chodzi o szukanie spółek, które są tanie po długim spadku. Chodzi o coś odwrotnego: **dobra spółka, która już rośnie, na chwilę tanieje, a potem znowu rusza w górę**. Kupowanie takiego „cofnięcia" w silnym trendzie jest zwykle bezpieczniejsze niż łapanie spadającego noża.

Monitor codziennie rano przed otwarciem Giełdy Papierów Wartościowych (GPW) przegląda kilkadziesiąt spółek i wybiera te, które najlepiej pasują do wzorca:

**dobra firma + trend wzrostowy + zdrowa korekta + wyraźne wsparcie + słabnąca podaż + pierwsze oznaki powrotu kupujących + sensowny stosunek zysku do ryzyka**

To jest ćwiczenie przesiewowe według ustalonych zasad, **nie porada inwestycyjna**. Dobra firma to nie to samo co dobry moment na zakup: wiele znanych spółek odpada, bo są w złym miejscu wykresu.

## Co robi monitor — krok po kroku

### 1. Sprawdza, czy giełda dziś pracuje
GPW nie handluje w weekendy i święta (np. 1 i 11 listopada, 6 stycznia, Wielkanoc). W takie dni raportu nie ma. **Dlaczego:** dane z dnia bez sesji nic by nie wniosły.

### 2. Pobiera notowania
Dla każdej spółki z uniwersum pobiera ok. 50 ostatnich sesji: cenę otwarcia, najwyższą, najniższą, zamknięcia i wolumen (liczbę handlowanych akcji). Raport przed otwarciem opiera się na **zamknięciu poprzedniej sesji**, bo poranne kursy są jeszcze nieaktualne. **Dlaczego:** wszystko dalej to matematyka na tych świecach; jeśli dane są stare lub niekompletne, raport mówi to wprost.

### 3. Ocenia rynek jako całość (reżim rynkowy)
Zanim wybierze spółki, patrzy na tło: indeksy WIG20, WIG, mWIG40 i sWIG80, szerokość rynku (ile spółek jest w trendzie), sektory, rynek USA (S&P 500, Nasdaq, indeks strachu VIX), rentowność obligacji, ropę, miedź, kursy złotego oraz kalendarz (decyzje RPP, Fed, dane o inflacji). **Dlaczego:** nawet świetna spółka potrafi spaść razem z rynkiem. Gdy otoczenie jest złe, raport mówi to wprost, zmniejsza liczbę kandydatów i sugeruje mniejsze pozycje albo czekanie.

### 4. Szuka spółek w trendzie wzrostowym
Używa średnich kroczących, czyli „uśrednionej ceny z ostatnich N dni": **EMA20** (ok. 1 miesiąc, reaguje szybko), **SMA50** (ok. 2,5 miesiąca). Dobry trend to taki, w którym cena jest nad średnimi, a krótsza średnia leży nad dłuższą, do tego wyższe szczyty i wyższe dołki oraz przewaga nad indeksem WIG (tzw. siła relatywna). **Dlaczego:** statystycznie łatwiej kupować to, co już rośnie, niż to, co spada.

### 5. Szuka zdrowej korekty
Interesuje go cofnięcie ok. **5–20% od niedawnego szczytu**, które wygląda na normalną realizację zysków albo ruch całego rynku, a nie na załamanie spółki. Dobra korekta jest uporządkowana, a **wolumen maleje** (sprzedających ubywa). Zła korekta to spadek na rosnącym wolumenie albo po złych wynikach. **Dlaczego:** korekta w silnym trendzie to okazja, a załamanie trendu to ryzyko.

### 6. Wyznacza wsparcia i strefę wejścia
**Wsparcie** to poziom ceny, przy którym spadek wcześniej się zatrzymywał (średnia krocząca, dawny opór, który stał się podłogą, luka cenowa). Monitor podaje **strefę wejścia**, czyli przedział, w którym zakup ma sens. **Dlaczego:** kupowanie „gdzie popadnie" daje przypadkowy wynik; kupowanie przy wsparciu daje logiczne miejsce na zlecenie ochronne.

### 7. Szuka śladów, że kupujący wracają (potwierdzenie)
Samo dotknięcie wsparcia nie wystarcza. Monitor sprawdza np. świecę odrzucenia (długi dolny cień), wyższy dołek, zamknięcie nad poprzednim dniem, odzyskanie EMA20, poprawę wskaźnika MACD oraz **rosnący wolumen przy odbiciu**. Na tej podstawie nadaje klasę:
- **A** — potwierdzenie już widać,
- **B** — korekta atrakcyjna, ale trzeba poczekać na sygnał (podany w raporcie jako „trigger"),
- **C** — wczesne i bardziej ryzykowne.

### 8. Sprawdza momentum (RSI i MACD)
**RSI** mierzy, czy ostatni ruch był „zbyt szybki". W silnym trendzie zdrowe cofnięcie często kończy się przy RSI 40–50, a nie poniżej 30. **MACD** pokazuje, czy rozpęd rośnie, czy słabnie. **Dlaczego:** pomaga odróżnić wyhamowanie od zmiany kierunku.

### 9. Sprawdza fundamenty
Czy firma rośnie i zarabia: przychody, zysk, marże, zadłużenie, ostatnie wyniki kwartalne, planowane wydarzenia (nowe kontrakty, dywidendy, skupy akcji). Spółki z wyraźnie pogorszoną sytuacją odpadają. **Dlaczego:** wykres bez tła biznesowego łatwo zwodzi.

### 10. Sprawdza daty raportów i dywidend
Wyniki kwartalne potrafią przesunąć kurs o kilka–kilkanaście procent w jeden dzień. Raporty w ciągu **14 dni** są oznaczane wytłuszczeniem, a poziomy są korygowane o dywidendy (po dniu odcięcia kurs spada o jej kwotę). **Dlaczego:** to ryzyko, które nie wynika z wykresu.

### 11. Liczy ryzyko i zysk
Dla każdego kandydata podaje:
- **Wejście** — strefa zakupu,
- **Stop** — poziom, po którego przebiciu teza przestaje być prawdziwa i pozycję się zamyka,
- **C1 i C2** — dwa cele zysku (np. poprzedni szczyt i jego rozszerzenie),
- **R** — stosunek potencjalnego zysku do ryzyka (np. „1,9 / 3,1" znaczy: do pierwszego celu zarabiasz 1,9 raza tyle, ile ryzykujesz; do drugiego 3,1 raza).

Stopy muszą wynikać z wykresu, a nie być sztucznie ciasne. Szukamy R od ok. 2 w górę. **Dlaczego:** nawet gdy połowa transakcji jest stratna, dodatni stosunek zysku do ryzyka może dawać wynik na plus.

### 12. Nadaje punkty (0–100)
Każda spółka dostaje sumę: fundamenty 20, trend długoterminowy 15, jakość korekty 15, jakość wsparcia 10, siła relatywna 10, momentum i potwierdzenie 10, wolumen 5, sektor 5, katalizatory 5, ryzyko/zysk 5. W tabeli pokazane są trzy liczby: **Fund/30** (fundamenty + sektor + katalizatory), **Tech/70** (wykres) i **Suma**. **Dlaczego:** punkty pozwalają ustawić kandydatów w kolejności i szybko porównać, ale nie zastępują czytania uzasadnienia.

### 13. Odrzuca to, co nie pasuje
Spółki w długim spadku, po załamaniu trendu, bez korekty (zbyt wykupione), niepłynne albo z naruszoną tezą trafiają do sekcji „Odrzucone" wraz z powodem. **Dlaczego:** wiedza, czego nie kupować, jest równie ważna jak lista kandydatów.

### 14. Rozlicza poprzedni raport
Sprawdza, co się stało z poprzednimi propozycjami: czy strefa wejścia została dotknięta, czy zadziałał trigger, czy cena doszła do celu albo do stopu. **Dlaczego:** uczciwa weryfikacja pokazuje, co naprawdę działa.

### 15. Publikuje raport
Powstaje plik raportu, strona jest generowana i trafia na romangpw.pl. Raport ma stałą kolejność sekcji: reżim rynkowy, ranking (10–15 spółek), TOP 3, szczegółowa analiza TOP 5, watchlista na 1–3 tygodnie, odrzucone, rozliczenie, metoda i zastrzeżenia.

## Jak czytać raport

- **Kurs** — ostatnie zamknięcie; przy datach w nawiasach (np. „3.11") dane są starsze niż reszta.
- **Od maks. 50s** — o ile procent kurs jest poniżej szczytu z ostatnich 50 sesji. 0% oznacza, że nie ma korekty, tylko szczyt.
- **Trend, Wsparcie, RSI** — krótki opis trendu, poziom wsparcia i wartość wskaźnika RSI.
- **Klasa** — A, B albo C (patrz krok 7).
- **Wejście / Stop / C1 / C2 / R** — plan transakcji (krok 11). R liczone od środka strefy wejścia.
- **Werdykty** w analizie TOP 5: STRONG BUY SETUP, GOOD SETUP, WATCH, WAIT FOR CONFIRMATION, AVOID. Dotyczą wyłącznie atrakcyjności układu według tej metody.
- **Watchlista** — spółki jeszcze niegotowe, z dokładnym warunkiem technicznym, który uczyniłby je interesującymi.

## Ograniczenia, o których warto wiedzieć

- Dane pochodzą z publicznych źródeł (m.in. biznesradar.pl, bankier.pl, serwisy z komunikatami spółek). Czasem są opóźnione, niekompletne albo zawierają błędy. Raport zaznacza, kiedy czegoś nie udało się zweryfikować.
- Dla spółek z GPW nie ma w darmowych źródłach średnich SMA100 i SMA200, więc nie są podawane.
- Ceny, wskaźniki i daty raportów nie są wymyślane. Jeśli czegoś brakuje, raport mówi to wprost i nie zgaduje.
- Metoda nie zna przyszłości. Stop-loss i niewielka pozycja ograniczają ryzyko, ale go nie eliminują.

**Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.**
