# QR-DQN / CVaR Smoke Example

This example turns toy QR-DQN return quantiles into CVaR-style exposure multipliers.
It uses synthetic quantiles only and does not expose private reward shaping, features, or thresholds.

| Action | Quantiles | Expected Return | Left-Tail CVaR | Multiplier |
|---|---:|---:|---:|---:|
| hold | 10 | 0.0005 | -0.0035 | 1.0 |
| short_spread | 10 | -0.0002 | -0.0190 | 0.5 |
| long_spread | 10 | -0.0036 | -0.0350 | 0.0 |

## Boundary

This is an educational risk-control pattern, not investment advice or a live trading rule.
