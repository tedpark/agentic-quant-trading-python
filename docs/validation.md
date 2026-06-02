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
- No private live strategy parameters in public docs
