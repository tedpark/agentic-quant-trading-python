from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from agentic_quant.research_os.agent_builder import run_agent_builder


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
    args = parser.parse_args()

    report = run_agent_builder(args.idea)
    outputs = {
        Path(args.output): report.to_markdown(),
        Path(args.spec_output): report.spec.to_json(),
        Path(args.contract_output): report.cycle.contract.to_json(),
        Path(args.state_output): report.state.to_json(),
    }
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
