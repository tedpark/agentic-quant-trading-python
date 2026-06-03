from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Sequence


@dataclass(frozen=True)
class NumeraiTournamentPrediction:
    identifier: str
    prediction: float


@dataclass(frozen=True)
class NumeraiSignalsPrediction:
    ticker: str
    signal: float
    ticker_column: str = "numerai_ticker"


def rank_to_unit_interval(values: Sequence[float]) -> tuple[float, ...]:
    """Convert raw scores to deterministic values in the open interval (0, 1)."""
    if not values:
        raise ValueError("values must not be empty")
    if any(not isfinite(value) for value in values):
        raise ValueError("values must be finite")

    ordered = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranked = [0.0] * len(values)
    denominator = len(values) + 1
    for rank, (index, _) in enumerate(ordered, start=1):
        ranked[index] = rank / denominator
    return tuple(ranked)


def validate_tournament_predictions(
    predictions: Sequence[NumeraiTournamentPrediction],
    *,
    min_rows: int = 1,
) -> None:
    if len(predictions) < min_rows:
        raise ValueError(f"expected at least {min_rows} predictions")

    seen: set[str] = set()
    for row in predictions:
        if not row.identifier:
            raise ValueError("identifier must not be empty")
        if row.identifier in seen:
            raise ValueError(f"duplicate identifier: {row.identifier}")
        seen.add(row.identifier)
        if not isfinite(row.prediction):
            raise ValueError(f"prediction must be finite for {row.identifier}")
        if row.prediction < 0.0 or row.prediction > 1.0:
            raise ValueError(f"prediction must be between 0 and 1 for {row.identifier}")


def validate_signals_predictions(
    predictions: Sequence[NumeraiSignalsPrediction],
    *,
    min_tickers: int = 100,
) -> None:
    if len(predictions) < min_tickers:
        raise ValueError(f"expected at least {min_tickers} signal rows")

    ticker_columns = {row.ticker_column for row in predictions}
    if len(ticker_columns) != 1:
        raise ValueError("all signal rows must use the same ticker column")
    ticker_column = next(iter(ticker_columns))
    if ticker_column not in {
        "cusip",
        "sedol",
        "bloomberg_ticker",
        "composite_figi",
        "numerai_ticker",
    }:
        raise ValueError(f"unsupported ticker column: {ticker_column}")

    seen: set[str] = set()
    for row in predictions:
        if not row.ticker:
            raise ValueError("ticker must not be empty")
        if row.ticker in seen:
            raise ValueError(f"duplicate ticker: {row.ticker}")
        seen.add(row.ticker)
        if not isfinite(row.signal):
            raise ValueError(f"signal must be finite for {row.ticker}")
        if row.signal <= 0.0 or row.signal >= 1.0:
            raise ValueError(f"signal must be in the open interval (0, 1) for {row.ticker}")


def format_tournament_csv(predictions: Sequence[NumeraiTournamentPrediction]) -> str:
    validate_tournament_predictions(predictions)
    return _write_csv(("id", "prediction"), ((row.identifier, row.prediction) for row in predictions))


def format_signals_csv(
    predictions: Sequence[NumeraiSignalsPrediction],
    *,
    min_tickers: int = 100,
) -> str:
    validate_signals_predictions(predictions, min_tickers=min_tickers)
    ticker_column = predictions[0].ticker_column
    return _write_csv((ticker_column, "signal"), ((row.ticker, row.signal) for row in predictions))


def synthetic_tournament_predictions(length: int = 120) -> tuple[NumeraiTournamentPrediction, ...]:
    if length <= 0:
        raise ValueError("length must be positive")
    raw_scores = [((index * 37) % 101) / 100 + (index % 7) * 0.001 for index in range(length)]
    ranked = rank_to_unit_interval(raw_scores)
    return tuple(
        NumeraiTournamentPrediction(identifier=f"n{index:05d}", prediction=score)
        for index, score in enumerate(ranked)
    )


def synthetic_signals_predictions(length: int = 120) -> tuple[NumeraiSignalsPrediction, ...]:
    if length < 100:
        raise ValueError("length must be at least 100 for a valid Signals-style live sample")
    raw_scores = [((index * 17) % 89) / 88 + (index % 5) * 0.0005 for index in range(length)]
    ranked = rank_to_unit_interval(raw_scores)
    return tuple(
        NumeraiSignalsPrediction(ticker=f"US{index:05d}", signal=score)
        for index, score in enumerate(ranked)
    )


def render_numerai_markdown() -> str:
    tournament_rows = synthetic_tournament_predictions()
    signals_rows = synthetic_signals_predictions()
    tournament_csv = format_tournament_csv(tournament_rows).splitlines()
    signals_csv = format_signals_csv(signals_rows).splitlines()

    lines = [
        "# Numerai Public Benchmark Trail",
        "",
        "This note prepares the first external benchmark layer for the public financial ML portfolio.",
        "It does not submit predictions, stake NMR, or claim performance.",
        "",
        "## Why This Exists",
        "",
        "The existing public repo already shows validation, serving, monitoring, and experiment logs.",
        "Numerai adds an external benchmark trail that recruiters can understand quickly.",
        "",
        "## Current Format Assumptions",
        "",
        "- Numerai Tournament submissions use an `id` column and a `prediction` column.",
        "- Tournament predictions are float values between 0 and 1.",
        "- Numerai Signals submissions use a valid ticker column and a `signal` column.",
        "- Signals values must be in the open interval `(0, 1)`.",
        "- Live Signals submissions need at least 100 valid universe tickers.",
        "",
        "## Public / Private Boundary",
        "",
        "Public:",
        "",
        "- submission format validation",
        "- synthetic examples",
        "- validation notes",
        "- tracker updates",
        "- first-submission receipt once created",
        "",
        "Private:",
        "",
        "- live trading rules",
        "- broker integration",
        "- account details",
        "- private alpha features",
        "- exact production thresholds",
        "",
        "## Synthetic Tournament CSV Preview",
        "",
        "```csv",
        *tournament_csv[:6],
        "```",
        "",
        "## Synthetic Signals CSV Preview",
        "",
        "```csv",
        *signals_csv[:6],
        "```",
        "",
        "## Next Manual Step",
        "",
        "1. Create or confirm Numerai account.",
        "2. Create a model id.",
        "3. Generate a real live prediction file from the current Numerai live dataset.",
        "4. Upload manually first.",
        "5. Record the receipt in `2026/trackers/numerai_progress.csv`.",
        "",
        "## Interview Message",
        "",
        "The goal of this step is not to overclaim a score.",
        "The goal is to create an external, reproducible benchmark trail for financial ML validation.",
    ]
    return "\n".join(lines) + "\n"


def _write_csv(header: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return output.getvalue()
