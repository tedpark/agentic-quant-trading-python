# Mini Backtest Orchestration Sample

This sample wires the public financial ML building blocks into one leakage-aware experiment loop.
It uses synthetic data only and does not publish a trading signal.

## Pipeline

```text
synthetic prices -> rolling features -> train-fitted regime labels -> validation threshold selection -> test simulation -> CVaR metrics
```

## Protocol

- Synthetic close-price series only
- Rolling feature rows are paired with the next-period forward return
- Feature standardization is fit on the training window only
- HMM-style Gaussian regime labels are fit on the training window only
- Thresholds are selected on validation rows only
- Test metrics are reported after the selection step
- CVaR-style risk multipliers reduce exposure in unfavorable tail-risk states

## Fold Results

| Fold | Train | Validation | Test | Threshold | Test Mean | Hit Rate | Turnover | CVaR | Max DD | Sharpe |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10-99 | 100-123 | 124-147 | 1.20 | 0.00009 | 1.00 | 0.04 | 0.00000 | 0.00000 | 3.31 |
| 2 | 34-123 | 124-147 | 148-171 | 1.20 | 0.00002 | 0.40 | 0.21 | -0.00110 | -0.00372 | 0.28 |
| 3 | 58-147 | 148-171 | 172-195 | 0.80 | 0.00044 | 0.46 | 0.54 | -0.00245 | -0.00420 | 2.58 |
| 4 | 82-171 | 172-195 | 196-219 | 0.00 | 0.00096 | 0.52 | 0.96 | -0.00293 | -0.00814 | 4.39 |
| 5 | 106-195 | 196-219 | 220-243 | 0.00 | -0.00029 | 0.50 | 1.00 | -0.00393 | -0.01607 | -1.88 |

## Sample Test Rows

| Fold | Timestamp | Regime | Z Momentum | Z Volatility | Drawdown | Forward Return |
|---:|---:|---|---:|---:|---:|---:|
| 1 | 124 | low_vol | 0.848 | -0.287 | -0.02381 | -0.00079 |
| 1 | 125 | low_vol | 0.388 | -0.555 | -0.02458 | -0.00406 |
| 1 | 126 | low_vol | -0.071 | -0.430 | -0.02854 | 0.00521 |
| 2 | 148 | low_vol | 0.456 | -1.056 | -0.01797 | -0.00406 |
| 2 | 149 | low_vol | 0.019 | -0.917 | -0.02196 | 0.00521 |
| 2 | 150 | low_vol | 1.017 | -0.793 | -0.01687 | 0.00194 |

## What This Proves

This artifact shows the shape of an inspectable financial ML experiment loop.
It connects feature engineering, regime labels, validation, a toy decision rule, transaction costs, and CVaR-style risk controls without using private strategy details.

## Boundary

This is an educational orchestration pattern, not investment advice, a trading signal, or a live trading rule.
It intentionally avoids private universes, broker data, alpha features, production thresholds, live execution, and account data.
