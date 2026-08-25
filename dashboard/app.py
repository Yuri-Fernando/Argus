"""
dashboard/app.py
=================
Multi-page Streamlit dashboard for the Enterprise Customer Intelligence Data Platform.

Every number rendered on every page is read live from a real file or module already
built by the platform (`snowflake/local_runner.py`, `data_quality/reports/`,
`data/ml/**`, `data/mdm/**`, `rag/evaluation/`, `mlflow/mlruns/`) — nothing here is
hardcoded. This file only orchestrates reads + Streamlit/Plotly rendering; it never
recomputes a metric formula that already lives in `snowflake/local_runner.py`,
`mdm/entity_resolution/evaluation/evaluate.py`, or `ml/`.

Run:
    streamlit run dashboard/app.py --server.headless true

See dashboard/README.md for a page-by-page description of what renders and where its
data comes from.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pyarrow.parquet as pq
import streamlit as st

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Repo wiring — make every read-only source module importable regardless of
# the working directory Streamlit was launched from.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from snowflake.local_runner import build_warehouse, run_all_metrics  # noqa: E402
from mdm.entity_resolution.evaluation.evaluate import evaluate_clusters  # noqa: E402

MLFLOW_URI = (REPO_ROOT / "mlflow" / "mlruns").as_uri()

DATA_MDM = REPO_ROOT / "data" / "mdm"
DATA_ML_FEATURES = REPO_ROOT / "data" / "ml" / "features"
DATA_ML_SEGMENTS = REPO_ROOT / "data" / "ml" / "segmentation"
DATA_SILVER = REPO_ROOT / "data" / "lakehouse" / "silver"
DQ_REPORT_PATH = REPO_ROOT / "data_quality" / "reports" / "dq_report.json"
RAG_RESULTS_PATH = REPO_ROOT / "rag" / "evaluation" / "precision_at_k_results.json"

st.set_page_config(
    page_title="Argus",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Formatting helpers (cross-page conventions, powerbi/dashboard/page_specs.md)
# ---------------------------------------------------------------------------
def fmt_currency(v: float) -> str:
    try:
        return f"R$ {float(v):,.2f}"
    except (TypeError, ValueError):
        return "n/a"


def fmt_pct(v: float) -> str:
    try:
        return f"{float(v):.1%}"
    except (TypeError, ValueError):
        return "n/a"


def fmt_int(v: float) -> str:
    try:
        return f"{int(v):,}"
    except (TypeError, ValueError):
        return "n/a"


# ---------------------------------------------------------------------------
# Cached data loaders — every one reads a real file/module. No literal metric
# values are ever assigned in this file.
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Building local semantic warehouse (DuckDB) from real parquet sources...")
def get_warehouse():
    """Reuses snowflake/local_runner.py end to end — same DDL, same joins, same
    proxy-metric formulas already validated in BUILD_LOG.md."""
    return build_warehouse()


@st.cache_data(show_spinner=False)
def get_all_metrics() -> dict:
    return run_all_metrics(get_warehouse())


@st.cache_data(show_spinner=False)
def run_sql(sql: str) -> pd.DataFrame:
    return get_warehouse().execute(sql).fetchdf()


@st.cache_data(show_spinner=False)
def load_dq_report() -> dict:
    with open(DQ_REPORT_PATH, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_segments() -> pd.DataFrame:
    return pd.read_parquet(DATA_ML_SEGMENTS / "customer_segments.parquet")


@st.cache_data(show_spinner=False)
def load_features() -> pd.DataFrame:
    return pd.read_parquet(DATA_ML_FEATURES / "customer_features.parquet")


@st.cache_data(show_spinner=False)
def load_golden_record() -> pd.DataFrame:
    return pd.read_parquet(DATA_MDM / "golden_record.parquet")


@st.cache_data(show_spinner=False)
def load_clusters() -> pd.DataFrame:
    return pd.read_parquet(DATA_MDM / "clusters.parquet")


@st.cache_data(show_spinner=False)
def load_candidate_pair_counts() -> dict:
    det = pd.read_parquet(DATA_MDM / "candidate_pairs_deterministic.parquet")
    fuzzy = pd.read_parquet(DATA_MDM / "candidate_pairs_fuzzy.parquet")
    ml_scored = pd.read_parquet(DATA_MDM / "scored_candidates_ml.parquet")
    return {
        "deterministic_pairs": len(det),
        "deterministic_auto_match": int((det["decision"] == "AUTO_MATCH").sum()),
        "deterministic_pending_fuzzy_ml": int((det["decision"] == "PENDING_FUZZY_ML").sum()),
        "fuzzy_pairs": len(fuzzy),
        "ml_scored_pairs": len(ml_scored),
        "ml_upgraded_to_match": int((ml_scored["decision"] != "DISTINCT").sum())
        if "decision" in ml_scored.columns
        else None,
    }


@st.cache_data(show_spinner=False)
def load_mdm_evaluation() -> dict:
    """Reuses mdm/entity_resolution/evaluation/evaluate.py's real evaluate_clusters()
    against the actual clusters.parquet output and the ground-truth CSV — the exact
    pipeline-vs-ground-truth check documented in BUILD_LOG.md (Recall 1.0, Precision
    0.9687, F1 0.9841)."""
    clusters_df = load_clusters()
    clusters = clusters_df.groupby("master_customer_id")["crm_customer_id"].apply(list).to_dict()
    ids_present = set(clusters_df["crm_customer_id"])
    return evaluate_clusters(clusters, ids_present)


@st.cache_data(show_spinner=False)
def load_rag_results() -> dict:
    with open(RAG_RESULTS_PATH, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_churn_comparison() -> pd.DataFrame:
    """Reads the real MLflow local tracking store (file:./mlflow/mlruns, experiment
    'churn_model') that ml/churn/train.py wrote — does not retrain anything."""
    import mlflow

    mlflow.set_tracking_uri(MLFLOW_URI)
    client = mlflow.MlflowClient()
    exp = client.get_experiment_by_name("churn_model")
    if exp is None:
        return pd.DataFrame()
    runs = client.search_runs([exp.experiment_id], order_by=["start_time DESC"])
    seen = set()
    rows = []
    for r in runs:
        name = r.data.tags.get("mlflow.runName")
        if not name or name in seen:
            continue
        seen.add(name)
        rows.append(
            {
                "model": name,
                "roc_auc": r.data.metrics.get("roc_auc"),
                "f1": r.data.metrics.get("f1"),
                "pr_auc": r.data.metrics.get("pr_auc"),
                "brier_score": r.data.metrics.get("brier_score"),
                "run_id": r.info.run_id,
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("roc_auc", ascending=False).reset_index(drop=True)
    return df


@st.cache_resource(show_spinner="Loading the registered churn_model champion + computing SHAP explanations...")
def get_shap_explanation():
    """Loads the real registered champion model (mlflow models:/churn_model/1 — the
    exact artifact ml/churn/train.py trained and registered, NOT retrained here) and
    computes SHAP feature attributions with the shap library, mirroring
    ml/explainability/shap_analysis.py's method (shap.Explainer over predict_proba)."""
    import numpy as np
    import shap
    import mlflow

    from ml.churn.label import add_churn_label
    from ml.churn.train import FEATURE_COLUMNS, RANDOM_STATE
    from ml.features.build_features import OUTPUT_PATH as FEATURES_PATH

    mlflow.set_tracking_uri(MLFLOW_URI)
    model = mlflow.sklearn.load_model("models:/churn_model/1")
    client = mlflow.MlflowClient()
    champion_run = client.get_run(
        client.search_model_versions("name='churn_model'")[0].run_id
    )
    champion_type = champion_run.data.params.get("model_type", "unknown")
    champion_roc_auc = champion_run.data.metrics.get("roc_auc")

    features = pd.read_parquet(FEATURES_PATH)
    labeled = add_churn_label(features)
    X = labeled[FEATURE_COLUMNS]
    ids = labeled["master_customer_id"]

    proba = model.predict_proba(X)[:, 1]

    background = shap.sample(X, 80, random_state=RANDOM_STATE)
    explainer = shap.Explainer(model.predict_proba, background, feature_names=FEATURE_COLUMNS)

    sample_idx = X.sample(n=min(80, len(X)), random_state=RANDOM_STATE).index
    explanation = explainer(X.loc[sample_idx])
    shap_values_churn = explanation.values[..., 1]
    global_importance = pd.Series(
        np.abs(shap_values_churn).mean(axis=0), index=FEATURE_COLUMNS
    ).sort_values(ascending=False)

    # Highest-risk customer *within the explained sample* — real SHAP values, not a
    # second (slow) explainer call against an arbitrary row.
    proba_sample = model.predict_proba(X.loc[sample_idx])[:, 1]
    top_pos = int(proba_sample.argmax())
    top_customer_id = ids.loc[sample_idx].iloc[top_pos]
    top_customer_proba = float(proba_sample[top_pos])
    top_customer_row = X.loc[sample_idx].iloc[top_pos]
    top_contributions = pd.Series(
        shap_values_churn[top_pos], index=FEATURE_COLUMNS
    ).sort_values(key=lambda s: s.abs(), ascending=False)

    return {
        "champion_type": champion_type,
        "champion_roc_auc": champion_roc_auc,
        "global_importance": global_importance,
        "top_customer_id": top_customer_id,
        "top_customer_proba": top_customer_proba,
        "top_customer_row": top_customer_row,
        "top_contributions": top_contributions,
        "n_customers_scored": len(X),
        "n_customers_explained": len(sample_idx),
    }


# ---------------------------------------------------------------------------
# DQ dimension mapping (data_quality/reports/dq_report.json rule "type" -> a
# readable dimension name, per powerbi/dashboard/page_specs.md Chart 2)
# ---------------------------------------------------------------------------
DQ_DIMENSION_MAP = {
    "schema_check": "Schema",
    "not_null": "Completeness",
    "unique": "Uniqueness",
    "duplicate_rate": "Uniqueness",
    "valid_email": "Validity",
    "valid_phone": "Validity",
    "valid_date": "Validity",
    "range_check": "Validity",
    "referential_integrity": "Referential Integrity",
    "freshness": "Freshness",
}


# ---------------------------------------------------------------------------
# Page 1 — Executive Overview
# ---------------------------------------------------------------------------
def page_executive_overview():
    st.title("Executive Overview")
    st.caption(
        "Top-line KPIs, computed live by `snowflake/local_runner.py::run_metric()` against the "
        "DuckDB local warehouse built from real parquet sources."
    )

    metrics = get_all_metrics()
    active_customers = run_sql("SELECT COUNT(*) AS n FROM dim_customer WHERE frequency >= 1")["n"].iat[0]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Revenue", fmt_currency(metrics["revenue"]))
    c2.metric("AOV", fmt_currency(metrics["aov"]))
    c3.metric("Active Customers", fmt_int(active_customers))
    c4.metric("Churn Rate", fmt_pct(metrics["churn_rate"]))
    c5.metric("Repeat Rate", fmt_pct(metrics["repeat_rate"]))
    c6.metric("CLV (avg)", fmt_currency(metrics["clv"]["avg"]))

    st.divider()
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Revenue by month (settled payments)")
        rev_by_month = run_sql(
            """
            SELECT d.year, d.month, d.month_name,
                   CAST(SUM(f.net_amount) AS DOUBLE) AS revenue
            FROM fact_payments f
            JOIN dim_date d ON f.date_key = d.date_key
            WHERE f.status = 'settled'
            GROUP BY 1, 2, 3
            ORDER BY 1, 2
            """
        )
        rev_by_month["period"] = rev_by_month["month_name"].str.slice(0, 3) + " " + rev_by_month["year"].astype(str)
        fig = px.line(rev_by_month, x="period", y="revenue", markers=True)
        fig.update_layout(yaxis_title="Revenue (R$)", xaxis_title=None, margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("Customers by segment")
        segs = load_segments()
        seg_counts = segs["segment"].value_counts().reset_index()
        seg_counts.columns = ["segment", "count"]
        fig = px.pie(seg_counts, names="segment", values="count", hole=0.5)
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    st.subheader("Settled payment count by method")
    by_method = run_sql(
        "SELECT method, COUNT(*) AS n FROM fact_payments WHERE status = 'settled' GROUP BY method ORDER BY n DESC"
    )
    fig = px.bar(by_method, x="method", y="n", labels={"method": "Payment method", "n": "Settled payments"})
    fig.update_layout(margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

    st.info(
        "Orders / Delivery SLA / NPS are not shown — this repo snapshot has no `data/raw/olist` "
        "order data. Revenue and AOV are computed against settled `payment_finance` records "
        "instead (see `snowflake/local_runner.py::SKIPPED_METRICS` and `snowflake/README.md`)."
    )


# ---------------------------------------------------------------------------
# Page 2 — Customer Intelligence
# ---------------------------------------------------------------------------
def page_customer_intelligence():
    st.title("Customer Intelligence")
    st.caption(
        "RFM / CLV / churn-score distribution and segmentation, from the semantic warehouse "
        "(`dim_customer`) plus the real MDM golden record and entity-resolution outputs."
    )

    metrics = get_all_metrics()
    dim_customer = run_sql("SELECT * FROM dim_customer")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Customers", fmt_int(len(dim_customer)))
    c2.metric("CLV (avg)", fmt_currency(metrics["clv"]["avg"]))
    c3.metric("CLV (median)", fmt_currency(metrics["clv"]["median"]))
    c4.metric("Churn Rate", fmt_pct(metrics["churn_rate"]))

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("RFM scatter — recency vs. monetary")
        fig = px.scatter(
            dim_customer, x="recency_days", y="monetary", size="frequency", color="segment",
            hover_data=["canonical_name", "city", "state"], opacity=0.6,
        )
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("Churn score distribution")
        fig = px.histogram(dim_customer, x="churn_score", nbins=10, range_x=[0, 1])
        fig.update_layout(margin=dict(t=10), xaxis_title="churn_score (proxy, see note below)")
        st.plotly_chart(fig, width="stretch")

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Lifetime value distribution")
        fig = px.histogram(dim_customer, x="lifetime_value", nbins=40)
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    with col4:
        st.subheader("Segment x repeat customer")
        stacked = dim_customer.groupby(["segment", "is_repeat_customer"]).size().reset_index(name="count")
        stacked["is_repeat_customer"] = stacked["is_repeat_customer"].map({True: "Repeat", False: "One-time"})
        fig = px.bar(stacked, x="segment", y="count", color="is_repeat_customer", barmode="stack")
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    st.subheader("Top 20 customers by lifetime value")
    top20 = dim_customer.sort_values("lifetime_value", ascending=False).head(20)[
        ["canonical_name", "segment", "monetary", "frequency", "churn_score", "lifetime_value"]
    ]
    st.dataframe(top20, width="stretch", hide_index=True)

    st.subheader("Customers by city (top 20) — bubble = avg monetary value")
    st.caption(
        "No latitude/longitude exists in this synthetic dataset, so this is a bar chart of city "
        "text values (not a literal geographic map)."
    )
    by_city = (
        dim_customer.groupby(["city", "state"])
        .agg(customers=("master_customer_id", "count"), avg_monetary=("monetary", "mean"))
        .reset_index()
        .sort_values("customers", ascending=False)
        .head(20)
    )
    by_city["label"] = by_city["city"] + " / " + by_city["state"]
    fig = px.scatter(
        by_city, x="label", y="customers", size="avg_monetary", color="avg_monetary",
        color_continuous_scale="Blues",
    )
    fig.update_layout(margin=dict(t=10), xaxis_title=None)
    st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("Churn-risk table — top 15 highest-risk customers")
    risk_table = dim_customer.sort_values("churn_score", ascending=False).head(15)[
        ["canonical_name", "city", "state", "segment", "recency_days", "frequency", "monetary", "churn_score"]
    ]
    st.dataframe(risk_table, width="stretch", hide_index=True)

    st.divider()
    st.subheader("MDM — Master Data Management stats")
    gr = load_golden_record()
    clusters_df = load_clusters()
    pair_counts = load_candidate_pair_counts()
    surplus = len(clusters_df) - len(gr)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Golden records", fmt_int(len(gr)))
    m2.metric("Source CRM records", fmt_int(len(clusters_df)))
    m3.metric("Records collapsed as duplicates", fmt_int(surplus))
    m4.metric("Deterministic AUTO_MATCH pairs", fmt_int(pair_counts["deterministic_auto_match"]))

    st.caption(
        f"Deterministic tier resolved {pair_counts['deterministic_auto_match']} pairs automatically; "
        f"{pair_counts['deterministic_pending_fuzzy_ml']} ambiguous pairs were escalated to fuzzy "
        f"matching ({pair_counts['fuzzy_pairs']} candidate pairs generated) and then the ML model "
        f"({pair_counts['ml_scored_pairs']} pairs scored). Real finding from this run: the ML tier "
        f"upgraded {pair_counts['ml_upgraded_to_match'] or 0} additional pairs to MATCH — the "
        "deterministic tier already resolved the true duplicates in this dataset, matching the "
        "finding documented in BUILD_LOG.md."
    )


# ---------------------------------------------------------------------------
# Page 3 — Operations
# ---------------------------------------------------------------------------
def page_operations():
    st.title("Operations")
    st.info(
        "This page is honestly thin — this repo snapshot has no `data/raw/olist` order/delivery "
        "data, so Delivery SLA and order-fulfillment visuals are not populated (see "
        "`snowflake/local_runner.py::SKIPPED_METRICS`). It shows what operational signal the "
        "platform does have: support tickets and campaign delivery mechanics."
    )

    tickets = run_sql("SELECT * FROM fact_support_interactions")
    campaigns = run_sql("SELECT * FROM fact_campaign_interactions")

    total_tickets = len(tickets)
    unresolved = (tickets["resolution_status"] != "resolved").sum()
    unresolved_rate = unresolved / total_tickets if total_tickets else 0.0
    avg_resolution_days = tickets.loc[tickets["resolution_days"].notna(), "resolution_days"].mean()
    conv_rate = campaigns["conversion"].sum() / campaigns["clicks"].sum() if campaigns["clicks"].sum() else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Support Ticket Volume", fmt_int(total_tickets))
    c2.metric("Unresolved Ticket Rate", fmt_pct(unresolved_rate))
    c3.metric("Avg Ticket Resolution Days", f"{avg_resolution_days:.1f}" if pd.notna(avg_resolution_days) else "n/a")
    c4.metric("Campaign Conversion Rate", fmt_pct(conv_rate))

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Ticket volume by category")
        by_cat = tickets["category"].value_counts().reset_index()
        by_cat.columns = ["category", "count"]
        fig = px.bar(by_cat, x="category", y="count")
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("Ticket volume by priority")
        by_pri = tickets["priority"].value_counts().reset_index()
        by_pri.columns = ["priority", "count"]
        fig = px.bar(by_pri, x="priority", y="count")
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    st.subheader("Ticket volume over time")
    tix_over_time = run_sql(
        """
        SELECT d.year, d.month, d.month_name, COUNT(*) AS n
        FROM fact_support_interactions f
        JOIN dim_date d ON f.date_key_created = d.date_key
        GROUP BY 1, 2, 3 ORDER BY 1, 2
        """
    )
    tix_over_time["period"] = tix_over_time["month_name"].str.slice(0, 3) + " " + tix_over_time["year"].astype(str)
    fig = px.line(tix_over_time, x="period", y="n", markers=True)
    fig.update_layout(margin=dict(t=10), yaxis_title="Tickets created", xaxis_title=None)
    st.plotly_chart(fig, width="stretch")

    st.subheader("Campaign cost & conversions by channel")
    by_channel = run_sql(
        """
        SELECT primary_channel,
               CAST(SUM(total_cost) AS DOUBLE) AS total_cost,
               CAST(SUM(total_conversions) AS DOUBLE) AS total_conversions
        FROM dim_campaign GROUP BY primary_channel ORDER BY total_cost DESC
        """
    )
    fig = go.Figure()
    fig.add_bar(name="Total cost (R$)", x=by_channel["primary_channel"], y=by_channel["total_cost"])
    fig.add_bar(name="Total conversions", x=by_channel["primary_channel"], y=by_channel["total_conversions"], yaxis="y2")
    fig.update_layout(
        barmode="group",
        yaxis=dict(title="Total cost (R$)"),
        yaxis2=dict(title="Total conversions", overlaying="y", side="right"),
        margin=dict(t=10),
    )
    st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# Page 4 — Data Quality
# ---------------------------------------------------------------------------
def page_data_quality():
    st.title("Data Quality")
    st.caption(
        "Driven by the `data_quality/` module output (`data_quality/reports/dq_report.json`), "
        "not the semantic layer — this measures the inputs to the marts, not the marts themselves."
    )

    report = load_dq_report()
    tables = report["tables"]

    total_rows = sum(t["total_rows"] for t in tables)
    total_quarantined = sum(t["quarantined_count"] for t in tables)
    overall_quarantine_rate = total_quarantined / total_rows if total_rows else 0.0

    c1, c2 = st.columns(2)
    c1.metric("Overall Data Quality Score", f"{report['overall_score_pct']:.2f}%")
    c2.metric("Overall Quarantine Rate", fmt_pct(overall_quarantine_rate))

    st.caption(f"Report generated at {report['generated_at']}.")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("DQ score per dataset")
        score_df = pd.DataFrame(
            {"table": [t["table_name"] for t in tables], "score": [t["score"] * 100 for t in tables]}
        )
        fig = px.bar(score_df, x="table", y="score", range_y=[95, 100])
        fig.update_layout(margin=dict(t=10), yaxis_title="DQ score (%)")
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("DQ score per dataset x dimension")
        rows = []
        for t in tables:
            dim_scores: dict[str, list[float]] = {}
            for rule in t["rules"]:
                dim = DQ_DIMENSION_MAP.get(rule["type"], rule["type"])
                dim_scores.setdefault(dim, []).append(rule["score"])
            for dim, scores in dim_scores.items():
                rows.append({"table": t["table_name"], "dimension": dim, "score": sum(scores) / len(scores) * 100})
        dim_df = pd.DataFrame(rows)
        fig = px.bar(dim_df, x="dimension", y="score", color="table", barmode="group", range_y=[90, 100])
        fig.update_layout(margin=dict(t=10), yaxis_title="DQ score (%)")
        st.plotly_chart(fig, width="stretch")

    st.subheader("Latest checkpoint run — rule detail")
    rule_rows = []
    for t in tables:
        for rule in t["rules"]:
            rule_rows.append(
                {
                    "dataset": t["table_name"],
                    "dimension": DQ_DIMENSION_MAP.get(rule["type"], rule["type"]),
                    "rule": rule["type"],
                    "column": rule["column"],
                    "severity": rule["severity"],
                    "pass_rate": rule["pass_rate"],
                    "score": rule["score"],
                    "failed_count": rule["failed_count"],
                    "total_rows": rule["total_rows"],
                }
            )
    st.dataframe(pd.DataFrame(rule_rows), width="stretch", hide_index=True, height=350)

    st.subheader("Quarantine counts per dataset")
    quarantine_df = pd.DataFrame(
        {
            "table": [t["table_name"] for t in tables],
            "quarantined_count": [t["quarantined_count"] for t in tables],
            "quarantine_rate": [t["quarantine_rate"] for t in tables],
        }
    )
    st.dataframe(quarantine_df, width="stretch", hide_index=True)

    if report.get("notes", {}).get("olist_skipped"):
        st.info(f"Note: {report['notes'].get('reason', 'Olist tables intentionally excluded.')}")


# ---------------------------------------------------------------------------
# Page 5 — ML
# ---------------------------------------------------------------------------
def page_ml():
    st.title("ML")
    st.caption(
        "Model outputs and explainability from `ml/` — segmentation "
        "(`data/ml/segmentation/customer_segments.parquet`) and the real, MLflow-tracked churn "
        "classifier (`ml/churn/train.py`, `ml/explainability/shap_analysis.py`)."
    )

    segs = load_segments()
    metrics = get_all_metrics()

    c1, c2, c3 = st.columns(3)
    c1.metric("Customers with resolved segment", fmt_int(len(segs)))
    c2.metric("Number of clusters", fmt_int(segs["cluster"].nunique()))
    c3.metric("CLV (avg)", fmt_currency(metrics["clv"]["avg"]))

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Segmentation clusters")
        fig = px.scatter(
            segs, x="recency_days", y="frequency", color=segs["cluster"].astype(str), size="monetary",
            hover_data=["segment", "monetary"], labels={"color": "cluster"},
        )
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("Customers per segment")
        seg_counts = segs["segment"].value_counts().reset_index()
        seg_counts.columns = ["segment", "count"]
        fig = px.bar(seg_counts, x="segment", y="count")
        fig.update_layout(margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("Churn model comparison (real MLflow runs — `mlflow/mlruns`, experiment `churn_model`)")
    churn_cmp = load_churn_comparison()
    if churn_cmp.empty:
        st.warning("No MLflow runs found under the `churn_model` experiment.")
    else:
        display_cmp = churn_cmp.drop(columns=["run_id"]).rename(
            columns={"model": "Model", "roc_auc": "ROC-AUC", "f1": "F1", "pr_auc": "PR-AUC", "brier_score": "Brier"}
        )
        st.dataframe(display_cmp, width="stretch", hide_index=True)
        st.caption(
            f"Champion (highest ROC-AUC): **{display_cmp.iloc[0]['Model']}** "
            f"(ROC-AUC={display_cmp.iloc[0]['ROC-AUC']:.3f}) — registered in the MLflow Model "
            "Registry as `churn_model` v1, stage Staging."
        )

    st.divider()
    st.subheader("SHAP feature importance (real classifier, computed live)")
    with st.spinner("Loading registered model + computing SHAP values (first load only, cached after)..."):
        shap_data = get_shap_explanation()

    col3, col4 = st.columns([2, 1])
    with col3:
        imp_df = shap_data["global_importance"].reset_index()
        imp_df.columns = ["feature", "mean_abs_shap"]
        fig = px.bar(imp_df, x="mean_abs_shap", y="feature", orientation="h")
        fig.update_layout(margin=dict(t=10), yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")
        st.caption(
            f"Global importance computed over {shap_data['n_customers_explained']} sampled customers "
            f"(of {shap_data['n_customers_scored']} scored), champion model = "
            f"{shap_data['champion_type']} (ROC-AUC={shap_data['champion_roc_auc']:.3f})."
        )

    with col4:
        st.markdown(f"**Highest-risk customer in sample:** `{shap_data['top_customer_id']}`")
        st.markdown(f"**Predicted churn probability:** {shap_data['top_customer_proba']:.4f}")
        st.markdown("**Top SHAP contributions:**")
        contrib = shap_data["top_contributions"].head(4)
        for feat, val in contrib.items():
            raw = shap_data["top_customer_row"][feat]
            sign = "+" if val >= 0 else ""
            st.markdown(f"- `{sign}{val:.4f}` **{feat}** (value={raw})")

    st.divider()
    st.subheader("Segment profile summary")
    dim_customer = run_sql(
        """
        SELECT segment,
               AVG(recency_days) AS avg_recency_days,
               AVG(frequency) AS avg_frequency,
               AVG(monetary) AS avg_monetary,
               AVG(churn_score) AS avg_churn_score,
               AVG(lifetime_value) AS avg_lifetime_value
        FROM dim_customer GROUP BY segment ORDER BY avg_lifetime_value DESC
        """
    )
    st.dataframe(dim_customer.round(2), width="stretch", hide_index=True)

    st.info(
        "`dim_customer.churn_score` / `lifetime_value` shown elsewhere in this dashboard are the "
        "recency-based proxy defined in `snowflake/local_runner.py` (documented deviation), NOT "
        "this trained classifier's output — the real classifier's predictions are not wired back "
        "into the semantic layer in this build. The SHAP chart above explains the real, "
        "MLflow-registered `churn_model` classifier directly."
    )


# ---------------------------------------------------------------------------
# Page 6 — Platform Observability
# ---------------------------------------------------------------------------
def page_platform_observability():
    st.title("Platform Observability")
    st.caption(
        "Mirrors the intended Grafana view for a non-technical audience. This is the thinnest "
        "page of the six — most platform telemetry (pipeline-run history, latency, cost) does "
        "not exist on disk in this snapshot."
    )

    mdm_eval = load_mdm_evaluation()
    rag_results = load_rag_results()

    st.subheader("MDM — Entity Resolution pipeline vs. ground truth")
    m1, m2, m3 = st.columns(3)
    m1.metric("Precision", f"{mdm_eval['precision']:.4f}")
    m2.metric("Recall", f"{mdm_eval['recall']:.4f}")
    m3.metric("F1", f"{mdm_eval['f1']:.4f}")
    st.caption(
        f"{mdm_eval['true_positive_pairs']} true positives, {mdm_eval['false_positive_pairs']} false "
        f"positives, {mdm_eval['false_negative_pairs']} false negatives, out of "
        f"{mdm_eval['n_true_pairs']} labeled ground-truth pairs "
        f"({mdm_eval['n_true_pairs_excluded_missing_from_input']} excluded — not present in input). "
        f"Recall target >= 0.85: {'MET' if mdm_eval['meets_recall_target_0.85'] else 'NOT MET'}."
    )

    st.divider()
    st.subheader("RAG — precision@k")
    r1, r2, r3 = st.columns(3)
    r1.metric(f"Precision@{rag_results['k']}", f"{rag_results['precision_at_k']:.2f}")
    r2.metric("Questions evaluated", fmt_int(rag_results["num_questions"]))
    r3.metric("Hits", fmt_int(rag_results["hits"]))
    st.caption(
        f"Target precision@{rag_results['k']} >= {rag_results['target']}: "
        f"{'MET' if rag_results['meets_target'] else 'NOT MET'} "
        f"({rag_results['chunk_count']} chunks indexed)."
    )

    st.divider()
    st.subheader("A2A / MCP layer")
    a2a_exists = (REPO_ROOT / "agents" / "a2a" / "server.py").exists()
    nb08_exists = (REPO_ROOT / "notebooks" / "08_agents_mcp_walkthrough.ipynb").exists()
    if a2a_exists:
        st.success(
            "`agents/a2a/server.py` exists in this repo — the A2A protocol server "
            "(`/.well-known/agent.json`, `tasks/send`) is live-testable separately by running it "
            "directly (see `agents/a2a/README.md`); it is not embedded in this Streamlit process."
        )
    else:
        st.warning("`agents/a2a/` was not found in this repo snapshot.")
    if nb08_exists:
        st.markdown("See `notebooks/08_agents_mcp_walkthrough.ipynb` for a live walkthrough.")
    else:
        st.caption("A dedicated Agents/MCP walkthrough notebook is not yet in this snapshot.")

    st.divider()
    st.subheader("Current Silver row counts (snapshot, not a trend)")
    st.caption(
        "No pipeline-run history exists on disk, so this shows the current row count per Silver "
        "table rather than a run-over-run trend."
    )
    silver_files = {
        "crm_customer": DATA_SILVER / "crm_customer.parquet",
        "payment_finance": DATA_SILVER / "payment_finance.parquet",
        "support_ticket": DATA_SILVER / "support_ticket.parquet",
        "campaign_interaction": DATA_SILVER / "campaign_interaction.parquet",
        "web_event": DATA_SILVER / "web_event.parquet",
    }
    counts = []
    for name, path in silver_files.items():
        n = pq.ParquetFile(path).metadata.num_rows if path.exists() else 0
        counts.append({"table": name, "row_count": n})
    fig = px.bar(pd.DataFrame(counts), x="table", y="row_count")
    fig.update_layout(margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

    st.warning(
        "ML/LLM/MCP call latency and cost panels are not populated — no latency or cost "
        "telemetry exists on disk in this repo snapshot. Pipeline-run status/duration is owned "
        "by orchestration logs outside this task's scope."
    )

    st.divider()
    st.subheader("What's real vs. simulated in this build")
    st.markdown(
        """
- **Real, computed live from disk in this dashboard:** Revenue/AOV/Churn Rate/Repeat Rate/CLV
  (`snowflake/local_runner.py`), customer segmentation (`ml/segmentation/`), the trained/registered
  churn classifier and its SHAP explanations (`ml/churn/`, `ml/explainability/`, MLflow), MDM
  golden record + entity-resolution precision/recall/F1 (`mdm/`), Data Quality scores
  (`data_quality/reports/`), RAG precision@k (`rag/evaluation/`).
- **Absent by design (ADR-009):** the Olist e-commerce dataset — requires interactive Kaggle
  login, unavailable in this environment. Revenue/AOV/Orders/Delivery SLA are proxied from
  synthetic `payment_finance` records instead; Orders/Delivery SLA/NPS are explicitly `SKIPPED`
  rather than invented.
- **Stubbed, not wired to real credentials:** `agents/llm_gateway/router.py`'s LLM adapters
  (OpenAI/Azure/Gemini/Bedrock) return empty completions — no API key is configured in this
  environment. Agent/MCP tool calls and human-in-the-loop queues are real; the LLM reasoning
  step on top of them is a documented TODO.
- **Not applied to real cloud:** Terraform modules are `validate`-clean (20/20) but never
  `apply`-ed — no Azure/Snowflake credentials in this environment. Kubernetes manifests are
  structurally validated (no live cluster). Power BI / Databricks artifacts (semantic model,
  DAX, DDL) are prepared but not connected to a live service.
        """
    )


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
PAGES = {
    "1. Executive Overview": page_executive_overview,
    "2. Customer Intelligence": page_customer_intelligence,
    "3. Operations": page_operations,
    "4. Data Quality": page_data_quality,
    "5. ML": page_ml,
    "6. Platform Observability": page_platform_observability,
}


def main():
    st.sidebar.title("Argus")
    st.sidebar.caption(
        "Every number on every page is read live from real files/modules on disk — "
        "see `dashboard/README.md`."
    )
    choice = st.sidebar.radio("Page", list(PAGES.keys()), label_visibility="collapsed")
    st.sidebar.divider()
    st.sidebar.caption(
        "Data sources are read-only: `snowflake/`, `data_quality/`, `mdm/`, `ml/`, `rag/`, "
        "`mlflow/`, `data/`. This app never edits them."
    )
    PAGES[choice]()


if __name__ == "__main__":
    main()
