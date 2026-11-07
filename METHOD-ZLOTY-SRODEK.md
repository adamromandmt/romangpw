# Złoty Środek — jak uzupełnić dane fundamentalne (`data/fundamentals.csv`)

Złoty Środek ocenia spółki po jakości (F-score Piotroskiego, zyskowność brutto do aktywów) i wycenie (EV/EBIT), a do tego potrzebuje rocznych sprawozdań. Repozytorium nie ma sieciowego źródła tych danych, więc plik `data/fundamentals.csv` wypełnia osobno człowiek albo sesja z dostępem do internetu (sesja, która buduje stronę, nie ma sieci). Dopóki w pliku jest sam nagłówek, strategia pokazuje w raporcie „Czeka na dane fundamentalne”, a jej portfel wirtualny stoi w gotówce. Reguły strategii opisuje `strategie/zloty-srodek/metodologia.md`; ten plik opisuje tylko dane.

## Co uzupełnić

- Niefinansowe spółki z naszej listy (`data/universe.json`). Banki i ubezpieczyciele (sektory `banki` i `fin` w `data/sectors.json`) są poza zakresem tej wersji, więc ich nie wpisujemy.
- Dla każdej spółki **dwa kolejne lata obrotowe**: ostatni opublikowany rok i rok wcześniejszy. Model porównuje je ze sobą (wzrost ROA, płynności, marży, rotacji aktywów, zmiana długu i liczby akcji). Bez poprzedniego roku spółka nie jest oceniana.
- Zacznij od najpłynniejszych: tylko spółki z medianą obrotu co najmniej 0,3 mln zł dziennie mogą wejść do rankingu. Listę (ok. 60 pozycji) daje polecenie:

```
python3 - <<'PY'
from strat import lib
ctx = lib.Ctx()
ok, _ = lib.screen(ctx, ctx.asof, 300_000)
for tic, info in sorted(ok.items(), key=lambda kv: -kv[1]["turn"]):
    if ctx.sector(tic) not in {"banki", "fin"}:
        print(tic, round(info["turn"] / 1e6, 1), "mln zł obrotu dziennie (mediana z 60 sesji)")
PY
```

## Format pliku

CSV w UTF-8, jeden wiersz na spółkę i rok obrotowy, nagłówek dokładnie taki jak w repozytorium:

`tic,fy,period_end,published,revenue,gross_profit,ebit,ebitda,net_income,cfo,capex,total_assets,equity,current_assets,current_liabilities,debt,cash,shares,source`

| Kolumna | Znaczenie |
|---|---|
| `tic` | Symbol z `data/universe.json` (np. `KGH`). |
| `fy` | Rok, w którym kończy się rok obrotowy (dla roku kończącego się 30 czerwca 2025: `2025`). |
| `period_end` | Koniec okresu sprawozdawczego, `RRRR-MM-DD`. |
| `published` | Data publikacji raportu rocznego (komunikat ESPI/EBI lub strona relacji inwestorskich), `RRRR-MM-DD`. Wpisz ją zawsze, gdy ją znasz; puste pole oznacza „koniec okresu plus 120 dni”. |
| `revenue` | Przychody ze sprzedaży. |
| `gross_profit` | Zysk brutto ze sprzedaży (przychody minus koszt sprzedanych produktów, towarów i usług). Spółki w układzie rodzajowym go nie podają: zostaw pole puste, a spółka nie będzie oceniana (nie zastępuj przybliżeniem). |
| `ebit` | Zysk z działalności operacyjnej. |
| `ebitda` | EBIT plus amortyzacja i odpisy (z rachunku przepływów albo z not). |
| `net_income` | Zysk netto roku (skonsolidowany; gdy raport rozdziela, zysk przypadający akcjonariuszom jednostki dominującej). |
| `cfo` | Przepływy pieniężne netto z działalności operacyjnej. |
| `capex` | Nakłady na rzeczowe aktywa trwałe i wartości niematerialne jako liczba **dodatnia** (wydatek). |
| `total_assets` | Aktywa razem. |
| `equity` | Kapitał własny (przypisany akcjonariuszom jednostki dominującej). |
| `current_assets` | Aktywa obrotowe. |
| `current_liabilities` | Zobowiązania krótkoterminowe. |
| `debt` | Zadłużenie oprocentowane na koniec roku: kredyty, pożyczki, obligacje i leasing, krótko- i długoterminowe (razem z leasingiem według MSSF 16). |
| `cash` | Środki pieniężne i ich ekwiwalenty. |
| `shares` | Liczba akcji na koniec roku **w sztukach** (wyemitowane, pomniejszone o akcje własne, jeśli spółka je podaje). |
| `source` | Adres albo nazwa dokumentu, z którego wzięto liczby. |

**Jednostki:** wszystkie kwoty w **tysiącach złotych**, a `shares` w sztukach. Spółka raportująca w milionach złotych: pomnóż przez 1000; w złotych: podziel przez 1000. Przecinek dziesiętny i spacje w liczbach są akceptowane, ale lepiej wpisywać liczby z kropką i bez spacji. Dane skonsolidowane, gdy spółka je publikuje; w przeciwnym razie jednostkowe.

Przykład (liczby wymyślone, tylko do pokazania formatu — nie wpisuj ich do pliku):

```
XYZ,2025,2025-12-31,2026-03-27,1200000,400000,160000,220000,100000,150000,40000,1100000,600000,500000,300000,180000,80000,10000000,https://example.com/raport-roczny-2025.pdf
```

## Zasady wiarygodności

1. **Tylko liczby z dokumentu.** Niczego nie szacujemy ani nie dopełniamy z pamięci. Gdy pole jest nieznane, zostaw je puste: wiersz z brakiem w którymkolwiek polu liczbowym nie wchodzi do oceny (raport pokaże to w lejku jako brak kompletu danych).
2. **Bez wyprzedzania faktów.** Wiersz obowiązuje dopiero od daty `published`, więc wpisz ją prawdziwie. Dane roku poprzedniego bierz z jego własnego raportu rocznego, nie z kolumny porównawczej następnego raportu: model ma odtwarzać to, co rynek znał w dniu sygnału (korekty wcześniejszych lat pomijamy, to świadome uproszczenie).
3. **Agregatory tylko jako pomoc.** Serwisy zbiorcze (np. BiznesRadar) wolno wykorzystać do znalezienia liczb, ale przed zapisem sprawdź je z oficjalnym sprawozdaniem i wpisz je w `source`.
4. **Nie nadpisuj historii.** Nowy rok dopisuj jako nowy wiersz; stare lata zostają.

## Kontrole przed zapisem

- Aktywa razem są większe od kapitału własnego i od aktywów obrotowych; zysk brutto ze sprzedaży nie przekracza przychodów; EBITDA nie jest niższa od EBIT (poza przypadkami z odpisami wykazanymi osobno); `capex` jest dodatni.
- Przychody do aktywów mieszczą się zwykle między 0,1 a 5. Wartość spoza tego przedziału zwykle znaczy pomyłkę jednostek.
- Liczba akcji to miliony albo dziesiątki milionów sztuk, nie tysiące.
- Kwoty obu lat tej samej spółki mają ten sam rząd wielkości (nagła zmiana o 1000 razy to pomyłka jednostek).
- Rok `fy` i `period_end` zgadzają się ze sobą, a `published` leży po `period_end`.

## Po uzupełnieniu pliku

```
python3 -m strat daily --only zloty-srodek --force
python3 build.py
python3 tools/check_site.py
python -m pytest -q
```

`--force` liczy sygnał na ostatnią sesję mimo że nie przypada na koniec maja ani października; zastępuje on zlecenia z poprzedniego sygnału, a portfel kupi skład na otwarciu następnej sesji. Potem otwórz raport `strategie/zloty-srodek/pl/<data>.md` i przeczytaj linię „Lejek”: pokazuje, ile spółek miało sprawozdania, ile było niefinansowych i płynnych, ile miało komplet danych z dwóch lat, ile dało się policzyć w rankingu i ile spełniło progi wejścia. Duży spadek między „ze sprawozdaniami” a „z kompletem danych” oznacza braki w wierszach (najczęściej puste `gross_profit`). Te same polecenia można uruchomić z GitHub Actions: Actions → „Strategie uzupełniające” → Run workflow, z `only=zloty-srodek` i `force=true`.

## Jak często

Raz w roku po sezonie raportów rocznych (większość spółek publikuje do końca kwietnia) i przed sygnałem z ostatniej sesji maja. Kolejny sygnał, z ostatniej sesji października, używa tych samych sprawozdań i odświeża głównie wycenę, bo model nie czyta wyników półrocznych. Spółka, która opublikowała raport rocznie później, dołączy do oceny przy najbliższym sygnale po dacie `published`.

Ćwiczenie przesiewowe według zadanego frameworku, nie porada inwestycyjna.
