# Harbor — methodology

Harbor picks the calmest stocks.

## Rules

1. Annual volatility from daily returns over 252 sessions.
2. We take the lowest volatility quintile.
3. We drop stocks with a maximum drawdown above 30% over 252 sessions.
4. 16 stocks, at most 4 per sector.
5. Rebalanced quarterly: March, June, September, December.

## Data

Needs at least 253 sessions of history.

## Virtual portfolio

- Capital PLN 100,000, commission 0.2% per trade, start 6 Nov 2026, first orders at the open on 9 Nov 2026.
- Benchmark: WIG20 (price index).
- A simulation on raw GPW archive prices. Dividends are not yet added to the portfolio and tax is not included.
- Missing data is not an error: the strategy stays in cash and the Report tab shows what is missing ("waiting for data").
- A screening exercise, not investment advice.
