"""Rejestr strategii uzupełniających: adresy stron, nazwy (PL/EN), krótkie opisy i zasady pokazywane na stronach portfeli.

Logika reguł jest w modułach strat/<moduł>.py; tu tylko metadane. Kolejność wpisów to kolejność zakładek w menu (S1–S5).
"""

STRATEGIES = [
    {
        "slug": "kompas", "slug_en": "compass", "module": "kompas",
        "name": {"pl": "Kompas", "en": "Compass"},
        "tagline": {"pl": "Który segment GPW prowadzi? Rotacja WIG20, mWIG40 i sWIG80 z filtrem trendu.",
                    "en": "Which GPW segment leads? Rotation across WIG20, mWIG40 and sWIG80 with a trend filter."},
        "cadence": {"pl": "raz w miesiącu", "en": "monthly"},
        "rules": {
            "pl": ["**Co trzymamy:** jedną pozycję w jednostkach indeksu (WIG20, mWIG40 albo sWIG80) lub gotówkę. Model pomija koszty i odchylenia ETF-ów od indeksu.",
                   "**Wybór:** raz w miesiącu indeks o najwyższym średnim zwrocie z 6 i 12 miesięcy.",
                   "**Filtr trendu:** pozycja tylko wtedy, gdy kurs wybranego indeksu leży nad średnią z 10 ostatnich zamknięć miesięcznych. Inaczej gotówka.",
                   "**Termin:** sygnał po ostatniej sesji miesiąca, zlecenie na otwarciu najbliższej sesji po publikacji raportu.",
                   "**Dane:** wskaźniki cenowe bez dywidend, więc wynik jest zaniżony względem ETF-ów na indeksy TR."],
            "en": ["**What we hold:** one position in units of an index (WIG20, mWIG40 or sWIG80) or cash. The model ignores ETF costs and tracking differences.",
                   "**Selection:** once a month, the index with the highest average 6- and 12-month return.",
                   "**Trend filter:** a position only if the chosen index sits above the average of its last 10 month-end closes. Otherwise cash.",
                   "**Timing:** the signal comes after the last session of the month, the order is placed at the open of the first session after the report is published.",
                   "**Data:** price indices without dividends, so the result is understated versus ETFs on the TR indices."]},
    },
    {
        "slug": "ped", "slug_en": "momentum", "module": "ped",
        "name": {"pl": "Pęd", "en": "Momentum"},
        "tagline": {"pl": "Kupuj siłę: spółki, które rosły najmocniej w ostatnich 12 miesiącach, z filtrem trendu.",
                    "en": "Buy strength: the stocks that rose the most over the last 12 months, with a trend filter."},
        "cadence": {"pl": "raz w miesiącu", "en": "monthly"},
        "rules": {
            "pl": ["**Uniwersum:** spółki z medianą obrotu z 60 sesji co najmniej 0,5 mln zł dziennie, notowane w co najmniej 90% sesji, bez skoków dziennych powyżej 30% w ostatnim roku (możliwe splity).",
                   "**Ranking:** zwrot z 12 miesięcy bez ostatniego miesiąca (12-1), ceny skorygowane o dywidendy.",
                   "**Filtr:** kurs nad średnią z 200 sesji.",
                   "**Portfel:** 12 spółek o równych wagach. Spółka zostaje, dopóki jest w czołowej 25. Maksymalnie 3 spółki z jednego sektora.",
                   "**Reżim:** gdy Kompas pokazuje gotówkę, nowe pozycje mają połowę zwykłej wielkości.",
                   "**Rebalans:** raz w miesiącu. Pozycji, które zostają, nie dokupujemy ani nie obcinamy."],
            "en": ["**Universe:** stocks with a 60-session median turnover of at least PLN 0.5m a day, quoted in at least 90% of sessions, with no daily jump above 30% in the last year (possible splits).",
                   "**Ranking:** return over 12 months excluding the latest month (12-1), prices adjusted for dividends.",
                   "**Filter:** price above the 200-session average.",
                   "**Portfolio:** 12 stocks, equally weighted. A stock stays while it is in the top 25. At most 3 stocks from one sector.",
                   "**Regime:** when Compass shows cash, new positions are half the usual size.",
                   "**Rebalance:** once a month. Positions that stay are neither topped up nor trimmed."]},
    },
    {
        "slug": "zloty-srodek", "slug_en": "golden-mean", "module": "zloty",
        "name": {"pl": "Złoty Środek", "en": "Golden Mean"},
        "tagline": {"pl": "Dobre firmy w rozsądnej cenie: jakość (F-score, zyskowność) połączona z wyceną EV/EBIT.",
                    "en": "Good companies at a sensible price: quality (F-score, profitability) combined with EV/EBIT valuation."},
        "cadence": {"pl": "dwa razy w roku", "en": "twice a year"},
        "rules": {
            "pl": ["**Dane:** roczne sprawozdania spółek niefinansowych z pliku data/fundamentals.csv. Bez danych portfel zostaje w gotówce.",
                   "**Progi wejścia:** F-score co najmniej 7, dodatni wolny przepływ pieniężny, dług netto do EBITDA do 3.",
                   "**Ranking:** wycena EV/EBIT (taniej znaczy lepiej) plus zyskowność brutto do aktywów (wyżej znaczy lepiej).",
                   "**Portfel:** 20 spółek o równych wagach. Zostają przy F-score co najmniej 5, długu netto do EBITDA do 4 i miejscu w czołowych 30.",
                   "**Limity:** maksymalnie 4 spółki z sektora i 8 łącznie z energetyki i paliw (sektory wrażliwe regulacyjnie).",
                   "**Rebalans:** ostatnia sesja maja (po raportach rocznych) i października (odświeża głównie wycenę, bo model czyta tylko roczne sprawozdania)."],
            "en": ["**Data:** annual statements of non-financial companies from data/fundamentals.csv. Without data the portfolio stays in cash.",
                   "**Entry thresholds:** F-score of at least 7, positive free cash flow, net debt to EBITDA up to 3.",
                   "**Ranking:** EV/EBIT valuation (cheaper is better) plus gross profit to assets (higher is better).",
                   "**Portfolio:** 20 stocks, equally weighted. They stay at an F-score of at least 5, net debt to EBITDA up to 4 and a place in the top 30.",
                   "**Limits:** at most 4 stocks per sector and 8 in total from power utilities and fuels (regulation-sensitive sectors).",
                   "**Rebalance:** the last session of May (after annual reports) and October (mainly refreshes the valuation, because the model reads annual statements only)."]},
    },
    {
        "slug": "przystan", "slug_en": "harbor", "module": "przystan",
        "name": {"pl": "Przystań", "en": "Harbor"},
        "tagline": {"pl": "Spokojny port na wzburzonym rynku: spółki o najniższej zmienności.",
                    "en": "A calm port in a rough market: the lowest-volatility stocks."},
        "cadence": {"pl": "raz na kwartał", "en": "quarterly"},
        "rules": {
            "pl": ["**Uniwersum:** mediana obrotu z 60 sesji co najmniej 0,3 mln zł dziennie, notowania w co najmniej 90% sesji, maksymalne obsunięcie z 12 miesięcy nie głębsze niż 30%.",
                   "**Wybór:** dolny kwintyl rocznej zmienności dziennych zwrotów (ceny skorygowane o dywidendy).",
                   "**Portfel:** do 16 spółek o równych wagach. Spółka zostaje, dopóki mieści się w najspokojniejszych 40% uniwersum. Maksymalnie 4 spółki z sektora.",
                   "**Rebalans:** raz na kwartał (koniec marca, czerwca, września i grudnia)."],
            "en": ["**Universe:** 60-session median turnover of at least PLN 0.3m a day, quoted in at least 90% of sessions, 12-month maximum drawdown no deeper than 30%.",
                   "**Selection:** the lowest quintile of annual volatility of daily returns (prices adjusted for dividends).",
                   "**Portfolio:** up to 16 stocks, equally weighted. A stock stays while it is in the calmest 40% of the universe. At most 4 stocks per sector.",
                   "**Rebalance:** quarterly (end of March, June, September and December)."]},
    },
    {
        "slug": "dryf", "slug_en": "drift", "module": "dryf",
        "name": {"pl": "Dryf", "en": "Drift"},
        "tagline": {"pl": "Płyń z prądem po wynikach: zdarzenia cenowo-wolumenowe w sezonie raportów.",
                    "en": "Ride the drift after results: price-and-volume events in the reporting season."},
        "cadence": {"pl": "skan codzienny w oknach raportowych", "en": "daily scan inside reporting windows"},
        "rules": {
            "pl": ["**Skan:** codziennie, w oknach publikacji raportów (1 lutego–30 kwietnia, 1–20 maja, 15 sierpnia–30 września, 1–20 listopada).",
                   "**Zdarzenie dodatnie:** luka otwarcia co najmniej +2%, wzrost dnia od +4% do +30%, wolumen co najmniej 2,5 raza wyższy niż mediana z 20 sesji, zamknięcie w górnej połowie dnia, mediana obrotu co najmniej 1 mln zł.",
                   "**Wejście:** kupno na otwarciu następnej sesji za stałe 10 000 zł (maksymalnie 10 pozycji). Zlecenie jest anulowane, gdy otwarcie leży na stopie lub poniżej.",
                   "**Wyjście:** stop na zamknięciu sprzed zdarzenia (przy luce po cenie otwarcia) albo po 40 sesjach.",
                   "**Lista „nie kupuj”:** lustrzane zdarzenia ujemne na 60 sesji, informacyjnie."],
            "en": ["**Scan:** daily, inside reporting windows (1 February–30 April, 1–20 May, 15 August–30 September, 1–20 November).",
                   "**Positive event:** opening gap of at least +2%, a day gain from +4% to +30%, volume at least 2.5 times the 20-session median, a close in the upper half of the day's range, median turnover of at least PLN 1m.",
                   "**Entry:** buy at the next session's open for a fixed PLN 10,000 (at most 10 positions). The order is cancelled if the open is at or below the stop.",
                   "**Exit:** a stop at the close before the event (at the open price on a gap) or after 40 sessions.",
                   "**No-buy list:** mirror-image negative events for 60 sessions, for information."]},
    },
]

BY_SLUG = {s["slug"]: s for s in STRATEGIES}
SLUGS = [s["slug"] for s in STRATEGIES]


def module(slug):
    """Moduł strat.<moduł> strategii o danym slugu (import leniwy, bez cykli)."""
    import importlib
    return importlib.import_module(f"strat.{BY_SLUG[slug]['module']}")


def slug_for_lang(slug, lang):
    return BY_SLUG[slug]["slug_en"] if lang == "en" else slug
