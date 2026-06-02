# Monitoring

## Goal

Show a public, strategy-safe pattern for feature drift monitoring.

This module uses synthetic feature distributions only. It does not expose a live trading universe, broker data, strategy thresholds, or private alpha research.

## Metrics

- PSI: population stability index over reference quantile buckets
- KS: two-sample empirical CDF distance
- Severity: `ok`, `moderate`, or `significant`

## Demo

```bash
make drift-demo
```

Output:

```text
docs/benchmarks/drift_report.md
```

## Implementation

- `src/agentic_quant/monitoring/drift.py`
- `src/agentic_quant/monitoring/demo_drift_report.py`
- `tests/test_drift_monitoring.py`

## Boundary

This is an engineering example for production ML monitoring. It is not investment advice, a signal, or a live trading rule.
