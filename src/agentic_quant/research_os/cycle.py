from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from typing import Callable, Mapping, Sequence

from agentic_quant.experiments.manifest import ExperimentManifest, build_mini_backtest_manifest
from agentic_quant.experiments.orchestration import ExperimentFoldResult, run_mini_experiment
from agentic_quant.features.regime import synthetic_market_bars
from agentic_quant.research_os.audit import ExperimentAuditReport, PromotionPolicy, audit_experiment
from agentic_quant.research_os.contract import (
    ExperimentRunContract,
    build_experiment_run_contract,
    validate_experiment_run_contract,
)
from agentic_quant.research_os.planner import ExperimentPlan, plan_experiment


ALLOWED_RESEARCH_TOOLS = (
    "plan_experiment",
    "build_experiment_config",
    "run_mini_backtest",
    "build_manifest",
    "audit_experiment",
    "write_report",
)

ALLOWED_RUNNERS = ("mini_backtest",)
ALLOWED_DATA_SOURCES = ("synthetic_market_bars",)
ALLOWED_STRATEGIES = (
    "pair_mean_reversion_regime_filter",
    "risk_aware_distributional_rl",
    "regime_aware_momentum",
)


@dataclass(frozen=True)
class ResearchCycleConfig:
    run_id: str
    idea: str
    runner: str
    strategy_name: str
    data_source: str
    train_size: int
    validation_size: int
    test_size: int
    step_size: int
    thresholds: tuple[float, ...]
    transaction_cost: float
    allow_live_trading: bool = False

    def to_json(self) -> str:
        return dumps(
            {
                "run_id": self.run_id,
                "idea": self.idea,
                "runner": self.runner,
                "strategy_name": self.strategy_name,
                "data_source": self.data_source,
                "train_size": self.train_size,
                "validation_size": self.validation_size,
                "test_size": self.test_size,
                "step_size": self.step_size,
                "thresholds": self.thresholds,
                "transaction_cost": self.transaction_cost,
                "allow_live_trading": self.allow_live_trading,
            },
            indent=2,
            sort_keys=True,
        )


@dataclass(frozen=True)
class ResearchToolCall:
    name: str
    arguments: Mapping[str, object]
    status: str
    summary: str


@dataclass(frozen=True)
class ResearchWorkflowState:
    idea: str
    run_id: str | None = None
    config_validated: bool = False
    runner_dispatched: bool = False
    manifest_run_id: str | None = None
    contract_validated: bool = False
    audit_decision: str | None = None
    completed_steps: tuple[str, ...] = ()

    def with_step(self, step: str, **updates: object) -> "ResearchWorkflowState":
        payload = asdict(self)
        payload.update(updates)
        payload["completed_steps"] = (*self.completed_steps, step)
        return ResearchWorkflowState(**payload)

    def to_json(self) -> str:
        return dumps(asdict(self), indent=2, sort_keys=True)


@dataclass(frozen=True)
class ResearchCycleReport:
    config: ResearchCycleConfig
    plan: ExperimentPlan
    folds: tuple[ExperimentFoldResult, ...]
    manifest: ExperimentManifest
    contract: ExperimentRunContract
    audit: ExperimentAuditReport
    tool_calls: tuple[ResearchToolCall, ...]
    state: ResearchWorkflowState

    def to_markdown(self) -> str:
        lines = [
            "# QuantSigma Lab Agent Research Cycle",
            "",
            "This report demonstrates a safe tool-calling research operator.",
            "The agent does not execute arbitrary shell commands or live trading.",
            "It calls allowlisted research tools, runs the trading-system backtest sample,",
            "builds a manifest, and applies the promotion gate.",
            "",
            "## Decision",
            "",
            f"- run id: `{self.config.run_id}`",
            f"- strategy: `{self.config.strategy_name}`",
            f"- promotion decision: `{self.audit.decision}`",
            f"- live trading allowed: `{self.config.allow_live_trading}`",
            f"- completed steps: {len(self.state.completed_steps)}",
            "",
            "## Tool Calls",
            "",
            "| Tool | Status | Summary |",
            "|---|---|---|",
        ]
        for call in self.tool_calls:
            lines.append(f"| `{call.name}` | `{call.status}` | {call.summary} |")

        lines.extend(
            [
                "",
                "## Experiment Config",
                "",
                "```json",
                self.config.to_json(),
                "```",
                "",
                self.plan.to_markdown().rstrip(),
                "",
                "## Backtest Summary",
                "",
                "| Fold | Train | Validation | Test | Threshold | Test Return | Test CVaR | Test Sharpe | Turnover |",
                "|---:|---|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for fold in self.folds:
            lines.append(
                f"| {fold.fold} | {fold.train_range} | {fold.validation_range} | {fold.test_range} | "
                f"{fold.selected_threshold:.3f} | {fold.test_metrics.mean_return:.6f} | "
                f"{fold.test_metrics.cvar:.6f} | {fold.test_metrics.sharpe:.3f} | "
                f"{fold.test_metrics.turnover:.3f} |"
            )

        lines.extend(
            [
                "",
                "## Manifest Snapshot",
                "",
                "```json",
                self.manifest.to_json(),
                "```",
                "",
                "## Experiment Run Contract",
                "",
                "```json",
                self.contract.to_json(),
                "```",
                "",
                "## Workflow State",
                "",
                "```json",
                self.state.to_json(),
                "```",
                "",
                self.audit.to_markdown().rstrip(),
            ]
        )
        return "\n".join(lines) + "\n"


RunnerFn = Callable[[ResearchCycleConfig], tuple[ExperimentFoldResult, ...]]


def build_experiment_config(idea: str) -> ResearchCycleConfig:
    normalized = idea.strip()
    if not normalized:
        raise ValueError("idea must not be empty")

    run_id = sha256(normalized.lower().encode("utf-8")).hexdigest()[:12]
    text = normalized.lower()
    thresholds = (0.0, 0.4, 0.8, 1.2)
    if "conservative" in text or "risk" in text:
        thresholds = (0.4, 0.8, 1.2, 1.6)

    return ResearchCycleConfig(
        run_id=run_id,
        idea=normalized,
        runner="mini_backtest",
        strategy_name=_strategy_name(text),
        data_source="synthetic_market_bars",
        train_size=90,
        validation_size=24,
        test_size=24,
        step_size=24,
        thresholds=thresholds,
        transaction_cost=0.0004,
        allow_live_trading=False,
    )


def validate_experiment_config(config: ResearchCycleConfig) -> ResearchCycleConfig:
    errors: list[str] = []
    if not config.run_id:
        errors.append("run_id is required")
    if not config.idea.strip():
        errors.append("idea is required")
    if config.runner not in ALLOWED_RUNNERS:
        errors.append(f"runner is not allowlisted: {config.runner}")
    if config.strategy_name not in ALLOWED_STRATEGIES:
        errors.append(f"strategy is not allowlisted: {config.strategy_name}")
    if config.data_source not in ALLOWED_DATA_SOURCES:
        errors.append(f"data source is not allowlisted: {config.data_source}")
    if config.allow_live_trading:
        errors.append("live trading must be disabled")
    if config.train_size <= 0 or config.validation_size <= 0 or config.test_size <= 0 or config.step_size <= 0:
        errors.append("window sizes must be positive")
    if config.train_size <= config.validation_size:
        errors.append("train_size should be larger than validation_size")
    if not config.thresholds:
        errors.append("thresholds must not be empty")
    if any(threshold < 0 for threshold in config.thresholds):
        errors.append("thresholds must be non-negative")
    if config.transaction_cost < 0:
        errors.append("transaction_cost must be non-negative")

    if errors:
        raise ValueError("invalid experiment config: " + "; ".join(errors))
    return config


def run_research_cycle(idea: str, *, policy: PromotionPolicy = PromotionPolicy()) -> ResearchCycleReport:
    tool_calls: list[ResearchToolCall] = []
    state = ResearchWorkflowState(idea=idea)

    plan = plan_experiment(idea)
    tool_calls.append(_tool_call("plan_experiment", {"idea": idea}, "created leakage-aware experiment plan"))
    state = state.with_step("plan_experiment")

    config = validate_experiment_config(build_experiment_config(idea))
    state = state.with_step("validate_experiment_config", run_id=config.run_id, config_validated=True)
    tool_calls.append(
        _tool_call(
            "build_experiment_config",
            {"run_id": config.run_id, "runner": config.runner},
            "created and validated safe synthetic-data config",
        )
    )

    folds = _run_registered_runner(config)
    state = state.with_step("run_registered_runner", runner_dispatched=True)
    tool_calls.append(_tool_call("run_mini_backtest", {"folds": len(folds)}, "ran walk-forward mini backtest"))

    manifest = build_mini_backtest_manifest(
        folds,
        parameters={
            "idea": config.idea,
            "strategy_name": config.strategy_name,
            "train_size": config.train_size,
            "validation_size": config.validation_size,
            "test_size": config.test_size,
            "step_size": config.step_size,
            "thresholds": config.thresholds,
            "transaction_cost": config.transaction_cost,
        },
        artifacts={
            "cycle_report": "docs/benchmarks/research_cycle_report.md",
            "manifest_report": "docs/benchmarks/experiment_manifest.md",
            "backtest_report": "docs/benchmarks/mini_backtest_orchestration.md",
            "audit_report": "docs/benchmarks/trading_experiment_audit.md",
        },
        name=f"research-cycle-{config.strategy_name}",
        data_source=config.data_source,
    )
    state = state.with_step("build_manifest", manifest_run_id=manifest.run_id)
    tool_calls.append(_tool_call("build_manifest", {"manifest_run_id": manifest.run_id}, "built experiment manifest"))

    audit = audit_experiment(manifest, folds, policy=policy)
    state = state.with_step("audit_experiment", audit_decision=audit.decision)
    tool_calls.append(_tool_call("audit_experiment", {"decision": audit.decision}, "applied promotion gate"))
    contract = validate_experiment_run_contract(build_experiment_run_contract(config, manifest, folds))
    state = state.with_step("validate_experiment_run_contract", contract_validated=True)
    tool_calls.append(
        _tool_call(
            "write_report",
            {
                "output": "docs/benchmarks/research_cycle_report.md",
                "contract": "docs/benchmarks/experiment_run_contract.json",
            },
            "rendered cycle report and experiment_run contract",
        )
    )

    return ResearchCycleReport(
        config=config,
        plan=plan,
        folds=tuple(folds),
        manifest=manifest,
        contract=contract,
        audit=audit,
        tool_calls=tuple(tool_calls),
        state=state,
    )


def _strategy_name(text: str) -> str:
    if "pair" in text or "spread" in text or "cointegration" in text:
        return "pair_mean_reversion_regime_filter"
    if "rl" in text or "qrdqn" in text or "qr-dqn" in text:
        return "risk_aware_distributional_rl"
    return "regime_aware_momentum"


def _run_registered_runner(config: ResearchCycleConfig) -> tuple[ExperimentFoldResult, ...]:
    runner = _runner_registry()[config.runner]
    return runner(config)


def _runner_registry() -> Mapping[str, RunnerFn]:
    return {"mini_backtest": _run_mini_backtest_from_config}


def _run_mini_backtest_from_config(config: ResearchCycleConfig) -> tuple[ExperimentFoldResult, ...]:
    return run_mini_experiment(
        synthetic_market_bars(240),
        train_size=config.train_size,
        validation_size=config.validation_size,
        test_size=config.test_size,
        step_size=config.step_size,
        thresholds=_as_float_tuple(config.thresholds),
        transaction_cost=config.transaction_cost,
    )


def _as_float_tuple(values: Sequence[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _tool_call(name: str, arguments: Mapping[str, object], summary: str) -> ResearchToolCall:
    if name not in ALLOWED_RESEARCH_TOOLS:
        raise ValueError(f"tool is not allowlisted: {name}")
    return ResearchToolCall(name=name, arguments=dict(arguments), status="ok", summary=summary)
