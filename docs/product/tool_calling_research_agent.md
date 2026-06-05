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

The current demo implements this as:

```bash
make research-cycle-demo
```

Output:

```text
docs/benchmarks/research_cycle_report.md
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
src/agentic_quant/research_os/demo_cycle.py
tests/test_research_cycle.py
docs/benchmarks/research_cycle_report.md
```

The generated report records:

- tool calls
- experiment config
- hypothesis-to-experiment plan
- fold-level backtest summary
- manifest snapshot
- promotion-gate decision

## Next Real Integration

The next useful step is a strict JSON adapter:

```text
experiment_run.json
```

The trading system should export that file, and the agent should run:

```bash
quant-gate review experiment_run.json
```

That is the bridge from demo to real trading-system integration.
