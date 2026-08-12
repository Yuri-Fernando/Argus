# Cortex benchmarks

What this measures and why: Cortex Analyst correctness/latency against the golden-question set in
[`snowflake/evaluations/`](../snowflake/evaluations/) — [ARCHITECTURE.md §12](../ARCHITECTURE.md#12-layer-9--snowflake-enterprise-dwh--cortex) —
plus RAG retrieval quality from [`rag/evaluation/`](../rag/evaluation/) —
[ARCHITECTURE.md §14](../ARCHITECTURE.md#14-layer-11--rag--document-intelligence). Every change to
a Semantic View is regression-tested against this set; retrieval precision@3 ≥ 0.8 is the Sprint 12
acceptance criteria.

| Metric | Value | Date measured | Sprint | Notes |
|---|---|---|---|---|
| SQL accuracy | | | | |
| answer accuracy | | | | |
| latency | | | | |
| regression rate | | | | |
| retrieval precision@3 | | | | |

## Related

[ARCHITECTURE.md §17](../ARCHITECTURE.md#17-layer-14--observability--finops) ·
[IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) backlog item 5 (FinOps cost guardrails)
