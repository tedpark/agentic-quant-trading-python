from __future__ import annotations

import argparse
from pathlib import Path

from agentic_quant.experiments.manifest import build_mini_backtest_manifest, render_manifest_markdown
from agentic_quant.experiments.orchestration import run_mini_experiment
from agentic_quant.features.regime import synthetic_market_bars


def render_markdown() -> str:
    parameters = {
        "synthetic_bars": 260,
        "train_size": 90,
        "validation_size": 24,
        "test_size": 24,
        "step_size": 24,
        "thresholds": "0.0,0.4,0.8,1.2",
        "transaction_cost": 0.0004,
    }
    results = run_mini_experiment(
        synthetic_market_bars(length=int(parameters["synthetic_bars"])),
        train_size=int(parameters["train_size"]),
        validation_size=int(parameters["validation_size"]),
        test_size=int(parameters["test_size"]),
        step_size=int(parameters["step_size"]),
        thresholds=(0.0, 0.4, 0.8, 1.2),
        transaction_cost=float(parameters["transaction_cost"]),
    )
    manifest = build_mini_backtest_manifest(
        results,
        parameters=parameters,
        artifacts={
            "orchestration_report": "docs/benchmarks/mini_backtest_orchestration.md",
            "manifest_report": "docs/benchmarks/experiment_manifest.md",
        },
    )
    return render_manifest_markdown(manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic experiment manifest report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/benchmarks/experiment_manifest.md"),
        help="Markdown output path.",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(), encoding="utf-8")
    print(f"wrote experiment manifest report: {args.output}")


if __name__ == "__main__":
    main()
