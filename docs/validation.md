# Validation Protocol

Financial ML validation must assume random train/test splits are unsafe.

## Rules

- Use time-ordered splits.
- Do not compute features with future information.
- Fit scalers/normalizers on training windows only.
- Evaluate with transaction costs where strategy examples are included.
- Record failure periods, not only average metrics.
- Keep public examples sample-only or synthetic.

## Walk-Forward Shape

```text
train window -> validation window -> test window
advance window -> repeat
aggregate metrics
```

## Runnable Sample

```bash
make walk-forward-demo
```

Output:

```text
docs/benchmarks/walk_forward_validation.md
```

The sample uses synthetic observations and keeps the protocol explicit:

- fit standardization on the training window only
- select thresholds on validation only
- evaluate the selected threshold on the untouched test window
- aggregate only test metrics across folds
- avoid private universes, broker data, alpha features, and production thresholds

## Purged + Embargoed Validation

```bash
make purged-embargo-demo
```

Output:

```text
docs/benchmarks/purged_embargo_validation.md
```

This sample focuses on label-overlap leakage:

- each sample has a forward-looking label interval
- train candidates whose label intervals overlap the held-out test label interval are purged
- samples immediately after the test block are embargoed
- all ranges are synthetic index ranges only

## HMM-Style Regime Features

```bash
make regime-feature-demo
```

Output:

```text
docs/benchmarks/hmm_regime_features.md
```

This sample focuses on leakage-aware feature engineering:

- rolling returns, realized volatility, drawdown, and momentum features are computed from available history
- feature standardization is fit on the training window only
- the Gaussian emission regime model is fit on the training window only
- low-vol / high-vol hidden states are decoded with Viterbi
- held-out test rows receive labels from the training-fitted model

## Mini Backtest Orchestration

```bash
make mini-backtest-demo
```

Output:

```text
docs/benchmarks/mini_backtest_orchestration.md
```

This sample connects the public building blocks into one experiment loop:

- rolling features are paired with next-period forward returns
- feature standardization and regime labels are fit on the training window only
- thresholds are selected on validation only
- test metrics are reported only after threshold selection
- transaction costs, CVaR-style tail risk, drawdown, and turnover are reported
- all data remains synthetic and strategy-agnostic

## Metrics

Recommended public metrics:

- hit rate
- turnover
- max drawdown
- Sharpe or Sortino for sample strategy examples
- tail-risk metric such as CVaR
- serving latency for production ML examples

## Leakage Checklist

- No future labels in features
- No global normalization before split
- No random shuffle split for time-series
- No post-hoc threshold selection on the test set
- No label interval overlap between train and held-out test labels
- No regime model fit using validation or test windows
- No validation threshold selection on the test window
- No private live strategy parameters in public docs
