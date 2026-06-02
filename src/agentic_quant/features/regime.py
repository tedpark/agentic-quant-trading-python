from __future__ import annotations

from dataclasses import dataclass
from math import log, pi
from statistics import mean, pstdev
from typing import Sequence

from agentic_quant.validation.walk_forward import make_walk_forward_splits


@dataclass(frozen=True)
class MarketBar:
    timestamp: int
    close: float


@dataclass(frozen=True)
class FeatureRow:
    timestamp: int
    return_1d: float
    realized_volatility: float
    drawdown: float
    momentum_5: float


@dataclass(frozen=True)
class FeatureStandardizer:
    means: dict[str, float]
    scales: dict[str, float]

    def transform(self, row: FeatureRow) -> dict[str, float]:
        return {
            name: (value - self.means[name]) / self.scales[name]
            for name, value in _feature_values(row).items()
        }


@dataclass(frozen=True)
class GaussianRegimeState:
    name: str
    mean_return: float
    volatility: float


@dataclass(frozen=True)
class GaussianRegimeModel:
    states: tuple[GaussianRegimeState, ...]
    transition: tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class RegimeClassification:
    timestamp: int
    regime: str
    return_1d: float
    realized_volatility: float
    drawdown: float
    momentum_5: float


@dataclass(frozen=True)
class RegimeFoldResult:
    fold: int
    train_range: tuple[int, int]
    test_range: tuple[int, int]
    train_regime_counts: dict[str, int]
    test_regime_counts: dict[str, int]
    train_feature_means: dict[str, float]
    sample_test_rows: tuple[RegimeClassification, ...]


def _feature_values(row: FeatureRow) -> dict[str, float]:
    return {
        "return_1d": row.return_1d,
        "realized_volatility": row.realized_volatility,
        "drawdown": row.drawdown,
        "momentum_5": row.momentum_5,
    }


def build_feature_rows(
    bars: Sequence[MarketBar],
    *,
    volatility_window: int = 10,
    momentum_window: int = 5,
) -> tuple[FeatureRow, ...]:
    if volatility_window <= 1:
        raise ValueError("volatility_window must be greater than 1")
    if momentum_window <= 0:
        raise ValueError("momentum_window must be positive")
    if len(bars) <= max(volatility_window, momentum_window):
        raise ValueError("not enough bars for requested feature windows")

    returns = [0.0]
    for index in range(1, len(bars)):
        previous = bars[index - 1].close
        if previous <= 0:
            raise ValueError("close prices must be positive")
        returns.append(bars[index].close / previous - 1.0)

    rows: list[FeatureRow] = []
    running_high = bars[0].close
    start = max(volatility_window, momentum_window)
    for index, bar in enumerate(bars):
        running_high = max(running_high, bar.close)
        if index < start:
            continue

        volatility_slice = returns[index - volatility_window + 1 : index + 1]
        realized_volatility = pstdev(volatility_slice)
        drawdown = bar.close / running_high - 1.0
        momentum_5 = bar.close / bars[index - momentum_window].close - 1.0
        rows.append(
            FeatureRow(
                timestamp=bar.timestamp,
                return_1d=float(returns[index]),
                realized_volatility=float(realized_volatility),
                drawdown=float(drawdown),
                momentum_5=float(momentum_5),
            )
        )
    return tuple(rows)


def fit_standardizer(rows: Sequence[FeatureRow]) -> FeatureStandardizer:
    if not rows:
        raise ValueError("rows must not be empty")

    columns = {name: [values[name] for values in map(_feature_values, rows)] for name in _feature_values(rows[0])}
    means = {name: float(mean(values)) for name, values in columns.items()}
    scales = {name: float(pstdev(values) or 1.0) for name, values in columns.items()}
    return FeatureStandardizer(means=means, scales=scales)


def _initial_state_index(row: FeatureRow, median_volatility: float) -> int:
    if row.realized_volatility > median_volatility:
        return 1
    return 0


def fit_regime_model(rows: Sequence[FeatureRow]) -> GaussianRegimeModel:
    if len(rows) < 20:
        raise ValueError("at least 20 rows are required to fit regime model")

    volatilities = sorted(row.realized_volatility for row in rows)
    median_volatility = volatilities[len(volatilities) // 2]
    buckets: list[list[FeatureRow]] = [[], []]
    assignments: list[int] = []
    for row in rows:
        state_index = _initial_state_index(row, median_volatility)
        assignments.append(state_index)
        buckets[state_index].append(row)

    if not all(buckets):
        raise ValueError("training rows did not produce two volatility buckets")

    states = (
        GaussianRegimeState(
            name="low_vol",
            mean_return=float(mean(row.return_1d for row in buckets[0])),
            volatility=float(mean(row.realized_volatility for row in buckets[0]) or 1e-6),
        ),
        GaussianRegimeState(
            name="high_vol",
            mean_return=float(mean(row.return_1d for row in buckets[1])),
            volatility=float(mean(row.realized_volatility for row in buckets[1]) or 1e-6),
        ),
    )

    counts = [[1.0, 1.0], [1.0, 1.0]]
    for previous, current in zip(assignments, assignments[1:]):
        counts[previous][current] += 1.0
    transition = tuple(tuple(value / sum(row) for value in row) for row in counts)
    return GaussianRegimeModel(states=states, transition=transition)


def _emission_log_prob(row: FeatureRow, state: GaussianRegimeState) -> float:
    variance = max(state.volatility * state.volatility, 1e-8)
    centered = row.return_1d - state.mean_return
    return -0.5 * (log(2 * pi * variance) + centered * centered / variance)


def classify_regimes(rows: Sequence[FeatureRow], model: GaussianRegimeModel) -> tuple[RegimeClassification, ...]:
    if not rows:
        raise ValueError("rows must not be empty")

    state_count = len(model.states)
    scores = [[0.0] * state_count for _ in rows]
    backpointers = [[0] * state_count for _ in rows]
    for state_index, state in enumerate(model.states):
        scores[0][state_index] = log(1.0 / state_count) + _emission_log_prob(rows[0], state)

    for row_index in range(1, len(rows)):
        for state_index, state in enumerate(model.states):
            candidates = [
                scores[row_index - 1][previous_index]
                + log(model.transition[previous_index][state_index])
                + _emission_log_prob(rows[row_index], state)
                for previous_index in range(state_count)
            ]
            best_previous = max(range(state_count), key=lambda index: candidates[index])
            scores[row_index][state_index] = candidates[best_previous]
            backpointers[row_index][state_index] = best_previous

    path = [max(range(state_count), key=lambda index: scores[-1][index])]
    for row_index in range(len(rows) - 1, 0, -1):
        path.append(backpointers[row_index][path[-1]])
    path.reverse()

    return tuple(
        RegimeClassification(
            timestamp=row.timestamp,
            regime=model.states[state_index].name,
            return_1d=row.return_1d,
            realized_volatility=row.realized_volatility,
            drawdown=row.drawdown,
            momentum_5=row.momentum_5,
        )
        for row, state_index in zip(rows, path)
    )


def _count_regimes(rows: Sequence[RegimeClassification]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.regime] = counts.get(row.regime, 0) + 1
    return counts


def run_regime_feature_pipeline(
    bars: Sequence[MarketBar],
    *,
    train_size: int,
    validation_size: int,
    test_size: int,
    step_size: int | None = None,
) -> tuple[RegimeFoldResult, ...]:
    features = build_feature_rows(bars)
    splits = make_walk_forward_splits(
        len(features),
        train_size=train_size,
        validation_size=validation_size,
        test_size=test_size,
        step_size=step_size,
    )

    results: list[RegimeFoldResult] = []
    for split in splits:
        train = features[split.train_start : split.train_end]
        test = features[split.test_start : split.test_end]
        standardizer = fit_standardizer(train)
        model = fit_regime_model(train)
        train_classified = classify_regimes(train, model)
        test_classified = classify_regimes(test, model)
        results.append(
            RegimeFoldResult(
                fold=split.fold,
                train_range=(train[0].timestamp, train[-1].timestamp),
                test_range=(test[0].timestamp, test[-1].timestamp),
                train_regime_counts=_count_regimes(train_classified),
                test_regime_counts=_count_regimes(test_classified),
                train_feature_means=standardizer.means,
                sample_test_rows=tuple(test_classified[:5]),
            )
        )
    return tuple(results)


def synthetic_market_bars(length: int = 220) -> tuple[MarketBar, ...]:
    if length < 80:
        raise ValueError("length must be at least 80")

    close = 100.0
    bars: list[MarketBar] = []
    for index in range(length):
        regime = index // 55
        drift = (0.0008, -0.0005, 0.0003, -0.0002)[regime % 4]
        volatility = (0.004, 0.012, 0.006, 0.016)[regime % 4]
        deterministic_noise = (((index * 17) % 23) - 11) / 11
        shock = deterministic_noise * volatility
        close = max(1.0, close * (1.0 + drift + shock))
        bars.append(MarketBar(timestamp=index, close=float(close)))
    return tuple(bars)
