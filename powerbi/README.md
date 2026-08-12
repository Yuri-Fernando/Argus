# powerbi/

Enterprise BI for human consumers — [ARCHITECTURE.md §13](../ARCHITECTURE.md#13-layer-10--power-bi), built in **[ROADMAP.md Sprint 9](../ROADMAP.md)**.

```
powerbi/
├── semantic_model/   # connects to Snowflake Semantic Views (ADR-005) — no direct-query to Gold tables
├── dax/                # measures/calculated columns layered on top of the semantic model, where DAX adds value beyond the metric already defined upstream
├── dashboards/           # .pbix / report definitions for the 5 pages below
└── documentation/         # per-page data lineage notes: which Semantic View/Metric View backs each visual
```

## The 5 report pages

1. **Executive Overview** — top-line KPIs (Revenue, Orders, AOV, active customers, churn rate).
2. **Customer Intelligence** — RFM, CLV, churn score distribution, segmentation breakdown.
3. **Operations** — delivery SLA, late-order rate, support ticket volume/sentiment.
4. **Data Quality** — the platform's own `dq_score` (per dataset and overall), quarantine rate.
5. **Platform Observability** — pipeline health, DQ score trend, ML/LLM/MCP latency, cost (mirrors the Grafana view for a non-technical audience).

## Hard rule: semantic layer only

Every visual on every page sources from **Snowflake Semantic Views** (or, where applicable,
**Unity Catalog Metric Views**) — **never directly from raw Gold tables**. This is not a style
preference, it's the mechanism that prevents the *"Power BI said R$10M, the agent said R$13M"*
failure mode described in [ARCHITECTURE.md §11](../ARCHITECTURE.md#11-layer-8--semantic-layer-three-implementations-one-contract)
and formalized in [ADR-005](../docs/decisions/ADR-005-semantic-layer.md). A metric changes in
exactly one place (`docs/semantic-dictionary.md`) and every consumer — Power BI, Cortex Analyst,
an agent — inherits the change automatically.

## What "done" looks like (Sprint 9 acceptance criteria)

Every visual's tooltip/data-source trace leads back to a semantic-layer object, never a raw
table — see [ROADMAP.md Sprint 9](../ROADMAP.md).

## Power BI MCP — experimental, not load-bearing

A **Power BI MCP** connection (remote + local, both **Public Preview** as of mid-2026 per
Microsoft Learn — see [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md)) is wired
up in [ROADMAP.md Sprint 15](../ROADMAP.md) so an agent can ask Power BI a question directly.
It is explicitly documented as an **experimental/advanced integration**, not a dependency of the
core platform: the primary agent-facing paths are the custom MCP server (`mcp/`) and Databricks
Managed MCP, both GA; Power BI MCP is included to demonstrate the integration and to benchmark it
against those two paths (`benchmarks/agents.md`), not because anything else in the platform
depends on it working.

## Related

- [ARCHITECTURE.md §13 — Layer 10: Power BI](../ARCHITECTURE.md#13-layer-10--power-bi)
- [ADR-005 — Semantic layer](../docs/decisions/ADR-005-semantic-layer.md)
- [docs/semantic-dictionary.md](../docs/semantic-dictionary.md) — canonical metric definitions
- [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) — Power BI MCP status research
