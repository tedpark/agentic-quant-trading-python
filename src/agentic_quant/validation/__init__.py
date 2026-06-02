"""Validation protocol examples."""

from agentic_quant.validation.walk_forward import (
    FoldResult,
    Observation,
    Standardizer,
    StrategyMetrics,
    WalkForwardSplit,
    aggregate_results,
    fit_standardizer,
    make_walk_forward_splits,
    run_walk_forward_validation,
    synthetic_regime_observations,
)

__all__ = [
    "FoldResult",
    "Observation",
    "Standardizer",
    "StrategyMetrics",
    "WalkForwardSplit",
    "aggregate_results",
    "fit_standardizer",
    "make_walk_forward_splits",
    "run_walk_forward_validation",
    "synthetic_regime_observations",
]
