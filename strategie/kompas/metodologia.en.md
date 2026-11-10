# Compass — methodology

Compass answers one question: which segment of the GPW is strongest today (large caps in the WIG20, mid caps in the mWIG40 or small caps in the sWIG80), and is it worth being in equities at all. It is a rotation across three indices with a trend filter, computed once a month.

This page describes the strategy itself. How the virtual portfolio works (capital, costs, order timing) is explained on the Portfolio tab; it is only a forward check of the forecasts from the start date.

## Hypothesis

Price trends persist for months, and a simple trend filter limits losses in long declines. Rotating across segments adds a second benefit: we do not sit in the weakest one. On the GPW this has a local rationale. In 2013–2022, according to Parkiet, the WIG20TR returned about −4%, the mWIG40TR +114% and the sWIG80TR +119%.

## Rules (as the code computes them)

1. After the last session of the month, for the WIG20, mWIG40 and sWIG80 we compute the 6- and 12-month return (closing levels of the price indices). **Momentum** is the average of these two returns.
2. We pick the index with the highest momentum.
3. **Trend filter:** we hold it only if its close is above the average of its last 10 month-end closes (the current month counts as the close on the signal date). Otherwise we hold cash. We do not switch to the second-best index then: when the strongest index fails the filter, everything sits in cash.
4. The first signal was made on 6 November 2026, outside the cycle. Later ones are computed on data from the last session of each month. We treat a month as closed only when a session of the next month appears in the data, so the report with such a signal comes out after the first session of the new month.

The report also shows, for information, the Faber variant: which of the three indices sit above their 10-month average.

## Parameters

The 6-, 12- and 10-month windows are classic (the 10 months come from Faber), but they are starting values, not the result of optimisation on GPW data. We did not test other windows. CXO Advisory warns that choosing exactly 10 months may be a product of data snooping, although windows of 3, 6, 9 and 12 months also beat buy-and-hold on the Sharpe ratio (gross).

The rule is a hybrid of two variants from our study: index selection as in dual momentum, and the absolute test as in Faber (the 10-month average). We did not use the version that compares the 12-month return with the return on cash, because the repository has no cash rate.

## Evidence and its limits

- **Faber** (as presented by CXO Advisory): 1973–2012, five asset classes in equal weights, monthly rebalancing. Timing by the 10-month average versus buy-and-hold: annual return 10.5% versus 9.9%, Sharpe ratio 0.73 versus 0.44, maximum annual drop −9.5% versus −46.0%, all before costs. The main benefit is limiting declines rather than a higher return.
- **Hurst, Ooi and Pedersen** and **Moskowitz, Ooi and Pedersen** describe trend-following over very long samples. We used them only as a pointer to direction and did not check the details.
- **GPW:** we found no rigorous study of dual momentum or of the Faber rule on TR indices. The one blog test we found (357 moving-average tests) pointed to the monthly interval as the best for indices, but in a flat six-year window the average failed to beat the benchmark in about half of the cases. It is a blog, not an academic paper, and we did not re-check it.
- **Haircut:** McLean and Pontiff studied 97 return predictors from 80 publications: out of sample, before publication, returns were 26% lower, and after publication 58% lower. We assume the real edge is at most half of that in a backtest.

## Benchmark

We compare the portfolio with the WIG20, because this forward check is meant to answer whether the strategy beats the WIG20. In the model, Compass holds units of price indices, which, like the WIG20, do not collect dividends, so the comparison itself is consistent. It is, however, understated against ETFs on TR indices and against the proper benchmark, the WIG20TR. According to Parkiet (7 May 2024), since the end of 2004 the WIG20 has gained about 25% and the WIG20TR about 155%; converted to an annual rate (our own calculation from these values, about 19.4 years) that is about 1.2% versus about 5.0% a year. The repository has no quotes of TR indices or ETFs, so we do not compute a comparison with the WIG20TR.

## Data and known limitations

- The signal is computed on price indices from the GPW archive, without dividends. Their share of the return can differ across segments, so a ranking based on TR indices could look different.
- The repository holds about a year of quotes, so this rule has no backtest on GPW data. It is a forward check from the start date, not proof of effectiveness.
- Rotation can fail in a sideways market (repeated false switches). A change of position in practice means realising a gain and 19% tax outside an IKE or IKZE account.
- ETFs on TR indices (e.g. ETFBW20TR, ETFBM40TR, ETFBS80TR) are only a pointer to check with your broker. Their liquidity, fees and whether they can be bought in an IKE or IKZE must be verified independently.
- We left out the seasonal overlay (winter half-year November–April versus summer May–October). The 2019 Strefa Inwestorów analysis rests on small samples (9–14 half-years), ends in 2019, ignores costs and taxes, and the cause of the effect is unknown.

## Role alongside swing

Compass is a regime switch. Momentum uses it as a filter: when Compass shows cash, new Momentum positions are half the usual size. The swing scanner does not use Compass automatically.

## Rule change history

- 7 November 2026: first version of the rules and the first signal (6 November 2026).

## Sources

- [CXO Advisory: Long-term outperformance from trends defined by moving averages (Faber)](https://www.cxoadvisory.com/technical-trading/long-term-outperformance-from-trends-defined-by-moving-averages)
- [Hurst, Ooi, Pedersen: A Century of Evidence on Trend-Following Investing](https://fairmodel.econ.yale.edu/ec439/hurst.pdf)
- [stockbroker.pl: Średnia krocząca, a blog test (in Polish)](https://stockbroker.pl/srednia-kroczaca/)
- [Strefa Inwestorów: Najlepszy okres inwestowania (in Polish)](https://strefainwestorow.pl/artykuly/analizy/20191106/najlepszy-okres-inwestowania)
- [Parkiet: Czemu wyniki WIG20 były w ostatnich latach tak słabe (in Polish)](https://www.parkiet.com/analizy-rynkowe/art38741821-czemu-wyniki-wig20-byly-w-ostatnich-latach-takie-slabe-3)
- [Parkiet: 30 lat z WIG20 (in Polish)](https://www.parkiet.com/felietony/art40303951-30-lat-z-wig20)
- [McLean, Pontiff: Does Academic Research Destroy Stock Return Predictability?](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

Screening exercise under the given framework, not investment advice.
