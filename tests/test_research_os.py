from __future__ import annotations

from pathlib import Path

import pytest

from agentic_quant.research_os import answer_question, build_research_index, plan_experiment, search_index


def test_research_index_splits_markdown_sections(tmp_path: Path) -> None:
    doc = tmp_path / "artifact.md"
    doc.write_text(
        "# Research Note\n\n"
        "Overview text.\n\n"
        "## HMM Regime Features\n\n"
        "Regime models must be fit on training windows only.\n\n"
        "## Walk-forward Validation\n\n"
        "Thresholds are selected on validation windows before test metrics are reported.\n",
        encoding="utf-8",
    )

    chunks = build_research_index([doc])

    assert len(chunks) == 3
    assert chunks[1].heading == "HMM Regime Features"
    assert "training windows only" in chunks[1].text


def test_search_returns_relevant_chunk_first(tmp_path: Path) -> None:
    doc = tmp_path / "artifact.md"
    doc.write_text(
        "# Research Note\n\n"
        "## Serving\n\n"
        "Checkpoint reloads need smoke tests.\n\n"
        "## Leakage-aware Validation\n\n"
        "Walk-forward validation keeps train and test windows time ordered.\n",
        encoding="utf-8",
    )
    chunks = build_research_index([doc])

    results = search_index("financial ML validation leakage walk-forward", chunks, limit=1)

    assert results[0].heading == "Leakage-aware Validation"


def test_copilot_answer_contains_citations(tmp_path: Path) -> None:
    doc = tmp_path / "artifact.md"
    doc.write_text(
        "# Research Note\n\n"
        "## RAG Evaluation\n\n"
        "Citation coverage and answer-support checks make RAG changes testable.\n",
        encoding="utf-8",
    )
    chunks = build_research_index([doc])

    answer = answer_question("How should RAG changes be evaluated?", chunks)

    assert "Citation coverage" in answer.answer
    assert answer.citations
    assert "answer-support" in answer.to_markdown()


def test_planner_creates_regime_aware_plan() -> None:
    plan = plan_experiment("HMM regime features improve pair spread entries")

    assert plan.run_id
    assert any("HMM-style regime label" == feature for feature in plan.feature_candidates)
    assert any("purging and embargo" in protocol for protocol in plan.validation_protocol)
    assert "CVaR" in plan.to_markdown()


def test_empty_idea_is_rejected() -> None:
    with pytest.raises(ValueError, match="idea"):
        plan_experiment("")
