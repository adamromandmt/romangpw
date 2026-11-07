# Drift — methodology

Drift trades the gap up after a quarterly report.

## Rules

1. Report window: the publication day and the next 3 sessions.
2. Signal: an open at least 2% above the previous close on volume at least 2.5 times the 20-session average.
3. Buy at the next session's open, a position of 5% of capital, at most 20 positions.
4. Stop: the close before the gap. Exit after 40 sessions.
5. A gap down on the same volume inside a report window puts the stock on a "do not buy" list for 60 sessions.

## Data

Report dates come from the swing reports (`reports/*.json`) and an optional `data/earnings.csv` (columns tic, date). Coverage is incomplete, so some stocks have no window yet.

## Virtual portfolio

- Capital PLN 100,000, commission 0.2% per trade, start 6 Nov 2026, first orders at the open on 9 Nov 2026.
- Benchmark: WIG20 (price index).
- A simulation on raw GPW archive prices. Dividends are not yet added to the portfolio and tax is not included.
- Missing data is not an error: the strategy stays in cash and the Report tab shows what is missing ("waiting for data").
- A screening exercise, not investment advice.
