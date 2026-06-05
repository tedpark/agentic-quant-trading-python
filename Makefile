.PHONY: test serve reload-demo drift-demo cvar-demo walk-forward-demo purged-embargo-demo regime-feature-demo mini-backtest-demo manifest-demo numerai-demo rag-eval-demo research-os-demo experiment-audit-demo research-cycle-demo agent-builder-demo contract-review-demo

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

rag-eval-demo:
	PYTHONPATH=src python -m agentic_quant.llm_eval.demo_rag_eval --output docs/benchmarks/rag_evaluation_harness.md

research-os-demo:
	PYTHONPATH=src python -m agentic_quant.research_os.demo_research_os --output docs/benchmarks/research_os_demo.md

experiment-audit-demo:
	PYTHONPATH=src python -m agentic_quant.research_os.demo_audit --output docs/benchmarks/trading_experiment_audit.md

research-cycle-demo:
	PYTHONPATH=src python -m agentic_quant.research_os.demo_cycle --output docs/benchmarks/research_cycle_report.md

agent-builder-demo:
	PYTHONPATH=src python -m agentic_quant.research_os.demo_agent_builder --output docs/benchmarks/agent_builder_report.md --spec-output docs/benchmarks/agent_spec.json --contract-output docs/benchmarks/experiment_run_contract.json --state-output docs/benchmarks/agent_builder_state.json --manifest-output docs/benchmarks/agent_builder_run_manifest.json --event-log-output docs/benchmarks/agent_builder_events.jsonl

contract-review-demo:
	PYTHONPATH=src python -m agentic_quant.research_os.demo_contract_review --input docs/benchmarks/experiment_run_contract.json --output docs/benchmarks/contract_promotion_review.md
