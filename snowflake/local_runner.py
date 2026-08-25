"""
snowflake/local_runner.py
==========================
Local-dev stand-in for the real Snowflake warehouse (see snowflake/README.md,
"Local development" section). Builds data/warehouse/local.duckdb from the DDL in
snowflake/ddl/*.sql, loads it from the real synthetic parquet sources already on
disk (lakehouse/silver, mdm, ml), and exposes run_metric() implementing the
canonical metric definitions from docs/semantic-dictionary.md wherever the
underlying data supports them.

No dbt, no Power BI, no real Snowflake account involved — pure DuckDB + pandas.
DuckDB is used here because the DDL in snowflake/ddl/*.sql is portable ANSI SQL
that also runs unmodified on a real Snowflake account.

Usage:
    python snowflake/local_runner.py                 # build + print all metrics
    python snowflake/local_runner.py --metric revenue # build + print one metric

As a library:
    from snowflake.local_runner import build_warehouse, run_metric
    con = build_warehouse()
    run_metric(con, "revenue")
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import duckdb
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DDL_DIR = REPO_ROOT / "snowflake" / "ddl"
DB_PATH = REPO_ROOT / "data" / "warehouse" / "local.duckdb"

SILVER = REPO_ROOT / "data" / "lakehouse" / "silver"
MDM = REPO_ROOT / "data" / "mdm"
ML_FEATURES = REPO_ROOT / "data" / "ml" / "features"
ML_SEGMENTS = REPO_ROOT / "data" / "ml" / "segmentation"


# ---------------------------------------------------------------------------
# Warehouse build
# ---------------------------------------------------------------------------

def _run_ddl(con: duckdb.DuckDBPyConnection) -> None:
    """Execute every CREATE TABLE statement in snowflake/ddl/*.sql, in file order."""
    for sql_file in sorted(DDL_DIR.glob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")
        # strip line comments so DuckDB doesn't choke on any edge case
        sql = re.sub(r"--.*", "", sql)
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                con.execute(stmt)


def _to_date_key(ts: pd.Series) -> pd.Series:
    return pd.to_datetime(ts).dt.strftime("%Y%m%d").astype("Int64")


def _build_bridge() -> pd.DataFrame:
    """crm_customer_id -> master_customer_id, exploded from golden_record.source_customer_ids
    (semicolon-delimited). This mapping is done in Python rather than SQL so the DDL in
    snowflake/ddl/ stays pure portable ANSI SQL (SPLIT/FLATTEN syntax differs between
    Snowflake and DuckDB)."""
    gr = pd.read_parquet(MDM / "golden_record.parquet")
    rows = []
    for master_id, src in zip(gr["master_customer_id"], gr["source_customer_ids"]):
        for crm_id in str(src).split(";"):
            rows.append((crm_id.strip(), master_id))
    return pd.DataFrame(rows, columns=["crm_customer_id", "master_customer_id"])


def _load_dim_date(con: duckdb.DuckDBPyConnection, min_date, max_date) -> None:
    dates = pd.date_range(min_date, max_date, freq="D")
    df = pd.DataFrame({"full_date": dates})
    df["date_key"] = df["full_date"].dt.strftime("%Y%m%d").astype(int)
    df["year"] = df["full_date"].dt.year
    df["quarter"] = df["full_date"].dt.quarter
    df["month"] = df["full_date"].dt.month
    df["month_name"] = df["full_date"].dt.strftime("%B")
    df["day"] = df["full_date"].dt.day
    df["day_of_week"] = df["full_date"].dt.dayofweek
    df["day_name"] = df["full_date"].dt.strftime("%A")
    df["is_weekend"] = df["day_of_week"].isin([5, 6])
    df = df[["date_key", "full_date", "year", "quarter", "month", "month_name",
             "day", "day_of_week", "day_name", "is_weekend"]]
    con.register("dim_date_df", df)
    con.execute("INSERT INTO dim_date SELECT * FROM dim_date_df")
    con.unregister("dim_date_df")


def build_warehouse(rebuild: bool = True) -> duckdb.DuckDBPyConnection:
    """Build (or reopen) the local DuckDB warehouse and return an open connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if rebuild and DB_PATH.exists():
        DB_PATH.unlink()

    con = duckdb.connect(str(DB_PATH))
    _run_ddl(con)

    # --- source reads -------------------------------------------------
    crm = pd.read_parquet(SILVER / "crm_customer.parquet")
    gr = pd.read_parquet(MDM / "golden_record.parquet")
    feats = pd.read_parquet(ML_FEATURES / "customer_features.parquet")
    segs = pd.read_parquet(ML_SEGMENTS / "customer_segments.parquet")
    payments = pd.read_parquet(SILVER / "payment_finance.parquet")
    tickets = pd.read_parquet(SILVER / "support_ticket.parquet")
    campaigns = pd.read_parquet(SILVER / "campaign_interaction.parquet")
    events = pd.read_parquet(SILVER / "web_event.parquet")

    bridge = _build_bridge()

    # --- dim_customer ---------------------------------------------------
    dim_customer = (
        gr.merge(feats, on="master_customer_id", how="left")
          .merge(segs[["master_customer_id", "cluster", "segment"]], on="master_customer_id", how="left")
    )
    dim_customer["is_repeat_customer"] = dim_customer["frequency"].fillna(0) >= 2
    # Proxy churn_score: recency-based heuristic standing in for the missing ml/churn/
    # model output (no ml/churn/ parquet exists in this snapshot). Matches the semantic
    # dictionary's "no purchase in trailing 90+ days" churn intuition, scaled to [0,1].
    dim_customer["churn_score"] = (dim_customer["recency_days"].fillna(365) / 365.0).clip(upper=1.0)
    # Proxy CLV, structurally per docs/semantic-dictionary.md CLV formula:
    # expected future Revenue over a 12-month horizon, weighted by (1 - churn_score),
    # using historical AOV proxy (monetary / frequency) and frequency as purchase rate.
    avg_order_value = (dim_customer["monetary"] / dim_customer["frequency"].replace(0, pd.NA)).fillna(0.0).astype(float)
    annual_frequency = dim_customer["frequency"].fillna(0)
    dim_customer["lifetime_value"] = (
        avg_order_value * annual_frequency * (1 - dim_customer["churn_score"])
    ).round(2)

    dim_customer = dim_customer.rename(columns={
        "created_at": "golden_record_created_at",
        "updated_at": "golden_record_updated_at",
    })
    dim_customer_cols = [
        "master_customer_id", "canonical_name", "canonical_email", "canonical_phone",
        "city", "state", "source_record_count", "golden_record_created_at",
        "golden_record_updated_at", "recency_days", "frequency", "monetary",
        "event_count", "distinct_event_types", "days_since_last_activity",
        "ticket_count", "avg_sentiment_score", "unresolved_count", "cluster",
        "segment", "is_repeat_customer", "churn_score", "lifetime_value",
    ]
    con.register("dim_customer_df", dim_customer[dim_customer_cols])
    con.execute("INSERT INTO dim_customer SELECT * FROM dim_customer_df")
    con.unregister("dim_customer_df")

    # --- dim_geography ----------------------------------------------------
    geo = gr[["city", "state"]].dropna(how="all").drop_duplicates().reset_index(drop=True)
    geo.insert(0, "geography_id", range(1, len(geo) + 1))
    geo["country"] = "Brazil"
    con.register("dim_geography_df", geo)
    con.execute("INSERT INTO dim_geography SELECT * FROM dim_geography_df")
    con.unregister("dim_geography_df")

    # --- dim_campaign -------------------------------------------------------
    camp_agg = campaigns.groupby("campaign_id").agg(
        primary_channel=("channel", lambda s: s.mode().iat[0] if not s.mode().empty else None),
        first_seen_at=("timestamp", "min"),
        last_seen_at=("timestamp", "max"),
        total_impressions=("impressions", "sum"),
        total_clicks=("clicks", "sum"),
        total_conversions=("conversion", "sum"),
        total_cost=("cost", "sum"),
    ).reset_index()
    con.register("dim_campaign_df", camp_agg)
    con.execute("INSERT INTO dim_campaign SELECT * FROM dim_campaign_df")
    con.unregister("dim_campaign_df")

    # --- dim_date: spans the min/max timestamp across every fact source -----
    all_min = min(payments["settled_at"].min(), tickets["created_at"].min(),
                   campaigns["timestamp"].min(), events["timestamp"].min())
    all_max = max(payments["settled_at"].max(), tickets["created_at"].max(),
                   campaigns["timestamp"].max(), events["timestamp"].max())
    _load_dim_date(con, all_min.normalize(), all_max.normalize())

    # --- fact_payments --------------------------------------------------------
    fp = payments.merge(bridge, left_on="customer_id", right_on="crm_customer_id", how="left")
    fp["date_key"] = _to_date_key(fp["settled_at"])
    fp = fp[["payment_id", "master_customer_id", "date_key", "gross_amount",
             "fee_amount", "net_amount", "method", "status", "settled_at"]]
    con.register("fact_payments_df", fp)
    con.execute("INSERT INTO fact_payments SELECT * FROM fact_payments_df")
    con.unregister("fact_payments_df")

    # --- fact_support_interactions --------------------------------------------
    fs = tickets.merge(bridge, left_on="customer_id", right_on="crm_customer_id", how="left")
    fs["date_key_created"] = _to_date_key(fs["created_at"])
    fs["date_key_resolved"] = _to_date_key(fs["resolved_at"])
    fs["resolution_days"] = (fs["resolved_at"] - fs["created_at"]).dt.days
    fs = fs[["ticket_id", "master_customer_id", "date_key_created", "date_key_resolved",
             "category", "priority", "sentiment", "resolution_status", "resolution_days",
             "created_at", "resolved_at"]]
    con.register("fact_support_interactions_df", fs)
    con.execute("INSERT INTO fact_support_interactions SELECT * FROM fact_support_interactions_df")
    con.unregister("fact_support_interactions_df")

    # --- fact_campaign_interactions --------------------------------------------
    fc = campaigns.merge(bridge, left_on="customer_id", right_on="crm_customer_id", how="left")
    fc["date_key"] = _to_date_key(fc["timestamp"])
    fc = fc.rename(columns={"timestamp": "event_timestamp"})
    fc = fc[["interaction_id", "master_customer_id", "campaign_id", "date_key", "channel",
             "impressions", "clicks", "conversion", "cost", "event_timestamp"]]
    con.register("fact_campaign_interactions_df", fc)
    con.execute("INSERT INTO fact_campaign_interactions SELECT * FROM fact_campaign_interactions_df")
    con.unregister("fact_campaign_interactions_df")

    # --- fact_web_events -----------------------------------------------------------
    fw = events.merge(bridge, left_on="customer_id", right_on="crm_customer_id", how="left")
    fw["date_key"] = _to_date_key(fw["timestamp"])
    fw["event_id"] = [f"WE{n:08d}" for n in range(len(fw))]
    fw = fw.rename(columns={"timestamp": "event_timestamp"})
    fw = fw[["session_id", "event_id", "master_customer_id", "date_key", "event_type",
             "product_id", "device", "browser", "source", "campaign", "event_timestamp"]]
    con.register("fact_web_events_df", fw)
    con.execute("INSERT INTO fact_web_events SELECT * FROM fact_web_events_df")
    con.unregister("fact_web_events_df")

    return con


# ---------------------------------------------------------------------------
# Metrics — implements docs/semantic-dictionary.md wherever data allows.
# Metrics requiring data/raw/olist (fact_orders, order_value, delivery dates) are
# NOT implemented here and raise NotImplementedError with an explanation, per
# ADR-005 (the canonical definition may exist before every implementation does).
# ---------------------------------------------------------------------------

SKIPPED_METRICS = {
    "orders": "Requires fact_orders (data/raw/olist), which is CONFIRMED ABSENT from this build.",
    "delivery_sla": "Requires order_delivered_customer_date / order_estimated_delivery_date "
                     "(data/raw/olist), which is CONFIRMED ABSENT from this build.",
    "nps": "Not yet implemented in any of the three semantic layers per "
           "docs/semantic-dictionary.md — defined canonically, tracked as Sprint 8+ backlog.",
    "data_quality_score": "Owned by data_quality/ module (read-only in this task's scope); "
                           "not a warehouse-native metric.",
}


def run_metric(con: duckdb.DuckDBPyConnection, name: str):
    """Compute one metric by canonical name. Returns a float or a dict of floats.
    Raises NotImplementedError (with reason) for metrics not computable from
    available data — see SKIPPED_METRICS."""
    name = name.lower().strip()

    if name in SKIPPED_METRICS:
        raise NotImplementedError(f"'{name}' skipped: {SKIPPED_METRICS[name]}")

    if name == "revenue":
        # Semantic dictionary: SUM(order_value) over completed orders, freight excluded.
        # No fact_orders exists here -> local stand-in: SUM(net_amount) over SETTLED
        # payments (fact_payments), which is this platform's closest completed-and-
        # recognized-revenue proxy. Documented deviation, see snowflake/README.md.
        row = con.execute(
            "SELECT SUM(net_amount) FROM fact_payments WHERE status = 'settled'"
        ).fetchone()
        return float(row[0] or 0.0)

    if name == "aov":
        # Semantic dictionary: SUM(order_value + freight_value) / COUNT(DISTINCT order_id)
        # over completed orders. Local stand-in: freight_value doesn't exist in
        # payment_finance, so AOV = SUM(gross_amount) / COUNT(payment_id) over settled
        # payments (gross_amount already includes fees the customer effectively pays,
        # the closest available "cost to the customer end to end" figure).
        row = con.execute(
            "SELECT SUM(gross_amount), COUNT(DISTINCT payment_id) "
            "FROM fact_payments WHERE status = 'settled'"
        ).fetchone()
        total, cnt = row
        return float(total or 0.0) / cnt if cnt else 0.0

    if name == "churn_rate":
        # Semantic dictionary: COUNT(churned=TRUE in period)/COUNT(active at period start),
        # excluding customers with <2 historical orders. No time-series churn labels exist
        # in this build (no ml/churn/ output) -> snapshot proxy: churned := recency_days > 90
        # (matches the "no purchase in trailing 90 days" label definition), using
        # dim_customer.frequency >= 2 as the "established behavior pattern" denominator filter.
        row = con.execute(
            "SELECT "
            "  SUM(CASE WHEN recency_days > 90 THEN 1 ELSE 0 END) AS churned, "
            "  COUNT(*) AS eligible "
            "FROM dim_customer WHERE frequency >= 2"
        ).fetchone()
        churned, eligible = row
        return float(churned or 0) / eligible if eligible else 0.0

    if name in ("repeat_rate", "retention", "retention_rate"):
        # Semantic dictionary Repeat Rate: COUNT(order_count>=2)/COUNT(order_count>=1),
        # using dim_customer.frequency as the completed-order-count proxy (no cancelled/
        # returned distinction exists in payment_finance to net out further).
        row = con.execute(
            "SELECT "
            "  SUM(CASE WHEN frequency >= 2 THEN 1 ELSE 0 END) AS repeat_customers, "
            "  SUM(CASE WHEN frequency >= 1 THEN 1 ELSE 0 END) AS active_customers "
            "FROM dim_customer"
        ).fetchone()
        repeat_c, active_c = row
        return float(repeat_c or 0) / active_c if active_c else 0.0

    if name == "clv":
        # Surfaces the pre-computed dim_customer.lifetime_value (proxy, see build_warehouse()
        # docstring) — per semantic dictionary, the semantic layer exposes this, it does not
        # re-derive it.
        row = con.execute(
            "SELECT AVG(lifetime_value), MIN(lifetime_value), MAX(lifetime_value), "
            "MEDIAN(lifetime_value) FROM dim_customer WHERE lifetime_value IS NOT NULL"
        ).fetchone()
        avg_v, min_v, max_v, median_v = row
        return {
            "avg": round(float(avg_v or 0), 2),
            "min": round(float(min_v or 0), 2),
            "max": round(float(max_v or 0), 2),
            "median": round(float(median_v or 0), 2),
        }

    raise ValueError(f"Unknown metric: {name!r}")


ALL_METRICS = ["revenue", "aov", "churn_rate", "repeat_rate", "clv"]


def run_all_metrics(con: duckdb.DuckDBPyConnection) -> dict:
    results = {}
    for m in ALL_METRICS:
        try:
            results[m] = run_metric(con, m)
        except NotImplementedError as e:
            results[m] = f"SKIPPED: {e}"
    for m, reason in SKIPPED_METRICS.items():
        results.setdefault(m, f"SKIPPED: {reason}")
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Local DuckDB warehouse runner")
    parser.add_argument("--metric", default=None, help="Run a single metric by name")
    parser.add_argument("--no-rebuild", action="store_true", help="Reuse existing local.duckdb")
    args = parser.parse_args()

    con = build_warehouse(rebuild=not args.no_rebuild)

    if args.metric:
        print(json.dumps({args.metric: run_metric(con, args.metric)}, indent=2, default=str))
    else:
        print(json.dumps(run_all_metrics(con), indent=2, default=str))

    con.close()


if __name__ == "__main__":
    main()
