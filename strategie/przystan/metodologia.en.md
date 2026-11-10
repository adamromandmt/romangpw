# Harbor — methodology

Harbor picks, once a quarter, up to 16 liquid stocks with the lowest volatility over the last year. It is a defensive portfolio: it is meant to limit swings and drawdowns rather than chase a rally.

This page describes the strategy itself. How the virtual portfolio works (capital, costs, order timing) is explained on the Portfolio tab; it is only a forward check of the forecasts from the start date.

## Hypothesis

Low-volatility stocks deliver better risk-adjusted returns over the long run than highly volatile ones (the low-volatility effect, described by, among others, Blitz and van Vliet and by Frazzini and Pedersen). For a long-only investor the main benefit is lower risk, not a sure excess return over the WIG20TR. In strong rallies the strategy may lag.

## Rules (as the code computes them)

1. **Universe.** Stocks from our list (data/universe.json) that meet all of these conditions on the signal date: the latest quote is no older than 10 days; at least 12 months of history; a 60-session median daily turnover of at least PLN 0.3m; candles in at least 90% of the last 120 sessions (rarely traded stocks have artificially low volatility); no daily price change (adjusted for dividends) above 30% in the last ~260 quotes; a maximum drawdown over the last 252 sessions no deeper than 30%. Stocks on the manual exclusion list (strategie/wykluczenia.json) drop out immediately.
2. **Volatility.** The standard deviation of daily log returns over the last ~250 sessions (dividend-adjusted price, at least 200 returns between consecutive exchange sessions), multiplied by the square root of 252.
3. **Selection.** Stocks from the lowest volatility quintile of the universe enter the portfolio, that is, the calmest fifth.
4. **Holdings.** Up to 16 stocks in equal weights. A stock already in the portfolio stays as long as it remains within the calmest 40% of the universe and the sector limit allows (hysteresis limits turnover). At most 4 stocks from one sector (a rough in-house classification in data/sectors.json; the "other" sector has no limit). The portfolio may hold fewer than 16 stocks if the lowest quintile is smaller after the sector limits.
5. **Timing.** We compute the signal on data from the last session of March, June, September and December, and the report comes out after the first session of the next month. The first holdings were set on 6 November 2026, outside the cycle.

## Parameters

The lowest quintile, the 40% threshold in the hysteresis, the limit of 16 stocks and 4 per sector, the PLN 0.3m turnover threshold and the 90% presence threshold are starting values, not research results or optimisation on GPW data.

**We added the 30% drawdown filter after looking at the first run on sample data**, before the first holdings were set. Without it the lowest volatility quintile would have included AMC, which had lost 31.1% from its peak over the year, and right behind it KRU (−31.7%). Low volatility of daily returns can hide a slow but deep slide in the price, and that is not a portfolio we want to call defensive. The study on which we based the strategy proposed a quality filter built from financial data (positive net income and ROE, an F-score of at least 5, no negative equity). Such data is not in the repository, so the drawdown filter is only a price-based stand-in safeguard. It is the only parameter we changed after looking at the data.

## Evidence and its limits

- **Blitz, Pang and van Vliet** (as presented by CXO Advisory): 30 emerging markets, December 1988 – December 2010, about 1,000 stocks a year. The lowest-volatility quintile beat the highest by 4.4% a year (geometric; 2.1% arithmetic), and the Sharpe ratio was 0.64 versus 0.29. A hedge portfolio (long low-volatility stocks, short high-volatility ones) beat the emerging-market index by 8.8% a year, mainly thanks to the short side. The three-factor alpha was 5.7%, and after adding momentum 3.1% and statistically insignificant. All before costs.
- **Poland 1989–2010** (from the same study): a portfolio long high-volatility and short low-volatility stocks returned −9.5% (t = −1.23). The direction is consistent with the low-volatility effect, but not statistically significant on its own. The Falkenblog blog read from the study's table that in 17 of 19 countries low-volatility stocks beat high-volatility ones (exceptions: Mexico and Russia); we did not re-check this reading.
- **Conclusion:** for a long-only investor the main benefit is lower risk, not a sure excess return over the WIG20TR. In strong rallies the strategy may lag.
- **Haircut:** McLean and Pontiff (97 predictors, 80 publications): out of sample, before publication, returns were 26% lower, and after publication 58% lower. We assume the real edge is at most half of that in a backtest.

## Benchmark

We compare the portfolio with the WIG20, but the WIG20 is a price index, without dividends. According to Parkiet (7 May 2024), since the end of 2004 the WIG20 has gained about 25% and the WIG20TR about 155%, which converts to about 1.2% versus about 5.0% a year (our own calculation from these values, about 19.4 years). Comparing with a price index therefore flatters a portfolio that collects dividends. In 2013–2022 the WIG20TR returned about −4%, the mWIG40TR +114% and the sWIG80TR +119%, so the bar is low. Harbor should not be judged by its return alone: its aim is smaller swings, so it is worth looking at the maximum drawdown as well, which the Portfolio tab shows. In a strong rally we expect it to lag.

## Data and known limitations

- We compute volatility from about a year of quotes (the whole history in the repository), so this rule has no backtest on GPW data.
- The universe is today's list of stocks, without delisted ones, so it is unsuitable for backtests without a survivorship-bias correction.
- There is no quality filter based on fundamental data (see above) and no valuation check: defensive stocks can be expensive.
- The portfolio may concentrate in defensive sectors, and the sector classification is rough, so the limit of 4 stocks per sector works only approximately.
- Some stocks have low liquidity, and a change of holdings means realising a gain and 19% tax outside an IKE or IKZE account.

## Role alongside swing

A defensive pillar and a candidate to replace cash in Compass when it shows risk-off. Such a variant needs a separate check and is not implemented today: in Compass, cash earns no interest.

## Rule change history

- 7 November 2026: first version of the rules. Before the first holdings (6 November 2026) the 30% drawdown filter was added (see Parameters).

## Sources

- [CXO Advisory: The Volatility Effect in Emerging Markets](https://www.cxoadvisory.com/?p=20977)
- [Falkenblog: Low volatility effect in emerging markets](https://falkenblog.blogspot.com/2012/05/low-volatility-effect-in-emerging.html)
- [Blitz, Pang, van Vliet (EconPapers)](https://econpapers.repec.org/RePEc:eee:ememar:v:16:y:2013:i:c:p:31-45)
- [Parkiet: Czemu wyniki WIG20 były w ostatnich latach tak słabe (in Polish)](https://www.parkiet.com/analizy-rynkowe/art38741821-czemu-wyniki-wig20-byly-w-ostatnich-latach-takie-slabe-3)
- [McLean, Pontiff: Does Academic Research Destroy Stock Return Predictability?](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

Screening exercise under the given framework, not investment advice.
