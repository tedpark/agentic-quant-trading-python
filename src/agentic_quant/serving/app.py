from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agentic_quant.serving.model_registry import ModelRegistry, ReloadError


class PredictRequest(BaseModel):
    features: list[float] = Field(min_length=1)


class ReloadRequest(BaseModel):
    checkpoint_path: str


def create_app(registry: ModelRegistry | None = None) -> FastAPI:
    app = FastAPI(title="Agentic Quant Serving Demo")
    active_registry = registry or ModelRegistry()

    @app.get("/health")
    def health() -> dict[str, str]:
        metadata = active_registry.metadata
        return {
            "status": "ok",
            "model_version": metadata.model_version,
            "loaded_at": metadata.loaded_at,
        }

    @app.post("/predict")
    def predict(request: PredictRequest) -> dict[str, float | str]:
        try:
            prediction = active_registry.predict(request.features)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "prediction": prediction.prediction,
            "model_version": prediction.model_version,
            "loaded_at": prediction.loaded_at,
        }

    @app.post("/reload")
    def reload_model(request: ReloadRequest) -> dict[str, str | int]:
        try:
            metadata = active_registry.reload(Path(request.checkpoint_path))
        except ReloadError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "model_version": metadata.model_version,
            "input_dim": metadata.input_dim,
            "loaded_at": metadata.loaded_at,
        }

    return app


app = create_app()
