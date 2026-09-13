from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

from agentic_quant.research_os.agent_builder import (
    AgentBuilderArtifactPaths,
    default_agent_builder_paths,
    parse_agent_spec_json,
    run_agent_builder,
    run_agent_builder_from_spec,
    write_agent_builder_artifacts,
)
from agentic_quant.research_os.audit import audit_experiment_run_contract
from agentic_quant.research_os.contract import parse_experiment_run_contract
from agentic_quant.research_os.cycle import run_research_cycle
from agentic_quant.research_os.model_runtime import (
    OpenAIResponsesToolSelector,
    load_model_agent_checkpoint,
    resume_model_agent,
    start_model_agent,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "cycle":
        _run_cycle(args)
        return 0
    if args.command == "build-agent":
        _run_build_agent(args)
        return 0
    if args.command == "validate-spec":
        _run_validate_spec(args)
        return 0
    if args.command == "review":
        _run_review(args)
        return 0
    if args.command == "model-agent":
        _run_model_agent(args)
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
    build_agent.add_argument("--idea")
    build_agent.add_argument("--spec-input", help="Run from an existing agent_spec.v1 JSON file.")
    build_agent.add_argument("--run-dir", help="Write artifacts under RUN_DIR/<run_id>/ for reproducible runs.")
    build_agent.add_argument("--output", default="docs/benchmarks/agent_builder_report.md")
    build_agent.add_argument("--spec-output", default="docs/benchmarks/agent_spec.json")
    build_agent.add_argument("--contract-output", default="docs/benchmarks/experiment_run_contract.json")
    build_agent.add_argument("--state-output", default="docs/benchmarks/agent_builder_state.json")
    build_agent.add_argument("--manifest-output", default="docs/benchmarks/agent_builder_run_manifest.json")
    build_agent.add_argument("--event-log-output", default="docs/benchmarks/agent_builder_events.jsonl")

    validate_spec = subcommands.add_parser("validate-spec", help="Validate an agent_spec.v1 JSON file without running it.")
    validate_spec.add_argument("--input", required=True)
    validate_spec.add_argument("--output", help="Optional path for the normalized validated spec JSON.")

    review = subcommands.add_parser("review", help="Review an experiment_run.v1 contract.")
    review.add_argument("--input", required=True)
    review.add_argument("--output", default="docs/benchmarks/contract_promotion_review.md")

    model_agent = subcommands.add_parser(
        "model-agent",
        help="Run or resume an OpenAI Responses tool-selecting agent with a human approval gate.",
    )
    model_agent.add_argument("--idea", help="Start a new model-directed research workflow.")
    model_agent.add_argument("--run-dir", default="docs/runs")
    model_agent.add_argument("--resume", help="Resume a persisted model_agent_checkpoint.json file.")
    approval = model_agent.add_mutually_exclusive_group()
    approval.add_argument("--approve", action="store_true", help="Approve the pending research-cycle call.")
    approval.add_argument("--reject", action="store_true", help="Reject the pending research-cycle call.")
    model_agent.add_argument("--model", default="gpt-5.6")
    model_agent.add_argument("--timeout", type=float, default=30.0)
    model_agent.add_argument("--max-retries", type=int, default=2)

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
    if args.spec_input:
        spec = parse_agent_spec_json(Path(args.spec_input).read_text(encoding="utf-8"))
        report = run_agent_builder_from_spec(spec)
    else:
        if not args.idea:
            raise ValueError("build-agent requires --idea or --spec-input")
        report = run_agent_builder(args.idea)

    if args.run_dir:
        paths = default_agent_builder_paths(Path(args.run_dir), run_id=report.spec.config.run_id)
    else:
        paths = AgentBuilderArtifactPaths(
            output=Path(args.output),
            spec_output=Path(args.spec_output),
            contract_output=Path(args.contract_output),
            state_output=Path(args.state_output),
            manifest_output=Path(args.manifest_output),
            event_log_output=Path(args.event_log_output),
        )
    write_agent_builder_artifacts(report, paths)


def _run_validate_spec(args: Namespace) -> None:
    spec = parse_agent_spec_json(Path(args.input).read_text(encoding="utf-8"))
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(spec.to_json(), encoding="utf-8")


def _run_review(args: Namespace) -> None:
    contract_path = Path(args.input)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    contract = parse_experiment_run_contract(contract_path.read_text(encoding="utf-8"))
    report = audit_experiment_run_contract(contract)
    output.write_text(report.to_markdown(), encoding="utf-8")


def _run_model_agent(args: Namespace) -> None:
    if bool(args.idea) == bool(args.resume):
        raise ValueError("model-agent requires exactly one of --idea or --resume")
    if args.idea and (args.approve or args.reject):
        raise ValueError("approval flags are only valid with --resume")

    model = args.model
    checkpoint_path: Path | None = None
    if args.resume:
        checkpoint_path = Path(args.resume)
        checkpoint = load_model_agent_checkpoint(checkpoint_path)
        model = checkpoint.model
        if not args.approve and not args.reject:
            raise ValueError("resuming an approval checkpoint requires --approve or --reject")

    selector = OpenAIResponsesToolSelector(
        model=model,
        timeout_seconds=args.timeout,
        max_retries=args.max_retries,
    )
    if checkpoint_path is not None:
        resume_model_agent(checkpoint_path, selector=selector, approve=args.approve)
    else:
        start_model_agent(args.idea, run_dir=Path(args.run_dir), selector=selector)


if __name__ == "__main__":
    raise SystemExit(main())
