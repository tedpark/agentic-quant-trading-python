# Walk-Forward Validation Sample

This sample demonstrates leakage-aware financial ML validation with synthetic data only.
Each fold fits preprocessing on the training window, selects a threshold on validation,
and reports performance on the untouched test window.

## Protocol

- Time-ordered train / validation / test windows
- No random shuffle split
- Standardization fit on the training window only
- Threshold selection on validation only
- Test metrics reported after the selection step
- Synthetic feature and return series only

## Fold Results

| Fold | Train | Validation | Test | Train Mean | Threshold | Test Mean Return | Hit Rate | Turnover | Sharpe |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | 0-71 | 72-95 | 96-119 | -0.3374 | 0.50 | 0.00060 | 0.94 | 0.75 | 17.52 |
| 2 | 24-95 | 96-119 | 120-143 | -0.1701 | 0.25 | 0.00050 | 0.79 | 0.79 | 11.29 |
| 3 | 48-119 | 120-143 | 144-167 | -0.0355 | 0.50 | 0.00077 | 0.89 | 0.79 | 17.45 |
| 4 | 72-143 | 144-167 | 168-191 | 0.0985 | 0.25 | 0.00087 | 0.80 | 0.83 | 14.28 |

## Aggregate Test Metrics

- observations: 96
- mean return: 0.00069
- hit rate: 0.86
- turnover: 0.79
- Sharpe: 15.14

## Boundary

This is an educational validation pattern, not investment advice, a signal, or a live trading rule.
It intentionally avoids private universes, broker data, alpha features, and production thresholds.
