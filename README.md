# Agentic Quant Trading with Python

Public companion lab for production-style financial ML/RL systems.

This project is not investment advice, a trading signal service, or a live trading bot. It is a public engineering companion for showing how financial ML systems can be built, validated, served, monitored, and explained without exposing private strategy details.

## What This Project Demonstrates

- Leakage-aware validation for financial time-series experiments
- Walk-forward evaluation instead of random train/test splits
- Purged and embargoed validation splits for label-overlap leakage control
- HMM-style regime detection and feature pipelines with train-only fitting
- Mini backtest orchestration that connects features, regimes, validation, and CVaR-style risk metrics
- Reproducible experiment manifests / run logs for public artifacts
- Trading experiment audit reports for validation, leakage, turnover, and risk checks
- Tool-calling research cycle with dynamic config generation, validation, runner dispatch, experiment_run contract export, manifest, audit, and report tools
- Numerai benchmark-trail preparation with submission format validation
- RAG evaluation harness with golden-set metrics, retrieval checks, citation coverage, and answer-support scoring
- QuantSigma Research OS prototype for artifact ingestion, research graph extraction, cited answers, and hypothesis-to-experiment manifests
- Risk-aware model evaluation with CVaR / Expected Shortfall
- Distributional RL patterns such as QR-DQN return quantiles
- FastAPI model serving with model version visibility
- Safer checkpoint hot reload for PyTorch inference services
- Drift monitoring with PSI / KS-style reports
- MLflow-style experiment tracking and reproducibility
- Clear public/private boundaries for financial ML work

## Public Proof Trail

This repo is one piece of a larger public artifact trail:

- Public hub: https://quantsigma.ai
- QR-DQN model card: https://huggingface.co/tedpark/stat-pair-qrdqn-v1
- QR-DQN release post: https://www.linkedin.com/feed/update/urn:li:share:7467475769485598720
- Medium notes: https://medium.com/@itstedpark
- English book: https://4273091654334.gumroad.com/l/stock-trading-ai-en

The intent is simple: code examples, model cards, technical writing, and LinkedIn activity should all support the same production ML story.

## Why Financial ML Is Hard

Financial ML is easy to overstate and hard to validate.

The difficult parts are usually not the model architecture. The difficult parts are:

- preventing look-ahead bias
- separating research data from serving data
- handling transaction costs and slippage
- measuring failure cases, not only average return
- detecting data drift and regime changes
- keeping model updates observable and reversible
- avoiding strategy leakage in public artifacts

This lab focuses on those engineering constraints.

## First Runnable Artifact

The first runnable artifact is implemented as a FastAPI model serving demo with safer PyTorch checkpoint hot reload.

Expected behavior:

- Prediction requests continue using the current model.
- Reload requests load a candidate checkpoint first.
- The candidate is shape-checked and smoke-tested before swap.
- Invalid reloads fail without mutating the active model.
- Inference responses expose `model_version`.

## Repo Structure

```text
agentic-quant-trading-python/
  README.md
  pyproject.toml
  Makefile
  data/
    sample/
  src/
    agentic_quant/
      serving/
      monitoring/
      risk/
      validation/
  tests/
  docs/
    architecture.md
    inventory.md
    validation.md
    serving.md
    benchmarks/
      serving_latency.md
      qrdqn_smoke.md
      cvar_position_sizing.md
      walk_forward_validation.md
      purged_embargo_validation.md
      hmm_regime_features.md
      mini_backtest_orchestration.md
      experiment_manifest.md
      numerai_benchmark_trail.md
      rag_evaluation_harness.md
      research_os_demo.md
      trading_experiment_audit.md
      research_cycle_report.md
      experiment_run_contract.json
    product/
      quant_research_os_implementation.md
      what_is_quant_research_os.md
      product_reality_check.md
      tool_calling_research_agent.md
```

## Public / Private Boundary

Public:

- sample or synthetic data
- validation protocol
- model serving patterns
- drift monitoring examples
- QR-DQN / CVaR educational modules
- HMM-style regime labeling and feature-pipeline examples
- mini backtest orchestration with synthetic data only
- experiment manifests and run logs for synthetic public artifacts
- benchmark methodology
- purged / embargoed validation split examples
- reproducible commands and tests

Private:

- broker integration
- live order execution
- account details
- production scheduler details
- exact trading universe
- private alpha research
- live strategy thresholds

## Writing Links

- QuantSigma.ai: https://quantsigma.ai
- Hugging Face QR-DQN model: https://huggingface.co/tedpark/stat-pair-qrdqn-v1
- LinkedIn QR-DQN model post: https://www.linkedin.com/feed/update/urn:li:share:7467475769485598720
- Medium: https://medium.com/@itstedpark
- Agentic Quant Trading with Python (EN): https://4273091654334.gumroad.com/l/stock-trading-ai-en
- Agentic Quant Trading with Python (KO): https://4273091654334.gumroad.com/l/stock-trading-ai-ko
- Agentic Quant Trading with Python (JA): https://4273091654334.gumroad.com/l/stock-trading-ai-ja
- Books page: https://tedpark.github.io/books

## Roadmap

1. FastAPI checkpoint hot-reload serving demo. Done as initial skeleton.
2. Live-server E2E test for health, predict, invalid reload, valid reload, and schema behavior. Done.
3. Add drift monitoring report with sample data. Done.
4. Add QR-DQN quantile smoke test. Done.
5. Add CVaR-aware position sizing example. Done.
6. Add walk-forward validation sample. Done.
7. Add purged + embargoed validation sample. Done.
8. Add HMM-style regime detection + feature pipeline sample. Done.
9. Add mini backtest orchestration sample. Done.
10. Add experiment manifest / run log for reproducibility. Done.
11. Add Numerai public benchmark trail preparation. Done.
12. Add deterministic RAG evaluation harness for LLM/RAG Evaluation roles. Done.
13. Add QuantSigma Research OS prototype for cited quant research answers and experiment manifest planning. Done.
14. Add trading experiment audit layer for validation, leakage, turnover, and risk review. Done.
15. Add allowlisted tool-calling research cycle runner. Done.
16. Add stable `experiment_run.v1` contract export and validation. Done.
17. Connect repo to QuantSigma.ai, Medium, and LinkedIn Featured.

## Local Commands

```bash
make test
make drift-demo
make cvar-demo
make walk-forward-demo
make purged-embargo-demo
make regime-feature-demo
make mini-backtest-demo
make manifest-demo
make numerai-demo
make rag-eval-demo
make research-os-demo
make experiment-audit-demo
make research-cycle-demo
make reload-demo
make serve
```

Current test coverage:

```text
72 tests passing, including CVaR risk logic, drift monitoring, walk-forward validation, purged/embargoed validation, HMM-style regime features, mini backtest orchestration, experiment manifests, trading experiment audit checks, tool-calling research cycle checks, config validation checks, experiment_run contract checks, Numerai submission-format checks, RAG evaluation harness checks, Research OS checks, and a subprocess-backed uvicorn E2E test.
```

Drift report demo:

```text
make drift-demo
```

Output:

```text
docs/benchmarks/drift_report.md
```

QR-DQN / CVaR demo:

```text
make cvar-demo
```

Output:

```text
docs/benchmarks/qrdqn_cvar_smoke.md
```

Walk-forward validation demo:

```text
make walk-forward-demo
```

Output:

```text
docs/benchmarks/walk_forward_validation.md
```

Numerai benchmark trail demo:

```text
make numerai-demo
```

Output:

```text
docs/benchmarks/numerai_benchmark_trail.md
```

Research OS demo:

```text
make research-os-demo
```

Output:

```text
docs/benchmarks/research_os_demo.md
```

Trading experiment audit demo:

```text
make experiment-audit-demo
```

Output:

```text
docs/benchmarks/trading_experiment_audit.md
```

Tool-calling research cycle demo:

```text
make research-cycle-demo
```

Output:

```text
docs/benchmarks/research_cycle_report.md
docs/benchmarks/experiment_run_contract.json
```

RAG evaluation harness demo:

```text
make rag-eval-demo
```

Output:

```text
docs/benchmarks/rag_evaluation_harness.md
```

Purged + embargoed validation demo:

```text
make purged-embargo-demo
```

Output:

```text
docs/benchmarks/purged_embargo_validation.md
```

HMM-style regime feature demo:

```text
make regime-feature-demo
```

Output:

```text
docs/benchmarks/hmm_regime_features.md
```

Mini backtest orchestration demo:

```text
make mini-backtest-demo
```

Output:

```text
docs/benchmarks/mini_backtest_orchestration.md
```

Experiment manifest demo:

```text
make manifest-demo
```

Output:

```text
docs/benchmarks/experiment_manifest.md
```

Demo reload request after `make reload-demo` and `make serve`:

```bash
curl -X POST http://127.0.0.1:8000/reload \
  -H 'Content-Type: application/json' \
  -d '{"checkpoint_path":"/tmp/agentic-quant-demo-v2.pt"}'
```
