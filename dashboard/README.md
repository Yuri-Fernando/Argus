# Dashboard

A 6-page Streamlit app that renders the platform's real, already-computed metrics live —
every number on every page is read from an actual file or module on disk at runtime
(`snowflake/local_runner.py`'s DuckDB warehouse, `data_quality/reports/`, `data/ml/**`,
`data/mdm/**`, `rag/evaluation/`, `mlflow/mlruns/`). Nothing in `dashboard/app.py` is a
hardcoded metric value; it only reuses the platform's own modules and renders their output.

It follows `powerbi/dashboard/page_specs.md` as its page-by-page blueprint.

## Run it

```bash
/c/Users/Yuri_/AppData/Local/Programs/Python/Python310/python.exe -m streamlit run dashboard/app.py
```

Or headless, on a fixed port:

```bash
/c/Users/Yuri_/AppData/Local/Programs/Python/Python310/python.exe -m streamlit run dashboard/app.py --server.headless true --server.port 8501
```

First load takes ~15-40s: it builds the local DuckDB warehouse
(`snowflake/local_runner.py::build_warehouse()`) from the real parquet sources, and the ML
page additionally loads the registered MLflow champion model and computes SHAP values.
Both are cached (`st.cache_resource` / `st.cache_data`) so subsequent page switches are fast.

## Pages

1. **Executive Overview** — Revenue, AOV, Active Customers, Churn Rate, Repeat Rate, CLV as
   KPI cards, plus a revenue-by-month line chart, settled-payment-count-by-method bar chart,
   and a customer-by-segment donut. All computed live via
   `snowflake/local_runner.py::run_metric()` / `run_all_metrics()` against the DuckDB
   warehouse built from `data/lakehouse/silver/`, `data/mdm/golden_record.parquet`,
   `data/ml/features/`, and `data/ml/segmentation/`.

2. **Customer Intelligence** — RFM scatter, churn-score/lifetime-value histograms,
   segment x repeat-customer bar, top-20-by-CLV table, and a churn-risk table, all from the
   `dim_customer` view of the DuckDB warehouse. Also shows real MDM golden-record stats
   (row counts from `data/mdm/golden_record.parquet` and `data/mdm/clusters.parquet`) and
   candidate-pair counts from `data/mdm/candidate_pairs_deterministic.parquet`,
   `candidate_pairs_fuzzy.parquet`, and `scored_candidates_ml.parquet`.

3. **Operations** — support-ticket volume/category/priority/time-series and campaign
   cost/conversion-by-channel, from `fact_support_interactions` / `fact_campaign_interactions`
   / `dim_campaign` in the DuckDB warehouse (built from `data/lakehouse/silver/support_ticket.parquet`
   and `campaign_interaction.parquet`). Explicitly thin — no Olist order/delivery data exists
   in this build, so Delivery SLA/Orders are omitted with an on-page note, per
   `snowflake/local_runner.py::SKIPPED_METRICS`.

4. **Data Quality** — overall + per-table DQ score, per-table x per-dimension score breakdown,
   full rule-level detail table, and quarantine counts — all read directly from
   `data_quality/reports/dq_report.json`.

5. **ML** — segmentation cluster scatter and per-segment counts from
   `data/ml/segmentation/customer_segments.parquet`; a real churn-model comparison table
   (ROC-AUC/F1/PR-AUC/Brier for Logistic Regression/Random Forest/Gradient Boosting) read
   from the local MLflow tracking store (`mlflow/mlruns`, experiment `churn_model`); a SHAP
   global-feature-importance bar chart plus one real customer's top contributions, computed
   live against the registered champion model (`models:/churn_model/1`) using the same
   feature-building (`ml/features/build_features.py`) and labeling (`ml/churn/label.py`)
   logic as `ml/explainability/shap_analysis.py`; and a segment profile summary table.

6. **Platform Observability** — MDM entity-resolution precision/recall/F1, computed live by
   reusing `mdm/entity_resolution/evaluation/evaluate.py::evaluate_clusters()` against
   `data/mdm/clusters.parquet` and the ground-truth CSV; RAG precision@k from
   `rag/evaluation/precision_at_k_results.json`; a note on the A2A/MCP layer
   (`agents/a2a/`, live-testable separately); current Silver row counts (a snapshot, not a
   trend — no pipeline-run history exists on disk); and an honest "what's real vs.
   simulated in this build" summary (Olist absent, LLM gateway stubbed, Terraform validated
   but not applied, Kubernetes structurally validated only).

## Notes

- All source modules this dashboard reads from (`snowflake/`, `data_quality/`, `mdm/`,
  `ml/`, `rag/`, `mlflow/`, `data/`) are read-only from this file's perspective — it never
  writes to them, except that MLflow's file store may create small housekeeping files on
  first client connection (no new runs are logged).
- Runs fully offline — no external API or CDN calls.
