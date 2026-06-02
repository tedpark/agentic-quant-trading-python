from __future__ import annotations

import argparse
from pathlib import Path

from agentic_quant.experiments.orchestration import run_mini_experiment
from agentic_quant.features.regime import synthetic_market_bars


def render_markdown() -> str:
    results = run_mini_experiment(
        synthetic_market_bars(length=260),
        train_size=90,
        validation_size=24,
        test_size=24,
        step_size=24,
        thresholds=(0.0, 0.4, 0.8, 1.2),
        transaction_cost=0.0004,
    )

    lines = [
        "# Mini Backtest Orchestration Sample",
        "",
        "This sample wires the public financial ML building blocks into one leakage-aware experiment loop.",
        "It uses synthetic data only and does not publish a trading signal.",
        "",
        "## Pipeline",
        "",
        "```text",
        "synthetic prices -> rolling features -> train-fitted regime labels -> validation threshold selection -> test simulation -> CVaR metrics",
        "```",
        "",
        "## Protocol",
        "",
        "- Synthetic close-price series only",
        "- Rolling feature rows are paired with the next-period forward return",
        "- Feature standardization is fit on the training window only",
        "- HMM-style Gaussian regime labels are fit on the training window only",
        "- Thresholds are selected on validation rows only",
        "- Test metrics are reported after the selection step",
        "- CVaR-style risk multipliers reduce exposure in unfavorable tail-risk states",
        "",
        "## Fold Results",
        "",
        "| Fold | Train | Validation | Test | Threshold | Test Mean | Hit Rate | Turnover | CVaR | Max DD | Sharpe |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in results:
        metrics = row.test_metrics
        lines.append(
            f"| {row.fold} | {row.train_range[0]}-{row.train_range[1]} | "
            f"{row.validation_range[0]}-{row.validation_range[1]} | {row.test_range[0]}-{row.test_range[1]} | "
            f"{row.selected_threshold:.2f} | {metrics.mean_return:.5f} | {metrics.hit_rate:.2f} | "
            f"{metrics.turnover:.2f} | {metrics.cvar:.5f} | {metrics.max_drawdown:.5f} | {metrics.sharpe:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Sample Test Rows",
            "",
            "| Fold | Timestamp | Regime | Z Momentum | Z Volatility | Drawdown | Forward Return |",
            "|---:|---:|---|---:|---:|---:|---:|",
        ]
    )
    for result in results[:2]:
        for row in result.sample_test_rows[:3]:
            lines.append(
                f"| {result.fold} | {row.timestamp} | {row.regime} | {row.z_momentum:.3f} | "
                f"{row.z_volatility:.3f} | {row.drawdown:.5f} | {row.forward_return:.5f} |"
            )

    lines.extend(
        [
            "",
            "## What This Proves",
            "",
            "This artifact shows the shape of an inspectable financial ML experiment loop.",
            "It connects feature engineering, regime labels, validation, a toy decision rule, transaction costs, and CVaR-style risk controls without using private strategy details.",
            "",
            "## Boundary",
            "",
            "This is an educational orchestration pattern, not investment advice, a trading signal, or a live trading rule.",
            "It intentionally avoids private universes, broker data, alpha features, production thresholds, live execution, and account data.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic mini backtest orchestration report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/benchmarks/mini_backtest_orchestration.md"),
        help="Markdown output path.",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(), encoding="utf-8")
    print(f"wrote mini backtest orchestration report: {args.output}")


if __name__ == "__main__":
    main()
