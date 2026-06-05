# QuantSigma Agent Builder Report

This report demonstrates a Wonderful-style builder pattern for financial ML research agents.
The builder creates an agent spec and dynamic config, then validates both before dispatching
to an allowlisted research runner. The generated agent cannot execute arbitrary code.

## Builder Decision

- agent id: `financial_ml_experiment_agent:0ce5bbd59dae`
- role: `financial_ml_experiment_agent`
- runner: `mini_backtest`
- strategy: `pair_mean_reversion_regime_filter`
- promotion decision: `review_required`

## Agent Spec

```json
{
  "agent_id": "financial_ml_experiment_agent:0ce5bbd59dae",
  "allowed_tools": [
    "plan_experiment",
    "build_experiment_config",
    "run_mini_backtest",
    "build_manifest",
    "audit_experiment",
    "write_report"
  ],
  "builder_version": "quant_sigma_agent_builder.v1",
  "config": {
    "allow_live_trading": false,
    "data_source": "synthetic_market_bars",
    "idea": "HMM regime features improve pair spread entries",
    "run_id": "0ce5bbd59dae",
    "runner": "mini_backtest",
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
  "constraints": [
    "contract_only_promotion_review",
    "leakage_aware_validation",
    "no_arbitrary_code",
    "no_live_trading",
    "public_or_synthetic_data_only"
  ],
  "goal": "Run a leakage-aware financial ML experiment from the idea, using only the `mini_backtest` runner and exporting an experiment_run.v1 contract.",
  "idea": "HMM regime features improve pair spread entries",
  "outputs": [
    "agent_spec",
    "dynamic_config",
    "experiment_manifest",
    "experiment_run.v1",
    "workflow_state_trace",
    "promotion_review",
    "markdown_report"
  ],
  "role": "financial_ml_experiment_agent",
  "schema_version": "agent_spec.v1"
}
```

## Builder State

```json
{
  "agent_spec_built": true,
  "agent_spec_validated": true,
  "completed_steps": [
    "build_agent_spec",
    "validate_agent_spec",
    "run_research_cycle_from_agent_spec"
  ],
  "config_validated": true,
  "cycle_completed": true,
  "idea": "HMM regime features improve pair spread entries"
}
```

## Downstream Research Cycle

# QuantSigma Lab Agent Research Cycle

This report demonstrates a safe tool-calling research operator.
The agent does not execute arbitrary shell commands or live trading.
It calls allowlisted research tools, runs the trading-system backtest sample,
builds a manifest, and applies the promotion gate.

## Decision

- run id: `0ce5bbd59dae`
- strategy: `pair_mean_reversion_regime_filter`
- promotion decision: `review_required`
- live trading allowed: `False`
- completed steps: 6

## Tool Calls

| Tool | Status | Summary |
|---|---|---|
| `plan_experiment` | `ok` | created leakage-aware experiment plan |
| `build_experiment_config` | `ok` | created and validated safe synthetic-data config |
| `run_mini_backtest` | `ok` | ran walk-forward mini backtest |
| `build_manifest` | `ok` | built experiment manifest |
| `audit_experiment` | `ok` | applied promotion gate |
| `write_report` | `ok` | rendered cycle report and experiment_run contract |

## Experiment Config

```json
{
  "allow_live_trading": false,
  "data_source": "synthetic_market_bars",
  "idea": "HMM regime features improve pair spread entries",
  "run_id": "0ce5bbd59dae",
  "runner": "mini_backtest",
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

- run id: `0ce5bbd59dae`
- hypothesis: If HMM regime features improve pair spread entries, then it should improve out-of-sample risk-adjusted performance under leakage-aware validation.

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
    "idea": "HMM regime features improve pair spread entries",
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
  "run_id": "2256975f1fb9",
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

## Experiment Run Contract

```json
{
  "allow_live_trading": false,
  "artifacts": {
    "audit_report": "docs/benchmarks/trading_experiment_audit.md",
    "backtest_report": "docs/benchmarks/mini_backtest_orchestration.md",
    "cycle_report": "docs/benchmarks/research_cycle_report.md",
    "manifest_report": "docs/benchmarks/experiment_manifest.md"
  },
  "benchmark_comparison": [
    {
      "benchmark_name": "zero_return_baseline",
      "cvar_delta": -0.000617,
      "mean_return_delta": 0.000376,
      "sharpe_delta": 2.640508
    }
  ],
  "cost_stress": [
    {
      "max_turnover": 0.9583333333333334,
      "mean_test_cvar": -0.001617,
      "mean_test_return": 0.000376,
      "scenario": "base_cost",
      "transaction_cost": 0.0004
    },
    {
      "max_turnover": 0.9583333333333334,
      "mean_test_cvar": -0.001809,
      "mean_test_return": -7e-06,
      "scenario": "double_cost_proxy",
      "transaction_cost": 0.0008
    }
  ],
  "data_source": "synthetic_market_bars",
  "features": [
    {
      "fit_scope": "train_only",
      "name": "rolling_return"
    },
    {
      "fit_scope": "train_only",
      "name": "realized_volatility"
    },
    {
      "fit_scope": "train_only",
      "name": "hmm_regime"
    },
    {
      "fit_scope": "train_only",
      "name": "spread_zscore"
    },
    {
      "fit_scope": "train_only",
      "name": "spread_half_life"
    }
  ],
  "folds": [
    {
      "fold": 1,
      "selected_threshold": 1.2,
      "test_metrics": {
        "cvar": 0.0,
        "hit_rate": 1.0,
        "max_drawdown": 0.0,
        "mean_return": 8.674242424242715e-05,
        "observations": 24,
        "sharpe": 3.310063706204223,
        "turnover": 0.041666666666666664
      },
      "test_range": [
        124,
        147
      ],
      "train_range": [
        10,
        99
      ],
      "validation_metrics": {
        "cvar": -0.00043136363636363744,
        "hit_rate": 0.75,
        "max_drawdown": -0.0021568181818181873,
        "mean_return": 7.509469696970104e-05,
        "observations": 24,
        "sharpe": 1.8461645656416394,
        "turnover": 0.16666666666666666
      },
      "validation_range": [
        100,
        123
      ]
    },
    {
      "fold": 2,
      "selected_threshold": 1.2,
      "test_metrics": {
        "cvar": -0.0010954545454545494,
        "hit_rate": 0.4,
        "max_drawdown": -0.0037227272727272716,
        "mean_return": 1.9507575757574834e-05,
        "observations": 24,
        "sharpe": 0.2801318565109455,
        "turnover": 0.20833333333333334
      },
      "test_range": [
        148,
        171
      ],
      "train_range": [
        34,
        123
      ],
      "validation_metrics": {
        "cvar": -0.00012909090909090973,
        "hit_rate": 0.5,
        "max_drawdown": -0.0006454545454545487,
        "mean_return": 5.984848484848762e-05,
        "observations": 24,
        "sharpe": 2.1550193819353667,
        "turnover": 0.08333333333333333
      },
      "validation_range": [
        124,
        147
      ]
    },
    {
      "fold": 3,
      "selected_threshold": 0.8,
      "test_metrics": {
        "cvar": -0.0024472727272727333,
        "hit_rate": 0.46153846153846156,
        "max_drawdown": -0.004200000000000004,
        "mean_return": 0.00043655303030302745,
        "observations": 24,
        "sharpe": 2.5845007079622486,
        "turnover": 0.5416666666666666
      },
      "test_range": [
        172,
        195
      ],
      "train_range": [
        58,
        147
      ],
      "validation_metrics": {
        "cvar": -0.001890000000000006,
        "hit_rate": 0.5,
        "max_drawdown": -0.0043590909090908845,
        "mean_return": 0.00020852272727272787,
        "observations": 24,
        "sharpe": 1.663294063843947,
        "turnover": 0.3333333333333333
      },
      "validation_range": [
        148,
        171
      ]
    },
    {
      "fold": 4,
      "selected_threshold": 0.0,
      "test_metrics": {
        "cvar": -0.002926363636363643,
        "hit_rate": 0.5217391304347826,
        "max_drawdown": -0.008136363636363594,
        "mean_return": 0.000960984848484843,
        "observations": 24,
        "sharpe": 4.387336463140422,
        "turnover": 0.9583333333333334
      },
      "test_range": [
        196,
        219
      ],
      "train_range": [
        82,
        171
      ],
      "validation_metrics": {
        "cvar": -0.0030718181818181864,
        "hit_rate": 0.4782608695652174,
        "max_drawdown": -0.008136363636363594,
        "mean_return": 0.0007914772727272717,
        "observations": 24,
        "sharpe": 3.5085341448325202,
        "turnover": 0.9583333333333334
      },
      "validation_range": [
        172,
        195
      ]
    }
  ],
  "manifest_run_id": "2256975f1fb9",
  "model_version": "research_demo_v1",
  "parameters": {
    "idea": "HMM regime features improve pair spread entries",
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
  "regime_breakdown": [
    {
      "cvar": -0.013291,
      "mean_return": -0.000382,
      "observations": 8,
      "regime": "high_vol"
    },
    {
      "cvar": -0.004064,
      "mean_return": 0.000505,
      "observations": 8,
      "regime": "low_vol"
    }
  ],
  "run_id": "0ce5bbd59dae",
  "runner": "mini_backtest",
  "schema_version": "experiment_run.v1",
  "strategy_name": "pair_mean_reversion_regime_filter"
}
```

## Workflow State

```json
{
  "audit_decision": "review_required",
  "completed_steps": [
    "plan_experiment",
    "validate_experiment_config",
    "run_registered_runner",
    "build_manifest",
    "audit_experiment",
    "validate_experiment_run_contract"
  ],
  "config_validated": true,
  "contract_validated": true,
  "idea": "HMM regime features improve pair spread entries",
  "manifest_run_id": "2256975f1fb9",
  "run_id": "0ce5bbd59dae",
  "runner_dispatched": true
}
```

# Trading Experiment Audit Report

- run id: `2256975f1fb9`
- decision: `review_required`
- pass: 11
- warning: 1
- fail: 0

## Checked Items

- manifest completeness
- time-ordered fold structure
- validation/test separation
- feature fit scope
- cost stress
- regime breakdown
- benchmark comparison
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
