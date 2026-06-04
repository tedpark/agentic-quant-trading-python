from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import mean
from typing import Sequence


@dataclass(frozen=True)
class Context:
    id: str
    text: str


@dataclass(frozen=True)
class GoldenQuestion:
    id: str
    question: str
    ground_truth: str
    relevant_context_ids: tuple[str, ...]
    category: str


@dataclass(frozen=True)
class RagAnswer:
    question_id: str
    answer: str
    retrieved_contexts: tuple[Context, ...]
    citations: tuple[str, ...]


@dataclass(frozen=True)
class RagEvaluationRow:
    question_id: str
    category: str
    retrieved_count: int
    relevant_retrieved: int
    context_precision: float
    context_recall: float
    hit_rate: float
    mrr: float
    citation_coverage: float
    answer_support: float


@dataclass(frozen=True)
class EvaluationReport:
    rows: tuple[RagEvaluationRow, ...]

    def metric_means(self) -> dict[str, float]:
        if not self.rows:
            return {
                "context_precision": 0.0,
                "context_recall": 0.0,
                "hit_rate": 0.0,
                "mrr": 0.0,
                "citation_coverage": 0.0,
                "answer_support": 0.0,
            }

        return {
            "context_precision": _round(mean(row.context_precision for row in self.rows)),
            "context_recall": _round(mean(row.context_recall for row in self.rows)),
            "hit_rate": _round(mean(row.hit_rate for row in self.rows)),
            "mrr": _round(mean(row.mrr for row in self.rows)),
            "citation_coverage": _round(mean(row.citation_coverage for row in self.rows)),
            "answer_support": _round(mean(row.answer_support for row in self.rows)),
        }

    def to_markdown(self) -> str:
        metrics = self.metric_means()
        lines = [
            "# RAG Evaluation Harness",
            "",
            "This public sample evaluates a small RAG run with a golden set.",
            "It uses deterministic metrics and synthetic content only, so it can run in CI without API keys.",
            "",
            "## Summary",
            "",
            "| Metric | Mean | What it checks |",
            "|---|---:|---|",
            f"| Context precision | {metrics['context_precision']:.3f} | Relevant contexts among retrieved contexts |",
            f"| Context recall | {metrics['context_recall']:.3f} | Required contexts recovered from the golden set |",
            f"| Hit rate | {metrics['hit_rate']:.3f} | Whether at least one relevant context was retrieved |",
            f"| MRR | {metrics['mrr']:.3f} | Rank of the first relevant retrieved context |",
            f"| Citation coverage | {metrics['citation_coverage']:.3f} | Whether cited sources cover required sources |",
            f"| Answer support | {metrics['answer_support']:.3f} | Token overlap between answer and retrieved evidence |",
            "",
            "## Per-question Results",
            "",
            "| Question | Category | Precision | Recall | Hit | MRR | Citation Coverage | Answer Support |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for row in self.rows:
            lines.append(
                "| "
                f"{row.question_id} | {row.category} | {row.context_precision:.3f} | "
                f"{row.context_recall:.3f} | {row.hit_rate:.3f} | {row.mrr:.3f} | "
                f"{row.citation_coverage:.3f} | {row.answer_support:.3f} |"
            )
        lines.extend(
            [
                "",
                "## Interview Message",
                "",
                "For RAG systems, I do not rely on demo quality alone.",
                "I want a golden set, retrieval metrics, citation checks, answer-support checks,",
                "and a regression threshold that can run before prompt or retriever changes ship.",
            ]
        )
        return "\n".join(lines) + "\n"


def evaluate_rag_run(
    golden_questions: Sequence[GoldenQuestion],
    answers: Sequence[RagAnswer],
) -> EvaluationReport:
    golden_by_id = {question.id: question for question in golden_questions}
    answer_by_id = {answer.question_id: answer for answer in answers}
    missing = sorted(set(golden_by_id) - set(answer_by_id))
    if missing:
        raise ValueError(f"missing answers for golden questions: {missing}")

    rows = []
    for question in golden_questions:
        answer = answer_by_id[question.id]
        rows.append(_evaluate_row(question, answer))
    return EvaluationReport(rows=tuple(rows))


def sample_rag_run() -> tuple[tuple[GoldenQuestion, ...], tuple[RagAnswer, ...]]:
    contexts = {
        "doc:walk-forward": Context(
            id="doc:walk-forward",
            text=(
                "Walk-forward validation trains on past windows, selects thresholds on validation windows, "
                "and reports untouched test-window metrics."
            ),
        ),
        "doc:purged": Context(
            id="doc:purged",
            text=(
                "Purged validation removes training labels that overlap the test label interval, "
                "then applies an embargo after the test window."
            ),
        ),
        "doc:hot-reload": Context(
            id="doc:hot-reload",
            text=(
                "A validation-first checkpoint reload loads a candidate model, runs smoke checks, "
                "and swaps it atomically only after validation passes."
            ),
        ),
        "doc:drift": Context(
            id="doc:drift",
            text=(
                "Feature drift monitoring compares reference and current distributions with PSI and KS metrics."
            ),
        ),
        "doc:risk": Context(
            id="doc:risk",
            text=(
                "CVaR-style risk evaluation focuses on left-tail outcomes rather than only average return."
            ),
        ),
    }
    golden = (
        GoldenQuestion(
            id="q001",
            question="Why is walk-forward validation useful for financial ML?",
            ground_truth="It keeps training, validation, and test windows time ordered and leaves test metrics untouched.",
            relevant_context_ids=("doc:walk-forward",),
            category="validation",
        ),
        GoldenQuestion(
            id="q002",
            question="What problem does purging and embargo handle?",
            ground_truth="It controls label-overlap leakage around a held-out test interval.",
            relevant_context_ids=("doc:purged",),
            category="leakage",
        ),
        GoldenQuestion(
            id="q003",
            question="How should a checkpoint reload be made safer?",
            ground_truth="Load a candidate first, smoke-test it, then atomically swap only after validation passes.",
            relevant_context_ids=("doc:hot-reload",),
            category="serving",
        ),
        GoldenQuestion(
            id="q004",
            question="Which metrics can show feature drift?",
            ground_truth="PSI and KS can compare reference and current feature distributions.",
            relevant_context_ids=("doc:drift",),
            category="monitoring",
        ),
        GoldenQuestion(
            id="q005",
            question="Why track CVaR-style risk?",
            ground_truth="It focuses on left-tail outcomes, not only average return.",
            relevant_context_ids=("doc:risk",),
            category="risk",
        ),
    )
    answers = (
        RagAnswer(
            question_id="q001",
            answer="Walk-forward validation keeps time windows ordered and reports untouched test metrics. [doc:walk-forward]",
            retrieved_contexts=(contexts["doc:walk-forward"], contexts["doc:drift"]),
            citations=("doc:walk-forward",),
        ),
        RagAnswer(
            question_id="q002",
            answer="Purging removes overlapping training labels and embargo handles samples after the test window. [doc:purged]",
            retrieved_contexts=(contexts["doc:purged"], contexts["doc:walk-forward"]),
            citations=("doc:purged",),
        ),
        RagAnswer(
            question_id="q003",
            answer="A safer reload validates a candidate checkpoint with smoke checks before an atomic swap. [doc:hot-reload]",
            retrieved_contexts=(contexts["doc:hot-reload"], contexts["doc:risk"]),
            citations=("doc:hot-reload",),
        ),
        RagAnswer(
            question_id="q004",
            answer="Feature drift can be checked with PSI and KS over reference and current distributions. [doc:drift]",
            retrieved_contexts=(contexts["doc:drift"], contexts["doc:risk"]),
            citations=("doc:drift",),
        ),
        RagAnswer(
            question_id="q005",
            answer="CVaR-style risk focuses on left-tail outcomes rather than average return alone. [doc:risk]",
            retrieved_contexts=(contexts["doc:risk"], contexts["doc:hot-reload"]),
            citations=("doc:risk",),
        ),
    )
    return golden, answers


def _evaluate_row(question: GoldenQuestion, answer: RagAnswer) -> RagEvaluationRow:
    if not question.relevant_context_ids:
        raise ValueError(f"question {question.id} must define at least one relevant context")
    if not answer.retrieved_contexts:
        raise ValueError(f"answer {question.id} must include at least one retrieved context")

    relevant = set(question.relevant_context_ids)
    retrieved_ids = tuple(context.id for context in answer.retrieved_contexts)
    retrieved_relevant = tuple(context_id for context_id in retrieved_ids if context_id in relevant)
    cited_relevant = tuple(context_id for context_id in answer.citations if context_id in relevant)
    first_relevant_rank = _first_relevant_rank(retrieved_ids, relevant)

    return RagEvaluationRow(
        question_id=question.id,
        category=question.category,
        retrieved_count=len(retrieved_ids),
        relevant_retrieved=len(retrieved_relevant),
        context_precision=_round(len(retrieved_relevant) / len(retrieved_ids)),
        context_recall=_round(len(set(retrieved_relevant)) / len(relevant)),
        hit_rate=1.0 if retrieved_relevant else 0.0,
        mrr=_round(1.0 / first_relevant_rank if first_relevant_rank else 0.0),
        citation_coverage=_round(len(set(cited_relevant)) / len(relevant)),
        answer_support=_round(_answer_support(answer.answer, answer.retrieved_contexts)),
    )


def _first_relevant_rank(retrieved_ids: Sequence[str], relevant_ids: set[str]) -> int | None:
    for index, context_id in enumerate(retrieved_ids, start=1):
        if context_id in relevant_ids:
            return index
    return None


def _answer_support(answer: str, contexts: Sequence[Context]) -> float:
    answer_terms = _content_terms(answer)
    if not answer_terms:
        return 0.0
    evidence_terms = set()
    for context in contexts:
        evidence_terms.update(_content_terms(context.text))
    if not evidence_terms:
        return 0.0
    return len(answer_terms & evidence_terms) / len(answer_terms)


def _content_terms(text: str) -> set[str]:
    stopwords = {
        "a",
        "after",
        "an",
        "and",
        "be",
        "before",
        "can",
        "it",
        "only",
        "on",
        "or",
        "rather",
        "than",
        "the",
        "to",
        "with",
    }
    terms = {
        token.strip(".,:;!?()[]{}\"'").lower()
        for token in text.replace("-", " ").split()
    }
    return {term for term in terms if len(term) > 2 and term not in stopwords}


def _round(value: float) -> float:
    if not isfinite(value):
        return 0.0
    return round(float(value), 4)
