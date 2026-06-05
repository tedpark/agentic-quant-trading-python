from __future__ import annotations

from collections import Counter
from re import findall
from typing import Sequence

from agentic_quant.research_os.schema import ResearchChunk


def search_index(query: str, chunks: Sequence[ResearchChunk], *, limit: int = 3) -> tuple[ResearchChunk, ...]:
    if limit <= 0:
        raise ValueError("limit must be positive")

    query_terms = _terms(query)
    scored: list[tuple[float, ResearchChunk]] = []
    for chunk in chunks:
        score = _score(query_terms, chunk)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda item: (-item[0], item[1].source_path, item[1].heading))
    return tuple(chunk for _, chunk in scored[:limit])


def _score(query_terms: Counter[str], chunk: ResearchChunk) -> float:
    if not query_terms:
        return 0.0

    body_terms = _terms(f"{chunk.title} {chunk.heading} {chunk.text}")
    overlap = sum(min(count, body_terms.get(term, 0)) for term, count in query_terms.items())
    if overlap == 0:
        return 0.0

    heading_bonus = sum(count for term, count in query_terms.items() if term in _terms(chunk.heading))
    return overlap + (heading_bonus * 1.5)


def _terms(text: str) -> Counter[str]:
    return Counter(token for token in findall(r"[a-zA-Z0-9]+", text.lower()) if len(token) >= 2)
