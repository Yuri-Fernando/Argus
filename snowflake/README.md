# snowflake/

Enterprise Data Warehouse + Cortex AI serving layer — ARCHITECTURE.md §12, built in **Sprint 7** (DWH) through **Sprint 15** (Cortex Agents comparison). See [ADR-002](../docs/decisions/ADR-002-lakehouse-vs-warehouse.md) for why this exists alongside Databricks, not instead of it.

```
snowflake/
├── databases/ schemas/ warehouses/ roles/ grants/   # human-readable SQL DDL mirrors of terraform/modules/snowflake/
├── tables/               # CORE dimensional model DDL (mirrors lakehouse/gold/, see DATA_MODEL.md §3)
├── views/
├── semantic_views/        # Sprint 8 — one of the three semantic layer implementations, see ADR-005
├── cortex/
│   ├── analyst/            # Semantic View bindings consumed by Cortex Analyst
│   ├── search/               # Cortex Search index config over rag/ output
│   ├── agents/                 # Cortex Agents config (Analyst + Search orchestration)
│   └── functions/               # AI_PARSE_DOCUMENT / AI_EXTRACT / AI_SENTIMENT / AI_EMBED / AI_REDACT usage
└── evaluations/                  # golden-question harness: questions.csv, ground_truth.sql, results/, metrics/
                                   # (SQL correctness, answer correctness, latency, regression — ARCHITECTURE.md §12)
```

## Status (Aug/2026 research — see IMPROVEMENTS_AND_RESEARCH.md)

Cortex Analyst and Cortex Agents are **GA** (Nov/2025); Semantic View SQL querying is **GA** (Mar/2026); Cortex AI Guardrails are **GA** (May/2026). This layer is treated as core/production-like, not experimental.

## Local development — DuckDB stand-in (no live Snowflake account)

There is no live Snowflake account in this environment. `snowflake/local_runner.py` is
the **local-dev stand-in for the real Snowflake warehouse**: it builds
`data/warehouse/local.duckdb` from the portable ANSI SQL in `snowflake/ddl/*.sql`
(the same DDL that also runs unmodified on a real Snowflake account), loads it from
the real synthetic parquet sources already on disk (`data/lakehouse/silver/`,
`data/mdm/golden_record.parquet`, `data/ml/features/`, `data/ml/segmentation/`), and
exposes `run_metric(con, name)` implementing the canonical metric definitions from
[`docs/semantic-dictionary.md`](../docs/semantic-dictionary.md) wherever the
available data supports them.

```
snowflake/
├── ddl/              # portable ANSI SQL CREATE TABLE — dim_customer, dim_date, dim_geography,
│                      #   dim_campaign, fact_payments, fact_support_interactions,
│                      #   fact_campaign_interactions, fact_web_events. Runs on Snowflake and DuckDB.
├── views/            # portable ANSI SQL views (vw_customer_360, vw_revenue_by_month) over the DDL above
├── local_runner.py   # DuckDB build + run_metric() — see below
└── semantic_views/customer_intelligence_semantic_view.sql
                       # real Snowflake Semantic View DDL (ADR-005), NOT executed here — no live account
```

Run it:

```bash
python snowflake/local_runner.py                  # build data/warehouse/local.duckdb, print every metric
python snowflake/local_runner.py --metric revenue  # build + print one metric
```

### Known limitations (documented deviations from docs/semantic-dictionary.md)

This platform snapshot has **no `data/raw/olist`** (confirmed absent) — there is no
`fact_orders` / `order_value` / delivery-date data anywhere in the build. As a result:

| Metric | Status | Local-runner definition |
|---|---|---|
| **Revenue** | Implemented (deviated) | `SUM(net_amount)` over `fact_payments WHERE status = 'settled'`, standing in for order-based `SUM(order_value)` — no `fact_orders` exists to compute the canonical form. |
| **AOV** | Implemented (deviated) | `SUM(gross_amount) / COUNT(DISTINCT payment_id)` over settled payments — no `freight_value` column exists in `payment_finance`, so `gross_amount` stands in as the "cost to the customer end to end" figure. |
| **Churn Rate** | Implemented (proxy) | `recency_days > 90` as the churn label (matches the semantic dictionary's 90-day intuition), since no `ml/churn/` time-series label output exists in this build — only `ml/features/` and `ml/segmentation/` are on disk. Denominator restricted to `frequency >= 2`, per the canonical exclusion rule. |
| **Repeat Rate** | Implemented | `frequency` (from `ml/features/customer_features.parquet`) used as the completed-order-count proxy. |
| **CLV** | Implemented (proxy) | Surfaces `dim_customer.lifetime_value`, computed structurally per the canonical formula (`AOV proxy × frequency × (1 − churn_score)`) but using the **proxy** `churn_score` above in place of a real `ml/churn/` model score, since that artifact doesn't exist in this build. |
| **Orders** | Skipped | Requires `fact_orders` (`data/raw/olist`) — absent. |
| **Delivery SLA** | Skipped | Requires `order_delivered_customer_date` / `order_estimated_delivery_date` (`data/raw/olist`) — absent. |
| **NPS** | Skipped | Not yet implemented in any of the three semantic layers per `docs/semantic-dictionary.md` — canonical definition exists, no implementation is claimed anywhere yet. |
| **Data Quality Score** | Skipped | Owned by the `data_quality/` module, not a warehouse-native metric. |

`snowflake/semantic_views/customer_intelligence_semantic_view.sql` implements the
same metric set (and the same documented deviations) in real Snowflake Semantic View
syntax, for parity comparison against `local_runner.py::run_metric()` — labeled
throughout as **not executed here, no live Snowflake account**.
