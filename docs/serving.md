# Model Serving Plan

## Goal

Serve a toy PyTorch model through FastAPI and support safer checkpoint hot reload.

Status: implemented as the first public skeleton.

## Reload Rule

The active model should never be mutated until the candidate checkpoint passes validation.

Reload flow:

```text
reload request
  -> load candidate checkpoint
  -> validate expected input/output shape
  -> run smoke inference
  -> swap active model atomically
  -> expose new model_version
```

Failure behavior:

```text
invalid checkpoint
  -> return error
  -> keep current model active
  -> keep current model_version unchanged
```

## API Shape

Prediction response:

```json
{
  "prediction": 0.42,
  "model_version": "demo-checkpoint-v2",
  "loaded_at": "2026-06-02T00:00:00Z"
}
```

## Tests

Required tests:

- prediction returns `model_version`
- valid reload changes `model_version`
- invalid reload keeps previous model active
- reload does not break prediction path

Current implementation:

- `src/agentic_quant/serving/model_registry.py`
- `src/agentic_quant/serving/app.py`
- `src/agentic_quant/serving/demo_checkpoint.py`
- `tests/test_model_registry.py`
- `tests/test_serving_app.py`
