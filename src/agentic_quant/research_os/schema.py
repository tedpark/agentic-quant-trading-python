from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchArtifact:
    id: str
    title: str
    source_path: str
    artifact_type: str
    text: str


@dataclass(frozen=True)
class ResearchChunk:
    id: str
    artifact_id: str
    title: str
    heading: str
    source_path: str
    text: str


@dataclass(frozen=True)
class ResearchCitation:
    chunk_id: str
    source_path: str
    heading: str


@dataclass(frozen=True)
class ResearchAnswer:
    question: str
    answer: str
    citations: tuple[ResearchCitation, ...]
    next_actions: tuple[str, ...]

    def to_markdown(self) -> str:
        lines = [
            "# QuantSigma Research OS Sample Answer",
            "",
            f"## Question",
            "",
            self.question,
            "",
            "## Answer",
            "",
            self.answer,
            "",
            "## Citations",
            "",
        ]
        for citation in self.citations:
            lines.append(f"- `{citation.chunk_id}`: {citation.source_path} / {citation.heading}")
        lines.extend(["", "## Next Actions", ""])
        lines.extend(f"- {action}" for action in self.next_actions)
        return "\n".join(lines) + "\n"
