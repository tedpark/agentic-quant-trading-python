from __future__ import annotations

import argparse
from pathlib import Path

from agentic_quant.validation.purged_embargo import make_purged_embargo_splits


def render_markdown() -> str:
    data_length = 101
    label_horizon = 5
    test_size = 12
    embargo_size = 3
    splits = make_purged_embargo_splits(
        data_length,
        label_horizon=label_horizon,
        test_size=test_size,
        embargo_size=embargo_size,
        step_size=test_size,
    )

    lines = [
        "# Purged + Embargoed Validation Sample",
        "",
        "This sample demonstrates label-overlap leakage control with synthetic index ranges only.",
        "Each sample has a forward-looking label interval. Training samples whose labels overlap",
        "the held-out test label interval are purged, and samples immediately after the test block",
        "are embargoed.",
        "",
        "## Protocol",
        "",
        f"- data length: {data_length}",
        f"- label horizon: {label_horizon}",
        f"- blocked test size: {test_size}",
        f"- embargo size: {embargo_size}",
        "- no private universe, broker data, alpha features, or production thresholds",
        "",
        "## Fold Results",
        "",
        "| Fold | Test Samples | Test Label Span | Train Count | Purged | Embargoed |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for split in splits:
        lines.append(
            f"| {split.fold} | {split.test_indices[0]}-{split.test_indices[-1]} | "
            f"{split.test_label_span[0]}-{split.test_label_span[1] - 1} | "
            f"{len(split.train_indices)} | {len(split.purged_indices)} | {len(split.embargoed_indices)} |"
        )

    lines.extend(
        [
            "",
            "## What Gets Removed",
            "",
            "- Purged samples: training candidates whose forward-looking labels overlap the test label span.",
            "- Embargoed samples: training candidates immediately after the test block, held out to reduce temporal bleed.",
            "",
            "## Boundary",
            "",
            "This is an educational validation pattern, not investment advice, a signal, or a live trading rule.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a purged/embargoed validation report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/benchmarks/purged_embargo_validation.md"),
        help="Markdown output path.",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(), encoding="utf-8")
    print(f"wrote purged/embargoed validation report: {args.output}")


if __name__ == "__main__":
    main()
