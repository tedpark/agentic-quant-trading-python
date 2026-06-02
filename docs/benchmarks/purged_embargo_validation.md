# Purged + Embargoed Validation Sample

This sample demonstrates label-overlap leakage control with synthetic index ranges only.
Each sample has a forward-looking label interval. Training samples whose labels overlap
the held-out test label interval are purged, and samples immediately after the test block
are embargoed.

## Protocol

- data length: 101
- label horizon: 5
- blocked test size: 12
- embargo size: 3
- no private universe, broker data, alpha features, or production thresholds

## Fold Results

| Fold | Test Samples | Test Label Span | Train Count | Purged | Embargoed |
|---:|---|---|---:|---:|---:|
| 1 | 0-11 | 0-15 | 78 | 4 | 3 |
| 2 | 12-23 | 12-27 | 74 | 8 | 3 |
| 3 | 24-35 | 24-39 | 74 | 8 | 3 |
| 4 | 36-47 | 36-51 | 74 | 8 | 3 |
| 5 | 48-59 | 48-63 | 74 | 8 | 3 |
| 6 | 60-71 | 60-75 | 74 | 8 | 3 |
| 7 | 72-83 | 72-87 | 74 | 8 | 3 |
| 8 | 84-95 | 84-99 | 80 | 5 | 0 |

## What Gets Removed

- Purged samples: training candidates whose forward-looking labels overlap the test label span.
- Embargoed samples: training candidates immediately after the test block, held out to reduce temporal bleed.

## Boundary

This is an educational validation pattern, not investment advice, a signal, or a live trading rule.
