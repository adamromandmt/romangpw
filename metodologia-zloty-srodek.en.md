# Golden Mean — methodology

Golden Mean looks for cheap stocks with sound fundamentals.

## Filters

- Piotroski F-score of at least 7.
- Positive free cash flow (FCF).
- Net debt / EBITDA of at most 3.
- No banks or insurers.

## Ranking and holdings

- The ranking combines EV/EBIT (lower is better) and gross profit / assets (higher is better).
- 20 stocks, no more than 8 from energy and fuels.
- Rebalanced in May and October.

## Data

The strategy reads `data/fundamentals.csv` (columns: tic, sector, f_score, fcf, net_debt_ebitda, ev_ebit, gross_profit_assets, is_financial, is_energy). While the file holds only a header, the portfolio stays in cash.

## Virtual portfolio

- Capital PLN 100,000, commission 0.2% per trade, start 6 Nov 2026, first orders at the open on 9 Nov 2026.
- Benchmark: WIG20 (price index).
- A simulation on raw GPW archive prices. Dividends are not yet added to the portfolio and tax is not included.
- Missing data is not an error: the strategy stays in cash and the Report tab shows what is missing ("waiting for data").
- A screening exercise, not investment advice.
