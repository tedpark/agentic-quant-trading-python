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
class FeatureContract:
    name: str
    fit_scope: str


@dataclass(frozen=True)
class CostStressContract:
    scenario: str
    transaction_cost: float
    mean_test_return: float
    mean_test_cvar: float
    max_turnover: float


@dataclass(frozen=True)
class RegimeBreakdownContract:
    regime: str
    observations: int
    mean_return: float
    cvar: float


@dataclass(frozen=True)
class BenchmarkComparisonContract:
    benchmark_name: str
    mean_return_delta: float
    sharpe_delta: float
    cvar_delta: float


@dataclass(frozen=True)
class ExperimentRunContract:
    schema_version: str
    run_id: str
    manifest_run_id: str
    runner: str
    strategy_name: str
    model_version: str
    data_source: str
    allow_live_trading: bool
    features: tuple[FeatureContract, ...]
    cost_stress: tuple[CostStressContract, ...]
    regime_breakdown: tuple[RegimeBreakdownContract, ...]
    benchmark_comparison: tuple[BenchmarkComparisonContract, ...]
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
        model_version="research_demo_v1",
        data_source=str(getattr(config, "data_source")),
        allow_live_trading=bool(getattr(config, "allow_live_trading")),
        features=_feature_contracts(str(getattr(config, "strategy_name"))),
        cost_stress=_cost_stress_contracts(manifest, folds),
        regime_breakdown=_regime_breakdown_contracts(folds),
        benchmark_comparison=_benchmark_comparison_contracts(manifest),
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
            model_version=str(data.get("model_version", "unknown")),
            data_source=str(data["data_source"]),
            allow_live_trading=bool(data["allow_live_trading"]),
            features=tuple(_parse_feature(row) for row in data.get("features", ())),
            cost_stress=tuple(_parse_cost_stress(row) for row in data.get("cost_stress", ())),
            regime_breakdown=tuple(_parse_regime_breakdown(row) for row in data.get("regime_breakdown", ())),
            benchmark_comparison=tuple(_parse_benchmark_comparison(row) for row in data.get("benchmark_comparison", ())),
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
    if not contract.model_version:
        errors.append("model_version is required")
    if not contract.features:
        errors.append("features must not be empty")
    if any(feature.fit_scope != "train_only" for feature in contract.features):
        errors.append("all feature fit_scope values must be train_only")
    if not contract.cost_stress:
        errors.append("cost_stress must not be empty")
    if not contract.regime_breakdown:
        errors.append("regime_breakdown must not be empty")
    if not contract.benchmark_comparison:
        errors.append("benchmark_comparison must not be empty")
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


def _feature_contracts(strategy_name: str) -> tuple[FeatureContract, ...]:
    base = [
        FeatureContract("rolling_return", "train_only"),
        FeatureContract("realized_volatility", "train_only"),
    ]
    if "pair" in strategy_name:
        base.extend(
            [
                FeatureContract("hmm_regime", "train_only"),
                FeatureContract("spread_zscore", "train_only"),
                FeatureContract("spread_half_life", "train_only"),
            ]
        )
    elif "rl" in strategy_name:
        base.extend(
            [
                FeatureContract("return_quantiles", "train_only"),
                FeatureContract("cvar_action_score", "train_only"),
            ]
        )
    else:
        base.append(FeatureContract("momentum_zscore", "train_only"))
    return tuple(base)


def _cost_stress_contracts(
    manifest: ExperimentManifest, folds: Sequence[ExperimentFoldResult]
) -> tuple[CostStressContract, ...]:
    max_turnover = max(fold.test_metrics.turnover for fold in folds)
    return (
        CostStressContract(
            scenario="base_cost",
            transaction_cost=float(manifest.parameters.get("transaction_cost", 0.0004)),
            mean_test_return=manifest.mean_test_return,
            mean_test_cvar=manifest.mean_test_cvar,
            max_turnover=max_turnover,
        ),
        CostStressContract(
            scenario="double_cost_proxy",
            transaction_cost=float(manifest.parameters.get("transaction_cost", 0.0004)) * 2,
            mean_test_return=round(manifest.mean_test_return - max_turnover * 0.0004, 6),
            mean_test_cvar=round(manifest.mean_test_cvar - max_turnover * 0.0002, 6),
            max_turnover=max_turnover,
        ),
    )


def _regime_breakdown_contracts(folds: Sequence[ExperimentFoldResult]) -> tuple[RegimeBreakdownContract, ...]:
    rows = [row for fold in folds for row in fold.sample_test_rows]
    if not rows:
        return (RegimeBreakdownContract("unknown", 0, 0.0, 0.0),)
    regimes = sorted({row.regime for row in rows})
    breakdown = []
    for regime in regimes:
        regime_returns = [row.forward_return for row in rows if row.regime == regime]
        breakdown.append(
            RegimeBreakdownContract(
                regime=regime,
                observations=len(regime_returns),
                mean_return=round(sum(regime_returns) / len(regime_returns), 6),
                cvar=round(min(regime_returns), 6),
            )
        )
    return tuple(breakdown)


def _benchmark_comparison_contracts(manifest: ExperimentManifest) -> tuple[BenchmarkComparisonContract, ...]:
    benchmark_mean_return = 0.0
    benchmark_sharpe = 0.0
    benchmark_cvar = -0.001
    return (
        BenchmarkComparisonContract(
            benchmark_name="zero_return_baseline",
            mean_return_delta=round(manifest.mean_test_return - benchmark_mean_return, 6),
            sharpe_delta=round(manifest.mean_test_sharpe - benchmark_sharpe, 6),
            cvar_delta=round(manifest.mean_test_cvar - benchmark_cvar, 6),
        ),
    )


def _parse_feature(data: object) -> FeatureContract:
    if not isinstance(data, Mapping):
        raise ValueError("feature must be an object")
    return FeatureContract(name=str(data["name"]), fit_scope=str(data["fit_scope"]))


def _parse_cost_stress(data: object) -> CostStressContract:
    if not isinstance(data, Mapping):
        raise ValueError("cost stress must be an object")
    return CostStressContract(
        scenario=str(data["scenario"]),
        transaction_cost=float(data["transaction_cost"]),
        mean_test_return=float(data["mean_test_return"]),
        mean_test_cvar=float(data["mean_test_cvar"]),
        max_turnover=float(data["max_turnover"]),
    )


def _parse_regime_breakdown(data: object) -> RegimeBreakdownContract:
    if not isinstance(data, Mapping):
        raise ValueError("regime breakdown must be an object")
    return RegimeBreakdownContract(
        regime=str(data["regime"]),
        observations=int(data["observations"]),
        mean_return=float(data["mean_return"]),
        cvar=float(data["cvar"]),
    )


def _parse_benchmark_comparison(data: object) -> BenchmarkComparisonContract:
    if not isinstance(data, Mapping):
        raise ValueError("benchmark comparison must be an object")
    return BenchmarkComparisonContract(
        benchmark_name=str(data["benchmark_name"]),
        mean_return_delta=float(data["mean_return_delta"]),
        sharpe_delta=float(data["sharpe_delta"]),
        cvar_delta=float(data["cvar_delta"]),
    )


def _range_tuple(value: object) -> tuple[int, int]:
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise ValueError("range must contain two values")
    return int(value[0]), int(value[1])
