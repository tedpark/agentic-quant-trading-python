from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from types import SimpleNamespace
from typing import Mapping, Sequence

import pytest

from agentic_quant.research_os import cli as cli_module
from agentic_quant.research_os.model_runtime import (
    MODEL_AGENT_RUNTIME_SCHEMA_VERSION,
    MODEL_AGENT_TOOL_DEFINITIONS,
    MODEL_AGENT_TOOL_SEQUENCE,
    ModelAgentCheckpoint,
    ModelToolCall,
    ModelUsage,
    OpenAIResponsesToolSelector,
    load_model_agent_checkpoint,
    model_agent_paths,
    resume_model_agent,
    start_model_agent,
)


IDEA = "HMM regime features improve pair spread entries"


@dataclass
class SequenceSelector:
    model: str = "test-model"
    invalid_name: str | None = None
    invalid_arguments: Mapping[str, object] | None = None

    def select_tool(
        self,
        checkpoint: ModelAgentCheckpoint,
        tools: Sequence[Mapping[str, object]],
    ) -> ModelToolCall:
        assert all(tool["strict"] is True for tool in tools)
        expected = MODEL_AGENT_TOOL_SEQUENCE[len(checkpoint.completed_tools)]
        name = self.invalid_name or expected
        arguments: Mapping[str, object]
        if self.invalid_arguments is not None:
            arguments = self.invalid_arguments
        elif name == "build_agent_spec":
            arguments = {"idea": checkpoint.idea}
        else:
            arguments = {"run_id": checkpoint.run_id}
        sequence = len(checkpoint.model_calls) + 1
        return ModelToolCall(
            call_id=f"call-{sequence}",
            response_id=f"response-{sequence}",
            name=name,
            arguments=arguments,
            usage=ModelUsage(input_tokens=10, output_tokens=2, total_tokens=12),
        )


class FakeResponses:
    def __init__(self, *, output: list[object]) -> None:
        self.output = output
        self.kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> object:
        self.kwargs = kwargs
        return SimpleNamespace(
            id="resp-123",
            output=self.output,
            usage=SimpleNamespace(input_tokens=31, output_tokens=7, total_tokens=38),
        )


class FakeClient:
    def __init__(self, *, output: list[object]) -> None:
        self.responses = FakeResponses(output=output)


def _run_id() -> str:
    return sha256(IDEA.lower().encode("utf-8")).hexdigest()[:12]


def test_model_agent_tool_definitions_are_strict_and_closed() -> None:
    assert tuple(tool["name"] for tool in MODEL_AGENT_TOOL_DEFINITIONS) == MODEL_AGENT_TOOL_SEQUENCE
    for tool in MODEL_AGENT_TOOL_DEFINITIONS:
        assert tool["type"] == "function"
        assert tool["strict"] is True
        parameters = tool["parameters"]
        assert isinstance(parameters, dict)
        assert parameters["additionalProperties"] is False
        assert len(parameters["required"]) == 1


def test_model_agent_checkpoints_before_approval_required_execution(tmp_path: Path) -> None:
    checkpoint = start_model_agent(IDEA, run_dir=tmp_path, selector=SequenceSelector())
    paths = model_agent_paths(tmp_path, checkpoint.run_id)

    assert checkpoint.schema_version == MODEL_AGENT_RUNTIME_SCHEMA_VERSION
    assert checkpoint.status == "awaiting_approval"
    assert checkpoint.completed_tools == ("build_agent_spec", "validate_agent_spec")
    assert checkpoint.pending_call is not None
    assert checkpoint.pending_call.name == "run_research_cycle"
    assert paths.checkpoint.exists()
    assert paths.spec.exists()
    assert not paths.cycle_report.exists()
    assert checkpoint.usage == ModelUsage(input_tokens=30, output_tokens=6, total_tokens=36)


def test_model_agent_resume_after_approval_completes_and_writes_artifacts(tmp_path: Path) -> None:
    paused = start_model_agent(IDEA, run_dir=tmp_path, selector=SequenceSelector())
    paths = model_agent_paths(tmp_path, paused.run_id)
    completed = resume_model_agent(paths.checkpoint, selector=SequenceSelector(), approve=True)

    assert completed.status == "completed"
    assert completed.approval_decision == "approved"
    assert completed.pending_call is None
    assert completed.completed_tools == MODEL_AGENT_TOOL_SEQUENCE
    assert len(completed.model_calls) == len(MODEL_AGENT_TOOL_SEQUENCE)
    assert completed.usage == ModelUsage(input_tokens=50, output_tokens=10, total_tokens=60)
    for path in (
        paths.spec,
        paths.cycle_report,
        paths.contract,
        paths.cycle_state,
        paths.promotion_review,
        paths.final_report,
    ):
        assert path.exists()
    assert '"schema_version": "experiment_run.v1"' in paths.contract.read_text(encoding="utf-8")
    assert "approval decision: `approved`" in paths.final_report.read_text(encoding="utf-8")
    reloaded = load_model_agent_checkpoint(paths.checkpoint)
    assert reloaded == completed


def test_model_agent_rejection_is_durable_and_does_not_execute_cycle(tmp_path: Path) -> None:
    paused = start_model_agent(IDEA, run_dir=tmp_path, selector=SequenceSelector())
    paths = model_agent_paths(tmp_path, paused.run_id)
    rejected = resume_model_agent(paths.checkpoint, selector=SequenceSelector(), approve=False)

    assert rejected.status == "rejected"
    assert rejected.approval_decision == "rejected"
    assert rejected.pending_call is None
    assert not paths.cycle_report.exists()
    assert load_model_agent_checkpoint(paths.checkpoint).status == "rejected"


def test_model_agent_fails_closed_on_non_allowlisted_tool(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-allowlisted tool"):
        start_model_agent(IDEA, run_dir=tmp_path, selector=SequenceSelector(invalid_name="shell"))

    checkpoint = load_model_agent_checkpoint(model_agent_paths(tmp_path, _run_id()).checkpoint)
    assert checkpoint.status == "failed"
    assert "non-allowlisted tool" in str(checkpoint.error)


def test_model_agent_fails_closed_on_arguments_that_do_not_match_state(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="expected only idea"):
        start_model_agent(
            IDEA,
            run_dir=tmp_path,
            selector=SequenceSelector(invalid_arguments={"idea": IDEA, "shell": "echo unsafe"}),
        )

    checkpoint = load_model_agent_checkpoint(model_agent_paths(tmp_path, _run_id()).checkpoint)
    assert checkpoint.status == "failed"
    assert checkpoint.completed_tools == ()


def test_openai_responses_selector_sends_strict_function_tools_and_parses_call() -> None:
    client = FakeClient(
        output=[
            SimpleNamespace(
                type="function_call",
                call_id="call-openai-1",
                name="build_agent_spec",
                arguments=dumps({"idea": IDEA}),
            )
        ]
    )
    selector = OpenAIResponsesToolSelector(model="gpt-test", client=client)
    checkpoint = ModelAgentCheckpoint(
        schema_version=MODEL_AGENT_RUNTIME_SCHEMA_VERSION,
        run_id=_run_id(),
        idea=IDEA,
        model="gpt-test",
        status="running",
    )

    call = selector.select_tool(checkpoint, MODEL_AGENT_TOOL_DEFINITIONS)

    assert call.name == "build_agent_spec"
    assert call.arguments == {"idea": IDEA}
    assert call.response_id == "resp-123"
    assert call.usage == ModelUsage(input_tokens=31, output_tokens=7, total_tokens=38)
    assert client.responses.kwargs is not None
    assert client.responses.kwargs["tool_choice"] == "required"
    assert client.responses.kwargs["parallel_tool_calls"] is False
    assert client.responses.kwargs["store"] is False
    assert all(tool["strict"] is True for tool in client.responses.kwargs["tools"])
    state = loads(str(client.responses.kwargs["input"]))
    assert state["next_required_action"] == "build_agent_spec"
    assert state["safety"]["live_trading"] == "blocked"


def test_openai_responses_selector_rejects_missing_or_multiple_function_calls() -> None:
    checkpoint = ModelAgentCheckpoint(
        schema_version=MODEL_AGENT_RUNTIME_SCHEMA_VERSION,
        run_id=_run_id(),
        idea=IDEA,
        model="gpt-test",
        status="running",
    )
    no_call = OpenAIResponsesToolSelector(
        model="gpt-test",
        client=FakeClient(output=[SimpleNamespace(type="message")]),
    )
    with pytest.raises(ValueError, match="exactly one function call"):
        no_call.select_tool(checkpoint, MODEL_AGENT_TOOL_DEFINITIONS)

    function_call = SimpleNamespace(
        type="function_call",
        call_id="call-1",
        name="build_agent_spec",
        arguments=dumps({"idea": IDEA}),
    )
    multiple = OpenAIResponsesToolSelector(
        model="gpt-test",
        client=FakeClient(output=[function_call, function_call]),
    )
    with pytest.raises(ValueError, match="received 2"):
        multiple.select_tool(checkpoint, MODEL_AGENT_TOOL_DEFINITIONS)


def test_model_agent_cli_starts_checkpoints_and_resumes_after_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def selector_factory(*, model: str, **_: object) -> SequenceSelector:
        return SequenceSelector(model=model)

    monkeypatch.setattr(cli_module, "OpenAIResponsesToolSelector", selector_factory)

    assert (
        cli_module.main(
            [
                "model-agent",
                "--idea",
                IDEA,
                "--run-dir",
                str(tmp_path),
                "--model",
                "test-model",
            ]
        )
        == 0
    )
    paths = model_agent_paths(tmp_path, _run_id())
    assert load_model_agent_checkpoint(paths.checkpoint).status == "awaiting_approval"

    assert cli_module.main(["model-agent", "--resume", str(paths.checkpoint), "--approve"]) == 0
    assert load_model_agent_checkpoint(paths.checkpoint).status == "completed"
    assert paths.final_report.exists()
