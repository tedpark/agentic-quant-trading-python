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
make agent-builder-demo
make research-cycle-demo
make contract-review-demo
quant-research build-agent --idea "HMM regime features improve pair spread entries"
quant-research build-agent --spec-input docs/benchmarks/agent_spec.json --run-dir docs/runs
quant-research cycle --idea "HMM regime features improve pair spread entries"
quant-research review --input docs/benchmarks/experiment_run_contract.json
```

Output:

```text
docs/benchmarks/agent_builder_report.md
docs/benchmarks/agent_spec.json
docs/benchmarks/agent_builder_state.json
docs/benchmarks/agent_builder_run_manifest.json
docs/benchmarks/agent_builder_events.jsonl
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

## Agent Builder Layer

The Wonderful-style version adds a meta agent:

```text
idea
  -> build_agent_spec
  -> validate_agent_spec
  -> validate_experiment_config
  -> run_research_cycle_from_config
```

The builder does not write runnable Python. It creates a structured `AgentSpec`:

```json
{
  "role": "financial_ml_experiment_agent",
  "allowed_tools": ["plan_experiment", "build_experiment_config", "run_mini_backtest"],
  "constraints": ["no_arbitrary_code", "no_live_trading", "contract_only_promotion_review"],
  "outputs": ["agent_spec", "experiment_run.v1", "markdown_report"]
}
```

`validate_agent_spec()` rejects non-allowlisted tools, missing
`experiment_run.v1` output, missing contract-only promotion review, and unsafe
experiment configs. This is how an "agent that builds agents" stays bounded:
the model can propose an agent spec, but the application executes only the
validated config through registered runners.

For production-style replay, the CLI can load an existing spec:

```bash
quant-research build-agent \
  --spec-input docs/benchmarks/agent_spec.json \
  --run-dir docs/runs
```

Spec validation can run without dispatching a backtest:

```bash
quant-research validate-spec \
  --input docs/benchmarks/agent_spec.json \
  --output /tmp/normalized_agent_spec.json
```

The `agent_spec.v1` loader is strict. Unknown keys, unsupported schema versions,
duplicate tools, non-allowlisted tools, and live-trading configs are rejected
before dispatch. Reports, specs, contracts, and state files are written through
atomic replacement.

The builder also writes a `agent_builder_run_manifest.v1` file containing
SHA-256 hashes for the generated spec, contract, state, and report. A JSONL
event log records ordered builder steps for audit and replay inspection.

## Current Implementation

Implemented files:

```text
src/agentic_quant/research_os/agent_builder.py
src/agentic_quant/research_os/cycle.py
src/agentic_quant/research_os/contract.py
src/agentic_quant/research_os/cli.py
src/agentic_quant/research_os/demo_agent_builder.py
src/agentic_quant/research_os/demo_cycle.py
src/agentic_quant/research_os/demo_contract_review.py
tests/test_research_cycle.py
tests/test_agent_builder.py
tests/test_experiment_run_contract.py
tests/test_research_cli.py
docs/benchmarks/agent_builder_report.md
docs/benchmarks/agent_spec.json
docs/benchmarks/agent_builder_state.json
docs/benchmarks/research_cycle_report.md
docs/benchmarks/experiment_run_contract.json
docs/benchmarks/research_workflow_state.json
docs/benchmarks/contract_promotion_review.md
```

Implemented safeguards:

- `build_experiment_config()` creates a dynamic config from an idea.
- `build_agent_spec()` wraps the idea and dynamic config in a structured agent
  definition.
- `validate_agent_spec()` checks role, allowed tools, safety constraints,
  required outputs, and config validity before any runner dispatch.
- `parse_agent_spec_json()` strictly loads replayable `agent_spec.v1` files.
- `write_agent_builder_artifacts()` writes reports, specs, contracts, and state
  files through atomic replacement.
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
  -> build_agent_spec
  -> validate_agent_spec
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
