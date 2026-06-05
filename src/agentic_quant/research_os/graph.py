from __future__ import annotations

from collections import defaultdict
from re import sub
from typing import Sequence

from agentic_quant.research_os.schema import ResearchChunk, ResearchEdge, ResearchGraph, ResearchNode


CONCEPT_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("validation:walk-forward", "Walk-forward validation", "validation", ("walk-forward", "walk forward")),
    ("validation:purged-embargo", "Purged / embargoed validation", "validation", ("purged", "embargo")),
    ("feature:hmm-regime", "HMM-style regime feature", "feature", ("hmm", "regime")),
    ("feature:cointegration-spread", "Cointegration spread feature", "feature", ("cointegration", "spread", "pair")),
    ("risk:cvar", "CVaR / Expected Shortfall", "risk", ("cvar", "expected shortfall", "tail risk")),
    ("model:qr-dqn", "QR-DQN distributional RL", "model", ("qr-dqn", "qrdqn", "distributional rl")),
    ("system:rag-evaluation", "RAG evaluation harness", "system", ("rag", "citation", "answer-support")),
    ("system:model-serving", "Validation-first model serving", "system", ("serving", "checkpoint", "reload")),
)

RELATION_RULES: tuple[tuple[str, str, str], ...] = (
    ("feature:hmm-regime", "validation:walk-forward", "must_be_validated_with"),
    ("feature:hmm-regime", "validation:purged-embargo", "needs_leakage_control"),
    ("feature:cointegration-spread", "validation:walk-forward", "must_be_validated_with"),
    ("model:qr-dqn", "risk:cvar", "optimizes_tail_risk_with"),
    ("system:rag-evaluation", "validation:walk-forward", "uses_regression_style_checks_like"),
    ("system:model-serving", "system:rag-evaluation", "should_be_tested_before_shipping_like"),
)


def build_research_graph(chunks: Sequence[ResearchChunk]) -> ResearchGraph:
    evidence: dict[str, set[str]] = defaultdict(set)
    for chunk in chunks:
        searchable = f"{chunk.title} {chunk.heading} {chunk.text}".lower()
        for concept_id, _label, _kind, phrases in CONCEPT_RULES:
            if any(phrase in searchable for phrase in phrases):
                evidence[concept_id].add(chunk.id)

    nodes = tuple(
        ResearchNode(
            id=concept_id,
            label=label,
            kind=kind,
            source_chunk_ids=tuple(sorted(evidence[concept_id])),
        )
        for concept_id, label, kind, _phrases in CONCEPT_RULES
        if concept_id in evidence
    )
    node_ids = {node.id for node in nodes}
    edges = tuple(
        ResearchEdge(source_id=source_id, target_id=target_id, relation=relation)
        for source_id, target_id, relation in RELATION_RULES
        if source_id in node_ids and target_id in node_ids
    )
    return ResearchGraph(nodes=nodes, edges=edges)


def concept_slug(label: str) -> str:
    return sub(r"[^a-zA-Z0-9]+", "-", label.lower()).strip("-")
