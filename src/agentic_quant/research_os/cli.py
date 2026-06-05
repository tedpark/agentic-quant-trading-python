from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

from agentic_quant.research_os.agent_builder import run_agent_builder
from agentic_quant.research_os.audit import audit_experiment_run_contract
from agentic_quant.research_os.contract import parse_experiment_run_contract
from agentic_quant.research_os.cycle import run_research_cycle


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "cycle":
        _run_cycle(args)
        return 0
    if args.command == "build-agent":
        _run_build_agent(args)
        return 0
    if args.command == "review":
        _run_review(args)
        return 0
    parser.print_help()
    return 2


def _parser() -> ArgumentParser:
    parser = ArgumentParser(prog="quant-research")
    subcommands = parser.add_subparsers(dest="command")

    cycle = subcommands.add_parser("cycle", help="Run an allowlisted research cycle from an idea.")
    cycle.add_argument("--idea", required=True)
    cycle.add_argument("--output", default="docs/benchmarks/research_cycle_report.md")
    cycle.add_argument("--contract-output", default="docs/benchmarks/experiment_run_contract.json")
    cycle.add_argument("--state-output", default="docs/benchmarks/research_workflow_state.json")

    build_agent = subcommands.add_parser("build-agent", help="Build, validate, and run a safe experiment agent spec.")
    build_agent.add_argument("--idea", required=True)
    build_agent.add_argument("--output", default="docs/benchmarks/agent_builder_report.md")
    build_agent.add_argument("--spec-output", default="docs/benchmarks/agent_spec.json")
    build_agent.add_argument("--contract-output", default="docs/benchmarks/experiment_run_contract.json")
    build_agent.add_argument("--state-output", default="docs/benchmarks/agent_builder_state.json")

    review = subcommands.add_parser("review", help="Review an experiment_run.v1 contract.")
    review.add_argument("--input", required=True)
    review.add_argument("--output", default="docs/benchmarks/contract_promotion_review.md")

    return parser


def _run_cycle(args: Namespace) -> None:
    report = run_research_cycle(args.idea)
    output = Path(args.output)
    contract_output = Path(args.contract_output)
    state_output = Path(args.state_output)
    for path in (output, contract_output, state_output):
        path.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(report.to_markdown(), encoding="utf-8")
    contract_output.write_text(report.contract.to_json(), encoding="utf-8")
    state_output.write_text(report.state.to_json(), encoding="utf-8")


def _run_build_agent(args: Namespace) -> None:
    report = run_agent_builder(args.idea)
    output = Path(args.output)
    spec_output = Path(args.spec_output)
    contract_output = Path(args.contract_output)
    state_output = Path(args.state_output)
    for path in (output, spec_output, contract_output, state_output):
        path.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(report.to_markdown(), encoding="utf-8")
    spec_output.write_text(report.spec.to_json(), encoding="utf-8")
    contract_output.write_text(report.cycle.contract.to_json(), encoding="utf-8")
    state_output.write_text(report.state.to_json(), encoding="utf-8")


def _run_review(args: Namespace) -> None:
    contract_path = Path(args.input)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    contract = parse_experiment_run_contract(contract_path.read_text(encoding="utf-8"))
    report = audit_experiment_run_contract(contract)
    output.write_text(report.to_markdown(), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
