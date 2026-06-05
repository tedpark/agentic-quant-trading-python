from __future__ import annotations

import pytest

from agentic_quant.research_os.audit import PromotionPolicy
from agentic_quant.research_os.cycle import build_experiment_config, run_research_cycle


def test_research_cycle_runs_allowlisted_tools_and_outputs_report() -> None:
    report = run_research_cycle("HMM regime features improve pair spread entries")

    assert report.config.allow_live_trading is False
    assert report.config.strategy_name == "pair_mean_reversion_regime_filter"
    assert {call.name for call in report.tool_calls} == {
        "plan_experiment",
        "build_experiment_config",
        "run_mini_backtest",
        "build_manifest",
        "audit_experiment",
        "write_report",
    }
    assert report.audit.decision in {"paper_trade_candidate", "review_required"}
    assert "QuantSigma Lab Agent Research Cycle" in report.to_markdown()
    assert "does not execute arbitrary shell commands" in report.to_markdown()


def test_research_cycle_can_reject_under_strict_policy() -> None:
    report = run_research_cycle(
        "HMM regime features improve pair spread entries",
        policy=PromotionPolicy(min_folds=999),
    )

    assert report.audit.decision == "reject"
    assert any(finding.severity == "fail" for finding in report.audit.findings)


def test_config_rejects_empty_idea() -> None:
    with pytest.raises(ValueError, match="idea"):
        build_experiment_config("")
