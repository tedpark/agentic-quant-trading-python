# What Is QuantSigma Research OS?

## Short Answer

QuantSigma Research OS is not a trading chatbot.

The stronger first product is more specific:

```text
QuantSigma Experiment Promotion Gate
```

It is a validation and promotion layer for ML-based trading systems. It helps
turn research notes, benchmark reports, model cards, and experiment artifacts
into:

- cited answers
- a financial ML concept graph
- leakage-aware experiment plans
- YAML experiment manifests
- validation and risk warnings
- trading experiment audit reports
- promotion decisions

The current implementation runs as a Python engine and demo command. A web chat
UI can be added later, but the product should not be reduced to a chat window.

## What "Execution" Means Here

Execution does not mean placing trades.

Execution means the system can run a research workflow:

```text
read artifacts
  -> split sections
  -> retrieve relevant evidence
  -> extract research graph
  -> answer with citations
  -> generate an experiment plan
  -> export a YAML manifest
```

It can also run a trading experiment audit workflow:

```text
trading system backtest folds + experiment manifest
  -> check time ordering
  -> check validation/test separation
  -> check leakage controls
  -> check turnover, CVaR, Sharpe, and failed folds
  -> check public/private execution boundary
  -> produce reject / review_required / paper_trade_candidate decision
```

And the agent can run a complete research cycle through allowlisted tools:

```text
idea
  -> plan_experiment
  -> build_experiment_config
  -> run_mini_backtest
  -> build_manifest
  -> audit_experiment
  -> write_report
```

The config is generated automatically from the idea, then validated before
execution. A config can choose an approved runner such as `mini_backtest`, but it
cannot request arbitrary shell execution or live trading.

Runnable command:

```bash
make research-os-demo
make experiment-audit-demo
make research-cycle-demo
```

Generated output:

```text
docs/benchmarks/research_os_demo.md
docs/benchmarks/trading_experiment_audit.md
docs/benchmarks/research_cycle_report.md
docs/benchmarks/experiment_run_contract.json
```

## What It Does Not Do

It does not:

- send broker orders
- run live trading
- expose private alpha logic
- guarantee profitable strategies
- let an LLM invent unsupported trading claims

Those boundaries are intentional. The public project should show engineering
discipline without leaking strategy details or making investment claims.

## Why Use This If a Trading System Already Exists?

A trading system can produce signals, backtests, model outputs, and run logs.
That does not automatically mean the experiment is trustworthy.

This layer answers a different question:

```text
Should this trading experiment be trusted, rejected, or reviewed before promotion?
```

It is useful when the trading system already exists because it checks the parts
that often break financial ML work:

- train/validation/test ordering
- leakage-prone feature fitting
- threshold selection behavior
- validation-to-test degradation
- regime-specific fragility
- tail risk and turnover
- transaction-cost sensitivity
- whether public artifacts accidentally imply live execution

The trading system generates the experiment. QuantSigma Research OS should act
as the promotion gate that decides whether the experiment can move forward.

That distinction matters. A report is optional; a promotion gate becomes part of
the workflow.

## Why This Is Better Than a Generic RAG Chatbot

A generic RAG chatbot answers questions over documents.

QuantSigma Research OS should answer a narrower and more valuable question:

```text
Can this financial ML experiment be promoted, and what blocks it?
```

That requires more than retrieval:

- feature candidates
- regime awareness
- leakage controls
- walk-forward validation
- purged / embargoed splits
- CVaR and tail-risk checks
- failure case tracking
- experiment manifests

The differentiator is not "chat with my quant notes." The differentiator is
"convert quant research into structured experiments with evidence and guardrails."

## Current Product Shape

Current:

```text
Python validation/research engine + generated demo reports
```

Near-term:

```text
CLI + FastAPI endpoint + small QuantSigma.ai UI panel
```

Long-term:

```text
Research Console
  left: artifacts
  center: promotion decision
  right: validation, leakage, risk, and cost warnings
  bottom: generated manifest and promotion checklist
```

## Example

Input idea:

```text
HMM sideways regime improves mean-reversion entries for cointegrated pairs.
```

Output:

- related research artifacts
- HMM regime feature node
- walk-forward validation relationship
- purged / embargo leakage warning
- CVaR risk check
- YAML experiment manifest
- promotion decision such as `paper_trade_candidate`, `review_required`, or `reject`

This is the story to use in portfolio and interviews:

```text
I am building a promotion-gate layer for ML-based trading experiments, not an
auto-trading bot. It reviews backtest folds, manifests, leakage controls,
validation behavior, turnover, and tail risk, then decides whether a candidate is
ready for paper-trading review or should be rejected.
```
