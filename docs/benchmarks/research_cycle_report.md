# QuantSigma Lab Agent Research Cycle

This report demonstrates a safe tool-calling research operator.
The agent does not execute arbitrary shell commands or live trading.
It calls allowlisted research tools, runs the trading-system backtest sample,
builds a manifest, and applies the promotion gate.

## Decision

- run id: `9ff3bb850f5f`
- strategy: `pair_mean_reversion_regime_filter`
- promotion decision: `review_required`
- live trading allowed: `False`

## Tool Calls

| Tool | Status | Summary |
|---|---|---|
| `plan_experiment` | `ok` | created leakage-aware experiment plan |
| `build_experiment_config` | `ok` | created safe synthetic-data config |
| `run_mini_backtest` | `ok` | ran walk-forward mini backtest |
| `build_manifest` | `ok` | built experiment manifest |
| `audit_experiment` | `ok` | applied promotion gate |
| `write_report` | `ok` | rendered cycle report |

## Experiment Config

```json
{
  "allow_live_trading": false,
  "data_source": "synthetic_market_bars",
  "idea": "HMM sideways regime improves mean-reversion entries for cointegrated pairs",
  "run_id": "9ff3bb850f5f",
  "step_size": 24,
  "strategy_name": "pair_mean_reversion_regime_filter",
  "test_size": 24,
  "thresholds": [
    0.0,
    0.4,
    0.8,
    1.2
  ],
  "train_size": 90,
  "transaction_cost": 0.0004,
  "validation_size": 24
}
```

# Hypothesis-to-Experiment Plan

- run id: `9ff3bb850f5f`
- hypothesis: If HMM sideways regime improves mean-reversion entries for cointegrated pairs, then it should improve out-of-sample risk-adjusted performance under leakage-aware validation.

## Feature Candidates

- rolling return / volatility features
- z-score velocity and acceleration
- spread mean-reversion strength
- HMM-style regime label
- regime transition probability
- regime-specific volatility
- cointegration residual
- spread half-life
- rolling correlation stability

## Validation Protocol

- Use walk-forward train / validation / test windows.
- Fit scalers, regime models, and feature transforms on training windows only.
- Use purging and embargo when labels overlap adjacent windows.
- Select thresholds on validation windows and report untouched test-window metrics.

## Risk Checks

- Report CVaR / Expected Shortfall, not only average return.
- Compare drawdown and turnover under transaction-cost assumptions.
- Break out performance by detected regime.

## Expected Failure Cases

- Signal disappears after transaction costs.
- Feature importance is unstable across folds.
- Performance concentrates in one regime and fails during regime shift.
- Validation improves while untouched test metrics degrade.

## Backtest Summary

| Fold | Train | Validation | Test | Threshold | Test Return | Test CVaR | Test Sharpe | Turnover |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 1 | (10, 99) | (100, 123) | (124, 147) | 1.200 | 0.000087 | 0.000000 | 3.310 | 0.042 |
| 2 | (34, 123) | (124, 147) | (148, 171) | 1.200 | 0.000020 | -0.001095 | 0.280 | 0.208 |
| 3 | (58, 147) | (148, 171) | (172, 195) | 0.800 | 0.000437 | -0.002447 | 2.585 | 0.542 |
| 4 | (82, 171) | (172, 195) | (196, 219) | 0.000 | 0.000961 | -0.002926 | 4.387 | 0.958 |

## Manifest Snapshot

```json
{
  "artifacts": {
    "audit_report": "docs/benchmarks/trading_experiment_audit.md",
    "backtest_report": "docs/benchmarks/mini_backtest_orchestration.md",
    "cycle_report": "docs/benchmarks/research_cycle_report.md",
    "manifest_report": "docs/benchmarks/experiment_manifest.md"
  },
  "data_source": "synthetic_market_bars",
  "fold_count": 4,
  "mean_test_cvar": -0.001617,
  "mean_test_return": 0.000376,
  "mean_test_sharpe": 2.640508,
  "name": "research-cycle-pair_mean_reversion_regime_filter",
  "parameters": {
    "idea": "HMM sideways regime improves mean-reversion entries for cointegrated pairs",
    "step_size": 24,
    "strategy_name": "pair_mean_reversion_regime_filter",
    "test_size": 24,
    "thresholds": [
      0.0,
      0.4,
      0.8,
      1.2
    ],
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
  "run_id": "6e729a7f9eda",
  "test_observations": 96,
  "validation_protocol": [
    "time-ordered train / validation / test windows",
    "feature standardization fit on the training window only",
    "HMM-style regime model fit on the training window only",
    "threshold selected on validation rows only",
    "test metrics reported only after threshold selection"
  ]
}
```

# Trading Experiment Audit Report

- run id: `6e729a7f9eda`
- decision: `review_required`
- pass: 11
- warning: 1
- fail: 0

## Checked Items

- manifest completeness
- time-ordered fold structure
- validation/test separation
- risk metrics and tail behavior
- public/private operational boundary

## Findings

| Severity | Category | Finding | Recommendation |
|---|---|---|---|
| `pass` | `manifest` | Manifest satisfies minimum fold count. | Keep fold count in every run log. |
| `pass` | `manifest` | Manifest satisfies minimum test observations. | Keep sample count visible. |
| `pass` | `manifest` | Manifest includes expected report artifacts. | Keep artifact paths stable. |
| `pass` | `validation` | Manifest declares train/validation/test separation. | Keep this explicit. |
| `pass` | `leakage` | Manifest declares train-only fitting. | Keep transform fitting scoped to train windows. |
| `pass` | `validation` | All folds are strictly time ordered. | Keep random splits out of financial ML. |
| `pass` | `validation` | Threshold selection varies across folds. | Track fold-level threshold choices. |
| `pass` | `generalization` | Validation/test behavior is not uniformly optimistic. | Still compare fold-level degradation before promotion. |
| `pass` | `risk` | Mean test CVaR is recorded as a left-tail loss metric. | Keep CVaR in the promotion gate. |
| `warning` | `cost` | High test turnover detected in folds: [4]. | Stress transaction costs and slippage before considering deployment. |
| `pass` | `risk` | All folds have positive test Sharpe. | Confirm this survives cost stress. |
| `pass` | `boundary` | Manifest explicitly excludes broker integration and live execution. | Keep public artifacts separate from private strategy operations. |
