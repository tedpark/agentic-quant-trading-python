from __future__ import annotations

import pytest

from agentic_quant.llm_eval.rag_eval import (
    Context,
    GoldenQuestion,
    RagAnswer,
    evaluate_rag_run,
    sample_rag_run,
)


def test_sample_rag_run_has_strong_retrieval_metrics() -> None:
    golden, answers = sample_rag_run()

    report = evaluate_rag_run(golden, answers)
    metrics = report.metric_means()

    assert len(report.rows) == 5
    assert metrics["context_precision"] == 0.5
    assert metrics["context_recall"] == 1.0
    assert metrics["hit_rate"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["citation_coverage"] == 1.0
    assert metrics["answer_support"] >= 0.5


def test_missing_answer_is_rejected() -> None:
    golden, answers = sample_rag_run()

    with pytest.raises(ValueError, match="missing answers"):
        evaluate_rag_run(golden, answers[:-1])


def test_retrieval_miss_is_visible_in_metrics() -> None:
    golden = (
        GoldenQuestion(
            id="q001",
            question="What is walk-forward validation?",
            ground_truth="A time-ordered validation protocol.",
            relevant_context_ids=("doc:walk-forward",),
            category="validation",
        ),
    )
    answers = (
        RagAnswer(
            question_id="q001",
            answer="It is a validation protocol.",
            retrieved_contexts=(Context(id="doc:wrong", text="This context is about monitoring."),),
            citations=("doc:wrong",),
        ),
    )

    report = evaluate_rag_run(golden, answers)
    row = report.rows[0]

    assert row.context_precision == 0.0
    assert row.context_recall == 0.0
    assert row.hit_rate == 0.0
    assert row.mrr == 0.0
    assert row.citation_coverage == 0.0


def test_markdown_report_contains_interview_message() -> None:
    golden, answers = sample_rag_run()

    markdown = evaluate_rag_run(golden, answers).to_markdown()

    assert "# RAG Evaluation Harness" in markdown
    assert "golden set" in markdown
    assert "regression threshold" in markdown
