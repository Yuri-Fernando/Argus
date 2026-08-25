# benchmarks/

The platform measures itself instead of asserting quality in prose — [ARCHITECTURE.md §17](../ARCHITECTURE.md#17-layer-14--observability--finops),
filled in progressively across sprints and completed in **[ROADMAP.md Sprint 16](../ROADMAP.md)**.
Referenced as an acceptance-criteria artifact by Sprints 12, 15 and 16 specifically.

```
benchmarks/
├── pipeline.md        # processing_time, records_per_second, failure_rate
├── data_quality.md      # completeness, validity, duplicate_rate, freshness (rolls up from data_quality/reports/)
├── ml.md                  # ROC-AUC, F1, precision/recall, calibration (churn model, ml/evaluation/)
├── cortex.md                # SQL accuracy, answer accuracy, latency, regression rate (mirrors snowflake/evaluations/) + RAG retrieval precision@k (rag/evaluation/)
└── agents.md                  # tool selection accuracy, task completion, latency, hallucination rate, cost per request
└── infra.md                    # Azure cost, Databricks DBU, Snowflake credits, storage, LLM tokens — FinOps
```

## Categories

| File | What it measures |
|---|---|
| **`pipeline.md`** | Ingestion → Bronze → Silver → Gold throughput and reliability: how long a run takes, how many records/sec it sustains, how often it fails. |
| **`data_quality.md`** | The platform's own trustworthiness — completeness, validity, duplicate rate, freshness per dataset and overall `dq_score`, sourced from `data_quality/reports/`. |
| **`ml.md`** | Champion churn model quality on the held-out set — ROC-AUC, F1, precision/recall, PR-AUC, calibration — sourced from `ml/evaluation/`. |
| **`cortex.md`** | Cortex Analyst SQL correctness/answer correctness/latency/regression rate against the golden-question set in `snowflake/evaluations/`, plus RAG retrieval precision@k from `rag/evaluation/` (Sprint 12 acceptance criteria: precision@3 ≥ 0.8). |
| **`agents.md`** | LangGraph agent quality — tool selection accuracy, task completion rate, latency, hallucination rate, and cost per request; also where the Sprint 15 three-way comparison (custom MCP vs. Databricks Managed MCP vs. Cortex Agents vs. Power BI MCP, same 10 questions) gets recorded. |
| **`infra.md`** | FinOps — Azure resource cost, Databricks DBU consumption, Snowflake credits, storage cost, LLM token spend, cost-per-1M-records and cost-per-agent-request as first-class tracked metrics, not an afterthought. |

## Why this exists

Every layer of this platform makes a measurable claim somewhere in `ARCHITECTURE.md` or
`ROADMAP.md` ("fuzzy matcher recall ≥ 0.85," "retrieval precision@3 ≥ 0.8," "no >90%-in-one-bucket
collapse"). `benchmarks/` is where those claims get a recorded number, a date, and a sprint —
instead of staying an assertion in a markdown file nobody re-checks. It is also the input to
FinOps cost-guardrail automation (backlog item 5 in
[IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md)): an automatic alert/shutdown on
daily cost overrun needs `infra.md`'s numbers to have a trend to alert against.

## How to use these templates

Each `.md` file in this directory is a template, not a report — the tables start empty. Fill in a
row **only** with a number you actually measured (from a GX Data Doc, an MLflow run, a Grafana
query, a cloud cost export, etc.). Do not backfill plausible-looking numbers to make a table look
complete; an empty row is more honest than an invented one, per
[ARCHITECTURE.md §21 — Production readiness / honesty note](../ARCHITECTURE.md#21-production-readiness--honesty-note).

## Related

- [ARCHITECTURE.md §17 — Layer 14: Observability & FinOps](../ARCHITECTURE.md#17-layer-14--observability--finops)
- [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) — backlog item 5, FinOps cost guardrails
- [ROADMAP.md Sprint 16](../ROADMAP.md) — "`benchmarks/` complete for pipeline, DQ, ML, Cortex, agents, infra"
- [`monitoring/`](../monitoring/) — the live Prometheus/Grafana counterpart these benchmarks are periodically snapshotted from
