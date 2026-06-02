# Agentic Quant Trading with Python

Public companion lab for production-style financial ML/RL systems.

This project is not investment advice, a trading signal service, or a live trading bot. It is a public engineering companion for showing how financial ML systems can be built, validated, served, monitored, and explained without exposing private strategy details.

## What This Project Demonstrates

- Leakage-aware validation for financial time-series experiments
- Walk-forward evaluation instead of random train/test splits
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
```

## Public / Private Boundary

Public:

- sample or synthetic data
- validation protocol
- model serving patterns
- drift monitoring examples
- QR-DQN / CVaR educational modules
- benchmark methodology
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
7. Connect repo to QuantSigma.ai, Medium, and LinkedIn Featured.

## Local Commands

```bash
make test
make drift-demo
make cvar-demo
make walk-forward-demo
make reload-demo
make serve
```

Current test coverage:

```text
23 tests passing, including CVaR risk logic, drift monitoring, walk-forward validation, and a subprocess-backed uvicorn E2E test.
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

Demo reload request after `make reload-demo` and `make serve`:

```bash
curl -X POST http://127.0.0.1:8000/reload \
  -H 'Content-Type: application/json' \
  -d '{"checkpoint_path":"/tmp/agentic-quant-demo-v2.pt"}'
```
