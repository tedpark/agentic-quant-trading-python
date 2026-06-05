# QuantSigma Research OS Demo

This demo shows the first implementation layer for a research operating system:
artifact ingestion, deterministic citation search, supported answers, and a hypothesis-to-experiment plan.

# Research Graph

## Nodes

| Node | Kind | Evidence chunks |
|---|---|---|
| Walk-forward validation | `validation` | `docs-benchmarks-walk-forward-validation-md::section-000`, `docs-benchmarks-walk-forward-validation-md::section-001`, `docs-benchmarks-walk-forward-validation-md::section-002`, `docs-benchmarks-walk-forward-validation-md::section-003`, `docs-benchmarks-walk-forward-validation-md::section-004`, `readme-md::section-001`, `readme-md::section-008`, `readme-md::section-009` |
| Purged / embargoed validation | `validation` | `readme-md::section-001`, `readme-md::section-005`, `readme-md::section-006`, `readme-md::section-008`, `readme-md::section-009` |
| HMM-style regime feature | `feature` | `docs-benchmarks-hmm-regime-features-md::section-000`, `docs-benchmarks-hmm-regime-features-md::section-001`, `docs-benchmarks-hmm-regime-features-md::section-002`, `docs-benchmarks-hmm-regime-features-md::section-003`, `docs-benchmarks-hmm-regime-features-md::section-004`, `docs-benchmarks-hmm-regime-features-md::section-005`, `readme-md::section-001`, `readme-md::section-003`, `readme-md::section-005`, `readme-md::section-006`, `readme-md::section-008`, `readme-md::section-009` |
| Cointegration spread feature | `feature` | `readme-md::section-002`, `readme-md::section-007` |
| CVaR / Expected Shortfall | `risk` | `readme-md::section-001`, `readme-md::section-005`, `readme-md::section-006`, `readme-md::section-008`, `readme-md::section-009` |
| QR-DQN distributional RL | `model` | `readme-md::section-001`, `readme-md::section-002`, `readme-md::section-005`, `readme-md::section-006`, `readme-md::section-007`, `readme-md::section-008`, `readme-md::section-009` |
| RAG evaluation harness | `system` | `docs-benchmarks-rag-evaluation-harness-md::section-000`, `docs-benchmarks-rag-evaluation-harness-md::section-001`, `docs-benchmarks-rag-evaluation-harness-md::section-002`, `docs-benchmarks-rag-evaluation-harness-md::section-003`, `readme-md::section-001`, `readme-md::section-003`, `readme-md::section-005`, `readme-md::section-008`, `readme-md::section-009` |
| Validation-first model serving | `system` | `docs-benchmarks-rag-evaluation-harness-md::section-002`, `readme-md::section-001`, `readme-md::section-003`, `readme-md::section-004`, `readme-md::section-005`, `readme-md::section-006`, `readme-md::section-008`, `readme-md::section-009` |

## Edges

| Source | Relation | Target |
|---|---|---|
| HMM-style regime feature | `must_be_validated_with` | Walk-forward validation |
| HMM-style regime feature | `needs_leakage_control` | Purged / embargoed validation |
| Cointegration spread feature | `must_be_validated_with` | Walk-forward validation |
| QR-DQN distributional RL | `optimizes_tail_risk_with` | CVaR / Expected Shortfall |
| RAG evaluation harness | `uses_regression_style_checks_like` | Walk-forward validation |
| Validation-first model serving | `should_be_tested_before_shipping_like` | RAG evaluation harness |


# QuantSigma Research OS Sample Answer

## Question

How should HMM regime features be validated in financial ML?

## Answer

- HMM-Style Regime Feature Pipeline Sample: This sample demonstrates a leakage-aware feature pipeline for financial ML with synthetic data only. Each fold builds rolling features, fits a small Gaussian HMM-style regime model on the training window, and applies the fitted regime model to the held-out... [docs-benchmarks-hmm-regime-features-md::section-000]
- Why Financial ML Is Hard: Financial ML is easy to overstate and hard to validate. The difficult parts are usually not the model architecture. The difficult parts are: - preventing look-ahead bias - separating research data from serving data - handling transaction costs and slippage... [readme-md::section-003]
- Agentic Quant Trading with Python: Public companion lab for production-style financial ML/RL systems. This project is not investment advice, a trading signal service, or a live trading bot. It is a public engineering companion for showing how financial ML systems can be built, validated, ser... [readme-md::section-000]

## Citations

- `docs-benchmarks-hmm-regime-features-md::section-000`: docs/benchmarks/hmm_regime_features.md / HMM-Style Regime Feature Pipeline Sample
- `readme-md::section-003`: README.md / Why Financial ML Is Hard
- `readme-md::section-000`: README.md / Agentic Quant Trading with Python

## Next Actions

- Turn the answer into an experiment manifest before changing model code.
- Check leakage controls before trusting any financial ML result.
- Compare metrics by regime, not only aggregate return.


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


## Experiment Manifest YAML

```yaml
run_id: 9ff3bb850f5f
system: QuantSigma Research OS
hypothesis: "If HMM sideways regime improves mean-reversion entries for cointegrated pairs, then it should improve out-of-sample risk-adjusted performance under leakage-aware validation."
feature_candidates:
  - "rolling return / volatility features"
  - "z-score velocity and acceleration"
  - "spread mean-reversion strength"
  - "HMM-style regime label"
  - "regime transition probability"
  - "regime-specific volatility"
  - "cointegration residual"
  - "spread half-life"
  - "rolling correlation stability"
validation_protocol:
  - "Use walk-forward train / validation / test windows."
  - "Fit scalers, regime models, and feature transforms on training windows only."
  - "Use purging and embargo when labels overlap adjacent windows."
  - "Select thresholds on validation windows and report untouched test-window metrics."
risk_checks:
  - "Report CVaR / Expected Shortfall, not only average return."
  - "Compare drawdown and turnover under transaction-cost assumptions."
  - "Break out performance by detected regime."
expected_failure_cases:
  - "Signal disappears after transaction costs."
  - "Feature importance is unstable across folds."
  - "Performance concentrates in one regime and fails during regime shift."
  - "Validation improves while untouched test metrics degrade."
public_boundary:
  - synthetic or public data only
  - no live broker integration
  - no private trading universe
  - no production thresholds
```
