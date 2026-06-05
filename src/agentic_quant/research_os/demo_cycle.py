from __future__ import annotations

from argparse import ArgumentParser

from agentic_quant.research_os.cli import main as cli_main


DEFAULT_IDEA = "HMM sideways regime improves mean-reversion entries for cointegrated pairs"


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--idea", default=DEFAULT_IDEA)
    parser.add_argument("--output", default="docs/benchmarks/research_cycle_report.md")
    args = parser.parse_args()

    output = args.output
    output_dir = output.rsplit("/", 1)[0] if "/" in output else "."
    cli_main(
        [
            "cycle",
            "--idea",
            args.idea,
            "--output",
            output,
            "--contract-output",
            f"{output_dir}/experiment_run_contract.json",
            "--state-output",
            f"{output_dir}/research_workflow_state.json",
        ]
    )


if __name__ == "__main__":
    main()
