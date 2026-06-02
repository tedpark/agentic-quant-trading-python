from __future__ import annotations

import argparse
from pathlib import Path

from agentic_quant.features.regime import run_regime_feature_pipeline, synthetic_market_bars


def render_markdown() -> str:
    results = run_regime_feature_pipeline(
        synthetic_market_bars(length=240),
        train_size=80,
        validation_size=20,
        test_size=20,
        step_size=20,
    )

    lines = [
        "# HMM-Style Regime Feature Pipeline Sample",
        "",
        "This sample demonstrates a leakage-aware feature pipeline for financial ML with synthetic data only.",
        "Each fold builds rolling features, fits a small Gaussian HMM-style regime model on the training window,",
        "and applies the fitted regime model to the held-out test window.",
        "",
        "## Protocol",
        "",
        "- Synthetic close-price series only",
        "- Rolling returns, realized volatility, drawdown, and momentum features",
        "- Feature standardizer fit on the training window only",
        "- Gaussian emission regime model fit on the training window only",
        "- Viterbi decoding for low-vol / high-vol hidden regime labels",
        "- Test rows receive regime labels from the training-fitted model",
        "",
        "## Fold Summary",
        "",
        "| Fold | Train | Test | Train Regimes | Test Regimes | Train Mean Return | Train Mean Vol |",
        "|---:|---|---|---|---|---:|---:|",
    ]
    for row in results:
        train_counts = ", ".join(f"{key}: {value}" for key, value in sorted(row.train_regime_counts.items()))
        test_counts = ", ".join(f"{key}: {value}" for key, value in sorted(row.test_regime_counts.items()))
        lines.append(
            f"| {row.fold} | {row.train_range[0]}-{row.train_range[1]} | {row.test_range[0]}-{row.test_range[1]} | "
            f"{train_counts} | {test_counts} | {row.train_feature_means['return_1d']:.5f} | "
            f"{row.train_feature_means['realized_volatility']:.5f} |"
        )

    lines.extend(
        [
            "",
            "## Sample Test Rows",
            "",
            "| Fold | Timestamp | Regime | Return | Realized Vol | Drawdown | Momentum 5 |",
            "|---:|---:|---|---:|---:|---:|---:|",
        ]
    )
    for result in results[:2]:
        for row in result.sample_test_rows[:3]:
            lines.append(
                f"| {result.fold} | {row.timestamp} | {row.regime} | {row.return_1d:.5f} | "
                f"{row.realized_volatility:.5f} | {row.drawdown:.5f} | {row.momentum_5:.5f} |"
            )

    lines.extend(
        [
            "",
            "## What This Proves",
            "",
            "The artifact shows how regime labels can be generated inside a time-ordered ML pipeline without using future test information.",
            "It is intentionally small, deterministic, and easy to inspect.",
            "",
            "## Boundary",
            "",
            "This is an educational feature-engineering pattern, not investment advice, a trading signal, or a live trading rule.",
            "It intentionally avoids private universes, broker data, alpha features, and production thresholds.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic HMM-style regime feature report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/benchmarks/hmm_regime_features.md"),
        help="Markdown output path.",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(), encoding="utf-8")
    print(f"wrote HMM-style regime feature report: {args.output}")


if __name__ == "__main__":
    main()
