# Dashboard Page Specs

Concrete, page-by-page blueprint for the 6 report pages. This is written to be the
**direct blueprint for a Streamlit dashboard** being built centrally afterward — every
chart names its exact backing metric/DAX measure/table/column, not a vague description.
All data sourced from the semantic model (`powerbi/semantic_model/`) / dbt marts
(`dbt/models/marts/`) — never a raw table (`powerbi/README.md` "Hard rule").

Six pages (the two extras beyond `powerbi/README.md`'s original 5 — **ML** and the
renamed **Platform Observability** — reflect this task's brief; content maps 1:1 to
what's actually computable in this repo snapshot).

---

## 1. Executive Overview

Top-line KPIs for a non-technical / leadership audience.

| Position | Visual | Metric / Field | Source |
|---|---|---|---|
| KPI card 1 | Big number | `[Revenue]` — R$ 15,515,805.42 | `fact_payments.net_amount`, `status="settled"` |
| KPI card 2 | Big number | `[AOV]` — R$ 1,751.79 | `fact_payments.gross_amount` / `payment_id` count |
| KPI card 3 | Big number | `[Active Customers]` | `dim_customer`, `frequency >= 1` |
| KPI card 4 | Big number | `[Churn Rate]` — 0.5308 | `dim_customer.recency_days`, `frequency` |
| KPI card 5 | Big number | `[Repeat Rate]` — 0.4033 | `dim_customer.frequency` |
| KPI card 6 | Big number | `[CLV (avg)]` — R$ 990.26 | `dim_customer.lifetime_value` |
| Chart 1 | Line chart | `[Revenue]` by `dim_date.month_name`/`year`, settled payments only | `fact_payments` x `dim_date` |
| Chart 2 | Bar chart | `[Settled Payment Count]` by `fact_payments.method` | `fact_payments.method` |
| Chart 3 | Donut | Customer count by `dim_customer.segment` | `dim_customer.segment` |
| Note | Text box | "Orders/Delivery SLA/NPS not shown — no `data/raw/olist` order data in this snapshot; Revenue/AOV computed against settled `payment_finance` records instead. See `docs/semantic-dictionary.md`." | static |

**Streamlit mapping**: `st.metric()` x6 for the KPI row, `st.line_chart`/plotly for
Chart 1, `st.bar_chart` for Chart 2, plotly pie/donut for Chart 3.

---

## 2. Customer Intelligence

RFM, CLV, churn score distribution, segmentation breakdown — the platform's core
data-science-facing page.

| Position | Visual | Metric / Field | Source |
|---|---|---|---|
| KPI card 1 | Big number | `[Total Customers]` | `dim_customer.master_customer_id` distinct count |
| KPI card 2 | Big number | `[CLV (avg)]` | `dim_customer.lifetime_value` |
| KPI card 3 | Big number | `[CLV (median)]` | `dim_customer.lifetime_value` |
| KPI card 4 | Big number | `[Churn Rate]` | `dim_customer.recency_days`, `frequency` |
| Chart 1 | Scatter plot | RFM: X = `recency_days`, Y = `monetary`, size = `frequency`, color = `segment` | `dim_customer` |
| Chart 2 | Histogram | Distribution of `dim_customer.churn_score` (bucketed 0.0–1.0 in 0.1 steps) | `dim_customer.churn_score` |
| Chart 3 | Histogram | Distribution of `dim_customer.lifetime_value` | `dim_customer.lifetime_value` |
| Chart 4 | Stacked bar | Customer count by `segment`, split by `is_repeat_customer` | `dim_customer.segment`, `is_repeat_customer` |
| Chart 5 | Table | Top 20 customers by `lifetime_value` — columns: `canonical_name`, `segment`, `monetary`, `frequency`, `churn_score`, `lifetime_value` | `dim_customer` |
| Chart 6 | Map (city bubble) | Customer count / avg `monetary` by `dim_geography.city`/`state` | `dim_geography` x `dim_customer` |

**Streamlit mapping**: plotly scatter for Chart 1, plotly histogram for Charts 2–3,
plotly stacked bar for Chart 4, `st.dataframe` for Chart 5, plotly scattergeo/mapbox
(or a Brazil choropleth by `state`) for Chart 6.

**Data note**: `cluster`/`segment` come from `data/ml/segmentation/customer_segments.parquet`
(ml/segmentation/ module) — read-only source for this page.

---

## 3. Operations

**Thin page** — this platform snapshot has no `data/raw/olist` order/delivery data, so
Delivery SLA and order-fulfillment visuals are **not populated**; the page instead
covers everything operations-adjacent that *is* computable: support ticket volume and
sentiment (from `support_ticket`) and campaign delivery mechanics (from
`campaign_interaction`).

| Position | Visual | Metric / Field | Source |
|---|---|---|---|
| KPI card 1 | Big number | `[Support Ticket Volume]` | `fact_support_interactions` row count |
| KPI card 2 | Big number | `[Unresolved Ticket Rate]` | `fact_support_interactions.resolution_status` |
| KPI card 3 | Big number | `[Avg Ticket Resolution Days]` | `fact_support_interactions.resolution_days` |
| KPI card 4 | Big number | `[Campaign Conversion Rate]` | `fact_campaign_interactions.conversion` / `clicks` |
| Chart 1 | Bar chart | Ticket count by `category` | `fact_support_interactions.category` |
| Chart 2 | Bar chart | Ticket count by `priority` | `fact_support_interactions.priority` |
| Chart 3 | Line chart | Ticket volume over time by `dim_date.month_name` (via `date_key_created`) | `fact_support_interactions` x `dim_date` |
| Chart 4 | Bar chart | `total_cost` and `total_conversions` by `dim_campaign.primary_channel` | `dim_campaign` |
| Empty-state note | Text box | "Delivery SLA and Orders are defined in `docs/semantic-dictionary.md` but **not computable** — this repo snapshot has no `data/raw/olist` order/delivery data (`snowflake/local_runner.py SKIPPED_METRICS`). This page shows what operational signal the platform *does* have: support and campaign delivery." | static |

**Streamlit mapping**: 4 `st.metric()`, plotly bar charts for Charts 1/2/4, plotly line
for Chart 3, an `st.info()` box for the empty-state note.

---

## 4. Data Quality

The platform's own `dq_score`, owned by `data_quality/` (out of this task's scope to
compute — this page's spec names what it displays, not new logic to build).

| Position | Visual | Metric / Field | Source |
|---|---|---|---|
| KPI card 1 | Big number | Overall `Data Quality Score` (weighted rollup, `docs/semantic-dictionary.md`) | `data_quality/reports/` output |
| KPI card 2 | Big number | Quarantine rate | `data_quality/reports/` output |
| Chart 1 | Bar chart | `dq_score` per dataset (`bronze.crm_customers`, `bronze.customer_payments`, `bronze.support_tickets`, `bronze.campaign_interactions`, `bronze.web_events`) | `data_quality/reports/` (per-dataset GX Core checkpoint results) |
| Chart 2 | Radar / grouped bar | `dq_score` sliced by DQ dimension (completeness, validity, uniqueness, referential integrity, freshness, schema, volume) per dataset | `data_quality/expectations/` + `data_quality/reports/` |
| Chart 3 | Table | Latest GX Core checkpoint run: dataset, dimension, pass/fail, row count | `data_quality/reports/` |
| Note | Text box | "This page is driven by the `data_quality/` module (Great Expectations Core checkpoints), not by the semantic layer marts — it measures the *inputs* to the marts, not the marts themselves." | static |

**Streamlit mapping**: read `data_quality/reports/*.json` (or the module's summary
output) directly; `st.metric()` for KPIs, plotly bar for Chart 1, plotly radar/grouped
bar for Chart 2, `st.dataframe` for Chart 3.

---

## 5. ML

Model outputs and explainability, from `ml/` (read-only source for this page).

| Position | Visual | Metric / Field | Source |
|---|---|---|---|
| KPI card 1 | Big number | Customer count with a resolved `segment` | `data/ml/segmentation/customer_segments.parquet` |
| KPI card 2 | Big number | Number of clusters (`distinct(cluster)`) | `data/ml/segmentation/customer_segments.parquet` |
| KPI card 3 | Big number | `[CLV (avg)]` (same measure as pages 1–2, ML-owned computation) | `dim_customer.lifetime_value` |
| Chart 1 | Scatter / PCA plot | Segmentation clusters, colored by `cluster`, sized by `monetary` | `ml/segmentation/` output + `customer_features` |
| Chart 2 | Bar chart | Customer count per `segment` | `customer_segments.segment` |
| Chart 3 | Feature importance bar | Top features from `ml/explainability/` (e.g. SHAP values) driving `churn_score` proxy | `ml/explainability/` output |
| Chart 4 | Table | Segment profile summary: avg `recency_days`, `frequency`, `monetary`, `churn_score`, `lifetime_value` per `segment` | `dim_customer` grouped by `segment` |
| Note | Text box | "No `ml/churn/` model artifact exists in this repo snapshot — `churn_score`/`lifetime_value` shown here are the recency-based proxy defined in `snowflake/local_runner.py`, not a trained classifier output. `ml/explainability/` reflects whatever model *is* on disk." | static |

**Streamlit mapping**: plotly scatter for Chart 1, plotly bar for Charts 2/3,
`st.dataframe` (or `st.bar_chart` per-metric) for Chart 4.

---

## 6. Platform Observability

Mirrors the Grafana view for a non-technical audience — pipeline health, DQ trend,
ML/LLM/MCP latency and cost. **Largely out of this task's scope to compute** (owned by
platform/observability tooling, not the semantic layer) — this page names the intended
panels so the Streamlit build knows what to wire up when that data exists.

| Position | Visual | Metric / Field | Source |
|---|---|---|---|
| KPI card 1 | Big number | Last pipeline run status (success/fail) | pipeline orchestration logs (out of scope here) |
| KPI card 2 | Big number | Last pipeline run duration | pipeline orchestration logs |
| Chart 1 | Line chart | `Data Quality Score` trend over recent pipeline runs | `data_quality/reports/` history |
| Chart 2 | Line chart | Row counts loaded per Silver table per run (`crm_customer`, `payment_finance`, `support_ticket`, `campaign_interaction`, `web_event`) | `lakehouse/silver/` run logs |
| Chart 3 | Bar chart | ML/LLM/MCP call latency (p50/p95) | out of scope in this repo snapshot — no latency telemetry on disk |
| Chart 4 | Bar chart | ML/LLM/MCP cost per run | out of scope in this repo snapshot — no cost telemetry on disk |
| Note | Text box | "This page is the thinnest of the six — no pipeline-run telemetry, latency, or cost data exists on disk in this repo snapshot (that instrumentation lives outside this task's scope: `lakehouse/`, `mdm/`, `ml/`, `data_quality/` are read-only here). Wire this page up once a run-metadata/telemetry table exists." | static |

**Streamlit mapping**: this page should render its empty-state note prominently and
degrade gracefully (e.g. `st.warning()` per missing panel) rather than fabricate
numbers — consistent with this platform's "no invention" principle
(`docs/semantic-dictionary.md`, `SKIPPED_METRICS` in `snowflake/local_runner.py`).

---

## Cross-page conventions

- Every KPI card and chart that reads a headline metric (Revenue, AOV, Churn Rate,
  Repeat Rate, CLV) uses the **exact DAX formula** in `powerbi/dax/measures.md`, which
  is cross-checked line-by-line against `snowflake/local_runner.py::run_metric()`.
- Currency fields format as `R$ #,0.00` (BRL, matching the synthetic dataset's locale).
- Percentage fields (`Churn Rate`, `Repeat Rate`, `Unresolved Ticket Rate`, conversion/
  click-through rates) format as `0.0%`.
- No visual on any page invents a number for Orders, Delivery SLA, or NPS — those are
  either omitted or shown with an explicit "not computable in this snapshot" note,
  per `docs/semantic-dictionary.md` and `snowflake/local_runner.py SKIPPED_METRICS`.
