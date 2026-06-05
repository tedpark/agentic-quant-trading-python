# Public Artifact Inventory

This repo is a sanitized public companion. It does not mirror the private trading system.

## Safe To Publish

| Artifact | Status | Notes |
|---|---|---|
| FastAPI model serving demo | initial skeleton done | Use toy checkpoints and sample requests. |
| Checkpoint hot reload | initial skeleton done | Validate candidate model before swapping active model. |
| Live-server E2E test | done | Starts uvicorn in a subprocess and verifies health, predict, invalid reload, valid reload, and wrong-dimension behavior over HTTP. |
| QR-DQN Hugging Face model card | published | Public model proof: https://huggingface.co/tedpark/stat-pair-qrdqn-v1 |
| QR-DQN LinkedIn release post | published | Career-facing release note: https://www.linkedin.com/feed/update/urn:li:share:7467475769485598720 |
| Drift report | done | Uses sample feature distributions only; reports PSI, KS, severity counts, and a Markdown boundary note. |
| QR-DQN quantile smoke test | done | Uses synthetic return quantiles only. |
| CVaR position sizing example | done | Demonstrates risk multiplier without private strategy thresholds. |
| Walk-forward validation doc | done | Demonstrates time-ordered train / validation / test windows. |
| Purged + embargoed validation doc | done | Demonstrates label-overlap leakage control. |
| HMM-style regime feature pipeline | done | Fits feature standardization and regime model on training windows only. |
| Mini backtest orchestration | done | Connects synthetic features, regimes, validation selection, transaction costs, and CVaR-style metrics. |
| Experiment manifest / run log | done | Records parameters, validation protocol, artifacts, and public/private boundaries for reproducible public runs. |
| Agent Builder spec / validator | done | Turns an idea into a validated financial ML experiment agent spec, then dispatches only allowlisted runners. |

## Keep Private

| Private Area | Reason |
|---|---|
| Broker integrations | Account and execution risk. |
| Live order scripts | Operational and strategy exposure. |
| Exact entry/exit thresholds | Strategy leakage. |
| Real trading universe | Strategy leakage. |
| Production scheduler/deploy config | Operational exposure. |
| Private alpha research notes | Research edge exposure. |
| Live backtest performance claims | Context and compliance risk. |

## First Public Module

Start with model serving because it is the cleanest production ML signal and does not require exposing private trading logic.

```text
FastAPI + PyTorch checkpoint hot reload + model_version response
```

## Current Public Modules

- FastAPI + PyTorch checkpoint hot reload + `model_version` response
- Live-server E2E test around the serving API
- Synthetic feature drift report with PSI / KS metrics
- QR-DQN / CVaR smoke example with synthetic quantiles
- Walk-forward validation
- Purged + embargoed validation
- HMM-style regime labels and rolling feature pipeline
- Mini backtest orchestration for an end-to-end synthetic experiment loop
- Experiment manifest / run log for synthetic public artifacts
- Agent Builder spec, validator, workflow state, and contract export

## Next Public Module Candidate

Add a small external benchmark trail such as Numerai, Kaggle, or another public leaderboard artifact.
