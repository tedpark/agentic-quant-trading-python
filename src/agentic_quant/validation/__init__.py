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
from agentic_quant.validation.purged_embargo import (
    LabelSpan,
    PurgedEmbargoSplit,
    assert_no_label_overlap,
    make_label_spans,
    make_purged_embargo_splits,
    purge_and_embargo_train_indices,
)

__all__ = [
    "FoldResult",
    "Observation",
    "Standardizer",
    "StrategyMetrics",
    "WalkForwardSplit",
    "LabelSpan",
    "PurgedEmbargoSplit",
    "aggregate_results",
    "assert_no_label_overlap",
    "fit_standardizer",
    "make_label_spans",
    "make_purged_embargo_splits",
    "make_walk_forward_splits",
    "purge_and_embargo_train_indices",
    "run_walk_forward_validation",
    "synthetic_regime_observations",
]
