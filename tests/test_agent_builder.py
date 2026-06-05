from __future__ import annotations

from pathlib import Path

import pytest

from json import dumps, loads

from agentic_quant.research_os.agent_builder import (
    AgentSpec,
    build_agent_spec,
    parse_agent_spec_json,
    run_agent_builder,
    run_agent_builder_from_spec,
    validate_agent_spec,
)
from agentic_quant.research_os.cli import main
from agentic_quant.research_os.cycle import ResearchCycleConfig


def test_agent_builder_creates_valid_spec_and_runs_cycle() -> None:
    report = run_agent_builder("HMM regime features improve pair spread entries")

    assert report.spec.role == "financial_ml_experiment_agent"
    assert report.spec.schema_version == "agent_spec.v1"
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
        schema_version=spec.schema_version,
        builder_version=spec.builder_version,
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
        schema_version=spec.schema_version,
        builder_version=spec.builder_version,
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


def test_agent_spec_json_round_trips_and_can_replay() -> None:
    original = build_agent_spec("risk-aware RL experiment")
    parsed = parse_agent_spec_json(original.to_json())
    report = run_agent_builder_from_spec(parsed)

    assert parsed == original
    assert report.spec == original
    assert report.cycle.config.run_id == original.config.run_id


def test_agent_spec_parser_rejects_unknown_keys() -> None:
    payload = loads(build_agent_spec("risk-aware RL experiment").to_json())
    payload["shell"] = "python"

    with pytest.raises(ValueError, match="unknown agent spec keys"):
        parse_agent_spec_json(dumps(payload))


def test_agent_spec_parser_rejects_unsupported_schema() -> None:
    payload = loads(build_agent_spec("risk-aware RL experiment").to_json())
    payload["schema_version"] = "agent_spec.v999"

    with pytest.raises(ValueError, match="unsupported agent spec schema"):
        parse_agent_spec_json(dumps(payload))


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


def test_cli_build_agent_can_replay_from_spec_input(tmp_path: Path) -> None:
    spec = tmp_path / "agent_spec.json"
    spec.write_text(build_agent_spec("HMM regime features improve pair spread entries").to_json(), encoding="utf-8")
    report = tmp_path / "agent_builder.md"
    spec_output = tmp_path / "agent_spec_out.json"
    contract = tmp_path / "experiment_run.json"
    state = tmp_path / "agent_builder_state.json"

    exit_code = main(
        [
            "build-agent",
            "--spec-input",
            str(spec),
            "--output",
            str(report),
            "--spec-output",
            str(spec_output),
            "--contract-output",
            str(contract),
            "--state-output",
            str(state),
        ]
    )

    assert exit_code == 0
    assert "QuantSigma Agent Builder Report" in report.read_text(encoding="utf-8")
    assert '"schema_version": "experiment_run.v1"' in contract.read_text(encoding="utf-8")
    assert '"cycle_completed": true' in state.read_text(encoding="utf-8")


def test_cli_build_agent_run_dir_writes_run_scoped_artifacts(tmp_path: Path) -> None:
    exit_code = main(
        [
            "build-agent",
            "--idea",
            "HMM regime features improve pair spread entries",
            "--run-dir",
            str(tmp_path),
        ]
    )

    run_id = build_agent_spec("HMM regime features improve pair spread entries").config.run_id
    run_dir = tmp_path / run_id
    assert exit_code == 0
    assert (run_dir / "agent_builder_report.md").exists()
    assert (run_dir / "agent_spec.json").exists()
    assert (run_dir / "experiment_run_contract.json").exists()
    assert (run_dir / "agent_builder_state.json").exists()
