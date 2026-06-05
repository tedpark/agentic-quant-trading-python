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
class ResearchNode:
    id: str
    label: str
    kind: str
    source_chunk_ids: tuple[str, ...]


@dataclass(frozen=True)
class ResearchEdge:
    source_id: str
    target_id: str
    relation: str


@dataclass(frozen=True)
class ResearchGraph:
    nodes: tuple[ResearchNode, ...]
    edges: tuple[ResearchEdge, ...]

    def nodes_by_kind(self, kind: str) -> tuple[ResearchNode, ...]:
        return tuple(node for node in self.nodes if node.kind == kind)

    def to_markdown(self) -> str:
        lines = [
            "# Research Graph",
            "",
            "## Nodes",
            "",
            "| Node | Kind | Evidence chunks |",
            "|---|---|---|",
        ]
        for node in self.nodes:
            evidence = ", ".join(f"`{chunk_id}`" for chunk_id in node.source_chunk_ids)
            lines.append(f"| {node.label} | `{node.kind}` | {evidence} |")

        lines.extend(["", "## Edges", "", "| Source | Relation | Target |", "|---|---|---|"])
        labels = {node.id: node.label for node in self.nodes}
        for edge in self.edges:
            lines.append(f"| {labels[edge.source_id]} | `{edge.relation}` | {labels[edge.target_id]} |")
        return "\n".join(lines) + "\n"


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
