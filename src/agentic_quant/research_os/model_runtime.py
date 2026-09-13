from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from json import JSONDecodeError, dumps, loads
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping, Protocol, Sequence

from agentic_quant.research_os.agent_builder import build_agent_spec, parse_agent_spec_json
from agentic_quant.research_os.audit import audit_experiment_run_contract
from agentic_quant.research_os.contract import parse_experiment_run_contract
from agentic_quant.research_os.cycle import run_research_cycle_from_config


MODEL_AGENT_RUNTIME_SCHEMA_VERSION = "model_agent_runtime.v1"
MODEL_AGENT_TOOL_SEQUENCE = (
    "build_agent_spec",
    "validate_agent_spec",
    "run_research_cycle",
    "review_promotion",
    "finalize_agent_report",
)
APPROVAL_REQUIRED_TOOLS = frozenset({"run_research_cycle"})
MODEL_AGENT_STATUSES = frozenset(
    {
        "running",
        "awaiting_approval",
        "completed",
        "rejected",
        "failed",
    }
)


def _function_tool(name: str, description: str, argument_name: str, argument_description: str) -> dict[str, object]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {
                argument_name: {
                    "type": "string",
                    "description": argument_description,
                }
            },
            "required": [argument_name],
            "additionalProperties": False,
        },
        "strict": True,
    }


MODEL_AGENT_TOOL_DEFINITIONS = (
    _function_tool(
        "build_agent_spec",
        "Build an agent_spec.v1 draft from the research idea without executing research code.",
        "idea",
        "The exact research idea from the durable runtime state.",
    ),
    _function_tool(
        "validate_agent_spec",
        "Validate the persisted agent spec, allowlisted tools, constraints, and experiment config.",
        "run_id",
        "The exact run id from the durable runtime state.",
    ),
    _function_tool(
        "run_research_cycle",
        "Run the approved synthetic-data research cycle. This action requires human approval.",
        "run_id",
        "The exact run id from the durable runtime state.",
    ),
    _function_tool(
        "review_promotion",
        "Review the experiment_run.v1 contract through the promotion gate.",
        "run_id",
        "The exact run id from the durable runtime state.",
    ),
    _function_tool(
        "finalize_agent_report",
        "Write the final model-agent trace and artifact summary after review.",
        "run_id",
        "The exact run id from the durable runtime state.",
    ),
)


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class ModelToolCall:
    call_id: str
    response_id: str
    name: str
    arguments: Mapping[str, object]
    usage: ModelUsage = ModelUsage()

    def to_dict(self) -> dict[str, object]:
        return {
            "call_id": self.call_id,
            "response_id": self.response_id,
            "name": self.name,
            "arguments": dict(self.arguments),
            "usage": self.usage.to_dict(),
        }


@dataclass(frozen=True)
class ModelAgentCheckpoint:
    schema_version: str
    run_id: str
    idea: str
    model: str
    status: str
    completed_tools: tuple[str, ...] = ()
    model_calls: tuple[ModelToolCall, ...] = ()
    pending_call: ModelToolCall | None = None
    approval_decision: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "idea": self.idea,
            "model": self.model,
            "status": self.status,
            "completed_tools": list(self.completed_tools),
            "model_calls": [call.to_dict() for call in self.model_calls],
            "pending_call": None if self.pending_call is None else self.pending_call.to_dict(),
            "approval_decision": self.approval_decision,
            "error": self.error,
            "usage": self.usage.to_dict(),
        }

    def to_json(self) -> str:
        return dumps(self.to_dict(), indent=2, sort_keys=True)

    @property
    def usage(self) -> ModelUsage:
        return ModelUsage(
            input_tokens=sum(call.usage.input_tokens for call in self.model_calls),
            output_tokens=sum(call.usage.output_tokens for call in self.model_calls),
            total_tokens=sum(call.usage.total_tokens for call in self.model_calls),
        )


@dataclass(frozen=True)
class ModelAgentArtifactPaths:
    checkpoint: Path
    spec: Path
    cycle_report: Path
    contract: Path
    cycle_state: Path
    promotion_review: Path
    final_report: Path


class ModelToolSelector(Protocol):
    model: str

    def select_tool(
        self,
        checkpoint: ModelAgentCheckpoint,
        tools: Sequence[Mapping[str, object]],
    ) -> ModelToolCall: ...


class OpenAIResponsesToolSelector:
    """Select the next allowlisted action with the OpenAI Responses API."""

    def __init__(
        self,
        *,
        model: str = "gpt-5.6",
        client: object | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        self.model = model
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError("Install the agent extra with `uv sync --extra agent`.") from exc
            client = OpenAI(timeout=timeout_seconds, max_retries=max_retries)
        self._client = client

    def select_tool(
        self,
        checkpoint: ModelAgentCheckpoint,
        tools: Sequence[Mapping[str, object]],
    ) -> ModelToolCall:
        expected = _expected_tool(checkpoint)
        state = {
            "schema_version": checkpoint.schema_version,
            "run_id": checkpoint.run_id,
            "idea": checkpoint.idea,
            "status": checkpoint.status,
            "completed_tools": list(checkpoint.completed_tools),
            "next_required_action": expected,
            "safety": {
                "arbitrary_code": "blocked",
                "live_trading": "blocked",
                "approval_required_for": sorted(APPROVAL_REQUIRED_TOOLS),
            },
        }
        response = self._client.responses.create(
            model=self.model,
            instructions=(
                "You are a financial ML research workflow router. Select exactly one function tool. "
                "Use the next_required_action from the durable state, copy its required argument exactly, "
                "and never request arbitrary code, shell access, broker access, or live trading."
            ),
            input=dumps(state, sort_keys=True),
            tools=[dict(tool) for tool in tools],
            tool_choice="required",
            parallel_tool_calls=False,
            store=False,
        )
        calls = [item for item in response.output if _value(item, "type") == "function_call"]
        if len(calls) != 1:
            raise ValueError(f"model must return exactly one function call, received {len(calls)}")
        item = calls[0]
        raw_arguments = _value(item, "arguments")
        try:
            arguments = loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        except JSONDecodeError as exc:
            raise ValueError(f"model returned invalid tool arguments: {exc.msg}") from exc
        if not isinstance(arguments, dict):
            raise ValueError("model tool arguments must be a JSON object")
        return ModelToolCall(
            call_id=str(_value(item, "call_id")),
            response_id=str(_value(response, "id")),
            name=str(_value(item, "name")),
            arguments=arguments,
            usage=_model_usage(_value(response, "usage", default=None)),
        )


def start_model_agent(
    idea: str,
    *,
    run_dir: Path,
    selector: ModelToolSelector,
) -> ModelAgentCheckpoint:
    normalized = idea.strip()
    if not normalized:
        raise ValueError("idea must not be empty")
    run_id = sha256(normalized.lower().encode("utf-8")).hexdigest()[:12]
    paths = model_agent_paths(run_dir, run_id)
    checkpoint = ModelAgentCheckpoint(
        schema_version=MODEL_AGENT_RUNTIME_SCHEMA_VERSION,
        run_id=run_id,
        idea=normalized,
        model=selector.model,
        status="running",
    )
    _write_checkpoint(checkpoint, paths.checkpoint)
    return _advance_model_agent(checkpoint, paths=paths, selector=selector)


def resume_model_agent(
    checkpoint_path: Path,
    *,
    selector: ModelToolSelector,
    approve: bool,
) -> ModelAgentCheckpoint:
    checkpoint = load_model_agent_checkpoint(checkpoint_path)
    if checkpoint.status != "awaiting_approval" or checkpoint.pending_call is None:
        raise ValueError("checkpoint is not awaiting approval")
    if selector.model != checkpoint.model:
        raise ValueError("selector model must match checkpoint model")
    paths = model_agent_paths(checkpoint_path.parent.parent, checkpoint.run_id)
    if paths.checkpoint.resolve() != checkpoint_path.resolve():
        raise ValueError("checkpoint path does not match its run id")
    if not approve:
        rejected = replace(
            checkpoint,
            status="rejected",
            pending_call=None,
            approval_decision="rejected",
        )
        _write_checkpoint(rejected, paths.checkpoint)
        return rejected

    try:
        _execute_tool(checkpoint.pending_call, checkpoint, paths)
        resumed = replace(
            checkpoint,
            status="running",
            completed_tools=(*checkpoint.completed_tools, checkpoint.pending_call.name),
            pending_call=None,
            approval_decision="approved",
            error=None,
        )
        _write_checkpoint(resumed, paths.checkpoint)
        return _advance_model_agent(resumed, paths=paths, selector=selector)
    except Exception as exc:
        failed = replace(checkpoint, status="failed", error=str(exc))
        _write_checkpoint(failed, paths.checkpoint)
        raise


def load_model_agent_checkpoint(path: Path) -> ModelAgentCheckpoint:
    try:
        payload = loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise ValueError(f"invalid model agent checkpoint JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("model agent checkpoint must be an object")
    checkpoint = ModelAgentCheckpoint(
        schema_version=_required_str(payload, "schema_version"),
        run_id=_required_str(payload, "run_id"),
        idea=_required_str(payload, "idea"),
        model=_required_str(payload, "model"),
        status=_required_str(payload, "status"),
        completed_tools=_string_tuple(payload.get("completed_tools", []), "completed_tools"),
        model_calls=tuple(_parse_tool_call(item) for item in _list(payload, "model_calls")),
        pending_call=None if payload.get("pending_call") is None else _parse_tool_call(payload["pending_call"]),
        approval_decision=_optional_str(payload.get("approval_decision"), "approval_decision"),
        error=_optional_str(payload.get("error"), "error"),
    )
    _validate_checkpoint(checkpoint)
    return checkpoint


def validate_model_tool_call(call: ModelToolCall, checkpoint: ModelAgentCheckpoint) -> ModelToolCall:
    expected = _expected_tool(checkpoint)
    if call.name not in MODEL_AGENT_TOOL_SEQUENCE:
        raise ValueError(f"model selected non-allowlisted tool: {call.name}")
    if call.name != expected:
        raise ValueError(f"model selected out-of-order tool: expected {expected}, received {call.name}")
    argument_name = "idea" if call.name == "build_agent_spec" else "run_id"
    if set(call.arguments) != {argument_name}:
        raise ValueError(f"invalid arguments for {call.name}: expected only {argument_name}")
    value = call.arguments[argument_name]
    if not isinstance(value, str):
        raise ValueError(f"invalid arguments for {call.name}: {argument_name} must be a string")
    expected_value = checkpoint.idea if argument_name == "idea" else checkpoint.run_id
    if value != expected_value:
        raise ValueError(f"invalid arguments for {call.name}: {argument_name} must match durable state")
    if not call.call_id.strip() or not call.response_id.strip():
        raise ValueError("model tool call ids must not be empty")
    return call


def model_agent_paths(run_dir: Path, run_id: str) -> ModelAgentArtifactPaths:
    root = run_dir / run_id
    return ModelAgentArtifactPaths(
        checkpoint=root / "model_agent_checkpoint.json",
        spec=root / "agent_spec.json",
        cycle_report=root / "research_cycle_report.md",
        contract=root / "experiment_run_contract.json",
        cycle_state=root / "research_workflow_state.json",
        promotion_review=root / "contract_promotion_review.md",
        final_report=root / "model_agent_report.md",
    )


def _advance_model_agent(
    checkpoint: ModelAgentCheckpoint,
    *,
    paths: ModelAgentArtifactPaths,
    selector: ModelToolSelector,
) -> ModelAgentCheckpoint:
    while checkpoint.status == "running":
        if len(checkpoint.completed_tools) == len(MODEL_AGENT_TOOL_SEQUENCE):
            checkpoint = replace(checkpoint, status="completed", error=None)
            _write_checkpoint(checkpoint, paths.checkpoint)
            return checkpoint
        try:
            call = validate_model_tool_call(
                selector.select_tool(checkpoint, MODEL_AGENT_TOOL_DEFINITIONS),
                checkpoint,
            )
            checkpoint = replace(checkpoint, model_calls=(*checkpoint.model_calls, call))
            if call.name in APPROVAL_REQUIRED_TOOLS:
                checkpoint = replace(checkpoint, status="awaiting_approval", pending_call=call)
                _write_checkpoint(checkpoint, paths.checkpoint)
                return checkpoint
            _execute_tool(call, checkpoint, paths)
            checkpoint = replace(
                checkpoint,
                completed_tools=(*checkpoint.completed_tools, call.name),
                error=None,
            )
            _write_checkpoint(checkpoint, paths.checkpoint)
        except Exception as exc:
            checkpoint = replace(checkpoint, status="failed", error=str(exc))
            _write_checkpoint(checkpoint, paths.checkpoint)
            raise
    return checkpoint


def _execute_tool(
    call: ModelToolCall,
    checkpoint: ModelAgentCheckpoint,
    paths: ModelAgentArtifactPaths,
) -> None:
    if call.name == "build_agent_spec":
        spec = build_agent_spec(checkpoint.idea)
        if spec.config.run_id != checkpoint.run_id:
            raise ValueError("agent spec run id does not match durable state")
        _atomic_write_text(paths.spec, spec.to_json())
        return
    if call.name == "validate_agent_spec":
        spec = parse_agent_spec_json(paths.spec.read_text(encoding="utf-8"))
        if spec.config.run_id != checkpoint.run_id:
            raise ValueError("validated spec run id does not match durable state")
        _atomic_write_text(paths.spec, spec.to_json())
        return
    if call.name == "run_research_cycle":
        spec = parse_agent_spec_json(paths.spec.read_text(encoding="utf-8"))
        report = run_research_cycle_from_config(spec.config)
        _atomic_write_text(paths.cycle_report, report.to_markdown())
        _atomic_write_text(paths.contract, report.contract.to_json())
        _atomic_write_text(paths.cycle_state, report.state.to_json())
        return
    if call.name == "review_promotion":
        contract = parse_experiment_run_contract(paths.contract.read_text(encoding="utf-8"))
        review = audit_experiment_run_contract(contract)
        _atomic_write_text(paths.promotion_review, review.to_markdown())
        return
    if call.name == "finalize_agent_report":
        _atomic_write_text(paths.final_report, _final_report(checkpoint, paths))
        return
    raise ValueError(f"tool is not implemented: {call.name}")


def _final_report(checkpoint: ModelAgentCheckpoint, paths: ModelAgentArtifactPaths) -> str:
    lines = [
        "# Model-Directed Research Agent Report",
        "",
        f"- runtime schema: `{checkpoint.schema_version}`",
        f"- model: `{checkpoint.model}`",
        f"- run id: `{checkpoint.run_id}`",
        f"- approval decision: `{checkpoint.approval_decision}`",
        f"- model calls: {len(checkpoint.model_calls)}",
        f"- input tokens: {checkpoint.usage.input_tokens}",
        f"- output tokens: {checkpoint.usage.output_tokens}",
        f"- total tokens: {checkpoint.usage.total_tokens}",
        "",
        "## Model-Selected Tools",
        "",
        "| Sequence | Tool | Response | Call |",
        "|---:|---|---|---|",
    ]
    for index, call in enumerate(checkpoint.model_calls, start=1):
        lines.append(f"| {index} | `{call.name}` | `{call.response_id}` | `{call.call_id}` |")
    lines.extend(
        [
            "",
            "## Durable Artifacts",
            "",
            f"- checkpoint: `{paths.checkpoint}`",
            f"- agent spec: `{paths.spec}`",
            f"- research cycle report: `{paths.cycle_report}`",
            f"- experiment contract: `{paths.contract}`",
            f"- workflow state: `{paths.cycle_state}`",
            f"- promotion review: `{paths.promotion_review}`",
            "",
            "The application validates every model-selected tool and argument against the durable state. ",
            "The research cycle cannot execute until a human explicitly approves the checkpoint.",
        ]
    )
    return "\n".join(lines) + "\n"


def _expected_tool(checkpoint: ModelAgentCheckpoint) -> str:
    if len(checkpoint.completed_tools) >= len(MODEL_AGENT_TOOL_SEQUENCE):
        raise ValueError("model agent has no remaining tools")
    return MODEL_AGENT_TOOL_SEQUENCE[len(checkpoint.completed_tools)]


def _write_checkpoint(checkpoint: ModelAgentCheckpoint, path: Path) -> None:
    _validate_checkpoint(checkpoint)
    _atomic_write_text(path, checkpoint.to_json())


def _validate_checkpoint(checkpoint: ModelAgentCheckpoint) -> None:
    if checkpoint.schema_version != MODEL_AGENT_RUNTIME_SCHEMA_VERSION:
        raise ValueError(f"unsupported model agent checkpoint schema: {checkpoint.schema_version}")
    if checkpoint.status not in MODEL_AGENT_STATUSES:
        raise ValueError(f"invalid model agent status: {checkpoint.status}")
    expected_prefix = MODEL_AGENT_TOOL_SEQUENCE[: len(checkpoint.completed_tools)]
    if checkpoint.completed_tools != expected_prefix:
        raise ValueError("completed tools must follow the allowlisted sequence")
    if checkpoint.status == "awaiting_approval":
        if checkpoint.pending_call is None or checkpoint.pending_call.name not in APPROVAL_REQUIRED_TOOLS:
            raise ValueError("awaiting approval checkpoint must contain an approval-required call")
    elif checkpoint.pending_call is not None:
        raise ValueError("pending call is only valid while awaiting approval")


def _parse_tool_call(payload: object) -> ModelToolCall:
    if not isinstance(payload, dict):
        raise ValueError("model tool call must be an object")
    arguments = payload.get("arguments")
    if not isinstance(arguments, dict):
        raise ValueError("model tool call arguments must be an object")
    usage_payload = payload.get("usage", {})
    if not isinstance(usage_payload, dict):
        raise ValueError("model usage must be an object")
    return ModelToolCall(
        call_id=_required_str(payload, "call_id"),
        response_id=_required_str(payload, "response_id"),
        name=_required_str(payload, "name"),
        arguments=arguments,
        usage=ModelUsage(
            input_tokens=_non_negative_int(usage_payload.get("input_tokens", 0), "input_tokens"),
            output_tokens=_non_negative_int(usage_payload.get("output_tokens", 0), "output_tokens"),
            total_tokens=_non_negative_int(usage_payload.get("total_tokens", 0), "total_tokens"),
        ),
    )


def _model_usage(payload: object) -> ModelUsage:
    if payload is None:
        return ModelUsage()
    return ModelUsage(
        input_tokens=int(_value(payload, "input_tokens", default=0)),
        output_tokens=int(_value(payload, "output_tokens", default=0)),
        total_tokens=int(_value(payload, "total_tokens", default=0)),
    )


def _value(payload: object, key: str, *, default: Any = ...) -> Any:
    if isinstance(payload, Mapping):
        if key in payload:
            return payload[key]
    elif hasattr(payload, key):
        return getattr(payload, key)
    if default is not ...:
        return default
    raise ValueError(f"model response is missing {key}")


def _required_str(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional_str(value: object, key: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string or null")
    return value


def _list(payload: Mapping[str, object], key: str) -> list[object]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _string_tuple(value: object, key: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return tuple(value)


def _non_negative_int(value: object, key: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{key} must be a non-negative integer")
    return value


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
