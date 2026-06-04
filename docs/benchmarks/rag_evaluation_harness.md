# RAG Evaluation Harness

This public sample evaluates a small RAG run with a golden set.
It uses deterministic metrics and synthetic content only, so it can run in CI without API keys.

## Summary

| Metric | Mean | What it checks |
|---|---:|---|
| Context precision | 0.500 | Relevant contexts among retrieved contexts |
| Context recall | 1.000 | Required contexts recovered from the golden set |
| Hit rate | 1.000 | Whether at least one relevant context was retrieved |
| MRR | 1.000 | Rank of the first relevant retrieved context |
| Citation coverage | 1.000 | Whether cited sources cover required sources |
| Answer support | 0.639 | Token overlap between answer and retrieved evidence |

## Per-question Results

| Question | Category | Precision | Recall | Hit | MRR | Citation Coverage | Answer Support |
|---|---|---:|---:|---:|---:|---:|---:|
| q001 | validation | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 0.667 |
| q002 | leakage | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 0.545 |
| q003 | serving | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 0.500 |
| q004 | monitoring | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 0.667 |
| q005 | risk | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 0.818 |

## Interview Message

For RAG systems, I do not rely on demo quality alone.
I want a golden set, retrieval metrics, citation checks, answer-support checks,
and a regression threshold that can run before prompt or retriever changes ship.
