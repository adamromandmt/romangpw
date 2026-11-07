# Momentum — methodology

Momentum buys strength: every month it picks 12 liquid stocks that rose the most over the last 12 months (skipping the latest one), provided their price is above the 200-session average. Swing buys a pullback in a trend, while Momentum buys stocks that are simply rising, regardless of any pullback.

This page describes the strategy itself. How the virtual portfolio works (capital, costs, order timing) is explained on the Portfolio tab; it is only a forward check of the forecasts from the start date.

## Hypothesis

Winners of recent months tend to stay winners more often than chance would suggest (cross-sectional momentum). On the US market, Jegadeesh and Titman (1993) found that winners of the last 3–12 months beat losers by about 1% a month (a figure from a secondary source). George and Hwang (2004) showed that proximity to the 52-week high predicts returns better than past returns alone. For the GPW the evidence is **mixed**, and this is the least well documented of the five strategies.

## Rules (as the code computes them)

1. **Universe.** Stocks from our list (data/universe.json) that meet all of these conditions on the signal date: the latest quote is no older than 10 days; at least 12 months of history; a 60-session median daily turnover of at least PLN 0.5m; candles in at least 90% of the last 120 sessions; no daily price change (adjusted for dividends) above 30% in the last ~260 quotes, which could mean a split or a shock. Stocks on the manual exclusion list (strategie/wykluczenia.json) drop out immediately.
2. **12-1 ranking.** The return from 12 months to 1 month before the signal date, on dividend-adjusted prices (data/dividends). We skip the latest month, following the classic 12-1 construction, because very short-term returns tend to reverse.
3. **Trend filter.** The price must be above the 200-session average.
4. **Holdings.** 12 stocks in equal weights. A stock already in the portfolio stays as long as it is in the top 25 of the ranking, is still above the 200-session average and fits within the sector limit (hysteresis limits turnover). Open slots go to the highest-ranked stocks that meet the trend filter and the limit: at most 3 stocks from one sector (a rough in-house classification in data/sectors.json; the "other" sector has no limit).
5. **Regime.** When Compass shows cash, new positions are half the usual size. Positions that stay are neither topped up nor trimmed.
6. **Timing.** We compute the signal on data from the last session of each month, and the report comes out after the first session of the next month. The first holdings were set on 6 November 2026, outside the cycle.

## Parameters

The count of 12 stocks, the threshold of 25 in the hysteresis, the limit of 3 per sector, the 200-session filter and the PLN 0.5m turnover threshold are starting values, not research results or optimisation on GPW data. The 12-1 window is classic, but on the GPW momentum tends to be detected only at shorter horizons (see below). We did not test other rankings; the report shows the 6-month return and the distance from the 52-week high for information only.

## Evidence and its limits

- **Daniel and Moskowitz** (USA, 1927–2013, as presented by Swedroe): momentum has positive averages, but there are rare, long runs of losses. They occur in "panic states", after market declines with high volatility, together with rebounds. Swedroe notes that long-only strategies do not suffer such deep crashes, because the largest losses arise on the short side.
- **GPW, a positive result:** a study described on CEEOL finds "some evidence" of momentum, but only at short horizons. The gain comes from smaller losses of winners, and at longer horizons a contrarian effect appears.
- **GPW, a negative result:** Zaremba and Konieczka (all GPW stocks, 2001–2013): the momentum, value and size premia appear only partially, strengthen together, but vanish once transaction costs and liquidity are taken into account.
- **Conclusion:** the classic 12-1 may not work on the GPW. This portfolio is a live test, not the deployment of a proven method.
- **Haircut:** McLean and Pontiff (97 predictors, 80 publications): out of sample, before publication, returns were 26% lower, and after publication 58% lower. We assume the real edge is at most half of that in a backtest.

We did not re-check several studies from the earlier review (including Applied Financial Economics 2013, Sekula and FIQF 2016), so we base no conclusions on them.

## Benchmark

We compare the portfolio with the WIG20, because this forward check is meant to answer whether the strategy beats the WIG20. The WIG20, however, is a price index, without dividends. According to Parkiet (7 May 2024), since the end of 2004 the WIG20 has gained about 25% and the WIG20TR about 155%, which converts to about 1.2% versus about 5.0% a year (our own calculation from these values, about 19.4 years). Comparing with a price index therefore flatters a portfolio that collects dividends. The bar is also low for structural reasons: in 2013–2022 the WIG20TR returned about −4%, the mWIG40TR +114% and the sWIG80TR +119%. Simply not holding the WIG20 can therefore give an edge that is not due to momentum. We do not run an equal-weight portfolio of the whole universe, which would let us tell selection apart from avoiding the WIG20, so the result against the WIG20 has to be read with this in mind.

## Data and known limitations

- The repository holds about a year of quotes, so there is no backtest, and a full 12-1 ranking is available only from the end of October 2026.
- The universe is today's list of stocks, without delisted ones, so it is unsuitable for backtests without a survivorship-bias correction.
- The dividend adjustment comes from data in data/dividends (dates and amounts); missing entries understate the return of dividend payers.
- The sector classification is rough, so the limit of 3 stocks per sector works only approximately.
- Momentum risks crashes on rebounds after market declines and requires frequent trading (turnover costs, 19% tax on realisation outside an IKE or IKZE).
- The same stocks may end up in both Momentum and the swing scanner; we do not measure the overlap of the portfolios.

## Role alongside swing

"Buy strength" regardless of any pullback, while swing buys a pullback in a trend. The regime filter comes from Compass.

## Rule change history

- 7 November 2026: first version of the rules and the first holdings (6 November 2026).

## Sources

- [NBER: Momentum Crashes (Daniel, Moskowitz)](https://www.nber.org/papers/w20439)
- [etf.com, Swedroe: The Downside of Momentum](https://www.etf.com/sections/index-investor-corner/swedroe-downside-momentum)
- [George, Hwang: The 52-Week High and Momentum Investing](https://typeset.io/pdf/the-52-week-high-and-momentum-investing-4u9j16d52p.pdf)
- [CEEOL: momentum on the GPW](https://www.ceeol.com/search/article-detail?id=762235)
- [Zaremba, Konieczka (FIQF 2017)](https://reference-global.com/article/10.1515/fiqf-2016-0119)
- [Jegadeesh, Titman (secondary source, CBS)](https://research.cbs.dk/en/studentProjects/88a3aa5c-bc3e-4141-8f23-4d678e9db4c1/)
- [Parkiet: Czemu wyniki WIG20 były w ostatnich latach tak słabe (in Polish)](https://www.parkiet.com/analizy-rynkowe/art38741821-czemu-wyniki-wig20-byly-w-ostatnich-latach-takie-slabe-3)
- [McLean, Pontiff: Does Academic Research Destroy Stock Return Predictability?](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

Screening exercise under the given framework, not investment advice.
