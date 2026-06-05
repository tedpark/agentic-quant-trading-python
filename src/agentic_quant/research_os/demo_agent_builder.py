from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from agentic_quant.research_os.agent_builder import AgentBuilderArtifactPaths, run_agent_builder, write_agent_builder_artifacts


def main() -> None:
    parser = ArgumentParser(description="Generate a safe agent-builder report from a research idea.")
    parser.add_argument(
        "--idea",
        default="HMM regime features improve pair spread entries",
        help="Research idea to turn into a validated experiment agent spec.",
    )
    parser.add_argument("--output", default="docs/benchmarks/agent_builder_report.md")
    parser.add_argument("--spec-output", default="docs/benchmarks/agent_spec.json")
    parser.add_argument("--contract-output", default="docs/benchmarks/experiment_run_contract.json")
    parser.add_argument("--state-output", default="docs/benchmarks/agent_builder_state.json")
    parser.add_argument("--manifest-output", default="docs/benchmarks/agent_builder_run_manifest.json")
    parser.add_argument("--event-log-output", default="docs/benchmarks/agent_builder_events.jsonl")
    args = parser.parse_args()

    report = run_agent_builder(args.idea)
    paths = AgentBuilderArtifactPaths(
        output=Path(args.output),
        spec_output=Path(args.spec_output),
        contract_output=Path(args.contract_output),
        state_output=Path(args.state_output),
        manifest_output=Path(args.manifest_output),
        event_log_output=Path(args.event_log_output),
    )
    write_agent_builder_artifacts(report, paths)
    for path in (
        paths.output,
        paths.spec_output,
        paths.contract_output,
        paths.state_output,
        paths.manifest_output,
        paths.event_log_output,
    ):
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
