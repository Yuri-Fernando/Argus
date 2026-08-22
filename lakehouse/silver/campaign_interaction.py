"""Silver build for `campaign_interaction` (from Bronze `campaign_interactions`)."""
from __future__ import annotations

import pandas as pd

from lakehouse.silver.common import drop_exact_duplicates, enforce_schema

SCHEMA = {
    "interaction_id": "string",
    "customer_id": "string",
    "campaign_id": "string",
    "channel": "string",
    "impressions": "Int64",
    "clicks": "Int64",
    "conversion": "Int64",
    "cost": "float64",
    "timestamp": "datetime64[ns]",
}


def build(bronze_df: pd.DataFrame) -> pd.DataFrame:
    df = drop_exact_duplicates(bronze_df, subset=["interaction_id"])
    df["channel"] = df["channel"].astype("string").str.strip().str.lower()
    df = enforce_schema(df, SCHEMA)
    return df
