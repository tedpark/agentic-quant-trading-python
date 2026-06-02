from pathlib import Path

from fastapi.testclient import TestClient

from agentic_quant.serving.app import create_app
from agentic_quant.serving.model_registry import ModelRegistry, build_checkpoint


def test_predict_endpoint_returns_model_version() -> None:
    client = TestClient(create_app(ModelRegistry(input_dim=3, model_version="demo-v1")))

    response = client.post("/predict", json={"features": [0.1, 0.2, 0.3]})

    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == "demo-v1"
    assert "prediction" in body


def test_reload_endpoint_keeps_current_model_on_invalid_checkpoint(tmp_path: Path) -> None:
    client = TestClient(create_app(ModelRegistry(input_dim=3, model_version="demo-v1")))
    missing = tmp_path / "missing.pt"

    failed = client.post("/reload", json={"checkpoint_path": str(missing)})
    current = client.post("/predict", json={"features": [0.1, 0.2, 0.3]})

    assert failed.status_code == 400
    assert current.json()["model_version"] == "demo-v1"


def test_reload_endpoint_swaps_to_valid_checkpoint(tmp_path: Path) -> None:
    client = TestClient(create_app(ModelRegistry(input_dim=3, model_version="demo-v1")))
    checkpoint = tmp_path / "demo-v2.pt"
    build_checkpoint(checkpoint, model_version="demo-v2", input_dim=3)

    reload_response = client.post("/reload", json={"checkpoint_path": str(checkpoint)})
    predict_response = client.post("/predict", json={"features": [0.1, 0.2, 0.3]})

    assert reload_response.status_code == 200
    assert reload_response.json()["model_version"] == "demo-v2"
    assert predict_response.json()["model_version"] == "demo-v2"
