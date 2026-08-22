"""Silver build for `support_ticket` (from Bronze `support_tickets`)."""
from __future__ import annotations

import pandas as pd

from lakehouse.silver.common import drop_exact_duplicates, enforce_schema

SCHEMA = {
    "ticket_id": "string",
    "customer_id": "string",
    "category": "string",
    "priority": "string",
    "sentiment": "string",
    "created_at": "datetime64[ns]",
    "resolved_at": "datetime64[ns]",
    "resolution_status": "string",
}


def build(bronze_df: pd.DataFrame) -> pd.DataFrame:
    df = drop_exact_duplicates(bronze_df, subset=["ticket_id"])
    for col in ("category", "priority", "sentiment", "resolution_status"):
        df[col] = df[col].astype("string").str.strip().str.lower()
    df = enforce_schema(df, SCHEMA)
    return df
