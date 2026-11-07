# Momentum — methodology

Momentum buys the stocks that rose the most over the past year, skipping the last month.

## Rules

1. 12-1 return: price change from 252 to 21 sessions ago.
2. Price must be above the SMA200.
3. The 12 highest scores, at most 3 per sector.
4. When Compass is in cash, new positions are half size.
5. Rebalanced monthly, at the open of the first session of the month.

## Data

Needs at least 253 sessions of history. Sectors come from the reports and the dividend assessment; a stock without a known sector is not grouped with others.

## Virtual portfolio

- Capital PLN 100,000, commission 0.2% per trade, start 6 Nov 2026, first orders at the open on 9 Nov 2026.
- Benchmark: WIG20 (price index).
- A simulation on raw GPW archive prices. Dividends are not yet added to the portfolio and tax is not included.
- Missing data is not an error: the strategy stays in cash and the Report tab shows what is missing ("waiting for data").
- A screening exercise, not investment advice.
