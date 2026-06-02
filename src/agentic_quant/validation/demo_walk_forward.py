from __future__ import annotations

import argparse
from pathlib import Path

from agentic_quant.validation.walk_forward import (
    aggregate_results,
    run_walk_forward_validation,
    synthetic_regime_observations,
)


def render_markdown() -> str:
    observations = synthetic_regime_observations(length=192)
    results = run_walk_forward_validation(
        observations,
        train_size=72,
        validation_size=24,
        test_size=24,
        step_size=24,
        thresholds=(0.0, 0.25, 0.5, 0.75, 1.0),
        transaction_cost=0.0004,
    )
    aggregate = aggregate_results(results)

    lines = [
        "# Walk-Forward Validation Sample",
        "",
        "This sample demonstrates leakage-aware financial ML validation with synthetic data only.",
        "Each fold fits preprocessing on the training window, selects a threshold on validation,",
        "and reports performance on the untouched test window.",
        "",
        "## Protocol",
        "",
        "- Time-ordered train / validation / test windows",
        "- No random shuffle split",
        "- Standardization fit on the training window only",
        "- Threshold selection on validation only",
        "- Test metrics reported after the selection step",
        "- Synthetic feature and return series only",
        "",
        "## Fold Results",
        "",
        "| Fold | Train | Validation | Test | Train Mean | Threshold | Test Mean Return | Hit Rate | Turnover | Sharpe |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in results:
        lines.append(
            f"| {row.fold} | {row.train_range[0]}-{row.train_range[1]} | "
            f"{row.validation_range[0]}-{row.validation_range[1]} | "
            f"{row.test_range[0]}-{row.test_range[1]} | "
            f"{row.train_mean:.4f} | {row.selected_threshold:.2f} | "
            f"{row.test_metrics.mean_return:.5f} | {row.test_metrics.hit_rate:.2f} | "
            f"{row.test_metrics.turnover:.2f} | {row.test_metrics.sharpe:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Aggregate Test Metrics",
            "",
            f"- observations: {aggregate.observations}",
            f"- mean return: {aggregate.mean_return:.5f}",
            f"- hit rate: {aggregate.hit_rate:.2f}",
            f"- turnover: {aggregate.turnover:.2f}",
            f"- Sharpe: {aggregate.sharpe:.2f}",
            "",
            "## Boundary",
            "",
            "This is an educational validation pattern, not investment advice, a signal, or a live trading rule.",
            "It intentionally avoids private universes, broker data, alpha features, and production thresholds.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic walk-forward validation report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/benchmarks/walk_forward_validation.md"),
        help="Markdown output path.",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(), encoding="utf-8")
    print(f"wrote walk-forward validation report: {args.output}")


if __name__ == "__main__":
    main()
