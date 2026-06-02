# QR-DQN Smoke Benchmark

Status: implemented as `qrdqn_cvar_smoke.md`.

## Goal

Show the shape of distributional RL output without publishing private trading logic.

## Public Scope

- toy state vector
- toy action space
- quantile output shape check
- CVaR calculation from left-tail quantiles

## Output

See:

```text
docs/benchmarks/qrdqn_cvar_smoke.md
```

Regenerate with:

```bash
make cvar-demo
```

## Private Scope

- live feature set
- real universe selection
- production reward shaping
- trading thresholds
