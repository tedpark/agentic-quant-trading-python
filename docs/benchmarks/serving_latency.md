# Serving Latency Benchmark

Status: planned.

## Goal

Measure whether checkpoint reload changes prediction latency or breaks inference continuity.

## Planned Metrics

- p50 latency
- p95 latency
- reload duration
- failed reload count
- active `model_version` before/after reload

## Expected Output

```text
scenario,p50_ms,p95_ms,reload_ms,model_version
baseline,0.0,0.0,0,demo-v1
after_valid_reload,0.0,0.0,0,demo-v2
after_invalid_reload,0.0,0.0,0,demo-v2
```
