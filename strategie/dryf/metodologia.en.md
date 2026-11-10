# Drift — methodology

Drift catches, in reporting seasons, stocks that open with a clear gap up on heavy volume, and holds them for up to 40 sessions. It is an approximation of post-earnings-announcement drift (PEAD) computed from prices and volume, because we do not use data on results, consensus or company filings.

This page describes the strategy itself. How the virtual portfolio works (capital, costs, order timing) is explained on the Portfolio tab; it is only a forward check of the forecasts from the start date.

## Hypothesis

Prices drift in the direction of the earnings surprise for weeks, even months, after the announcement (Ball and Brown 1968, Bernard and Thomas 1989). If the market reacts to good results gradually, buying after the first reaction can still earn something. For the GPW the evidence is **mixed**, and the samples are small.

## Rules

1. **Scan windows.** We look for events only in the windows when reports are published: 1 February – 30 April, 1–20 May, 15 August – 30 September and 1–20 November. Without ESPI data we treat a move in these windows as a proxy for the reaction to results. Outside the windows we do not look for new events, but open positions are still managed.
2. **Positive event** (day E): a stock with a 60-session median daily turnover of at least PLN 1m whose opening gap versus the previous close is at least +2% (adjusted for the ex-dividend date), whose day gain (price adjusted for dividends) is between +4% and +30%, whose volume is at least 2.5 times the median of the previous 20 sessions, and whose close is in the upper half of the day's range. We reject moves above 30% as possible share consolidations. The previous session must have a quote.
3. **Negative event.** The mirror image: a gap of at least −2%, a day drop from −4% to −30%, the same volume and turnover thresholds, a close in the lower half of the day's range. A stock with a negative event goes on a "do not buy" list for 60 sessions. The list is information for your own decisions; the swing scanner does not use it automatically.
4. **Entry.** Buy at the open of the session after a positive event, for a fixed PLN 10,000 per stock, at most 10 positions at a time. The order is cancelled if the open is at or below the stop.
5. **Stop.** The close of the day before the event (that is, the gap being filled). The stop works intraday: if the price touches that level, we exit at the stop price, and if the session opens below it, at the opening price.
6. **Time exit.** After 40 sessions, at the close.
7. **Timing.** A scan after every session.

## Parameters

All thresholds (gap 2%, gain 4%, volume 2.5 times, turnover PLN 1m, the windows, 40 sessions, PLN 10,000 per position, 10 positions) are starting values, not research results or optimisation. The study on which we based the strategy assumed holding for 40–60 sessions and entering on a surprise in the top quintile; we chose 40 sessions and a price-and-volume event.

We set the thresholds by the number of events, not by how prices behaved after them. In our quote history (from 23 October 2025 to 6 November 2026) these conditions were met by 35 positive events (20 inside the reporting windows) and 20 negative ones (10 inside the windows).

## Evidence and its limits

- **Sojka** (Bank i Kredyt 52(2), 2021; data 2004–2018): a PEAD-based strategy returned on average 5.4% on the Polish market within 90 days of forming the portfolio. We cite the abstract; the full text of the working version (SSRN) could not be downloaded.
- **Jagliński** (Financial Sciences 2020; events from 2017–2019; the surprise measured against analysts' forecasts, whereas the earlier Sojka study used autoregressive models): no PEAD for stocks above expectations, drift only in the group below expectations. The author links this to limited availability of short selling in Poland.
- **Szyszka** (2001), according to a search-engine snippet: the clearest result is a significant negative drift after clearly disappointing results.
- **Conclusion:** the best documented effect on the GPW is the negative surprise, hence the "do not buy" list. The long side is supported by Sojka but not by Jagliński, so the result depends on the surprise measure and the period.
- **Haircut:** McLean and Pontiff (97 predictors, 80 publications): out of sample, before publication, returns were 26% lower, and after publication 58% lower. We assume the real edge is at most half of that in a backtest.

Our study also describes reinforcements that this version does not have: a surprise computed from financial data or consensus, insider purchases (MAR notifications) and announcements of share buybacks. We have no data for them.

## Example of an event (an illustration, not proof)

LPP, 18 September 2026 (inside a reporting window): previous close PLN 22,380, open PLN 23,200 (gap +3.7%), close PLN 24,160 (+8.0%), volume 10.0 times the median of the previous 20 sessions, a close in the upper part of the day's range. All conditions of a positive event were met. The highest close after the event (PLN 28,080, 5 November 2026) was about 16% above the close on the day of the event, and the latest (PLN 27,480, 6 November 2026) about 14% above it.

This is a single example that we knew from earlier scans, not a representative sample: it shows what an event looks like, not that the strategy works. With a fixed PLN 10,000 per position, stocks priced above that amount, like LPP, cannot be bought at all.

## Benchmark

We compare the portfolio with the WIG20, but the WIG20 is a price index, without dividends. According to Parkiet (7 May 2024), since the end of 2004 the WIG20 has gained about 25% and the WIG20TR about 155%, which converts to about 1.2% versus about 5.0% a year (our own calculation from these values, about 19.4 years). In 2013–2022 the WIG20TR returned about −4%, the mWIG40TR +114% and the sWIG80TR +119%, so the bar is low. Drift holds cash until events appear, so the comparison with the WIG20 has to be read with regard to how much of the capital is invested (see the Portfolio tab).

## Data and known limitations

- A price-and-volume event is not the same as a surprise in results: a move inside a reporting window may have another cause, and companies publish reports on different days, including outside our windows.
- The information may already be priced in on the day of the report, and we buy only after the gap. Price gaps and liquidity increase the risk of slippage.
- The samples are small and the research results contradict each other (Sojka and Jagliński). We have about a year of quote history, so there is no backtest.
- The universe is today's list of stocks, without delisted ones (survivorship bias).
- Frequent trading in an ordinary account means 19% tax on every realised gain, which eats the edge; IKE and IKZE accounts would suit it better.

## Role alongside swing

Complementary in the calendar: the swing scanner treats a report within the next 14 days as a risk, while Drift trades right after a report. It also extends the event-driven approach from dividends alone to results.

## Rule change history

- 7 November 2026: first version of the rules and the first scan (6 November 2026).
- 7 November 2026 (review before the first trade): rules unchanged; we clarified that the amount per position is fixed (PLN 10,000, i.e. 10% of the starting capital) and does not grow or shrink with the portfolio value.

## Sources

- [Sojka: PEAD na polskim rynku akcji, Bank i Kredyt 2021 (in Polish)](https://bankandcredit.nbp.pl/content/2021/02/BIK_02_2021_03.pdf)
- [Jagliński: The Impact of Quarterly Earnings Announcements on Stock Prices](https://journals.ue.wroc.pl/fins/article/view/233)
- [Szyszka (2001), SSRN](https://ssrn.com/abstract=295299)
- [Parkiet: Czemu wyniki WIG20 były w ostatnich latach tak słabe (in Polish)](https://www.parkiet.com/analizy-rynkowe/art38741821-czemu-wyniki-wig20-byly-w-ostatnich-latach-takie-slabe-3)
- [McLean, Pontiff: Does Academic Research Destroy Stock Return Predictability?](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)

Screening exercise under the given framework, not investment advice.
