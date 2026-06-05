from __future__ import annotations

from typing import Sequence

from agentic_quant.research_os.schema import ResearchAnswer, ResearchChunk, ResearchCitation
from agentic_quant.research_os.search import search_index


def answer_question(question: str, chunks: Sequence[ResearchChunk], *, limit: int = 3) -> ResearchAnswer:
    retrieved = search_index(question, chunks, limit=limit)
    if not retrieved:
        return ResearchAnswer(
            question=question,
            answer="No supported answer was produced because the research index did not contain matching evidence.",
            citations=(),
            next_actions=("Add a relevant artifact to the research index.",),
        )

    evidence_lines = []
    citations = []
    for chunk in retrieved:
        evidence_lines.append(f"- {chunk.heading}: {_shorten(chunk.text)} [{chunk.id}]")
        citations.append(ResearchCitation(chunk_id=chunk.id, source_path=chunk.source_path, heading=chunk.heading))

    return ResearchAnswer(
        question=question,
        answer="\n".join(evidence_lines),
        citations=tuple(citations),
        next_actions=_next_actions(question),
    )


def _shorten(text: str, *, max_chars: int = 260) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _next_actions(question: str) -> tuple[str, ...]:
    normalized = question.lower()
    actions = [
        "Turn the answer into an experiment manifest before changing model code.",
        "Check leakage controls before trusting any financial ML result.",
    ]
    if "regime" in normalized or "hmm" in normalized:
        actions.append("Compare metrics by regime, not only aggregate return.")
    if "rag" in normalized or "llm" in normalized:
        actions.append("Run citation coverage and answer-support checks before publishing.")
    return tuple(actions)
