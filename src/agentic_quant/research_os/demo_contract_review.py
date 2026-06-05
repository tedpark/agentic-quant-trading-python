from __future__ import annotations

from argparse import ArgumentParser

from agentic_quant.research_os.cli import main as cli_main


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--input", default="docs/benchmarks/experiment_run_contract.json")
    parser.add_argument("--output", default="docs/benchmarks/contract_promotion_review.md")
    args = parser.parse_args()

    cli_main(["review", "--input", args.input, "--output", args.output])


if __name__ == "__main__":
    main()
