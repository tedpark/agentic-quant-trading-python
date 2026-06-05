from __future__ import annotations

from pathlib import Path
from re import sub
from typing import Iterable

from agentic_quant.research_os.schema import ResearchArtifact, ResearchChunk


def build_research_index(paths: Iterable[Path | str]) -> tuple[ResearchChunk, ...]:
    artifacts = [_load_markdown_artifact(Path(path)) for path in paths]
    chunks: list[ResearchChunk] = []
    for artifact in artifacts:
        chunks.extend(_split_markdown_sections(artifact))
    return tuple(chunks)


def _load_markdown_artifact(path: Path) -> ResearchArtifact:
    text = path.read_text(encoding="utf-8")
    title = _first_heading(text) or path.stem.replace("_", " ").replace("-", " ").title()
    return ResearchArtifact(
        id=_slug(path.as_posix()),
        title=title,
        source_path=path.as_posix(),
        artifact_type="markdown",
        text=text,
    )


def _split_markdown_sections(artifact: ResearchArtifact) -> tuple[ResearchChunk, ...]:
    sections: list[tuple[str, list[str]]] = []
    current_heading = artifact.title
    current_lines: list[str] = []

    for line in artifact.text.splitlines():
        if line.startswith("#"):
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = line.lstrip("#").strip() or artifact.title
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, current_lines))

    chunks = []
    for index, (heading, lines) in enumerate(sections):
        text = _normalize("\n".join(lines))
        if not text:
            continue
        chunks.append(
            ResearchChunk(
                id=f"{artifact.id}::section-{index:03d}",
                artifact_id=artifact.id,
                title=artifact.title,
                heading=heading,
                source_path=artifact.source_path,
                text=text,
            )
        )
    return tuple(chunks)


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None


def _normalize(text: str) -> str:
    return sub(r"\s+", " ", text).strip()


def _slug(value: str) -> str:
    slug = sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "artifact"
