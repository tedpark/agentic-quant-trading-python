from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from agentic_quant.research_os.audit import audit_experiment_run_contract
from agentic_quant.research_os.contract import parse_experiment_run_contract


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--input", default="docs/benchmarks/experiment_run_contract.json")
    parser.add_argument("--output", default="docs/benchmarks/contract_promotion_review.md")
    args = parser.parse_args()

    contract_path = Path(args.input)
    contract = parse_experiment_run_contract(contract_path.read_text(encoding="utf-8"))
    report = audit_experiment_run_contract(contract)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
