from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

from agentic_quant.research_os.copilot import answer_question
from agentic_quant.research_os.ingest import build_research_index
from agentic_quant.research_os.planner import plan_experiment


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--output", default="docs/benchmarks/research_os_demo.md")
    args = parser.parse_args()

    paths = [
        Path("README.md"),
        Path("docs/benchmarks/walk_forward_validation.md"),
        Path("docs/benchmarks/hmm_regime_features.md"),
        Path("docs/benchmarks/rag_evaluation_harness.md"),
    ]
    chunks = build_research_index(path for path in paths if path.exists())
    answer = answer_question("How should HMM regime features be validated in financial ML?", chunks)
    plan = plan_experiment("HMM sideways regime improves mean-reversion entries for cointegrated pairs")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(
            [
                "# QuantSigma Research OS Demo",
                "",
                "This demo shows the first implementation layer for a research operating system:",
                "artifact ingestion, deterministic citation search, supported answers, and a hypothesis-to-experiment plan.",
                "",
                answer.to_markdown(),
                "",
                plan.to_markdown(),
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
