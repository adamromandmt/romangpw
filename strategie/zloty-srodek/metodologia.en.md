# Golden Mean — methodology

Golden Mean looks for good companies at a sensible price. Twice a year it picks 20 non-financial stocks that combine high quality (the Piotroski score, gross profitability to assets) with a low EV/EBIT valuation. It is a slow core holding with a different source of return than swing: it is meant to earn from earnings growth and re-rating of companies, not from price pullbacks.

This page describes the strategy itself. How the virtual portfolio works (capital, costs, order timing) is explained on the Portfolio tab; it is only a forward check of the forecasts from the start date.

## Hypothesis

Gross profitability (gross profit to assets) predicts returns about as well as classic valuation ratios, and it is strongly negatively correlated with them, so combining the two signals improves the result relative to value alone (Novy-Marx). Simple tests of profitability, leverage and efficiency (the Piotroski F-score) help weed out stocks that are cheap because their condition is deteriorating. A similar combination of quality and price lies behind Greenblatt's Magic Formula and the "quality minus junk" factor (Asness, Frazzini and Pedersen). On the GPW we add a limit on political risk: a cap on stocks from regulation-sensitive sectors.

## Rules

1. **Data.** Annual financial statements of non-financial companies, collected separately from public annual reports. A statement counts only from its publication date (when there is no date: period end plus 120 days), so that we do not look ahead. Until the statements are collected, the strategy names no stocks and the virtual portfolio stays in cash.
2. **Universe.** Stocks from our watch list of GPW companies other than banks and financial companies that meet these conditions on the signal date: the latest quote is no older than 10 days; at least 12 months of history; a 60-session median daily turnover of at least PLN 0.3m; candles in at least 90% of the last 120 sessions; no daily price change above 30% in the last ~260 quotes. Statements for two consecutive years are required. Banks and insurers need different measures (P/B, ROE, capital buffers) and are outside the scope of this version.
3. **Indicators.** For each stock we compute the F-score (a simplified Piotroski), free cash flow, net debt to EBITDA, EV/EBIT and gross profitability to assets. The definitions are in the "Indicators" section below.
4. **Entry thresholds** (for stocks outside the portfolio): an F-score of at least 7, positive FCF, net debt to EBITDA up to 3.
5. **Ranking.** The sum of the positions in the EV/EBIT ranking (the cheaper the better) and in the gross profitability ranking (the higher the better); a lower sum means a higher place. Ties are broken by the higher F-score, then by the lower EV/EBIT.
6. **Holdings.** 20 stocks in equal weights. A stock already in the portfolio stays as long as it has an F-score of at least 5, net debt to EBITDA up to 4 and a place in the top 30 of the ranking. At most 4 stocks from one sector (a simplified in-house classification; the "other" sector has no limit) and 8 in total from regulation-sensitive sectors (power utilities, fuels), which is 40% of the portfolio.
7. **Timing.** We compute the signal on data from the last session of May and October, and the report comes out after the first session of the next month. The first signal was made on 6 November 2026, outside the cycle.

## Indicators

- **F-score** (a simplified Piotroski version, 9 tests of 1 point each): positive ROA; positive operating cash flow; ROA up year on year; operating cash flow to assets higher than ROA; debt to assets not up; current ratio up; share count up by no more than 0.5%; gross margin up; asset turnover up.
- **Free cash flow** (FCF): operating cash flow minus capital expenditure.
- **Net debt to EBITDA**: debt minus cash, divided by EBITDA. A company with net cash scores 0, and a company with net debt and non-positive EBITDA fails.
- **EV/EBIT**: enterprise value (market capitalisation at the latest closing price plus net debt) to EBIT. It requires positive EBIT, positive EV and positive equity.
- **Gross profitability**: gross profit to assets.

## Parameters

The F-score thresholds (7 at entry, 5 to hold), net debt to EBITDA (3 and 4), the count of 20 stocks, the place 30 in the hysteresis, the limits of 4 and 8, and the PLN 0.3m turnover threshold are starting values from our study, not research results or optimisation on GPW data. Instead of the full Magic Formula (return on capital) we used Novy-Marx's gross profitability to assets. We did not test other weights between valuation and quality: the two rankings count equally.

## Evidence and its limits

- **Novy-Marx** (US data): gross profitability predicts returns about as well as classic valuation ratios and is strongly negatively correlated with them (the correlation of the returns of a long/short strategy with book-to-price: −0.71 for large and −0.24 for small stocks). Combining the two signals clearly improves the result relative to value alone: for large stocks about 3.1% a year above the benchmark net (information ratio 0.66), and for the Magic Formula about 1.9% (information ratio 0.37).
- **Quality minus junk** (CXO Advisory on the work of Asness, Frazzini and Pedersen): 24 developed markets; in the global sample (June 1989 – December 2016) on average 0.36% a month gross; positive in 21 of 24 countries, and a positive four-factor alpha in 23 of 24. Results are gross, without short-selling costs; the CXO summary has no result for the GPW alone.
- **GPW:** Zaremba and Konieczka (all GPW stocks, 2001–2013): the value premium appears partially, but vanishes once transaction costs and liquidity are taken into account. According to an abstract that we did not re-check, Pilch (2021) confirmed the F-score on the GPW for the IT and gaming industries in 2017–2019, on a narrow sample.
- **Political risk:** Parkiet points to it as one cause of the weak WIG20TR results, and the financial sector makes up more than 40% of that index. The cap on stocks from regulation-sensitive sectors is only partial protection.
- **Haircut:** McLean and Pontiff (97 predictors, 80 publications): out of sample, before publication, returns were 26% lower, and after publication 58% lower. We assume the real edge is at most half of that in a backtest.

## Benchmark

We compare the portfolio with the WIG20, but the WIG20 is a price index, without dividends. According to Parkiet (7 May 2024), since the end of 2004 the WIG20 has gained about 25% and the WIG20TR about 155%, which converts to about 1.2% versus about 5.0% a year (our own calculation from these values, about 19.4 years). Comparing with a price index therefore flatters a portfolio that collects dividends. In 2013–2022 the WIG20TR returned about −4%, the mWIG40TR +114% and the sWIG80TR +119%, so the bar is low. Golden Mean excludes banks and financial companies, which according to Parkiet make up more than 40% of the WIG20, so its result against the WIG20 also depends on how the financial sector fared.

## Data and known limitations

- This is the hardest of the five strategies to automate: it needs fundamental data that is entered separately and must be checked by hand.
- The input data are annual statements. The October signal therefore mainly refreshes the valuation (the price), not the quality; half-year results do not enter the assessment.
- Cheap stocks are often cheap for political or regulatory reasons (value traps).
- The shareholder-yield bonus (dividends and buybacks) described in our study is not in the ranking; the dividend over the last 12 months appears in the report as information only.
- A rare rebalance (twice a year) means a long time in a bad regime. We have about a year of quote history, so this rule has no backtest on GPW data.
- The universe is today's list of stocks, without delisted ones (survivorship bias), and the sector classification is rough.
- A change of holdings means realising a gain and 19% tax outside an IKE or IKZE account.

## Role alongside swing

A slow core with decisions twice a year. The source of return (re-rating and earnings growth) differs from swing, so the correlation should be lower; this needs checking.

## Rule change history

- 7 November 2026: first version of the rules and the first signal (6 November 2026).
- 7 November 2026 (review before the first trade): the leverage test in the F-score (debt to assets did not rise year on year) now also passes companies whose debt ratio is unchanged, including debt-free ones. Previously it required a decrease, so a debt-free company lost a point.

## Sources

- [Novy-Marx: The Other Side of Value](https://www.ivey.uwo.ca/media/3775548/novy-marx.pdf)
- [CXO Advisory: Quality Minus Junk](https://www.cxoadvisory.com/fundamental-valuation/stock-quality-and-future-returns/)
- [Zaremba, Konieczka (FIQF 2017)](https://reference-global.com/article/10.1515/fiqf-2016-0119)
- [Pilch: F-score on the GPW (abstract, not re-checked)](https://journals.umcs.pl/h/article/view/11872)
- [Parkiet: Czemu wyniki WIG20 były w ostatnich latach tak słabe (in Polish)](https://www.parkiet.com/analizy-rynkowe/art38741821-czemu-wyniki-wig20-byly-w-ostatnich-latach-takie-slabe-3)
- [McLean, Pontiff: Does Academic Research Destroy Stock Return Predictability?](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

Screening exercise under the given framework, not investment advice.
