# QuantSigma Research OS Implementation

## Build Direction

Do not start with a generic chat UI or an AI backtest analyzer.

The first useful product is a tested experiment promotion layer:

```text
research artifacts -> cited answers -> experiment plans -> validation reports
trading experiment outputs -> promotion gate -> paper-trading review decision
trading idea -> allowlisted tool calls -> research cycle report
```

This matters because financial ML credibility comes from leakage control,
reproducible experiments, regime analysis, and risk-aware evaluation. A model
that only summarizes a backtest is not differentiated enough.

## Repository Split

- Python engine: `agentic-quant-trading-python`
- Public product site: `quantsigma-ai`
- Career and roadmap docs: `resume_portfolio/2026/plans`

The Python engine should move first. The website should only expose artifacts
after the code, tests, and generated benchmark documents exist.

## Product Boundary

This is not a chatbot that executes trades.

It can execute a research workflow:

```text
artifact ingestion -> retrieval -> graph extraction -> cited answer -> manifest export
```

It does not execute live orders, connect to brokers, expose private alpha logic,
or make investment recommendations. A chat UI can be added later, but the core
product is a financial ML experiment promotion layer.

## Why Existing Trading Systems Still Need It

The trading system produces candidate signals, backtest folds, metrics, and run
logs. QuantSigma Research OS reviews whether those outputs are eligible for the
next stage.

The review layer checks:

- time-ordered fold structure
- validation/test separation
- train-only fitting language
- threshold selection behavior
- validation-to-test degradation
- CVaR and tail-risk metrics
- turnover and transaction-cost exposure
- public/private execution boundary

The strongest product verb is not `chat`. It is `promote` or `reject`.

## MVP 1: Research Copilot

Inputs:

- README files
- benchmark reports
- experiment manifests
- model cards
- Medium / LinkedIn technical drafts
- notebook summaries converted to Markdown

Outputs:

- answer with citations
- source artifact links
- leakage / validation warnings
- next experiment suggestions

The first version intentionally avoids paid LLM dependencies. It uses
deterministic indexing and keyword scoring so the system can be tested in CI.
After this works, an LLM can be added as a composer, not as the source of truth.

## MVP 2: Hypothesis-to-Experiment Planner

Input:

```text
HMM sideways regime improves mean-reversion entries for cointegrated pairs.
```

Output:

- hypothesis
- feature candidates
- validation protocol
- risk checks
- expected failure cases
- experiment manifest draft

The planner must always include leakage-aware validation and tail-risk checks.
That is the portfolio signal: the project is not just "AI for trading"; it is
financial ML engineering discipline.

## Current Implementation

Implemented package:

```text
src/agentic_quant/research_os/
  ingest.py       # Markdown artifact ingestion and section chunking
  search.py       # deterministic keyword retrieval
  graph.py        # financial ML concept graph extraction
  audit.py        # trading experiment validation and risk audit layer
  contract.py     # stable experiment_run.v1 contract export and validation
  copilot.py      # cited answer composer
  planner.py      # hypothesis-to-experiment planner and YAML manifest export
  schema.py       # typed artifacts, chunks, citations, graph nodes, answers
```

Implemented tests:

```text
tests/test_research_os.py
```

Demo command:

```bash
make research-os-demo
```

Demo output:

```text
docs/benchmarks/research_os_demo.md
```

Experiment audit demo:

```bash
make experiment-audit-demo
```

Audit output:

```text
docs/benchmarks/trading_experiment_audit.md
```

Research cycle demo:

```bash
make research-cycle-demo
```

Cycle output:

```text
docs/benchmarks/research_cycle_report.md
docs/benchmarks/experiment_run_contract.json
docs/benchmarks/research_workflow_state.json
```

Contract-only promotion review:

```bash
make contract-review-demo
```

Contract review output:

```text
docs/benchmarks/contract_promotion_review.md
```

CLI:

```bash
quant-research cycle --idea "HMM regime features improve pair spread entries"
quant-research review --input docs/benchmarks/experiment_run_contract.json
```

The research cycle now has three explicit layers:

```text
build_experiment_config()
  -> validate_experiment_config()
  -> runner registry dispatch
  -> experiment_run.v1 contract export
  -> contract-only promotion review
  -> workflow state snapshot
```

The config is dynamic, but execution is constrained by an allowlist. This keeps
the chat interface flexible while preventing arbitrary shell or live-trading
execution.

Concept document:

```text
docs/product/what_is_quant_research_os.md
docs/product/product_reality_check.md
docs/product/tool_calling_research_agent.md
```

## Next Build Steps

Done:

- Markdown artifact ingestion
- deterministic retrieval
- cited answers
- financial ML research graph
- hypothesis-to-experiment planning
- YAML experiment manifest export
- trading experiment audit reports
- allowlisted research cycle runner
- experiment_run.v1 contract export and validation
- feature fit scope, cost stress, regime breakdown, and benchmark comparison in the contract
- CI-friendly tests

Next:

1. Add a real trading-system adapter that exports `experiment_run.v1`.
2. Add citation coverage and answer-support evaluation for Research OS answers.
3. Add a small UI page on `quantsigma.ai` showing the Research OS pipeline.
4. Publish a LinkedIn / Medium post explaining why quant research is an
   experiment lifecycle problem, not a chat problem.
5. Add one portfolio bullet:

```text
Built QuantSigma Research OS, a deterministic financial ML research operator that
turns ideas into validated experiment configs, dispatches allowlisted backtest
runners, exports `experiment_run.v1` contracts, and applies a promotion gate for
leakage, validation, turnover, and tail-risk checks.
```
