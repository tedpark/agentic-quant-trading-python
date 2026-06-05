from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from agentic_quant.experiments.manifest import build_mini_backtest_manifest
from agentic_quant.experiments.orchestration import run_mini_experiment
from agentic_quant.features.regime import synthetic_market_bars
from agentic_quant.research_os.audit import audit_experiment


def render_markdown() -> str:
    folds = run_mini_experiment(
        synthetic_market_bars(240),
        train_size=90,
        validation_size=24,
        test_size=24,
        step_size=24,
        thresholds=(0.0, 0.4, 0.8, 1.2),
    )
    manifest = build_mini_backtest_manifest(
        folds,
        parameters={
            "train_size": 90,
            "validation_size": 24,
            "test_size": 24,
            "step_size": 24,
            "thresholds": (0.0, 0.4, 0.8, 1.2),
        },
        artifacts={
            "manifest_report": "docs/benchmarks/experiment_manifest.md",
            "backtest_report": "docs/benchmarks/mini_backtest_orchestration.md",
            "audit_report": "docs/benchmarks/trading_experiment_audit.md",
        },
    )
    report = audit_experiment(manifest, folds)
    return report.to_markdown()


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--output", default="docs/benchmarks/trading_experiment_audit.md")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
