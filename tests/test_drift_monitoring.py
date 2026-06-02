from pathlib import Path

import pytest

from agentic_quant.monitoring.demo_drift_report import sample_features
from agentic_quant.monitoring.drift import (
    classify_drift,
    detect_drift,
    ks_statistic,
    population_stability_index,
)


def test_ks_statistic_detects_separated_distributions() -> None:
    ks = ks_statistic([0, 0, 0, 0], [1, 1, 1, 1])

    assert ks == 1.0


def test_psi_is_near_zero_for_identical_distribution() -> None:
    values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]

    psi = population_stability_index(values, values, bins=3)

    assert psi == pytest.approx(0.0)


def test_detect_drift_orders_significant_features_first() -> None:
    reference, current = sample_features()

    report = detect_drift(reference, current, bins=5)

    assert report.worst_feature is not None
    assert report.worst_feature.severity == "significant"
    assert report.worst_feature.name in {"regime_score", "volatility_z"}
    assert report.severity_counts()["significant"] >= 1


def test_detect_drift_rejects_missing_feature() -> None:
    with pytest.raises(ValueError, match="missing features"):
        detect_drift({"spread_z": [0.1, 0.2]}, {})


def test_markdown_report_contains_public_boundary() -> None:
    reference, current = sample_features()

    markdown = detect_drift(reference, current, bins=5).to_markdown()

    assert "# Drift Report" in markdown
    assert "synthetic data only" in markdown
    assert "not investment advice" in markdown


def test_demo_report_writes_markdown(tmp_path: Path) -> None:
    output = tmp_path / "drift_report.md"
    reference, current = sample_features()

    output.write_text(detect_drift(reference, current, bins=5).to_markdown(), encoding="utf-8")

    assert output.read_text(encoding="utf-8").startswith("# Drift Report")
