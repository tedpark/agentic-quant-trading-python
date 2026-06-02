from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean, pstdev
from typing import Sequence

from agentic_quant.features.regime import (
    FeatureRow,
    MarketBar,
    build_feature_rows,
    classify_regimes,
    fit_regime_model,
    fit_standardizer,
)
from agentic_quant.risk.cvar import left_tail_cvar, risk_multiplier
from agentic_quant.validation.walk_forward import make_walk_forward_splits


@dataclass(frozen=True)
class ExperimentRow:
    timestamp: int
    regime: str
    z_momentum: float
    z_volatility: float
    drawdown: float
    forward_return: float


@dataclass(frozen=True)
class ExperimentMetrics:
    observations: int
    mean_return: float
    hit_rate: float
    turnover: float
    cvar: float
    max_drawdown: float
    sharpe: float


@dataclass(frozen=True)
class ExperimentFoldResult:
    fold: int
    train_range: tuple[int, int]
    validation_range: tuple[int, int]
    test_range: tuple[int, int]
    selected_threshold: float
    validation_metrics: ExperimentMetrics
    test_metrics: ExperimentMetrics
    sample_test_rows: tuple[ExperimentRow, ...]


def _paired_forward_returns(features: Sequence[FeatureRow]) -> tuple[tuple[FeatureRow, float], ...]:
    if len(features) < 2:
        raise ValueError("at least two feature rows are required")
    return tuple((features[index], features[index + 1].return_1d) for index in range(len(features) - 1))


def _make_experiment_rows(
    feature_rows: Sequence[FeatureRow],
    forward_returns: Sequence[float],
    *,
    train_rows: Sequence[FeatureRow],
) -> tuple[ExperimentRow, ...]:
    if len(feature_rows) != len(forward_returns):
        raise ValueError("feature_rows and forward_returns must have the same length")
    if not feature_rows:
        raise ValueError("feature_rows must not be empty")

    standardizer = fit_standardizer(train_rows)
    regime_model = fit_regime_model(train_rows)
    regimes = classify_regimes(feature_rows, regime_model)
    rows: list[ExperimentRow] = []
    for feature, regime, forward_return in zip(feature_rows, regimes, forward_returns):
        transformed = standardizer.transform(feature)
        rows.append(
            ExperimentRow(
                timestamp=feature.timestamp,
                regime=regime.regime,
                z_momentum=transformed["momentum_5"],
                z_volatility=transformed["realized_volatility"],
                drawdown=feature.drawdown,
                forward_return=float(forward_return),
            )
        )
    return tuple(rows)


def _return_quantiles(row: ExperimentRow, direction: float) -> tuple[float, ...]:
    center = direction * row.forward_return
    tail_width = 0.004 + max(row.z_volatility, 0.0) * 0.0015
    if row.regime == "high_vol":
        tail_width *= 1.7
    return tuple(center + (index - 5) * tail_width / 10 for index in range(11))


def _row_strategy_return(row: ExperimentRow, *, threshold: float, transaction_cost: float) -> float:
    if abs(row.z_momentum) < threshold:
        return 0.0

    direction = 1.0 if row.z_momentum > 0 else -1.0
    quantiles = _return_quantiles(row, direction)
    multiplier = risk_multiplier(left_tail_cvar(quantiles, tail_fraction=0.2), stop_level=-0.02, reduce_level=-0.01)
    if row.regime == "high_vol":
        multiplier *= 0.5
    if row.drawdown < -0.08:
        multiplier *= 0.5
    if multiplier == 0:
        return 0.0
    return direction * row.forward_return * multiplier - transaction_cost * multiplier


def simulate_rows(
    rows: Sequence[ExperimentRow],
    *,
    threshold: float,
    transaction_cost: float = 0.0004,
) -> ExperimentMetrics:
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    if transaction_cost < 0:
        raise ValueError("transaction_cost must be non-negative")
    if not rows:
        raise ValueError("rows must not be empty")

    returns = [_row_strategy_return(row, threshold=threshold, transaction_cost=transaction_cost) for row in rows]
    non_zero = [value for value in returns if value != 0.0]
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in returns:
        equity += value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)

    return_std = pstdev(returns)
    return ExperimentMetrics(
        observations=len(rows),
        mean_return=float(mean(returns)),
        hit_rate=0.0 if not non_zero else sum(value > 0 for value in non_zero) / len(non_zero),
        turnover=len(non_zero) / len(rows),
        cvar=left_tail_cvar(returns, tail_fraction=0.2),
        max_drawdown=float(max_drawdown),
        sharpe=0.0 if return_std == 0 else float(mean(returns) / return_std * sqrt(252)),
    )


def _select_threshold(
    validation_rows: Sequence[ExperimentRow],
    *,
    thresholds: Sequence[float],
    transaction_cost: float,
) -> tuple[float, ExperimentMetrics]:
    if not thresholds:
        raise ValueError("thresholds must not be empty")
    scored = [
        (
            float(threshold),
            simulate_rows(validation_rows, threshold=float(threshold), transaction_cost=transaction_cost),
        )
        for threshold in thresholds
    ]
    return max(scored, key=lambda item: (item[1].mean_return, item[1].sharpe, -item[0]))


def run_mini_experiment(
    bars: Sequence[MarketBar],
    *,
    train_size: int,
    validation_size: int,
    test_size: int,
    thresholds: Sequence[float],
    transaction_cost: float = 0.0004,
    step_size: int | None = None,
) -> tuple[ExperimentFoldResult, ...]:
    features = build_feature_rows(bars)
    paired = _paired_forward_returns(features)
    feature_only = tuple(row for row, _ in paired)
    forward_returns = tuple(forward_return for _, forward_return in paired)
    splits = make_walk_forward_splits(
        len(feature_only),
        train_size=train_size,
        validation_size=validation_size,
        test_size=test_size,
        step_size=step_size,
    )

    results: list[ExperimentFoldResult] = []
    for split in splits:
        train_features = feature_only[split.train_start : split.train_end]
        validation_features = feature_only[split.validation_start : split.validation_end]
        test_features = feature_only[split.test_start : split.test_end]
        validation_forward = forward_returns[split.validation_start : split.validation_end]
        test_forward = forward_returns[split.test_start : split.test_end]

        validation_rows = _make_experiment_rows(
            validation_features,
            validation_forward,
            train_rows=train_features,
        )
        test_rows = _make_experiment_rows(
            test_features,
            test_forward,
            train_rows=train_features,
        )
        threshold, validation_metrics = _select_threshold(
            validation_rows,
            thresholds=thresholds,
            transaction_cost=transaction_cost,
        )
        test_metrics = simulate_rows(test_rows, threshold=threshold, transaction_cost=transaction_cost)
        results.append(
            ExperimentFoldResult(
                fold=split.fold,
                train_range=(train_features[0].timestamp, train_features[-1].timestamp),
                validation_range=(validation_features[0].timestamp, validation_features[-1].timestamp),
                test_range=(test_features[0].timestamp, test_features[-1].timestamp),
                selected_threshold=threshold,
                validation_metrics=validation_metrics,
                test_metrics=test_metrics,
                sample_test_rows=tuple(test_rows[:4]),
            )
        )
    return tuple(results)
