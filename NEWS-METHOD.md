# NEWS-METHOD — zakładka „Newsy dnia” (GPW)

Instrukcja dla codziennego zadania (patrz `METHOD.md`, krok „Newsy dnia”). Zakładka ma pokazywać **tylko istotne i ciekawe informacje, w neutralnym tonie**. Jeżeli danego dnia nic nie przekracza progu, **nie tworzysz wydania** (zakładka dalej pokazuje ostatnie istniejące). Źródła i progi zmieniamy w `newsy/sources.json`, kryteria w tym pliku — bez zmian w kodzie.

## Źródła
Używaj wyłącznie źródeł z `newsy/sources.json` z `enabled: true`, w kolejności `priority`. Dane pobieraj WebFetch (po jednym zapytaniu naraz, najwyżej 3 równolegle). Wiadomość opieraj na treści artykułu lub komunikatu, a nie na samym nagłówku. Fakt liczbowy potwierdź w tekście; jeśli dwa źródła podają różne liczby, wybierz źródło pierwotne (komunikat spółki) albo pomiń, albo napisz, że liczby się różnią. Nie czytaj i nie omijaj źródeł zablokowanych (robots, paywall).

## Ocena istotności (0–10)
Dla każdej kandydującej wiadomości oceń:
- **Materialność (0–4):** czy to twardy fakt, który zmienia obraz spółki, sektora albo rynku: wyniki lub szacunki wyników względem konsensusu i rok do roku, zmiana prognoz lub dywidendy, skup akcji, emisja, M&A i wezwania, kontrakty istotne względem przychodów, decyzje regulacyjne, rewizje indeksów (WIG20/MSCI/FTSE), decyzje RPP/NBP i dane makro, zdarzenia na rynkach globalnych wpływające na GPW (USA, surowce, kurs PLN).
- **Skala (0–2):** duża spółka lub indeks (WIG20, mWIG40) albo cały sektor = 2; spółka z naszego rankingu swing, portfela lub listy dywidend = co najmniej 1; mała spółka bez związku = 0.
- **Nowość (0–2):** informacja z ostatnich `max_age_hours` godzin i nieopisana w poprzednich `dedup_last_issues` wydaniach = 2; kontynuacja = 1; powtórka = 0.
- **Wiarygodność (0–2):** komunikat spółki/ESPI/EBI, oficjalne dane lub depesza z podanym źródłem = 2; media z czytelnym odwołaniem do źródła pierwotnego = 1; plotka, opinia bez danych = 0.
Wchodzi wynik **≥ `min_score`**, najwyżej `max_items` pozycji, od najwyższego wyniku. Wyniki nie są pokazywane czytelnikowi.

Nie wchodzą: wypowiedzi bez nowej informacji, prognozy kursów, komentarze „co dalej z rynkiem”, rekomendacje domów maklerskich bez zmiany ceny docelowej lub oceny (a ze zmianą — tylko jako fakt), emocjonalne podsumowania sesji, ogólne artykuły edukacyjne, treści płatne.

## Język (bez emocji)
- Same fakty: kto, co, ile, względem czego (konsensus, rok wcześniej, poprzedni kwartał), kiedy. Liczby z jednostką i źródłem.
- Bez przymiotników oceniających („fatalne”, „rewelacyjne”, „szok”, „kłopoty”), wykrzykników, metafor i spekulacji o kursie. Zamiast „mocny kwartał” napisz „skorygowana EBITDA 133 mln zł wobec konsensusu 108,8 mln zł”.
- Opinie tylko wprost przypisane (imię, instytucja) i tylko gdy same są informacją; oddziel je od faktów. Wypowiedzi influencerów i analityków nie są sygnałem — jeżeli się pojawiają, to jako „X powiedział/napisał Y” z linkiem.
- Wyraźnie odróżniaj: komunikat wstępny/szacunkowy od ostatecznego, wybór oferty od podpisanej umowy, plan od decyzji.
- Nie dodawaj wniosków inwestycyjnych ani ocen „dobre/złe dla spółki”. Wolno wskazać, których tickerów i dlaczego dotyczy informacja.

## Format wydania (`newsy/RRRR-MM-DD.md`)
Nagłówek `# Newsy dnia — <dzień tygodnia> <D miesiąc RRRR>` i jedna linia: z jakiego przedziału czasu pochodzą wiadomości. Potem sekcje `## Rynek i makro` oraz `## Spółki` (pomiń pustą). Każda pozycja:

```
### Neutralny tytuł z faktem i liczbą
Fakty w 2–4 zdaniach (kto, co, ile, względem czego).

**Dlaczego istotne:** jedno zdanie — których tickerów/sektora dotyczy i przez jaki mechanizm (bez prognozy kursu).

*Źródło: [Nazwa](url) · D.MM, GG:MM*
```
Na końcu sekcja `## Poniżej progu` (jedna linia: tytuły pominiętych wiadomości z oceną 4–5 — to pomaga dostrajać algorytm) oraz linia `*Sprawdzone źródła: …*`. Ostatnia linia: `Informacje zebrane automatycznie z publicznych źródeł, nie porada inwestycyjna.`

## Wersja angielska
Przetłumacz wydanie do `newsy-en/RRRR-MM-DD.md` (ta sama struktura, tytuł `# News of the day — Friday 6 November 2026`, sekcje `## Market and macro`, `## Companies`, `## Below the threshold`, liczby w formacie angielskim; ostatnia linia: `Information collected automatically from public sources, not investment advice.`).

## Gdy nic nie przekracza progu
Nie twórz pliku ani commita dla newsów, w podsumowaniu zadania napisz „Newsy dnia: brak wydania (nic powyżej progu)”.

## Dostrajanie
Po każdym wydaniu użytkownik może poprosić o zmianę źródeł (`newsy/sources.json`), progu (`min_score`), liczby pozycji albo kryteriów (ten plik). Zmiany wprowadzaj w tych plikach, nie w kodzie. Sekcja „Poniżej progu” pokazuje, co zostało odrzucone.
