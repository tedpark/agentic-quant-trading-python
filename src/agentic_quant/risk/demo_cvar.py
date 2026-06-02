from __future__ import annotations

import argparse
from pathlib import Path

from agentic_quant.risk.cvar import evaluate_action_risk


def toy_qrdqn_quantiles() -> dict[str, list[float]]:
    return {
        "hold": [-0.004, -0.003, -0.002, -0.001, 0.0, 0.001, 0.002, 0.003, 0.004, 0.005],
        "long_spread": [-0.042, -0.028, -0.018, -0.01, -0.004, 0.002, 0.008, 0.012, 0.018, 0.026],
        "short_spread": [-0.022, -0.016, -0.011, -0.006, -0.002, 0.003, 0.007, 0.011, 0.014, 0.02],
    }


def render_markdown() -> str:
    rows = evaluate_action_risk(toy_qrdqn_quantiles(), tail_fraction=0.2)
    lines = [
        "# QR-DQN / CVaR Smoke Example",
        "",
        "This example turns toy QR-DQN return quantiles into CVaR-style exposure multipliers.",
        "It uses synthetic quantiles only and does not expose private reward shaping, features, or thresholds.",
        "",
        "| Action | Quantiles | Expected Return | Left-Tail CVaR | Multiplier |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.action} | {row.quantile_count} | {row.expected_return:.4f} | "
            f"{row.cvar:.4f} | {row.multiplier:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is an educational risk-control pattern, not investment advice or a live trading rule.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a toy QR-DQN / CVaR report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/benchmarks/qrdqn_cvar_smoke.md"),
        help="Markdown output path.",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(), encoding="utf-8")
    print(f"wrote QR-DQN / CVaR report: {args.output}")


if __name__ == "__main__":
    main()
