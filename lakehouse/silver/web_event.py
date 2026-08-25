"""Silver build for `web_event` (from Bronze `web_events`)."""
from __future__ import annotations

import pandas as pd

from lakehouse.silver.common import drop_exact_duplicates, enforce_schema

SCHEMA = {
    "session_id": "string",
    "customer_id": "string",
    "event_type": "string",
    "product_id": "string",
    "timestamp": "datetime64[ns]",
    "device": "string",
    "browser": "string",
    "source": "string",
    "campaign": "string",
}


def build(bronze_df: pd.DataFrame) -> pd.DataFrame:
    # Full-row exact duplicates only — session_id + event_type + timestamp
    # legitimately repeats across e.g. multiple page_views in one session.
    df = drop_exact_duplicates(bronze_df)
    for col in ("event_type", "device", "browser", "source"):
        df[col] = df[col].astype("string").str.strip().str.lower()
    df["campaign"] = df["campaign"].astype("string").str.strip()
    df = enforce_schema(df, SCHEMA)
    return df
