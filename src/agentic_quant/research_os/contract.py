from __future__ import annotations

from dataclasses import asdict, dataclass
from json import dumps, loads
from typing import Mapping, Sequence

from agentic_quant.experiments.manifest import ExperimentManifest
from agentic_quant.experiments.orchestration import ExperimentFoldResult


@dataclass(frozen=True)
class FoldMetricsContract:
    observations: int
    mean_return: float
    hit_rate: float
    turnover: float
    cvar: float
    max_drawdown: float
    sharpe: float


@dataclass(frozen=True)
class FoldContract:
    fold: int
    train_range: tuple[int, int]
    validation_range: tuple[int, int]
    test_range: tuple[int, int]
    selected_threshold: float
    validation_metrics: FoldMetricsContract
    test_metrics: FoldMetricsContract


@dataclass(frozen=True)
class ExperimentRunContract:
    schema_version: str
    run_id: str
    manifest_run_id: str
    runner: str
    strategy_name: str
    data_source: str
    allow_live_trading: bool
    parameters: Mapping[str, object]
    folds: tuple[FoldContract, ...]
    artifacts: Mapping[str, str]
    public_boundary: tuple[str, ...]

    def to_json(self) -> str:
        return dumps(asdict(self), indent=2, sort_keys=True)


def build_experiment_run_contract(
    config: object,
    manifest: ExperimentManifest,
    folds: Sequence[ExperimentFoldResult],
) -> ExperimentRunContract:
    return ExperimentRunContract(
        schema_version="experiment_run.v1",
        run_id=str(getattr(config, "run_id")),
        manifest_run_id=manifest.run_id,
        runner=str(getattr(config, "runner")),
        strategy_name=str(getattr(config, "strategy_name")),
        data_source=str(getattr(config, "data_source")),
        allow_live_trading=bool(getattr(config, "allow_live_trading")),
        parameters=dict(manifest.parameters),
        folds=tuple(_fold_contract(fold) for fold in folds),
        artifacts=dict(manifest.artifacts),
        public_boundary=tuple(manifest.public_boundary),
    )


def parse_experiment_run_contract(payload: str) -> ExperimentRunContract:
    data = loads(payload)
    try:
        return ExperimentRunContract(
            schema_version=str(data["schema_version"]),
            run_id=str(data["run_id"]),
            manifest_run_id=str(data["manifest_run_id"]),
            runner=str(data["runner"]),
            strategy_name=str(data["strategy_name"]),
            data_source=str(data["data_source"]),
            allow_live_trading=bool(data["allow_live_trading"]),
            parameters=dict(data["parameters"]),
            folds=tuple(_parse_fold(row) for row in data["folds"]),
            artifacts=dict(data["artifacts"]),
            public_boundary=tuple(str(item) for item in data["public_boundary"]),
        )
    except KeyError as error:
        raise ValueError(f"missing experiment run contract field: {error.args[0]}") from error


def validate_experiment_run_contract(contract: ExperimentRunContract) -> ExperimentRunContract:
    errors: list[str] = []
    if contract.schema_version != "experiment_run.v1":
        errors.append(f"unsupported schema_version: {contract.schema_version}")
    if not contract.run_id:
        errors.append("run_id is required")
    if not contract.manifest_run_id:
        errors.append("manifest_run_id is required")
    if contract.allow_live_trading:
        errors.append("allow_live_trading must be false for public research contracts")
    if not contract.folds:
        errors.append("folds must not be empty")
    if "backtest_report" not in contract.artifacts:
        errors.append("backtest_report artifact is required")
    if "manifest_report" not in contract.artifacts:
        errors.append("manifest_report artifact is required")

    for fold in contract.folds:
        if not (fold.train_range[1] < fold.validation_range[0] and fold.validation_range[1] < fold.test_range[0]):
            errors.append(f"fold {fold.fold} is not time ordered")
        if fold.test_metrics.observations <= 0:
            errors.append(f"fold {fold.fold} has no test observations")
        if fold.test_metrics.turnover < 0:
            errors.append(f"fold {fold.fold} has negative turnover")

    boundary = " ".join(contract.public_boundary).lower()
    if "no live execution" not in boundary:
        errors.append("public boundary must exclude live execution")
    if "no broker" not in boundary:
        errors.append("public boundary must exclude broker data or broker integration")

    if errors:
        raise ValueError("invalid experiment run contract: " + "; ".join(errors))
    return contract


def _fold_contract(fold: ExperimentFoldResult) -> FoldContract:
    return FoldContract(
        fold=fold.fold,
        train_range=fold.train_range,
        validation_range=fold.validation_range,
        test_range=fold.test_range,
        selected_threshold=fold.selected_threshold,
        validation_metrics=_metrics_contract(fold.validation_metrics),
        test_metrics=_metrics_contract(fold.test_metrics),
    )


def _metrics_contract(metrics: object) -> FoldMetricsContract:
    return FoldMetricsContract(
        observations=int(getattr(metrics, "observations")),
        mean_return=float(getattr(metrics, "mean_return")),
        hit_rate=float(getattr(metrics, "hit_rate")),
        turnover=float(getattr(metrics, "turnover")),
        cvar=float(getattr(metrics, "cvar")),
        max_drawdown=float(getattr(metrics, "max_drawdown")),
        sharpe=float(getattr(metrics, "sharpe")),
    )


def _parse_fold(data: Mapping[str, object]) -> FoldContract:
    return FoldContract(
        fold=int(data["fold"]),
        train_range=_range_tuple(data["train_range"]),
        validation_range=_range_tuple(data["validation_range"]),
        test_range=_range_tuple(data["test_range"]),
        selected_threshold=float(data["selected_threshold"]),
        validation_metrics=_parse_metrics(data["validation_metrics"]),
        test_metrics=_parse_metrics(data["test_metrics"]),
    )


def _parse_metrics(data: object) -> FoldMetricsContract:
    if not isinstance(data, Mapping):
        raise ValueError("metrics must be an object")
    return FoldMetricsContract(
        observations=int(data["observations"]),
        mean_return=float(data["mean_return"]),
        hit_rate=float(data["hit_rate"]),
        turnover=float(data["turnover"]),
        cvar=float(data["cvar"]),
        max_drawdown=float(data["max_drawdown"]),
        sharpe=float(data["sharpe"]),
    )


def _range_tuple(value: object) -> tuple[int, int]:
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise ValueError("range must contain two values")
    return int(value[0]), int(value[1])
