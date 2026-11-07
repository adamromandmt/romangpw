# Kompas — metodologia

Kompas wybiera jeden z trzech indeksów GPW albo gotówkę.

## Reguły

1. Porównujemy WIG20, mWIG40 i sWIG80.
2. Dla każdego liczymy średnią ze stóp zwrotu 6-miesięcznej i 12-miesięcznej (na zamknięciach miesięcznych).
3. Wybieramy indeks z najwyższą średnią.
4. Trzymamy go tylko wtedy, gdy jego kurs jest powyżej średniej z ostatnich 10 zamknięć miesięcznych. W przeciwnym razie portfel jest w gotówce.
5. Decyzja raz w miesiącu, wykonanie na otwarciu pierwszej sesji miesiąca.

## Odstępstwa od wzorca

- Indeksy cenowe zamiast całkowitego zwrotu (TR).
- Gotówka bez odsetek.
- Wykonanie po cenie otwarcia, bez kosztów śledzenia indeksu (pozycja w jednostkach indeksu).

## Dane

Potrzebne pliki `data/market/_WIG20.csv`, `_MWIG40.csv`, `_SWIG80.csv` i co najmniej 13 zamknięć miesięcznych.

## Portfel wirtualny

- Kapitał 100 000 PLN, prowizja 0,2% od transakcji, start 6.11.2026, pierwsze zlecenia na otwarciu 9.11.2026.
- Benchmark: WIG20 (indeks cenowy).
- To symulacja na surowych notowaniach z archiwum GPW. Dywidendy nie są jeszcze doliczane do portfela, podatek nie jest uwzględniony.
- Brak danych nie jest błędem: strategia zostaje w gotówce, a zakładka Raport pokazuje, czego brakuje („czeka na dane").
- Ćwiczenie przesiewowe, nie porada inwestycyjna.
