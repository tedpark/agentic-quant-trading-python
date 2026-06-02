# Experiment Manifest / Run Log

This document records a reproducible public run log for the mini backtest orchestration sample.
It is intentionally small and synthetic, but it shows the experiment metadata that should be captured before comparing model or strategy variants.

## Run Summary

- run id: `d0425f9b937b`
- experiment: `mini-backtest-orchestration`
- data source: `synthetic_market_bars`
- folds: 5
- test observations: 120
- mean test return: 0.000242
- mean test CVaR: -0.002081
- mean test Sharpe: 1.737048

## Parameters

| Parameter | Value |
|---|---:|
| `synthetic_bars` | `260` |
| `train_size` | `90` |
| `validation_size` | `24` |
| `test_size` | `24` |
| `step_size` | `24` |
| `thresholds` | `0.0,0.4,0.8,1.2` |
| `transaction_cost` | `0.0004` |

## Validation Protocol

- time-ordered train / validation / test windows
- feature standardization fit on the training window only
- HMM-style regime model fit on the training window only
- threshold selected on validation rows only
- test metrics reported only after threshold selection

## Artifacts

| Artifact | Path |
|---|---|
| `orchestration_report` | `docs/benchmarks/mini_backtest_orchestration.md` |
| `manifest_report` | `docs/benchmarks/experiment_manifest.md` |

## Public Boundary

- synthetic data only
- no private trading universe
- no broker data or account data
- no live execution logic
- no production thresholds or private alpha features

## JSON Snapshot

```json
{
  "artifacts": {
    "manifest_report": "docs/benchmarks/experiment_manifest.md",
    "orchestration_report": "docs/benchmarks/mini_backtest_orchestration.md"
  },
  "data_source": "synthetic_market_bars",
  "fold_count": 5,
  "mean_test_cvar": -0.002081,
  "mean_test_return": 0.000242,
  "mean_test_sharpe": 1.737048,
  "name": "mini-backtest-orchestration",
  "parameters": {
    "step_size": 24,
    "synthetic_bars": 260,
    "test_size": 24,
    "thresholds": "0.0,0.4,0.8,1.2",
    "train_size": 90,
    "transaction_cost": 0.0004,
    "validation_size": 24
  },
  "public_boundary": [
    "synthetic data only",
    "no private trading universe",
    "no broker data or account data",
    "no live execution logic",
    "no production thresholds or private alpha features"
  ],
  "run_id": "d0425f9b937b",
  "test_observations": 120,
  "validation_protocol": [
    "time-ordered train / validation / test windows",
    "feature standardization fit on the training window only",
    "HMM-style regime model fit on the training window only",
    "threshold selected on validation rows only",
    "test metrics reported only after threshold selection"
  ]
}
```
