# CVaR Position Sizing Example

Status: implemented as a toy QR-DQN / CVaR smoke example.

## Goal

Demonstrate how return quantiles can produce a risk multiplier.

## Example

```text
low tail risk    -> multiplier 1.0
medium tail risk -> multiplier 0.5
high tail risk   -> multiplier 0.0
```

This is an educational example only. It is not a live trading rule.

## Output

See:

```text
docs/benchmarks/qrdqn_cvar_smoke.md
```

Regenerate with:

```bash
make cvar-demo
```
