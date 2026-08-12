# Semantic Dictionary

The **canonical metric definitions** for this platform — referenced everywhere else a metric is mentioned: [ARCHITECTURE.md §11](../ARCHITECTURE.md#11-layer-8--semantic-layer-three-implementations-one-contract), [ADR-005](decisions/ADR-005-semantic-layer.md), [`dbt/README.md`](../dbt/README.md). This is the "one metric, one definition" text source of truth described in [ARCHITECTURE.md §11](../ARCHITECTURE.md#11-layer-8--semantic-layer-three-implementations-one-contract) — it exists in **prose form here first**, and is then implemented (never re-defined) in up to three places:

| Implementation | Where | GA status |
|---|---|---|
| **dbt / MetricFlow** | [`dbt/models/marts/`](../dbt/README.md) | Apache 2.0, open-sourced late 2025 |
| **Unity Catalog Metric Views** | `databricks/unity_catalog/metric_views/` | GA Apr/2026 |
| **Snowflake Semantic Views** | [`snowflake/semantic_views/`](../snowflake/README.md) | GA Mar/2026 |

An automated parity test (`tests/data/test_metric_parity.py`, per [ADR-005](decisions/ADR-005-semantic-layer.md)) fails CI if any two implementations disagree on the same question against the same data. Every entry below states which implementation(s) *currently* carry it — a metric can be defined here before its dbt/UC/Snowflake implementation exists; the "Implemented in" column is the source of truth for what's actually built, not what's planned.

---

## Revenue

| | |
|---|---|
| **Formula** | `SUM(order_value)` |
| **Grain** | One row per completed order (`fact_orders`) |
| **Filters / exclusions** | `status = 'completed'` only — excludes `cancelled`, `returned`, and in-flight orders. Freight (`freight_value`) is **excluded** from Revenue; see AOV below for where it's included. |
| **Owner** | Finance / Commercial |
| **Implemented in** | dbt/MetricFlow, Unity Catalog Metric Views, Snowflake Semantic Views |

## Orders

| | |
|---|---|
| **Formula** | `COUNT(DISTINCT order_id)` |
| **Grain** | One row per order (`fact_orders`), any status unless filtered by a dimension slice |
| **Filters / exclusions** | Unfiltered by default (includes cancelled/returned) — use `Orders WHERE status = 'completed'` for the completed-only variant, which is a separate named metric slice, not a redefinition |
| **Owner** | Commercial / Operations |
| **Implemented in** | dbt/MetricFlow, Unity Catalog Metric Views, Snowflake Semantic Views |

## AOV (Average Order Value)

| | |
|---|---|
| **Formula** | `SUM(order_value + freight_value) / COUNT(DISTINCT order_id)` — over completed orders |
| **Grain** | Order-level average, evaluated per completed order |
| **Filters / exclusions** | `status = 'completed'` only. Unlike Revenue, freight **is** included, because AOV answers "what does a completed order cost the customer end to end," not "what does the business recognize as revenue" |
| **Owner** | Commercial |
| **Implemented in** | dbt/MetricFlow, Snowflake Semantic Views |

## Churn Rate

| | |
|---|---|
| **Formula** | `COUNT(DISTINCT master_customer_id WHERE churned = TRUE in period) / COUNT(DISTINCT master_customer_id active at period start)` |
| **Grain** | Customer-month (evaluated monthly; `churned` is defined by the churn model's label window — no purchase in the trailing 90 days as of period end, matching the label definition in `ml/churn/`) |
| **Filters / exclusions** | Customers with fewer than 2 historical orders are excluded from the denominator — a single-order customer has no established behavior pattern to "churn" from, and including them inflates the rate misleadingly |
| **Owner** | Customer Success / Data Science |
| **Implemented in** | Unity Catalog Metric Views, Snowflake Semantic Views |

## Repeat Rate

| | |
|---|---|
| **Formula** | `COUNT(DISTINCT master_customer_id WHERE order_count >= 2) / COUNT(DISTINCT master_customer_id WHERE order_count >= 1)` |
| **Grain** | Customer-level, evaluated over a rolling 12-month window unless a dashboard specifies a different window explicitly |
| **Filters / exclusions** | Cancelled/returned orders do not count toward `order_count` — a repeat customer must have two *completed* orders |
| **Owner** | Commercial / Customer Success |
| **Implemented in** | dbt/MetricFlow |

## CLV (Customer Lifetime Value)

| | |
|---|---|
| **Formula** | `dim_customer.lifetime_value` — the ML-modeled projection (not a simple historical sum), computed as expected future Revenue over a fixed forward horizon, weighted by the customer's churn probability (`1 − churn_score`) and historical AOV/purchase-frequency features |
| **Grain** | One value per `master_customer_id`, refreshed on each scheduled churn/segmentation model run |
| **Filters / exclusions** | Only customers with a `master_customer_id` resolved by the Golden Record (i.e., post-MDM) are eligible — CLV is never computed against an unresolved source-system customer record |
| **Owner** | Data Science / Customer Success |
| **Implemented in** | Snowflake Semantic Views (surfaces the pre-computed `lifetime_value` column; the *computation* itself lives in [`ml/`](../ml/README.md), not in the semantic layer — the semantic layer exposes a model output, it does not re-derive it) |

## NPS (Net Promoter Score)

| | |
|---|---|
| **Formula** | `(% Promoters − % Detractors)` where Promoters = `review_score >= 9` and Detractors = `review_score <= 6`, on a 0–10 satisfaction scale mapped from the Olist 1–5 review scale (`review_score_10 = review_score * 2`) combined with `support_tickets.sentiment` where a review is absent |
| **Grain** | Aggregate, evaluated per period (monthly) and sliceable by `customer_segment` |
| **Filters / exclusions** | Reviews with no free-text and no numeric score are excluded, not imputed |
| **Owner** | Customer Success |
| **Implemented in** | Not yet implemented in any of the three layers — defined here first, per the "canonical definition precedes implementation" rule; tracked as a Sprint 8+ backlog item alongside the other marts |

## Delivery SLA

| | |
|---|---|
| **Formula** | `COUNT(DISTINCT order_id WHERE order_delivered_customer_date <= order_estimated_delivery_date) / COUNT(DISTINCT order_id WHERE order_delivered_customer_date IS NOT NULL)` |
| **Grain** | Order-level, evaluated only over orders that actually reached delivery (in-flight orders are excluded, not counted as failures) |
| **Filters / exclusions** | Orders cancelled before dispatch are excluded entirely — SLA measures delivery performance, not order completion |
| **Owner** | Operations / Logistics |
| **Implemented in** | dbt/MetricFlow, Unity Catalog Metric Views |

## Data Quality Score

| | |
|---|---|
| **Formula** | Weighted rollup of the per-dataset `dq_score` values produced by the GX Core checkpoint run ([ARCHITECTURE.md §7](../ARCHITECTURE.md#7-layer-4--data-quality)), weighted by row-count share of the dataset in the current pipeline run: `SUM(dataset_dq_score * dataset_row_count) / SUM(dataset_row_count)` |
| **Grain** | One value per pipeline run, sliceable by dataset (`bronze.olist_customers`, `bronze.crm_customers`, etc.) and by DQ dimension (completeness/validity/uniqueness/referential integrity/freshness/schema/volume — [ARCHITECTURE.md §7](../ARCHITECTURE.md#7-layer-4--data-quality)) |
| **Filters / exclusions** | Datasets under active backfill/replay are excluded from the platform-level rollup until the backfill completes, to avoid a large historical reprocessing run temporarily depressing the live score |
| **Owner** | Data Engineering / Data Governance |
| **Implemented in** | Unity Catalog Metric Views (consumed directly by the Data Quality Agent, [ARCHITECTURE.md §15](../ARCHITECTURE.md#15-layer-12--mcp--agentic-ai), and the Power BI Data Quality dashboard) |

---

## Related

- [ADR-005 — Semantic layer](decisions/ADR-005-semantic-layer.md) — why three implementations exist for one canonical definition.
- [ARCHITECTURE.md §11](../ARCHITECTURE.md#11-layer-8--semantic-layer-three-implementations-one-contract) — the "one metric, one definition" principle this document enforces.
- [`dbt/README.md`](../dbt/README.md) — where the dbt/MetricFlow implementation lives.
- [`docs/data_dictionary.md`](data_dictionary.md) — the column-level (not metric-level) companion dictionary.
