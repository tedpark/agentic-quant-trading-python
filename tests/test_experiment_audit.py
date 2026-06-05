from __future__ import annotations

import pytest

from agentic_quant.experiments.manifest import build_mini_backtest_manifest
from agentic_quant.experiments.orchestration import ExperimentFoldResult, run_mini_experiment
from agentic_quant.features.regime import synthetic_market_bars
from agentic_quant.research_os.audit import PromotionPolicy, audit_experiment


def _sample_folds() -> tuple[ExperimentFoldResult, ...]:
    return run_mini_experiment(
        synthetic_market_bars(220),
        train_size=80,
        validation_size=20,
        test_size=20,
        step_size=20,
        thresholds=(0.0, 0.4, 0.8),
    )


def test_audit_reviews_manifest_validation_risk_and_boundary() -> None:
    folds = _sample_folds()
    manifest = build_mini_backtest_manifest(
        folds,
        parameters={"train_size": 80, "validation_size": 20, "test_size": 20},
        artifacts={
            "manifest_report": "docs/benchmarks/experiment_manifest.md",
            "backtest_report": "docs/benchmarks/mini_backtest_orchestration.md",
        },
    )

    report = audit_experiment(manifest, folds)

    assert report.run_id == manifest.run_id
    assert report.decision in {"paper_trade_candidate", "review_required"}
    assert report.severity_counts()["pass"] >= 4
    assert any(finding.category == "validation" for finding in report.findings)
    assert any(finding.category == "risk" for finding in report.findings)
    assert "Trading Experiment Audit Report" in report.to_markdown()


def test_audit_flags_missing_artifacts() -> None:
    folds = _sample_folds()
    manifest = build_mini_backtest_manifest(
        folds,
        parameters={"train_size": 80},
        artifacts={"manifest_report": "docs/benchmarks/experiment_manifest.md"},
    )

    report = audit_experiment(manifest, folds)

    assert report.decision == "review_required"
    assert any("missing expected artifacts" in finding.message for finding in report.findings)


def test_audit_rejects_when_promotion_policy_is_not_met() -> None:
    folds = _sample_folds()
    manifest = build_mini_backtest_manifest(
        folds,
        parameters={"train_size": 80},
        artifacts={
            "manifest_report": "docs/benchmarks/experiment_manifest.md",
            "backtest_report": "docs/benchmarks/mini_backtest_orchestration.md",
        },
    )

    report = audit_experiment(manifest, folds, policy=PromotionPolicy(min_folds=999))

    assert report.decision == "reject"
    assert any("below policy minimum" in finding.message for finding in report.findings)


def test_audit_rejects_non_time_ordered_fold() -> None:
    folds = _sample_folds()
    bad_fold = ExperimentFoldResult(
        fold=folds[0].fold,
        train_range=(10, 40),
        validation_range=(35, 55),
        test_range=(56, 75),
        selected_threshold=folds[0].selected_threshold,
        validation_metrics=folds[0].validation_metrics,
        test_metrics=folds[0].test_metrics,
        sample_test_rows=folds[0].sample_test_rows,
    )
    bad_folds = (bad_fold, *folds[1:])
    manifest = build_mini_backtest_manifest(
        bad_folds,
        parameters={"train_size": 80},
        artifacts={
            "manifest_report": "docs/benchmarks/experiment_manifest.md",
            "backtest_report": "docs/benchmarks/mini_backtest_orchestration.md",
        },
    )

    report = audit_experiment(manifest, bad_folds)

    assert report.decision == "reject"
    assert any(finding.severity == "fail" and finding.category == "validation" for finding in report.findings)


def test_audit_rejects_empty_folds() -> None:
    folds = _sample_folds()
    manifest = build_mini_backtest_manifest(
        folds,
        parameters={},
        artifacts={
            "manifest_report": "docs/benchmarks/experiment_manifest.md",
            "backtest_report": "docs/benchmarks/mini_backtest_orchestration.md",
        },
    )

    with pytest.raises(ValueError, match="folds"):
        audit_experiment(manifest, ())
