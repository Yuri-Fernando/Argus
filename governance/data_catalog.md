# Data Catalog

How the platform catalogs itself: the Unity Catalog registry structure on the Databricks side, its Snowflake equivalent, and where the human-readable data dictionary fits alongside both.

## Unity Catalog structure

```
customer_intelligence                    # catalog
├── bronze                                # schema — near-exact copy of raw, Delta-ified
│   ├── olist_customers, olist_orders, olist_order_items, olist_products,
│   │   olist_sellers, olist_payments, olist_reviews, olist_geolocation
│   ├── crm_customers, marketing_events, support_tickets, web_events
├── silver                                # schema — normalized, deduplicated (structural), typed
│   ├── customer, order, order_item, product, payment, support, web_event
├── gold                                  # schema — business-ready dimensional model
│   ├── dim_customer, dim_product, dim_seller, dim_date
│   ├── fact_orders, fact_order_items, fact_payments,
│   │   fact_customer_interactions, fact_support
├── ml                                    # schema — feature tables + registered models
│   ├── churn_features, segmentation_features, matching_features
│   └── (models registered in the MLflow Model Registry, linked via UC Models)
└── monitoring                            # schema — DQ scores, pipeline run metadata, agent/LLM telemetry
    ├── dq_score_history, pipeline_run_log, agent_run_log
```

This mirrors [ARCHITECTURE.md §6](../ARCHITECTURE.md#6-layer-3--lakehouse-azure-databricks) exactly — the catalog is the enforcement point for both the Medallion architecture and the RBAC model in [`access_control.md`](access_control.md). Every table is registered with Unity Catalog's own metadata (owner, comment, tags), which is what feeds automatic lineage ([`lineage.md`](lineage.md)) and PII tagging ([`pii.md`](pii.md)).

## Snowflake equivalent

```
CUSTOMER_INTELLIGENCE                     # database
├── RAW                                   # schema — landed via Streams + Tasks from Databricks Gold/Silver
├── STAGING                               # schema — light typing/renaming pass, mirrors dbt staging models
├── CORE                                  # schema — dimensional model, mirrors gold.* (DATA_MODEL.md §3)
│   ├── DIM_CUSTOMER, DIM_PRODUCT, DIM_SELLER, DIM_DATE
│   ├── FACT_ORDERS, FACT_ORDER_ITEMS, FACT_PAYMENTS,
│   │   FACT_CUSTOMER_INTERACTIONS, FACT_SUPPORT
├── ANALYTICS                             # schema — marts consumed by Power BI / ad-hoc analysis
├── SEMANTIC                              # schema — Snowflake Semantic Views (one of the three semantic
│                                          #   layer implementations, ADR-005)
└── AI                                    # schema — Cortex objects: Cortex Search indexes, Cortex Agents
                                           #   config, AI Function bindings (AI_PARSE_DOCUMENT, AI_EXTRACT,
                                           #   AI_SENTIMENT, AI_EMBED, AI_REDACT)
```

This mirrors [`snowflake/README.md`](../snowflake/README.md) and [ARCHITECTURE.md §12](../ARCHITECTURE.md#12-layer-9--snowflake-enterprise-dwh--cortex). `CORE` is the Snowflake-side twin of Databricks `gold` — kept in sync via Streams + Tasks, with the honest lineage caveat documented in [`lineage.md`](lineage.md).

## Catalog ↔ catalog mapping

| Unity Catalog schema | Snowflake schema | Relationship |
|---|---|---|
| `bronze` | `RAW` | Both are the least-transformed layer, but `RAW` in Snowflake is populated *from* Databricks Gold/Silver, not from the original source systems directly — Snowflake never re-ingests Olist/CRM/etc. on its own |
| `silver` | `STAGING` | Snowflake's `STAGING` is a lighter pass than Databricks Silver — most cleansing already happened upstream by the time data reaches Snowflake |
| `gold` | `CORE` | Direct dimensional-model mirror — same grain, same keys (`master_customer_id`, `order_id`, etc.) |
| `ml` | — (no direct equivalent) | Feature engineering and model training live in Databricks; Snowflake consumes derived scores (`churn_score`, `lifetime_value`) already materialized into `CORE.DIM_CUSTOMER`, it does not train models itself |
| — (no direct equivalent) | `ANALYTICS`, `SEMANTIC`, `AI` | Snowflake-specific layers: BI marts, the Semantic View implementation of the semantic layer, and the Cortex AI serving surface — these exist because Snowflake, not Databricks, is the platform's designated AI serving / governed-DWH layer ([ARCHITECTURE.md §3](../ARCHITECTURE.md#3-tech-stack-rationale)) |

## Where `docs/data_dictionary.md` fits

Both registries above are the **machine-enforced** catalog — grants, lineage, tags, and query-time enforcement live there, in Unity Catalog and Snowflake themselves (and are provisioned via `terraform/modules/{databricks,snowflake}/`). [`docs/data_dictionary.md`](../docs/data_dictionary.md) is the **human-readable companion**: a single flat, git-versioned Markdown document listing every column across both registries — type, source system, PII classification (cross-referencing [`pii.md`](pii.md)), and a one-line description — the document a new engineer or a recruiter reviewing the repo reads *without* needing Databricks/Snowflake credentials. The two are meant to describe the same reality from two different vantage points: the catalog is the source of truth at query time, `docs/data_dictionary.md` is the source of truth for anyone reading the repository.

## Related

- [`docs/data_dictionary.md`](../docs/data_dictionary.md) — column-by-column human-readable dictionary.
- [`docs/semantic-dictionary.md`](../docs/semantic-dictionary.md) — the metric-level (not column-level) companion, one layer up.
- [`lineage.md`](lineage.md) — how lineage is tracked across and between these two catalogs.
- [`pii.md`](pii.md) — the classification tags applied to columns in both catalogs.
- [ARCHITECTURE.md §20](../ARCHITECTURE.md#20-repository-structure) — full repository structure this catalog design fits into.
