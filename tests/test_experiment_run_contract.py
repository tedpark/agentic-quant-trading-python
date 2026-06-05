from __future__ import annotations

import pytest

from agentic_quant.research_os.contract import (
    ExperimentRunContract,
    build_experiment_run_contract,
    parse_experiment_run_contract,
    validate_experiment_run_contract,
)
from agentic_quant.research_os.cycle import run_research_cycle


def test_contract_round_trips_from_research_cycle() -> None:
    report = run_research_cycle("HMM regime features improve pair spread entries")

    parsed = parse_experiment_run_contract(report.contract.to_json())
    validated = validate_experiment_run_contract(parsed)

    assert validated.schema_version == "experiment_run.v1"
    assert validated.run_id == report.config.run_id
    assert validated.manifest_run_id == report.manifest.run_id
    assert validated.runner == "mini_backtest"
    assert validated.allow_live_trading is False
    assert validated.folds


def test_contract_validator_rejects_live_trading_contract() -> None:
    report = run_research_cycle("HMM regime features improve pair spread entries")
    contract = ExperimentRunContract(
        schema_version=report.contract.schema_version,
        run_id=report.contract.run_id,
        manifest_run_id=report.contract.manifest_run_id,
        runner=report.contract.runner,
        strategy_name=report.contract.strategy_name,
        data_source=report.contract.data_source,
        allow_live_trading=True,
        parameters=report.contract.parameters,
        folds=report.contract.folds,
        artifacts=report.contract.artifacts,
        public_boundary=report.contract.public_boundary,
    )

    with pytest.raises(ValueError, match="allow_live_trading"):
        validate_experiment_run_contract(contract)


def test_contract_validator_rejects_non_time_ordered_fold() -> None:
    report = run_research_cycle("HMM regime features improve pair spread entries")
    first = report.contract.folds[0]
    bad_fold = type(first)(
        fold=first.fold,
        train_range=(10, 40),
        validation_range=(35, 50),
        test_range=first.test_range,
        selected_threshold=first.selected_threshold,
        validation_metrics=first.validation_metrics,
        test_metrics=first.test_metrics,
    )
    contract = ExperimentRunContract(
        schema_version=report.contract.schema_version,
        run_id=report.contract.run_id,
        manifest_run_id=report.contract.manifest_run_id,
        runner=report.contract.runner,
        strategy_name=report.contract.strategy_name,
        data_source=report.contract.data_source,
        allow_live_trading=report.contract.allow_live_trading,
        parameters=report.contract.parameters,
        folds=(bad_fold, *report.contract.folds[1:]),
        artifacts=report.contract.artifacts,
        public_boundary=report.contract.public_boundary,
    )

    with pytest.raises(ValueError, match="not time ordered"):
        validate_experiment_run_contract(contract)


def test_contract_builder_uses_manifest_and_fold_outputs() -> None:
    report = run_research_cycle("risk-aware RL experiment")

    contract = build_experiment_run_contract(report.config, report.manifest, report.folds)

    assert contract.parameters["strategy_name"] == report.config.strategy_name
    assert contract.artifacts["backtest_report"] == "docs/benchmarks/mini_backtest_orchestration.md"
    assert contract.folds[0].test_metrics.observations > 0
