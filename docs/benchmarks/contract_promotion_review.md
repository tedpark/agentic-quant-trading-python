# Trading Experiment Audit Report

- run id: `9ff3bb850f5f`
- decision: `review_required`
- pass: 13
- warning: 1
- fail: 0

## Checked Items

- experiment_run.v1 contract completeness
- time-ordered fold structure
- validation/test separation
- risk metrics and tail behavior
- public/private operational boundary

## Findings

| Severity | Category | Finding | Recommendation |
|---|---|---|---|
| `pass` | `contract` | Contract satisfies minimum fold count. | Keep fold count stable. |
| `pass` | `contract` | Contract satisfies minimum test observations. | Keep sample count visible. |
| `pass` | `contract` | Contract includes expected report artifacts. | Keep artifact paths stable. |
| `pass` | `leakage` | All contract features declare train-only fit scope. | Keep fit scope explicit. |
| `pass` | `cost` | Contract includes cost-stress scenarios. | Keep cost stress in promotion review. |
| `pass` | `regime` | Contract includes regime breakdown. | Keep regime-level fragility visible. |
| `pass` | `benchmark` | Contract includes benchmark comparison. | Compare against a baseline. |
| `pass` | `validation` | All contract folds are strictly time ordered. | Keep random splits out of financial ML. |
| `pass` | `validation` | Threshold selection varies across contract folds. | Track fold-level choices. |
| `pass` | `generalization` | Contract validation/test behavior is not uniformly optimistic. | Still compare fold-level degradation before promotion. |
| `pass` | `risk` | Contract records CVaR as a left-tail loss metric. | Keep CVaR in the promotion gate. |
| `warning` | `cost` | High test turnover detected in contract folds: [4]. | Stress transaction costs and slippage before considering deployment. |
| `pass` | `risk` | All contract folds have positive test Sharpe. | Confirm this survives cost stress. |
| `pass` | `boundary` | Contract explicitly excludes live execution and broker access. | Keep public contracts separate from private strategy operations. |
