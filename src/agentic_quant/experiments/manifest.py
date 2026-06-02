from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from typing import Mapping, Sequence

from agentic_quant.experiments.orchestration import ExperimentFoldResult


@dataclass(frozen=True)
class ExperimentManifest:
    run_id: str
    name: str
    data_source: str
    parameters: Mapping[str, object]
    validation_protocol: tuple[str, ...]
    artifacts: Mapping[str, str]
    public_boundary: tuple[str, ...]
    fold_count: int
    test_observations: int
    mean_test_return: float
    mean_test_cvar: float
    mean_test_sharpe: float

    def to_json(self) -> str:
        return dumps(asdict(self), indent=2, sort_keys=True)


def _round_float(value: float) -> float:
    return round(float(value), 6)


def build_mini_backtest_manifest(
    results: Sequence[ExperimentFoldResult],
    *,
    parameters: Mapping[str, object],
    artifacts: Mapping[str, str],
    name: str = "mini-backtest-orchestration",
    data_source: str = "synthetic_market_bars",
) -> ExperimentManifest:
    if not results:
        raise ValueError("results must not be empty")
    total_observations = sum(row.test_metrics.observations for row in results)
    if total_observations <= 0:
        raise ValueError("test observations must be positive")

    payload = dumps(
        {
            "name": name,
            "data_source": data_source,
            "parameters": dict(parameters),
            "folds": [
                {
                    "fold": row.fold,
                    "train_range": row.train_range,
                    "validation_range": row.validation_range,
                    "test_range": row.test_range,
                    "selected_threshold": row.selected_threshold,
                    "test_mean_return": _round_float(row.test_metrics.mean_return),
                    "test_cvar": _round_float(row.test_metrics.cvar),
                    "test_sharpe": _round_float(row.test_metrics.sharpe),
                }
                for row in results
            ],
        },
        sort_keys=True,
    )
    run_id = sha256(payload.encode("utf-8")).hexdigest()[:12]

    return ExperimentManifest(
        run_id=run_id,
        name=name,
        data_source=data_source,
        parameters=dict(parameters),
        validation_protocol=(
            "time-ordered train / validation / test windows",
            "feature standardization fit on the training window only",
            "HMM-style regime model fit on the training window only",
            "threshold selected on validation rows only",
            "test metrics reported only after threshold selection",
        ),
        artifacts=dict(artifacts),
        public_boundary=(
            "synthetic data only",
            "no private trading universe",
            "no broker data or account data",
            "no live execution logic",
            "no production thresholds or private alpha features",
        ),
        fold_count=len(results),
        test_observations=total_observations,
        mean_test_return=_round_float(
            sum(row.test_metrics.mean_return * row.test_metrics.observations for row in results) / total_observations
        ),
        mean_test_cvar=_round_float(
            sum(row.test_metrics.cvar * row.test_metrics.observations for row in results) / total_observations
        ),
        mean_test_sharpe=_round_float(sum(row.test_metrics.sharpe for row in results) / len(results)),
    )


def render_manifest_markdown(manifest: ExperimentManifest) -> str:
    lines = [
        "# Experiment Manifest / Run Log",
        "",
        "This document records a reproducible public run log for the mini backtest orchestration sample.",
        "It is intentionally small and synthetic, but it shows the experiment metadata that should be captured before comparing model or strategy variants.",
        "",
        "## Run Summary",
        "",
        f"- run id: `{manifest.run_id}`",
        f"- experiment: `{manifest.name}`",
        f"- data source: `{manifest.data_source}`",
        f"- folds: {manifest.fold_count}",
        f"- test observations: {manifest.test_observations}",
        f"- mean test return: {manifest.mean_test_return:.6f}",
        f"- mean test CVaR: {manifest.mean_test_cvar:.6f}",
        f"- mean test Sharpe: {manifest.mean_test_sharpe:.6f}",
        "",
        "## Parameters",
        "",
        "| Parameter | Value |",
        "|---|---:|",
    ]
    for key, value in manifest.parameters.items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Validation Protocol", ""])
    lines.extend(f"- {item}" for item in manifest.validation_protocol)

    lines.extend(["", "## Artifacts", "", "| Artifact | Path |", "|---|---|"])
    for key, value in manifest.artifacts.items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Public Boundary", ""])
    lines.extend(f"- {item}" for item in manifest.public_boundary)

    lines.extend(["", "## JSON Snapshot", "", "```json", manifest.to_json(), "```"])
    return "\n".join(lines) + "\n"
