# Pipeline benchmarks

What this measures and why: throughput and reliability of the ingestion → Bronze → Silver → Gold
pipeline (Databricks jobs / Databricks Asset Bundles, [ARCHITECTURE.md §6](../ARCHITECTURE.md#6-layer-3--lakehouse-azure-databricks)).
A pipeline that "works" in a demo but silently degrades in throughput or fails intermittently
isn't production-like — these numbers are what makes "it runs" a checkable claim instead of an
assumption.

| Metric | Value | Date measured | Sprint | Notes |
|---|---|---|---|---|
| processing_time | | | | |
| records_per_second | | | | |
| failure_rate | | | | |

## Related

[ARCHITECTURE.md §17](../ARCHITECTURE.md#17-layer-14--observability--finops) ·
[IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) backlog item 5 (FinOps cost guardrails)
