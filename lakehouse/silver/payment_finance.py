"""Silver build for `payment_finance` (from Bronze `customer_payments`)."""
from __future__ import annotations

import pandas as pd

from lakehouse.silver.common import drop_exact_duplicates, enforce_schema

SCHEMA = {
    "payment_id": "string",
    "customer_id": "string",
    "gross_amount": "float64",
    "fee_amount": "float64",
    "net_amount": "float64",
    "method": "string",
    "settled_at": "datetime64[ns]",
    "status": "string",
}


def build(bronze_df: pd.DataFrame) -> pd.DataFrame:
    df = drop_exact_duplicates(bronze_df, subset=["payment_id"])
    for col in ("method", "status"):
        df[col] = df[col].astype("string").str.strip().str.lower()
    df = enforce_schema(df, SCHEMA)
    return df
