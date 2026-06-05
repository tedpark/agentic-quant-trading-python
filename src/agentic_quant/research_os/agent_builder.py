from __future__ import annotations

from dataclasses import asdict, dataclass
from json import dumps, loads

from agentic_quant.research_os.cycle import (
    ALLOWED_RESEARCH_TOOLS,
    ResearchCycleConfig,
    ResearchCycleReport,
    build_experiment_config,
    run_research_cycle_from_config,
    validate_experiment_config,
)


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


@dataclass(frozen=True)
class AgentSpec:
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


def build_agent_spec(idea: str) -> AgentSpec:
    config = build_experiment_config(idea)
    role = "financial_ml_experiment_agent"
    return AgentSpec(
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
    if not spec.agent_id.strip():
        errors.append("agent_id is required")
    if spec.role not in ALLOWED_AGENT_ROLES:
        errors.append(f"role is not allowlisted: {spec.role}")
    if spec.idea != spec.config.idea:
        errors.append("spec idea must match config idea")
    if set(spec.allowed_tools) - set(ALLOWED_RESEARCH_TOOLS):
        errors.append("agent spec contains non-allowlisted tools")
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


def _goal_from_config(config: ResearchCycleConfig) -> str:
    return (
        "Run a leakage-aware financial ML experiment from the idea, using only "
        f"the `{config.runner}` runner and exporting an experiment_run.v1 contract."
    )
