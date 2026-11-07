# Dryf — metodologia

Dryf gra na luce w górę po raporcie kwartalnym.

## Reguły

1. Okno raportu: dzień publikacji i 3 kolejne sesje.
2. Sygnał: otwarcie co najmniej 2% powyżej poprzedniego zamknięcia, a wolumen co najmniej 2,5 razy większy od średniej z 20 sesji.
3. Kupno na otwarciu następnej sesji, pozycja 5% kapitału, maksymalnie 20 pozycji.
4. Stop: poprzednie zamknięcie sprzed luki. Wyjście po 40 sesjach.
5. Luka w dół z takim samym wolumenem w oknie raportu wpisuje spółkę na listę „nie kupuj" na 60 sesji.

## Dane

Daty raportów pochodzą z raportów swing (`reports/*.json`) i opcjonalnego pliku `data/earnings.csv` (kolumny tic, date). Pokrycie jest niepełne, więc część spółek nie ma jeszcze okna.

## Portfel wirtualny

- Kapitał 100 000 PLN, prowizja 0,2% od transakcji, start 6.11.2026, pierwsze zlecenia na otwarciu 9.11.2026.
- Benchmark: WIG20 (indeks cenowy).
- To symulacja na surowych notowaniach z archiwum GPW. Dywidendy nie są jeszcze doliczane do portfela, podatek nie jest uwzględniony.
- Brak danych nie jest błędem: strategia zostaje w gotówce, a zakładka Raport pokazuje, czego brakuje („czeka na dane").
- Ćwiczenie przesiewowe, nie porada inwestycyjna.
