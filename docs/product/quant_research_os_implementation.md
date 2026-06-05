# QuantSigma Research OS Implementation

## Build Direction

Do not start with a generic chat UI or an AI backtest analyzer.

The first useful product is a tested research workflow engine:

```text
research artifacts -> cited answers -> experiment plans -> validation reports
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
  copilot.py      # cited answer composer
  planner.py      # hypothesis-to-experiment planner
  schema.py       # typed artifacts, chunks, citations, answers
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

## Next Build Steps

1. Add experiment-manifest YAML export from the planner.
2. Add citation coverage and answer-support evaluation for Research OS answers.
3. Add a small UI page on `quantsigma.ai` showing the Research OS pipeline.
4. Publish a LinkedIn / Medium post explaining why quant research is an
   experiment lifecycle problem, not a chat problem.
5. Add one portfolio bullet:

```text
Built QuantSigma Research OS, a deterministic financial ML research workflow
engine that ingests research artifacts, returns cited answers, and converts
trading ideas into leakage-aware experiment plans.
```
