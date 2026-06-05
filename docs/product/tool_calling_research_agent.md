# Tool-Calling Research Agent Design

## Core Answer

Code calling works when the chatbot is not allowed to run arbitrary code.

The reliable design is:

```text
Chat UI
  -> planner
  -> allowlisted tool router
  -> trading research code
  -> manifest
  -> promotion gate
  -> report
```

The model should decide which approved tool to call and with which structured
arguments. The application code should execute the tool, validate the result,
and record the tool call.

The config is dynamic, but the schema is fixed. The agent can create a config
draft, but the runner only executes it after validation.

## What Not To Build

Do not start with:

```text
LLM writes arbitrary Python
  -> shell executes it
  -> strategy files or thresholds mutate
  -> report is generated
```

That is hard to reproduce and creates avoidable safety problems.

## What To Build

Start with an allowlisted runner:

```text
plan_experiment
build_experiment_config
run_mini_backtest
build_manifest
audit_experiment
write_report
```

The config carries a runner id and parameters:

```json
{
  "runner": "mini_backtest",
  "strategy_name": "pair_mean_reversion_regime_filter",
  "data_source": "synthetic_market_bars",
  "allow_live_trading": false
}
```

The runner id maps to code through a registry:

```text
mini_backtest -> run_mini_experiment(...)
```

If the config requests an unregistered runner such as `shell`, or sets
`allow_live_trading` to `true`, validation rejects it before any research code
runs.

The current demo implements this as:

```bash
make research-cycle-demo
make contract-review-demo
quant-research cycle --idea "HMM regime features improve pair spread entries"
quant-research review --input docs/benchmarks/experiment_run_contract.json
```

Output:

```text
docs/benchmarks/research_cycle_report.md
docs/benchmarks/experiment_run_contract.json
docs/benchmarks/research_workflow_state.json
docs/benchmarks/contract_promotion_review.md
```

## Safety Boundary

Allowed:

- synthetic/public data research runs
- backtest execution
- walk-forward validation
- experiment manifest generation
- promotion-gate audit
- markdown report generation

Blocked:

- broker orders
- live trading
- account access
- private alpha thresholds
- arbitrary shell commands
- unlimited file mutation

## Why This Works Better

The agent can still feel conversational:

```text
Try HMM regime features for pair mean reversion.
```

But underneath, it becomes a deterministic workflow:

```text
idea
  -> config
  -> backtest
  -> manifest
  -> audit
  -> report
```

This is the useful version of a chatbot for trading research. It is not a
chatbot that trades. It is an operator that calls approved research tools and
documents the result.

## Current Implementation

Implemented files:

```text
src/agentic_quant/research_os/cycle.py
src/agentic_quant/research_os/contract.py
src/agentic_quant/research_os/cli.py
src/agentic_quant/research_os/demo_cycle.py
src/agentic_quant/research_os/demo_contract_review.py
tests/test_research_cycle.py
tests/test_experiment_run_contract.py
tests/test_research_cli.py
docs/benchmarks/research_cycle_report.md
docs/benchmarks/experiment_run_contract.json
docs/benchmarks/research_workflow_state.json
docs/benchmarks/contract_promotion_review.md
```

Implemented safeguards:

- `build_experiment_config()` creates a dynamic config from an idea.
- `validate_experiment_config()` checks runner, strategy, data source, safety,
  window sizes, thresholds, and transaction cost.
- `_runner_registry()` maps approved runner ids to implementation functions.
- `build_experiment_run_contract()` exports the stable `experiment_run.v1`
  contract that downstream promotion gates can validate.
- `validate_experiment_run_contract()` rejects live-trading contracts,
  non-time-ordered folds, missing artifacts, non-train-only feature fitting,
  missing cost stress, missing regime breakdown, missing benchmark comparison,
  and weak public boundaries.
- `audit_experiment_run_contract()` reviews an external `experiment_run.v1`
  file without needing internal Python manifest or fold objects.
- `ResearchWorkflowState` records graph-style state transitions so the workflow
  can later move to LangGraph without changing product semantics.
- The generated report records the tool-call trace.

The generated report records:

- tool calls
- experiment config
- hypothesis-to-experiment plan
- fold-level backtest summary
- manifest snapshot
- promotion-gate decision
- workflow state snapshot

## Stable Contract

The real integration point is now a strict JSON adapter:

```text
experiment_run.json
```

The current demo writes:

```text
docs/benchmarks/experiment_run_contract.json
```

The contract now carries:

- model version
- feature list and fit scope
- fold-level validation/test metrics
- cost-stress scenarios
- regime breakdown
- benchmark comparison
- artifact paths
- public/private execution boundary

The trading system should export the same schema, and the agent should run:

```bash
make contract-review-demo
```

That is the bridge from demo to real trading-system integration.

## LangGraph Readiness

The current implementation is plain Python, but the state shape already maps to
LangGraph-style nodes:

```text
idea
  -> plan_experiment
  -> validate_experiment_config
  -> run_registered_runner
  -> build_manifest
  -> audit_experiment
  -> validate_experiment_run_contract
```

The exported state file is:

```text
docs/benchmarks/research_workflow_state.json
```

This is useful because the workflow can later add checkpointing,
human-in-the-loop approval, and resume behavior without changing the core
trading research contract.
