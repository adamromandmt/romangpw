# Compass — methodology

Compass picks one of three GPW indices, or cash.

## Rules

1. We compare WIG20, mWIG40 and sWIG80.
2. For each we take the average of the 6-month and 12-month returns (on month-end closes).
3. We choose the index with the highest average.
4. We hold it only if its price is above the average of the last 10 month-end closes. Otherwise the portfolio is in cash.
5. One decision a month, executed at the open of the first session of the month.

## Deviations from the textbook version

- Price indices instead of total return (TR).
- Cash earns no interest.
- Execution at the open, with no index-tracking costs (the position is held in index units).

## Data

Needs `data/market/_WIG20.csv`, `_MWIG40.csv`, `_SWIG80.csv` and at least 13 month-end closes.

## Virtual portfolio

- Capital PLN 100,000, commission 0.2% per trade, start 6 Nov 2026, first orders at the open on 9 Nov 2026.
- Benchmark: WIG20 (price index).
- A simulation on raw GPW archive prices. Dividends are not yet added to the portfolio and tax is not included.
- Missing data is not an error: the strategy stays in cash and the Report tab shows what is missing ("waiting for data").
- A screening exercise, not investment advice.
