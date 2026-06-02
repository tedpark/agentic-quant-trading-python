from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean, pstdev
from typing import Sequence


@dataclass(frozen=True)
class Observation:
    timestamp: int
    feature: float
    forward_return: float


@dataclass(frozen=True)
class WalkForwardSplit:
    fold: int
    train_start: int
    train_end: int
    validation_start: int
    validation_end: int
    test_start: int
    test_end: int


@dataclass(frozen=True)
class Standardizer:
    mean: float
    scale: float

    def transform(self, value: float) -> float:
        return (value - self.mean) / self.scale


@dataclass(frozen=True)
class StrategyMetrics:
    observations: int
    mean_return: float
    hit_rate: float
    turnover: float
    sharpe: float


@dataclass(frozen=True)
class FoldResult:
    fold: int
    train_range: tuple[int, int]
    validation_range: tuple[int, int]
    test_range: tuple[int, int]
    train_mean: float
    train_scale: float
    selected_threshold: float
    validation_score: float
    test_metrics: StrategyMetrics


def make_walk_forward_splits(
    data_length: int,
    *,
    train_size: int,
    validation_size: int,
    test_size: int,
    step_size: int | None = None,
) -> tuple[WalkForwardSplit, ...]:
    if min(data_length, train_size, validation_size, test_size) <= 0:
        raise ValueError("data_length and window sizes must be positive")

    step = step_size or test_size
    if step <= 0:
        raise ValueError("step_size must be positive")

    splits: list[WalkForwardSplit] = []
    start = 0
    fold = 1
    total_window = train_size + validation_size + test_size
    while start + total_window <= data_length:
        train_start = start
        train_end = train_start + train_size
        validation_start = train_end
        validation_end = validation_start + validation_size
        test_start = validation_end
        test_end = test_start + test_size
        splits.append(
            WalkForwardSplit(
                fold=fold,
                train_start=train_start,
                train_end=train_end,
                validation_start=validation_start,
                validation_end=validation_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        start += step
        fold += 1

    if not splits:
        raise ValueError("window sizes are too large for the dataset")
    return tuple(splits)


def assert_time_ordered_split(split: WalkForwardSplit) -> None:
    if not split.train_start < split.train_end <= split.validation_start < split.validation_end <= split.test_start < split.test_end:
        raise ValueError(f"fold {split.fold} is not time ordered")


def fit_standardizer(observations: Sequence[Observation]) -> Standardizer:
    if not observations:
        raise ValueError("training observations must not be empty")

    values = [row.feature for row in observations]
    scale = pstdev(values)
    if scale == 0:
        scale = 1.0
    return Standardizer(mean=float(mean(values)), scale=float(scale))


def strategy_return(z_score: float, forward_return: float, threshold: float, *, transaction_cost: float) -> float:
    if abs(z_score) < threshold:
        return 0.0
    direction = 1.0 if z_score > 0 else -1.0
    return direction * forward_return - transaction_cost


def evaluate_threshold(
    observations: Sequence[Observation],
    standardizer: Standardizer,
    *,
    threshold: float,
    transaction_cost: float,
) -> StrategyMetrics:
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    if transaction_cost < 0:
        raise ValueError("transaction_cost must be non-negative")
    if not observations:
        raise ValueError("observations must not be empty")

    returns = [
        strategy_return(
            standardizer.transform(row.feature),
            row.forward_return,
            threshold,
            transaction_cost=transaction_cost,
        )
        for row in observations
    ]
    non_zero = [value for value in returns if value != 0.0]
    return_std = pstdev(returns)
    sharpe = 0.0 if return_std == 0 else mean(returns) / return_std * sqrt(252)
    hit_rate = 0.0 if not non_zero else sum(value > 0 for value in non_zero) / len(non_zero)
    return StrategyMetrics(
        observations=len(observations),
        mean_return=float(mean(returns)),
        hit_rate=float(hit_rate),
        turnover=len(non_zero) / len(observations),
        sharpe=float(sharpe),
    )


def select_threshold(
    validation: Sequence[Observation],
    standardizer: Standardizer,
    *,
    thresholds: Sequence[float],
    transaction_cost: float,
) -> tuple[float, StrategyMetrics]:
    if not thresholds:
        raise ValueError("thresholds must not be empty")

    scored = [
        (
            float(threshold),
            evaluate_threshold(
                validation,
                standardizer,
                threshold=float(threshold),
                transaction_cost=transaction_cost,
            ),
        )
        for threshold in thresholds
    ]
    return max(scored, key=lambda item: (item[1].mean_return, item[1].sharpe, -item[0]))


def run_walk_forward_validation(
    observations: Sequence[Observation],
    *,
    train_size: int,
    validation_size: int,
    test_size: int,
    thresholds: Sequence[float],
    transaction_cost: float = 0.0005,
    step_size: int | None = None,
) -> tuple[FoldResult, ...]:
    splits = make_walk_forward_splits(
        len(observations),
        train_size=train_size,
        validation_size=validation_size,
        test_size=test_size,
        step_size=step_size,
    )

    results: list[FoldResult] = []
    for split in splits:
        assert_time_ordered_split(split)
        train = observations[split.train_start : split.train_end]
        validation = observations[split.validation_start : split.validation_end]
        test = observations[split.test_start : split.test_end]

        standardizer = fit_standardizer(train)
        selected_threshold, validation_metrics = select_threshold(
            validation,
            standardizer,
            thresholds=thresholds,
            transaction_cost=transaction_cost,
        )
        test_metrics = evaluate_threshold(
            test,
            standardizer,
            threshold=selected_threshold,
            transaction_cost=transaction_cost,
        )
        results.append(
            FoldResult(
                fold=split.fold,
                train_range=(train[0].timestamp, train[-1].timestamp),
                validation_range=(validation[0].timestamp, validation[-1].timestamp),
                test_range=(test[0].timestamp, test[-1].timestamp),
                train_mean=standardizer.mean,
                train_scale=standardizer.scale,
                selected_threshold=selected_threshold,
                validation_score=validation_metrics.mean_return,
                test_metrics=test_metrics,
            )
        )
    return tuple(results)


def synthetic_regime_observations(length: int = 180) -> tuple[Observation, ...]:
    if length < 60:
        raise ValueError("length must be at least 60")

    rows: list[Observation] = []
    for index in range(length):
        regime = index // 60
        drift = (regime - 1) * 0.35
        cycle = ((index % 17) - 8) / 8
        micro_noise = ((index * 7) % 11 - 5) / 50
        feature = drift + cycle + micro_noise
        forward_return = 0.0018 * feature + ((index * 5) % 9 - 4) / 10000
        rows.append(Observation(timestamp=index, feature=feature, forward_return=forward_return))
    return tuple(rows)


def aggregate_results(results: Sequence[FoldResult]) -> StrategyMetrics:
    if not results:
        raise ValueError("results must not be empty")

    observations = sum(row.test_metrics.observations for row in results)
    weighted_mean = sum(row.test_metrics.mean_return * row.test_metrics.observations for row in results) / observations
    weighted_hit_rate = sum(row.test_metrics.hit_rate * row.test_metrics.observations for row in results) / observations
    weighted_turnover = sum(row.test_metrics.turnover * row.test_metrics.observations for row in results) / observations
    weighted_sharpe = sum(row.test_metrics.sharpe * row.test_metrics.observations for row in results) / observations
    return StrategyMetrics(
        observations=observations,
        mean_return=float(weighted_mean),
        hit_rate=float(weighted_hit_rate),
        turnover=float(weighted_turnover),
        sharpe=float(weighted_sharpe),
    )
