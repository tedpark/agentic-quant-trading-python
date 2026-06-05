from __future__ import annotations

import pytest

from agentic_quant.research_os.audit import PromotionPolicy
from agentic_quant.research_os.cycle import ResearchCycleConfig, build_experiment_config, run_research_cycle, validate_experiment_config


def test_research_cycle_runs_allowlisted_tools_and_outputs_report() -> None:
    report = run_research_cycle("HMM regime features improve pair spread entries")

    assert report.config.allow_live_trading is False
    assert report.config.runner == "mini_backtest"
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
    assert report.state.config_validated is True
    assert report.state.runner_dispatched is True
    assert report.state.contract_validated is True
    assert report.state.audit_decision == report.audit.decision
    assert report.state.completed_steps == (
        "plan_experiment",
        "validate_experiment_config",
        "run_registered_runner",
        "build_manifest",
        "audit_experiment",
        "validate_experiment_run_contract",
    )
    assert "QuantSigma Lab Agent Research Cycle" in report.to_markdown()
    assert "does not execute arbitrary shell commands" in report.to_markdown()
    assert "Workflow State" in report.to_markdown()


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


def test_config_validator_blocks_unregistered_runner_and_live_trading() -> None:
    config = build_experiment_config("HMM regime features improve pair spread entries")
    invalid = ResearchCycleConfig(
        run_id=config.run_id,
        idea=config.idea,
        runner="shell",
        strategy_name=config.strategy_name,
        data_source=config.data_source,
        train_size=config.train_size,
        validation_size=config.validation_size,
        test_size=config.test_size,
        step_size=config.step_size,
        thresholds=config.thresholds,
        transaction_cost=config.transaction_cost,
        allow_live_trading=True,
    )

    with pytest.raises(ValueError, match="runner is not allowlisted"):
        validate_experiment_config(invalid)


def test_config_validator_accepts_generated_config() -> None:
    config = build_experiment_config("risk-aware RL experiment")

    assert validate_experiment_config(config) == config
