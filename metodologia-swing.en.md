# Swing Methodology — how the monitor works

*A description for people who are just getting started. This page explains what the daily GPW swing scanner does, step by step and why. The detailed technical instructions (for the automation) are in the `METHOD.md` file in the repository. Whenever the way the morning report is prepared changes, this page is updated together with it.*

## Why all this

**Swing trading** means buying shares for a few days or weeks (our horizon is about 1 month) in order to catch a single upward "swing" in the price. It is not about hunting for companies that are cheap after a long decline. It is about the opposite: **a good company that is already rising, gets cheaper for a moment, and then moves up again**. Buying such a "pullback" in a strong trend is usually safer than trying to catch a falling knife.

Every morning before the Warsaw Stock Exchange (GPW) opens, the monitor goes through several dozen companies and picks those that best fit the pattern:

**good company + uptrend + healthy correction + clear support + fading supply + first signs of buyers returning + sensible reward-to-risk ratio**

This is a screening exercise based on fixed rules, **not investment advice**. A good company is not the same thing as a good moment to buy: many well-known companies are dropped because they are in the wrong place on the chart.

## What the monitor does — step by step

### 1. Checks whether the exchange is open today
GPW does not trade on weekends and public holidays (e.g. 1 and 11 November, 6 January, Easter). There is no report on those days. **Why:** data from a day without a session would add nothing.

### 2. Downloads the quotes
For each company in the universe it downloads about 50 recent sessions: the opening, highest, lowest and closing price, and the volume (the number of shares traded). The pre-market report is based on the **previous session's close**, because morning prices are not yet up to date. **Why:** everything that follows is math on these candles; if the data is old or incomplete, the report says so plainly.

### 3. Assesses the market as a whole (market regime)
Before it picks companies, it looks at the backdrop: the WIG20, WIG, mWIG40 and sWIG80 indices, market breadth (how many companies are in a trend), sectors, the US market (S&P 500, Nasdaq, the VIX fear index), bond yields, oil, copper, the zloty exchange rates and the calendar (Monetary Policy Council decisions, the Fed, inflation data). **Why:** even a great company can fall together with the market. When conditions are bad, the report says so plainly, reduces the number of candidates and suggests smaller positions or waiting.

### 4. Looks for companies in an uptrend
It uses moving averages, i.e. "the averaged price over the last N days": **EMA20** (about 1 month, reacts quickly) and **SMA50** (about 2.5 months). A good trend is one in which the price is above the averages and the shorter average lies above the longer one, along with higher highs and higher lows and outperformance of the WIG index (so-called relative strength). **Why:** statistically, it is easier to buy what is already rising than what is falling.

### 5. Looks for a healthy correction
It is interested in a pullback of about **5–20% from a recent high** that looks like normal profit-taking or a move of the whole market, rather than a collapse of the company. A good correction is orderly and the **volume shrinks** (there are fewer sellers). A bad correction is a decline on rising volume or after poor results. **Why:** a correction in a strong trend is an opportunity, while a broken trend is a risk.

### 6. Determines supports and the entry zone
**Support** is a price level at which a decline has stopped before (a moving average, a former resistance that has become a floor, a price gap). The monitor gives an **entry zone**, i.e. the range in which buying makes sense. **Why:** buying "wherever" gives a random result; buying at support gives a logical place for a protective order.

### 7. Looks for signs that buyers are returning (confirmation)
Merely touching support is not enough. The monitor checks, for example, a rejection candle (a long lower shadow), a higher low, a close above the previous day, a reclaim of the EMA20, an improvement in the MACD indicator, and **rising volume on the bounce**. On this basis it assigns a class:
- **A** — confirmation is already visible,
- **B** — the correction is attractive, but you need to wait for a signal (given in the report as the "trigger"),
- **C** — early and riskier.

### 8. Checks momentum (RSI and MACD)
**RSI** measures whether the latest move was "too fast". In a strong trend a healthy pullback often ends at an RSI of 40–50, not below 30. **MACD** shows whether momentum is increasing or fading. **Why:** it helps tell a slowdown from a change of direction.

### 9. Checks the fundamentals
Whether the company is growing and making money: revenue, profit, margins, debt, the latest quarterly results, and planned events (new contracts, dividends, share buybacks). Companies with a clearly worsened situation are dropped. **Why:** a chart without a business backdrop is easy to be fooled by.

### 10. Checks report and dividend dates
Quarterly results can move the price by a few to a dozen or so percent in a single day. Reports within **14 days** are marked in bold, and the levels are adjusted for dividends (after the ex-dividend day the price drops by the dividend amount). **Why:** this is a risk that does not show up on the chart.

### 11. Calculates risk and reward
For each candidate it gives:
- **Entry** — the buying zone,
- **Stop** — the level whose break means the thesis is no longer true and the position is closed,
- **T1 and T2** — two profit targets (e.g. the previous high and its extension),
- **R** — the ratio of potential reward to risk (e.g. "1.9 / 3.1" means: to the first target you earn 1.9 times what you risk; to the second, 3.1 times).

Stops must follow from the chart and not be artificially tight. We look for R of about 2 and up. **Why:** even if half of your trades are losers, a positive reward-to-risk ratio can still produce a profit.

### 12. Awards points (0–100)
Each company gets a total: fundamentals 20, long-term trend 15, correction quality 15, support quality 10, relative strength 10, momentum and confirmation 10, volume 5, sector 5, catalysts 5, risk/reward 5. The table shows three numbers: **Fund/30** (fundamentals + sector + catalysts), **Tech/70** (the chart) and **Total**. **Why:** points let you rank the candidates and compare them quickly, but they do not replace reading the rationale.

### 13. Rejects what does not fit
Companies in a long decline, after a trend breakdown, without a correction (too overbought), illiquid, or with a damaged thesis go to the "Rejected" section together with the reason. **Why:** knowing what not to buy is just as important as the list of candidates.

### 14. Reviews the previous report
It checks what happened to the previous suggestions: whether the entry zone was touched, whether the trigger fired, whether the price reached the target or the stop. **Why:** an honest review shows what really works.

### 15. Publishes the report
A report file is created, the page is generated and goes to romangpw.pl. The report has a fixed order of sections: market regime, ranking (10–15 companies), TOP 3, detailed analysis of the TOP 5, watchlist for 1–3 weeks, rejected, review, method and disclaimers.

## How to read the report

- **Price** — the latest close; where there is a date in brackets (e.g. "3.11"), the data is older than the rest.
- **From 50-session high** — by what percentage the price is below the high of the last 50 sessions. 0% means there is no correction, just a peak.
- **Trend, Support, RSI** — a short description of the trend, the support level and the RSI value.
- **Class** — A, B or C (see step 7).
- **Entry / Stop / T1 / T2 / R** — the trade plan (step 11). R is calculated from the middle of the entry zone.
- **Verdicts** in the TOP 5 analysis: STRONG BUY SETUP, GOOD SETUP, WATCH, WAIT FOR CONFIRMATION, AVOID. They refer solely to how attractive the setup is according to this method.
- **Watchlist** — companies that are not ready yet, with the exact technical condition that would make them interesting.

## Limitations worth knowing about

- The data comes from public sources (including biznesradar.pl, bankier.pl, and services with company announcements). It is sometimes delayed, incomplete or contains errors. The report notes when something could not be verified.
- For GPW companies, the SMA100 and SMA200 averages are not available in free sources, so they are not provided.
- Prices, indicators and report dates are not made up. If something is missing, the report says so plainly and does not guess.
- The method does not know the future. A stop-loss and a small position limit the risk, but they do not eliminate it.

**A screening exercise based on a given framework, not investment advice.**
