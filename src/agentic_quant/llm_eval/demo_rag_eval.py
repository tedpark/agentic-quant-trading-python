from __future__ import annotations

import argparse
from pathlib import Path

from agentic_quant.llm_eval.rag_eval import evaluate_rag_run, sample_rag_run


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a deterministic RAG evaluation report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/benchmarks/rag_evaluation_harness.md"),
        help="Markdown output path.",
    )
    args = parser.parse_args()

    golden, answers = sample_rag_run()
    report = evaluate_rag_run(golden, answers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.to_markdown(), encoding="utf-8")
    print(f"wrote RAG evaluation report: {args.output}")


if __name__ == "__main__":
    main()
