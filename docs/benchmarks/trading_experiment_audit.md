# Trading Experiment Audit Report

- run id: `7c39122f5fe7`
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
