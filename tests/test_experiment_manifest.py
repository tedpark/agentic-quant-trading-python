import json

from agentic_quant.experiments.demo_manifest import render_markdown
from agentic_quant.experiments.manifest import build_mini_backtest_manifest
from agentic_quant.experiments.orchestration import run_mini_experiment
from agentic_quant.features.regime import synthetic_market_bars


def test_manifest_captures_parameters_and_artifacts() -> None:
    results = run_mini_experiment(
        synthetic_market_bars(180),
        train_size=70,
        validation_size=20,
        test_size=20,
        thresholds=(0.0, 0.5, 1.0),
    )
    manifest = build_mini_backtest_manifest(
        results,
        parameters={"train_size": 70, "validation_size": 20, "test_size": 20},
        artifacts={"report": "docs/benchmarks/example.md"},
    )

    assert manifest.run_id
    assert manifest.fold_count == len(results)
    assert manifest.test_observations == sum(row.test_metrics.observations for row in results)
    assert manifest.parameters["train_size"] == 70
    assert manifest.artifacts["report"] == "docs/benchmarks/example.md"
    assert "synthetic data only" in manifest.public_boundary


def test_manifest_is_deterministic_for_same_inputs() -> None:
    kwargs = dict(train_size=70, validation_size=20, test_size=20, thresholds=(0.0, 0.5, 1.0))
    first = build_mini_backtest_manifest(
        run_mini_experiment(synthetic_market_bars(180), **kwargs),
        parameters=kwargs,
        artifacts={"report": "docs/benchmarks/example.md"},
    )
    second = build_mini_backtest_manifest(
        run_mini_experiment(synthetic_market_bars(180), **kwargs),
        parameters=kwargs,
        artifacts={"report": "docs/benchmarks/example.md"},
    )

    assert first.run_id == second.run_id
    assert first.to_json() == second.to_json()


def test_manifest_json_snapshot_is_parseable() -> None:
    markdown = render_markdown()
    json_block = markdown.split("```json\n", 1)[1].split("\n```", 1)[0]
    parsed = json.loads(json_block)

    assert parsed["name"] == "mini-backtest-orchestration"
    assert parsed["artifacts"]["manifest_report"] == "docs/benchmarks/experiment_manifest.md"
    assert parsed["fold_count"] > 0
    assert "threshold selected on validation rows only" in parsed["validation_protocol"]


def test_manifest_rejects_empty_results() -> None:
    try:
        build_mini_backtest_manifest((), parameters={}, artifacts={})
    except ValueError as error:
        assert "results must not be empty" in str(error)
    else:
        raise AssertionError("expected ValueError")
