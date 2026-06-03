from __future__ import annotations

import argparse
from pathlib import Path

from agentic_quant.benchmarks.numerai import render_numerai_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a public Numerai benchmark trail note.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/benchmarks/numerai_benchmark_trail.md"),
        help="Markdown output path.",
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_numerai_markdown(), encoding="utf-8")
    print(f"wrote Numerai benchmark trail note: {args.output}")


if __name__ == "__main__":
    main()
