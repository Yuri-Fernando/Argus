# Data Lineage

How lineage — "where did this value come from, and what does it feed downstream" — is tracked across the platform, and where that tracking honestly stops.

## Two lineage systems, two scopes

| System | Scope | Mechanism |
|---|---|---|
| **Unity Catalog automatic lineage** | Everything inside Azure Databricks: `bronze` → `silver` → `gold` table/column lineage, notebook/job → table lineage, model → feature-table lineage | Automatic, captured at query/job execution time from Spark/SQL execution plans — no manual annotation required |
| **Microsoft Purview** | Cross-platform discovery layer, connected to the Unity Catalog metastore | Purview scans/connects to Unity Catalog and surfaces its lineage graph, classifications and glossary terms in a single enterprise catalog view alongside other Azure data estate assets |

## Unity Catalog: what it captures automatically

For every table under the `customer_intelligence` catalog ([`data_catalog.md`](data_catalog.md)):

- **Table-level lineage**: which upstream tables/views a given table (or view) was produced from, and which downstream tables/dashboards/models read it.
- **Column-level lineage**: which upstream columns a given column was derived from — this is what lets `governance/pii.md`'s classification propagate correctly (a column derived from `email` should inherit "direct identifier" status even under a different name, and Unity Catalog's column lineage is how that gets verified rather than assumed).
- **Job/notebook lineage**: which Databricks Workflow/notebook run produced a given table version, tying a `gold.dim_customer` row back to the exact Golden Record merge run that produced it — the same run referenced in the survivorship log ([DATA_MODEL.md §4](../DATA_MODEL.md#4-golden-record--survivorship-rules)).
- **Model lineage**: which feature tables and which Gold tables a registered MLflow model (churn, segmentation, match/dedup — [ARCHITECTURE.md §10](../ARCHITECTURE.md#10-layer-7--machine-learning)) was trained from.

This lineage is visible in the Unity Catalog UI/API without any extra instrumentation in `lakehouse/` or `mdm/` code — it is a property of running the transformation as Delta/Spark inside Databricks.

## Purview: cross-platform discovery

Microsoft Purview connects to the Unity Catalog metastore as a data source and surfaces:

- A unified searchable catalog spanning Databricks alongside other Azure data estate assets (ADLS raw zones, Azure SQL if present, etc.).
- Sensitivity labels and classification tags that can be applied consistently across the Azure estate, complementing (not replacing) Unity Catalog's own PII tagging ([`pii.md`](pii.md)).
- A single pane of glass for a data steward asking "what tables reference `master_customer_id` anywhere in the Azure estate," without needing separate credentials per system.

## The honest gap: Databricks → Snowflake boundary

Lineage does **not** propagate automatically across the Databricks → Snowflake boundary. When `gold.dim_customer` in Unity Catalog is replicated into `CUSTOMER_INTELLIGENCE.CORE.DIM_CUSTOMER` in Snowflake via Streams + Tasks ([ARCHITECTURE.md §12](../ARCHITECTURE.md#12-layer-9--snowflake-enterprise-dwh--cortex)), Unity Catalog's lineage graph ends at the point the data leaves Databricks, and Snowflake's own lineage/access-history features begin a fresh graph on the Snowflake side. Purview connecting to Unity Catalog does not close this gap either — Purview's Snowflake connector, if enabled, would produce a **separate** lineage graph, not a continuous cross-platform trail from Delta table to Semantic View to Cortex Analyst answer.

**This is a known, documented limitation, not an oversight.** A fully continuous lineage trail across both platforms would require either a paid cross-platform lineage product (e.g. a metadata-lineage SaaS layered on top of both) or custom column-hash-based reconciliation — both out of scope for this portfolio project.

### How the gap is actually handled

Instead of a continuous lineage graph, the platform substitutes **evaluation-based parity verification**: `snowflake/evaluations/` runs a golden-question harness (`questions.csv` + `ground_truth.sql`) that checks, for the *same* business question, that the Snowflake-side answer (via Semantic Views / Cortex Analyst) matches the Databricks-side answer (via dbt/MetricFlow or Unity Catalog Metric Views) — [ARCHITECTURE.md §12](../ARCHITECTURE.md#12-layer-9--snowflake-enterprise-dwh--cortex) and [ADR-005](../docs/decisions/ADR-005-semantic-layer.md). This does not tell you "which exact upstream row produced this Snowflake value" the way Unity Catalog lineage does inside Databricks — it tells you "the two platforms still agree," which is the practical guarantee that actually matters for the "Power BI said R$10M, the agent said R$13M" failure mode this platform was built to prevent. Cross-platform lineage and cross-platform metric parity are answering two different questions, and only the second one is fully solved here.

## Related

- [`data_catalog.md`](data_catalog.md) — the catalog/schema/table registry lineage is anchored to.
- [`pii.md`](pii.md) — how column-level lineage supports PII classification propagation.
- [ADR-005 — Semantic layer](../docs/decisions/ADR-005-semantic-layer.md) — the metric parity test that substitutes for cross-platform lineage.
- [ARCHITECTURE.md §16](../ARCHITECTURE.md#16-layer-13--governance--security) — where Unity Catalog and Purview sit in the overall governance layer.
