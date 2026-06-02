# Architecture

This public lab separates research, validation, serving, and monitoring.

```text
sample data
  -> feature pipeline
  -> validation split
  -> model or baseline
  -> risk-aware evaluation
  -> model registry
  -> FastAPI serving
  -> monitoring report
```

## Modules

| Module | Purpose |
|---|---|
| `features` | Build sample features without future leakage. |
| `validation` | Time-series split and walk-forward protocol. |
| `risk` | CVaR and risk multiplier examples. |
| `serving` | FastAPI inference and checkpoint reload. |
| `monitoring` | PSI / KS drift reports and serving health examples. |

## Boundary

The public architecture shows production ML workflow, not private trading strategy.

## Implemented Public Flow

```text
toy checkpoint
  -> FastAPI serving
  -> live-server E2E test
  -> synthetic feature drift report
  -> QuantSigma.ai / LinkedIn / Medium proof trail
```
