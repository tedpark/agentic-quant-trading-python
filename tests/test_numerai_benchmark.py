from __future__ import annotations

import pytest

from agentic_quant.benchmarks.numerai import (
    NumeraiSignalsPrediction,
    NumeraiTournamentPrediction,
    format_signals_csv,
    format_tournament_csv,
    rank_to_unit_interval,
    render_numerai_markdown,
    synthetic_signals_predictions,
    synthetic_tournament_predictions,
    validate_signals_predictions,
    validate_tournament_predictions,
)


def test_rank_to_unit_interval_is_strictly_between_zero_and_one() -> None:
    ranked = rank_to_unit_interval([3.0, 1.0, 2.0])

    assert ranked == (0.75, 0.25, 0.5)
    assert all(0.0 < value < 1.0 for value in ranked)


def test_tournament_predictions_validate_and_format_csv() -> None:
    rows = synthetic_tournament_predictions(length=3)

    validate_tournament_predictions(rows)
    csv_text = format_tournament_csv(rows)

    assert csv_text.splitlines()[0] == "id,prediction"
    assert csv_text.count("\n") == 4


def test_tournament_predictions_reject_duplicate_ids() -> None:
    rows = (
        NumeraiTournamentPrediction("n00001", 0.2),
        NumeraiTournamentPrediction("n00001", 0.8),
    )

    with pytest.raises(ValueError, match="duplicate identifier"):
        validate_tournament_predictions(rows)


def test_signals_predictions_validate_and_format_csv() -> None:
    rows = synthetic_signals_predictions(length=100)

    validate_signals_predictions(rows)
    csv_text = format_signals_csv(rows)

    assert csv_text.splitlines()[0] == "numerai_ticker,signal"
    assert csv_text.count("\n") == 101


def test_signals_predictions_reject_too_few_tickers() -> None:
    rows = (
        NumeraiSignalsPrediction("US00001", 0.2),
        NumeraiSignalsPrediction("US00002", 0.8),
    )

    with pytest.raises(ValueError, match="expected at least 100"):
        validate_signals_predictions(rows)


def test_signals_predictions_reject_closed_interval_values() -> None:
    rows = tuple(
        NumeraiSignalsPrediction(f"US{index:05d}", 0.5)
        for index in range(99)
    ) + (NumeraiSignalsPrediction("US99999", 1.0),)

    with pytest.raises(ValueError, match="open interval"):
        validate_signals_predictions(rows)


def test_render_numerai_markdown_includes_boundary_and_csv_previews() -> None:
    markdown = render_numerai_markdown()

    assert "# Numerai Public Benchmark Trail" in markdown
    assert "Public / Private Boundary" in markdown
    assert "id,prediction" in markdown
    assert "numerai_ticker,signal" in markdown
