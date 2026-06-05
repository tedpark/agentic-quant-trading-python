from __future__ import annotations

from pathlib import Path

import pytest

from agentic_quant.research_os.agent_builder import AgentSpec, build_agent_spec, run_agent_builder, validate_agent_spec
from agentic_quant.research_os.cli import main
from agentic_quant.research_os.cycle import ResearchCycleConfig


def test_agent_builder_creates_valid_spec_and_runs_cycle() -> None:
    report = run_agent_builder("HMM regime features improve pair spread entries")

    assert report.spec.role == "financial_ml_experiment_agent"
    assert report.spec.config.runner == "mini_backtest"
    assert "no_arbitrary_code" in report.spec.constraints
    assert "contract_only_promotion_review" in report.spec.constraints
    assert "experiment_run.v1" in report.spec.outputs
    assert report.state.agent_spec_built is True
    assert report.state.agent_spec_validated is True
    assert report.state.config_validated is True
    assert report.state.cycle_completed is True
    assert report.cycle.contract.schema_version == "experiment_run.v1"
    assert "QuantSigma Agent Builder Report" in report.to_markdown()
    assert "cannot execute arbitrary code" in report.to_markdown()


def test_agent_spec_validator_rejects_non_allowlisted_tool() -> None:
    spec = build_agent_spec("risk-aware RL experiment")
    invalid = AgentSpec(
        agent_id=spec.agent_id,
        role=spec.role,
        goal=spec.goal,
        idea=spec.idea,
        config=spec.config,
        allowed_tools=(*spec.allowed_tools, "shell"),
        constraints=spec.constraints,
        outputs=spec.outputs,
    )

    with pytest.raises(ValueError, match="non-allowlisted tools"):
        validate_agent_spec(invalid)


def test_agent_spec_validator_rejects_live_trading_config() -> None:
    spec = build_agent_spec("risk-aware RL experiment")
    live_config = ResearchCycleConfig(
        run_id=spec.config.run_id,
        idea=spec.config.idea,
        runner=spec.config.runner,
        strategy_name=spec.config.strategy_name,
        data_source=spec.config.data_source,
        train_size=spec.config.train_size,
        validation_size=spec.config.validation_size,
        test_size=spec.config.test_size,
        step_size=spec.config.step_size,
        thresholds=spec.config.thresholds,
        transaction_cost=spec.config.transaction_cost,
        allow_live_trading=True,
    )
    invalid = AgentSpec(
        agent_id=spec.agent_id,
        role=spec.role,
        goal=spec.goal,
        idea=spec.idea,
        config=live_config,
        allowed_tools=spec.allowed_tools,
        constraints=spec.constraints,
        outputs=spec.outputs,
    )

    with pytest.raises(ValueError, match="live trading must be disabled"):
        validate_agent_spec(invalid)


def test_cli_build_agent_writes_report_spec_contract_and_state(tmp_path: Path) -> None:
    report = tmp_path / "agent_builder.md"
    spec = tmp_path / "agent_spec.json"
    contract = tmp_path / "experiment_run.json"
    state = tmp_path / "agent_builder_state.json"

    exit_code = main(
        [
            "build-agent",
            "--idea",
            "HMM regime features improve pair spread entries",
            "--output",
            str(report),
            "--spec-output",
            str(spec),
            "--contract-output",
            str(contract),
            "--state-output",
            str(state),
        ]
    )

    assert exit_code == 0
    assert "QuantSigma Agent Builder Report" in report.read_text(encoding="utf-8")
    assert '"role": "financial_ml_experiment_agent"' in spec.read_text(encoding="utf-8")
    assert '"schema_version": "experiment_run.v1"' in contract.read_text(encoding="utf-8")
    assert '"cycle_completed": true' in state.read_text(encoding="utf-8")
