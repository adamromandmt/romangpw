# Złoty Środek — metodologia

Złoty Środek szuka tanich spółek o solidnych fundamentach.

## Filtry

- F-score Piotroskiego co najmniej 7.
- Dodatni wolny przepływ pieniężny (FCF).
- Dług netto / EBITDA co najwyżej 3.
- Bez banków i ubezpieczycieli.

## Ranking i skład

- Ranking łączy EV/EBIT (niżej lepiej) i zysk brutto / aktywa (wyżej lepiej).
- 20 spółek, nie więcej niż 8 z sektora energii i paliw.
- Rebalans w maju i w październiku.

## Dane

Strategia czyta `data/fundamentals.csv` (kolumny: tic, sector, f_score, fcf, net_debt_ebitda, ev_ebit, gross_profit_assets, is_financial, is_energy). Dopóki plik ma tylko nagłówek, portfel zostaje w gotówce.

## Portfel wirtualny

- Kapitał 100 000 PLN, prowizja 0,2% od transakcji, start 6.11.2026, pierwsze zlecenia na otwarciu 9.11.2026.
- Benchmark: WIG20 (indeks cenowy).
- To symulacja na surowych notowaniach z archiwum GPW. Dywidendy nie są jeszcze doliczane do portfela, podatek nie jest uwzględniony.
- Brak danych nie jest błędem: strategia zostaje w gotówce, a zakładka Raport pokazuje, czego brakuje („czeka na dane").
- Ćwiczenie przesiewowe, nie porada inwestycyjna.
