from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from agentic_quant.research_os.cycle import run_research_cycle


DEFAULT_IDEA = "HMM sideways regime improves mean-reversion entries for cointegrated pairs"


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--idea", default=DEFAULT_IDEA)
    parser.add_argument("--output", default="docs/benchmarks/research_cycle_report.md")
    args = parser.parse_args()

    report = run_research_cycle(args.idea)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
