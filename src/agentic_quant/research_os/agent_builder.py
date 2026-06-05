from __future__ import annotations

from dataclasses import asdict, dataclass
from json import JSONDecodeError, dumps, loads
from pathlib import Path
from tempfile import NamedTemporaryFile

from agentic_quant.research_os.cycle import (
    ALLOWED_RESEARCH_TOOLS,
    ResearchCycleConfig,
    ResearchCycleReport,
    build_experiment_config,
    run_research_cycle_from_config,
    validate_experiment_config,
)


AGENT_SPEC_SCHEMA_VERSION = "agent_spec.v1"
AGENT_BUILDER_VERSION = "quant_sigma_agent_builder.v1"
ALLOWED_AGENT_ROLES = ("financial_ml_experiment_agent",)
ALLOWED_AGENT_CONSTRAINTS = {
    "no_arbitrary_code",
    "no_live_trading",
    "public_or_synthetic_data_only",
    "leakage_aware_validation",
    "contract_only_promotion_review",
}
DEFAULT_AGENT_OUTPUTS = (
    "agent_spec",
    "dynamic_config",
    "experiment_manifest",
    "experiment_run.v1",
    "workflow_state_trace",
    "promotion_review",
    "markdown_report",
)
AGENT_SPEC_KEYS = {
    "schema_version",
    "builder_version",
    "agent_id",
    "role",
    "goal",
    "idea",
    "config",
    "allowed_tools",
    "constraints",
    "outputs",
}
CONFIG_KEYS = {
    "run_id",
    "idea",
    "runner",
    "strategy_name",
    "data_source",
    "train_size",
    "validation_size",
    "test_size",
    "step_size",
    "thresholds",
    "transaction_cost",
    "allow_live_trading",
}


@dataclass(frozen=True)
class AgentSpec:
    schema_version: str
    builder_version: str
    agent_id: str
    role: str
    goal: str
    idea: str
    config: ResearchCycleConfig
    allowed_tools: tuple[str, ...]
    constraints: tuple[str, ...]
    outputs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "builder_version": self.builder_version,
            "agent_id": self.agent_id,
            "role": self.role,
            "goal": self.goal,
            "idea": self.idea,
            "config": loads(self.config.to_json()),
            "allowed_tools": list(self.allowed_tools),
            "constraints": list(self.constraints),
            "outputs": list(self.outputs),
        }

    def to_json(self) -> str:
        return dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True)
class AgentBuilderState:
    idea: str
    agent_spec_built: bool = False
    agent_spec_validated: bool = False
    config_validated: bool = False
    cycle_completed: bool = False
    completed_steps: tuple[str, ...] = ()

    def with_step(self, step: str, **updates: object) -> "AgentBuilderState":
        payload = asdict(self)
        payload.update(updates)
        payload["completed_steps"] = (*self.completed_steps, step)
        return AgentBuilderState(**payload)

    def to_json(self) -> str:
        return dumps(asdict(self), indent=2, sort_keys=True)


@dataclass(frozen=True)
class AgentBuilderReport:
    spec: AgentSpec
    cycle: ResearchCycleReport
    state: AgentBuilderState

    def to_markdown(self) -> str:
        lines = [
            "# QuantSigma Agent Builder Report",
            "",
            "This report demonstrates a Wonderful-style builder pattern for financial ML research agents.",
            "The builder creates an agent spec and dynamic config, then validates both before dispatching",
            "to an allowlisted research runner. The generated agent cannot execute arbitrary code.",
            "",
            "## Builder Decision",
            "",
            f"- agent id: `{self.spec.agent_id}`",
            f"- role: `{self.spec.role}`",
            f"- runner: `{self.spec.config.runner}`",
            f"- strategy: `{self.spec.config.strategy_name}`",
            f"- promotion decision: `{self.cycle.audit.decision}`",
            "",
            "## Agent Spec",
            "",
            "```json",
            self.spec.to_json(),
            "```",
            "",
            "## Builder State",
            "",
            "```json",
            self.state.to_json(),
            "```",
            "",
            "## Downstream Research Cycle",
            "",
            self.cycle.to_markdown().rstrip(),
        ]
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class AgentBuilderArtifactPaths:
    output: Path
    spec_output: Path
    contract_output: Path
    state_output: Path


def build_agent_spec(idea: str) -> AgentSpec:
    config = build_experiment_config(idea)
    role = "financial_ml_experiment_agent"
    return AgentSpec(
        schema_version=AGENT_SPEC_SCHEMA_VERSION,
        builder_version=AGENT_BUILDER_VERSION,
        agent_id=f"{role}:{config.run_id}",
        role=role,
        goal=_goal_from_config(config),
        idea=config.idea,
        config=config,
        allowed_tools=tuple(ALLOWED_RESEARCH_TOOLS),
        constraints=tuple(sorted(ALLOWED_AGENT_CONSTRAINTS)),
        outputs=DEFAULT_AGENT_OUTPUTS,
    )


def validate_agent_spec(spec: AgentSpec) -> AgentSpec:
    errors: list[str] = []
    if spec.schema_version != AGENT_SPEC_SCHEMA_VERSION:
        errors.append(f"unsupported agent spec schema: {spec.schema_version}")
    if spec.builder_version != AGENT_BUILDER_VERSION:
        errors.append(f"unsupported agent builder version: {spec.builder_version}")
    if not spec.agent_id.strip():
        errors.append("agent_id is required")
    if spec.role not in ALLOWED_AGENT_ROLES:
        errors.append(f"role is not allowlisted: {spec.role}")
    if not spec.agent_id.startswith(f"{spec.role}:"):
        errors.append("agent_id must be namespaced by role")
    if spec.idea != spec.config.idea:
        errors.append("spec idea must match config idea")
    if len(spec.allowed_tools) != len(set(spec.allowed_tools)):
        errors.append("agent spec contains duplicate tools")
    if set(spec.allowed_tools) - set(ALLOWED_RESEARCH_TOOLS):
        errors.append("agent spec contains non-allowlisted tools")
    if len(spec.constraints) != len(set(spec.constraints)):
        errors.append("agent spec contains duplicate constraints")
    if set(spec.constraints) - ALLOWED_AGENT_CONSTRAINTS:
        errors.append("agent spec contains non-allowlisted constraints")
    if "experiment_run.v1" not in spec.outputs:
        errors.append("agent spec must export experiment_run.v1")
    if "contract_only_promotion_review" not in spec.constraints:
        errors.append("agent spec must require contract-only promotion review")
    if "no_arbitrary_code" not in spec.constraints:
        errors.append("agent spec must block arbitrary code")

    try:
        validate_experiment_config(spec.config)
    except ValueError as exc:
        errors.append(str(exc))

    if errors:
        raise ValueError("invalid agent spec: " + "; ".join(errors))
    return spec


def parse_agent_spec_json(text: str) -> AgentSpec:
    try:
        payload = loads(text)
    except JSONDecodeError as exc:
        raise ValueError(f"invalid agent spec JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ValueError("invalid agent spec: root must be an object")

    unknown = set(payload) - AGENT_SPEC_KEYS
    missing = AGENT_SPEC_KEYS - set(payload)
    errors: list[str] = []
    if unknown:
        errors.append(f"unknown agent spec keys: {', '.join(sorted(unknown))}")
    if missing:
        errors.append(f"missing agent spec keys: {', '.join(sorted(missing))}")
    if errors:
        raise ValueError("invalid agent spec: " + "; ".join(errors))

    config_payload = payload["config"]
    if not isinstance(config_payload, dict):
        raise ValueError("invalid agent spec: config must be an object")
    unknown_config = set(config_payload) - CONFIG_KEYS
    missing_config = CONFIG_KEYS - set(config_payload)
    if unknown_config or missing_config:
        parts: list[str] = []
        if unknown_config:
            parts.append(f"unknown config keys: {', '.join(sorted(unknown_config))}")
        if missing_config:
            parts.append(f"missing config keys: {', '.join(sorted(missing_config))}")
        raise ValueError("invalid agent spec config: " + "; ".join(parts))

    spec = AgentSpec(
        schema_version=_require_str(payload, "schema_version"),
        builder_version=_require_str(payload, "builder_version"),
        agent_id=_require_str(payload, "agent_id"),
        role=_require_str(payload, "role"),
        goal=_require_str(payload, "goal"),
        idea=_require_str(payload, "idea"),
        config=_parse_research_cycle_config(config_payload),
        allowed_tools=_require_str_tuple(payload, "allowed_tools"),
        constraints=_require_str_tuple(payload, "constraints"),
        outputs=_require_str_tuple(payload, "outputs"),
    )
    return validate_agent_spec(spec)


def run_agent_builder(idea: str) -> AgentBuilderReport:
    state = AgentBuilderState(idea=idea)
    spec = build_agent_spec(idea)
    state = state.with_step("build_agent_spec", agent_spec_built=True)

    spec = validate_agent_spec(spec)
    state = state.with_step(
        "validate_agent_spec",
        agent_spec_validated=True,
        config_validated=True,
    )

    cycle = run_research_cycle_from_config(spec.config)
    state = state.with_step("run_research_cycle_from_agent_spec", cycle_completed=True)
    return AgentBuilderReport(spec=spec, cycle=cycle, state=state)


def run_agent_builder_from_spec(spec: AgentSpec) -> AgentBuilderReport:
    state = AgentBuilderState(idea=spec.idea)
    spec = validate_agent_spec(spec)
    state = state.with_step("validate_agent_spec", agent_spec_validated=True, config_validated=True)

    cycle = run_research_cycle_from_config(spec.config)
    state = state.with_step("run_research_cycle_from_agent_spec", cycle_completed=True)
    return AgentBuilderReport(spec=spec, cycle=cycle, state=state)


def write_agent_builder_artifacts(report: AgentBuilderReport, paths: AgentBuilderArtifactPaths) -> None:
    writes = {
        paths.output: report.to_markdown(),
        paths.spec_output: report.spec.to_json(),
        paths.contract_output: report.cycle.contract.to_json(),
        paths.state_output: report.state.to_json(),
    }
    for path, text in writes.items():
        _atomic_write_text(path, text)


def default_agent_builder_paths(run_dir: Path | None = None, *, run_id: str | None = None) -> AgentBuilderArtifactPaths:
    if run_dir is None:
        return AgentBuilderArtifactPaths(
            output=Path("docs/benchmarks/agent_builder_report.md"),
            spec_output=Path("docs/benchmarks/agent_spec.json"),
            contract_output=Path("docs/benchmarks/experiment_run_contract.json"),
            state_output=Path("docs/benchmarks/agent_builder_state.json"),
        )
    if run_id:
        run_dir = run_dir / run_id
    return AgentBuilderArtifactPaths(
        output=run_dir / "agent_builder_report.md",
        spec_output=run_dir / "agent_spec.json",
        contract_output=run_dir / "experiment_run_contract.json",
        state_output=run_dir / "agent_builder_state.json",
    )


def _goal_from_config(config: ResearchCycleConfig) -> str:
    return (
        "Run a leakage-aware financial ML experiment from the idea, using only "
        f"the `{config.runner}` runner and exporting an experiment_run.v1 contract."
    )


def _parse_research_cycle_config(payload: dict[str, object]) -> ResearchCycleConfig:
    thresholds = payload["thresholds"]
    if not isinstance(thresholds, list | tuple):
        raise ValueError("invalid agent spec config: thresholds must be a list")
    return ResearchCycleConfig(
        run_id=_require_str(payload, "run_id"),
        idea=_require_str(payload, "idea"),
        runner=_require_str(payload, "runner"),
        strategy_name=_require_str(payload, "strategy_name"),
        data_source=_require_str(payload, "data_source"),
        train_size=_require_int(payload, "train_size"),
        validation_size=_require_int(payload, "validation_size"),
        test_size=_require_int(payload, "test_size"),
        step_size=_require_int(payload, "step_size"),
        thresholds=tuple(_require_float(value, "thresholds") for value in thresholds),
        transaction_cost=_require_float(payload["transaction_cost"], "transaction_cost"),
        allow_live_trading=_require_bool(payload, "allow_live_trading"),
    )


def _require_str(payload: dict[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"invalid agent spec: {key} must be a string")
    return value


def _require_str_tuple(payload: dict[str, object], key: str) -> tuple[str, ...]:
    value = payload[key]
    if not isinstance(value, list | tuple):
        raise ValueError(f"invalid agent spec: {key} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"invalid agent spec: {key} must contain only strings")
    return tuple(value)


def _require_int(payload: dict[str, object], key: str) -> int:
    value = payload[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"invalid agent spec config: {key} must be an integer")
    return value


def _require_bool(payload: dict[str, object], key: str) -> bool:
    value = payload[key]
    if not isinstance(value, bool):
        raise ValueError(f"invalid agent spec config: {key} must be a boolean")
    return value


def _require_float(value: object, key: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"invalid agent spec config: {key} must be numeric")
    return float(value)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
