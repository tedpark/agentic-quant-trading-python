.PHONY: test serve reload-demo drift-demo cvar-demo walk-forward-demo purged-embargo-demo regime-feature-demo mini-backtest-demo manifest-demo numerai-demo

test:
	python -m pytest

serve:
	PYTHONPATH=src uvicorn agentic_quant.serving.app:app --host 127.0.0.1 --port 8000

reload-demo:
	PYTHONPATH=src python -m agentic_quant.serving.demo_checkpoint /tmp/agentic-quant-demo-v2.pt

drift-demo:
	PYTHONPATH=src python -m agentic_quant.monitoring.demo_drift_report --output docs/benchmarks/drift_report.md

cvar-demo:
	PYTHONPATH=src python -m agentic_quant.risk.demo_cvar --output docs/benchmarks/qrdqn_cvar_smoke.md

walk-forward-demo:
	PYTHONPATH=src python -m agentic_quant.validation.demo_walk_forward --output docs/benchmarks/walk_forward_validation.md

purged-embargo-demo:
	PYTHONPATH=src python -m agentic_quant.validation.demo_purged_embargo --output docs/benchmarks/purged_embargo_validation.md

regime-feature-demo:
	PYTHONPATH=src python -m agentic_quant.features.demo_regime_features --output docs/benchmarks/hmm_regime_features.md

mini-backtest-demo:
	PYTHONPATH=src python -m agentic_quant.experiments.demo_mini_backtest --output docs/benchmarks/mini_backtest_orchestration.md

manifest-demo:
	PYTHONPATH=src python -m agentic_quant.experiments.demo_manifest --output docs/benchmarks/experiment_manifest.md

numerai-demo:
	PYTHONPATH=src python -m agentic_quant.benchmarks.demo_numerai --output docs/benchmarks/numerai_benchmark_trail.md
