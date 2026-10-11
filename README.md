# data-gap-ranker

Which single missing SDG series would unlock the most country comparisons? This tool ranks
missing series by what they would unlock, not by raw missing counts.

**Not an official UN product.** No endorsement by the United Nations or WHO is implied.
Data: UN Statistics Division, SDG Global Database (https://unstats.un.org/sdgapi). See `DATA.md`.

## How it works
- Fetches SDG 3 metadata and observation data into a local cache, with a query ledger
  (URL, params, time, SHA-256). CI never calls a live API.
- Builds a three-state matrix per country x series-slice x year (2015-2024):
  `PRESENT` (the `Nature` flag is kept: reported / estimated / modelled), `MISSING`, `NOT_APPLICABLE`.
- A comparison is a pair of countries over a bundle of slices, comparable only when every
  required slice has a value for both. For each slice it reports three separate numbers:
  `unlocks_now` (the only missing input), `rows_blocked` (among the missing), `raw_missing`.
  A greedy order recomputes marginal gain after each pick.
- `NOT_APPLICABLE` is never inferred: only from cited rules in `rules/` (v1: WHO malaria-free
  certification). The API gives no such signal. See `rules/README.md`.

## Usage
```
uv sync
uv run gapranker fetch --commit        # metadata snapshot (dry-run without --commit)
uv run gapranker fetch-data --commit   # SDG 3 series (~280 requests, ~190 MB)
uv run gapranker catalog-check         # gate: 0 pass / 1 blocked / 2 could not evaluate
uv run gapranker rank --rules          # example 7-slice bundle; use --slice to choose
```
Check the data owner's terms before downloading; the downloaded data is not redistributed here.

## Limits
- Obtaining a slice is assumed to fill it for every country: an upper bound, not a forecast.
- The universe is the areas with any SDG 3 data in the window; territories use the source's labels.
- The example bundle is illustrative, not a composite index. No countries are ranked.
- Status: R2 complete (matrix, ranking, rules). HTML report with citations is next.
