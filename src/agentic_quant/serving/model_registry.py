from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any

import torch
from torch import nn


class ReloadError(ValueError):
    """Raised when a candidate checkpoint is not safe to activate."""


class DemoLinearModel(nn.Module):
    def __init__(self, input_dim: int, output_dim: int = 1) -> None:
        super().__init__()
        self.linear = nn.Linear(input_dim, output_dim)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.linear(features)


@dataclass(frozen=True)
class ModelMetadata:
    model_version: str
    input_dim: int
    output_dim: int
    loaded_at: str


@dataclass(frozen=True)
class Prediction:
    prediction: float
    model_version: str
    loaded_at: str


def utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_checkpoint(
    path: Path,
    *,
    model_version: str,
    input_dim: int,
    output_dim: int = 1,
    seed: int = 7,
) -> None:
    torch.manual_seed(seed)
    model = DemoLinearModel(input_dim=input_dim, output_dim=output_dim)
    checkpoint = {
        "model_version": model_version,
        "input_dim": input_dim,
        "output_dim": output_dim,
        "state_dict": model.state_dict(),
    }
    torch.save(checkpoint, path)


class ModelRegistry:
    def __init__(self, *, input_dim: int = 3, model_version: str = "demo-v1") -> None:
        self._lock = Lock()
        self._model = DemoLinearModel(input_dim=input_dim)
        self._model.eval()
        self._metadata = ModelMetadata(
            model_version=model_version,
            input_dim=input_dim,
            output_dim=1,
            loaded_at=utc_timestamp(),
        )

    @property
    def metadata(self) -> ModelMetadata:
        return self._metadata

    def predict(self, features: list[float]) -> Prediction:
        metadata = self._metadata
        if len(features) != metadata.input_dim:
            raise ValueError(f"expected {metadata.input_dim} features, got {len(features)}")

        with self._lock:
            model = self._model
            active_metadata = self._metadata

        with torch.inference_mode():
            tensor = torch.tensor([features], dtype=torch.float32)
            output = model(tensor).squeeze().item()

        return Prediction(
            prediction=float(output),
            model_version=active_metadata.model_version,
            loaded_at=active_metadata.loaded_at,
        )

    def reload(self, checkpoint_path: Path) -> ModelMetadata:
        checkpoint = self._load_checkpoint(checkpoint_path)
        candidate, metadata = self._build_candidate(checkpoint)
        self._smoke_test(candidate, metadata.input_dim, metadata.output_dim)

        with self._lock:
            self._model = candidate
            self._metadata = metadata

        return metadata

    def _load_checkpoint(self, checkpoint_path: Path) -> dict[str, Any]:
        if not checkpoint_path.exists():
            raise ReloadError(f"checkpoint not found: {checkpoint_path}")

        try:
            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        except TypeError:
            checkpoint = torch.load(checkpoint_path, map_location="cpu")

        if not isinstance(checkpoint, dict):
            raise ReloadError("checkpoint must be a dict")
        return checkpoint

    def _build_candidate(self, checkpoint: dict[str, Any]) -> tuple[DemoLinearModel, ModelMetadata]:
        required = {"model_version", "input_dim", "output_dim", "state_dict"}
        missing = required - checkpoint.keys()
        if missing:
            raise ReloadError(f"checkpoint missing keys: {sorted(missing)}")

        input_dim = int(checkpoint["input_dim"])
        output_dim = int(checkpoint["output_dim"])
        if input_dim <= 0 or output_dim != 1:
            raise ReloadError("checkpoint dimensions are not supported")

        candidate = DemoLinearModel(input_dim=input_dim, output_dim=output_dim)
        try:
            candidate.load_state_dict(checkpoint["state_dict"])
        except RuntimeError as exc:
            raise ReloadError(f"state_dict shape mismatch: {exc}") from exc
        candidate.eval()

        metadata = ModelMetadata(
            model_version=str(checkpoint["model_version"]),
            input_dim=input_dim,
            output_dim=output_dim,
            loaded_at=utc_timestamp(),
        )
        return candidate, metadata

    def _smoke_test(self, model: DemoLinearModel, input_dim: int, output_dim: int) -> None:
        with torch.inference_mode():
            output = model(torch.zeros((1, input_dim), dtype=torch.float32))
        if tuple(output.shape) != (1, output_dim):
            raise ReloadError(f"unexpected output shape: {tuple(output.shape)}")
