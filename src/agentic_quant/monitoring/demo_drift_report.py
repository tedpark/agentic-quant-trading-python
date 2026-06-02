from __future__ import annotations

import argparse
from pathlib import Path

from agentic_quant.monitoring.drift import detect_drift


def sample_features() -> tuple[dict[str, list[float]], dict[str, list[float]]]:
    reference = {
        "spread_z": [-1.2, -0.8, -0.4, -0.1, 0.0, 0.2, 0.5, 0.9, 1.1, 1.4],
        "volatility_z": [-0.7, -0.5, -0.2, -0.1, 0.1, 0.2, 0.3, 0.5, 0.6, 0.8],
        "regime_score": [0.12, 0.18, 0.2, 0.24, 0.27, 0.31, 0.36, 0.4, 0.44, 0.48],
    }
    current = {
        "spread_z": [-1.1, -0.7, -0.3, 0.0, 0.1, 0.3, 0.5, 0.8, 1.0, 1.3],
        "volatility_z": [0.1, 0.2, 0.4, 0.6, 0.9, 1.0, 1.2, 1.3, 1.5, 1.7],
        "regime_score": [0.35, 0.39, 0.43, 0.48, 0.52, 0.58, 0.62, 0.67, 0.72, 0.78],
    }
    return reference, current


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic feature drift report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/benchmarks/drift_report.md"),
        help="Markdown output path.",
    )
    args = parser.parse_args()

    reference, current = sample_features()
    report = detect_drift(reference, current, bins=5)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.to_markdown(), encoding="utf-8")
    print(f"wrote drift report: {args.output}")


if __name__ == "__main__":
    main()
