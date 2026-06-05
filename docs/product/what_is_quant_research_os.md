# What Is QuantSigma Research OS?

## Short Answer

QuantSigma Research OS is not a trading chatbot.

It is a financial ML research workflow engine that helps turn research notes,
benchmark reports, model cards, and experiment artifacts into:

- cited answers
- a financial ML concept graph
- leakage-aware experiment plans
- YAML experiment manifests
- validation and risk warnings

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

Runnable command:

```bash
make research-os-demo
```

Generated output:

```text
docs/benchmarks/research_os_demo.md
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

## Why This Is Better Than a Generic RAG Chatbot

A generic RAG chatbot answers questions over documents.

QuantSigma Research OS should answer a narrower and more valuable question:

```text
How should this financial ML idea become a testable, reproducible experiment?
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
Python research engine + generated demo report
```

Near-term:

```text
CLI + FastAPI endpoint + small QuantSigma.ai UI panel
```

Long-term:

```text
Research Console
  left: artifacts
  center: cited answer
  right: experiment plan and risk warnings
  bottom: generated manifest and validation report
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

This is the story to use in portfolio and interviews:

```text
I am building a financial ML research workflow engine, not an auto-trading bot.
It uses RAG-style retrieval, a domain-specific research graph, and deterministic
evaluation/export steps to make quant experiments more reproducible and less
prone to leakage.
```
