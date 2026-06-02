from pathlib import Path

import pytest
import torch

from agentic_quant.serving.model_registry import (
    ModelRegistry,
    ReloadError,
    build_checkpoint,
)


def test_valid_reload_changes_model_version(tmp_path: Path) -> None:
    registry = ModelRegistry(input_dim=3, model_version="demo-v1")
    checkpoint = tmp_path / "demo-v2.pt"
    build_checkpoint(checkpoint, model_version="demo-v2", input_dim=3)

    before = registry.predict([0.1, 0.2, 0.3])
    metadata = registry.reload(checkpoint)
    after = registry.predict([0.1, 0.2, 0.3])

    assert before.model_version == "demo-v1"
    assert metadata.model_version == "demo-v2"
    assert after.model_version == "demo-v2"


def test_invalid_reload_keeps_current_model_active(tmp_path: Path) -> None:
    registry = ModelRegistry(input_dim=3, model_version="demo-v1")
    invalid_checkpoint = tmp_path / "invalid.pt"
    torch.save({"model_version": "broken"}, invalid_checkpoint)

    with pytest.raises(ReloadError):
        registry.reload(invalid_checkpoint)

    prediction = registry.predict([0.1, 0.2, 0.3])
    assert prediction.model_version == "demo-v1"


def test_prediction_rejects_wrong_feature_dimension() -> None:
    registry = ModelRegistry(input_dim=3)

    with pytest.raises(ValueError, match="expected 3 features"):
        registry.predict([0.1, 0.2])
