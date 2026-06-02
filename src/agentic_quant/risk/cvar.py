from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ActionRisk:
    action: str
    expected_return: float
    cvar: float
    multiplier: float
    quantile_count: int


def sorted_quantiles(quantiles: Sequence[float]) -> list[float]:
    if not quantiles:
        raise ValueError("quantiles must not be empty")
    return sorted(float(value) for value in quantiles)


def left_tail_cvar(quantiles: Sequence[float], *, tail_fraction: float = 0.1) -> float:
    if not 0 < tail_fraction <= 1:
        raise ValueError("tail_fraction must be in (0, 1]")

    values = sorted_quantiles(quantiles)
    tail_count = max(1, round(len(values) * tail_fraction))
    return float(mean(values[:tail_count]))


def risk_multiplier(cvar: float, *, stop_level: float = -0.03, reduce_level: float = -0.015) -> float:
    if stop_level >= reduce_level:
        raise ValueError("stop_level must be lower than reduce_level")
    if cvar <= stop_level:
        return 0.0
    if cvar <= reduce_level:
        return 0.5
    return 1.0


def evaluate_action_risk(
    action_quantiles: Mapping[str, Sequence[float]],
    *,
    tail_fraction: float = 0.1,
    stop_level: float = -0.03,
    reduce_level: float = -0.015,
) -> tuple[ActionRisk, ...]:
    rows: list[ActionRisk] = []
    for action, quantiles in action_quantiles.items():
        values = sorted_quantiles(quantiles)
        cvar = left_tail_cvar(values, tail_fraction=tail_fraction)
        rows.append(
            ActionRisk(
                action=action,
                expected_return=float(mean(values)),
                cvar=cvar,
                multiplier=risk_multiplier(cvar, stop_level=stop_level, reduce_level=reduce_level),
                quantile_count=len(values),
            )
        )
    return tuple(sorted(rows, key=lambda row: (-row.multiplier, -row.expected_return, row.action)))
