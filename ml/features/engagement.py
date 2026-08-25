"""Web engagement features from `web_event.parquet`."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml.features.entity_map import map_to_master_id

WEB_EVENT_PATH = Path("data/lakehouse/silver/web_event.parquet")


def build_engagement_features(
    id_map: pd.DataFrame,
    reference_date: pd.Timestamp,
    web_event_path: Path = WEB_EVENT_PATH,
) -> pd.DataFrame:
    """Compute event volume, event diversity, and recency of activity per `master_customer_id`.

    Args:
        id_map: `crm_customer_id -> master_customer_id` lookup.
        reference_date: shared "as of" timestamp, see `ml/features/rfm.py` for the rationale.
        web_event_path: path to the Silver web event table.

    Returns:
        DataFrame with columns `["event_count", "distinct_event_types", "days_since_last_activity"]`.
        Customers with no recorded web events (present in the golden record but never browsed —
        e.g. offline/phone-only customers) get `event_count=0`, `distinct_event_types=0`, and
        `days_since_last_activity` equal to the widest observed gap + 1, matching the RFM
        no-activity convention in `ml/features/rfm.py`.
    """
    events = pd.read_parquet(web_event_path)
    events = map_to_master_id(events, "customer_id", id_map)

    grouped = events.groupby("master_customer_id").agg(
        event_count=("session_id", "count"),
        distinct_event_types=("event_type", "nunique"),
        days_since_last_activity=("timestamp", lambda s: (reference_date - s.max()).days),
    )

    all_customers = id_map["master_customer_id"].drop_duplicates()
    worst_gap = int(grouped["days_since_last_activity"].max()) + 1 if not grouped.empty else 1
    result = grouped.reindex(all_customers).fillna(
        {"event_count": 0, "distinct_event_types": 0, "days_since_last_activity": worst_gap}
    )
    result["event_count"] = result["event_count"].astype(int)
    result["distinct_event_types"] = result["distinct_event_types"].astype(int)
    result["days_since_last_activity"] = result["days_since_last_activity"].astype(int)
    result.index.name = "master_customer_id"
    return result.reset_index()
