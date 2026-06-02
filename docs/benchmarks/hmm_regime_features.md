# HMM-Style Regime Feature Pipeline Sample

This sample demonstrates a leakage-aware feature pipeline for financial ML with synthetic data only.
Each fold builds rolling features, fits a small Gaussian HMM-style regime model on the training window,
and applies the fitted regime model to the held-out test window.

## Protocol

- Synthetic close-price series only
- Rolling returns, realized volatility, drawdown, and momentum features
- Feature standardizer fit on the training window only
- Gaussian emission regime model fit on the training window only
- Viterbi decoding for low-vol / high-vol hidden regime labels
- Test rows receive regime labels from the training-fitted model

## Fold Summary

| Fold | Train | Test | Train Regimes | Test Regimes | Train Mean Return | Train Mean Vol |
|---:|---|---|---|---|---:|---:|
| 1 | 10-89 | 110-129 | high_vol: 33, low_vol: 47 | high_vol: 20 | 0.00017 | 0.00416 |
| 2 | 30-109 | 130-149 | high_vol: 53, low_vol: 27 | low_vol: 20 | -0.00003 | 0.00535 |
| 3 | 50-129 | 150-169 | high_vol: 52, low_vol: 28 | high_vol: 5, low_vol: 15 | -0.00009 | 0.00586 |
| 4 | 70-149 | 170-189 | high_vol: 39, low_vol: 41 | high_vol: 20 | 0.00013 | 0.00554 |
| 5 | 90-169 | 190-209 | high_vol: 24, low_vol: 56 | high_vol: 20 | 0.00034 | 0.00482 |
| 6 | 110-189 | 210-229 | high_vol: 25, low_vol: 55 | high_vol: 10, low_vol: 10 | 0.00028 | 0.00535 |

## Sample Test Rows

| Fold | Timestamp | Regime | Return | Realized Vol | Drawdown | Momentum 5 |
|---:|---:|---|---:|---:|---:|---:|
| 1 | 110 | high_vol | -0.00188 | 0.00629 | -0.02992 | -0.00614 |
| 1 | 111 | high_vol | -0.00515 | 0.00629 | -0.03492 | -0.00752 |
| 1 | 112 | high_vol | 0.00412 | 0.00645 | -0.03094 | 0.00696 |
| 2 | 130 | low_vol | -0.00461 | 0.00350 | -0.02740 | -0.00289 |
| 2 | 131 | low_vol | 0.00466 | 0.00376 | -0.02286 | 0.00584 |
| 2 | 132 | low_vol | 0.00139 | 0.00350 | -0.02151 | 0.00202 |

## What This Proves

The artifact shows how regime labels can be generated inside a time-ordered ML pipeline without using future test information.
It is intentionally small, deterministic, and easy to inspect.

## Boundary

This is an educational feature-engineering pattern, not investment advice, a trading signal, or a live trading rule.
It intentionally avoids private universes, broker data, alpha features, and production thresholds.
