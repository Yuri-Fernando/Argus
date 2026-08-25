"""Silver build for `crm_customer` (from Bronze `crm_customers`)."""
from __future__ import annotations

import pandas as pd

from lakehouse.silver.common import (
    drop_exact_duplicates,
    enforce_schema,
    normalize_city,
    normalize_email,
    normalize_name,
    normalize_phone,
    normalize_state,
)

SCHEMA = {
    "crm_customer_id": "string",
    "name": "string",
    "email": "string",
    "phone": "string",
    "document_hash": "string",
    "birth_date": "datetime64[ns]",
    "address": "string",
    "city": "string",
    "state": "string",
    "created_at": "datetime64[ns]",
    "updated_at": "datetime64[ns]",
}


def build(bronze_df: pd.DataFrame) -> pd.DataFrame:
    df = drop_exact_duplicates(bronze_df, subset=["crm_customer_id"])
    df["name"] = normalize_name(df["name"])
    df["email"] = normalize_email(df["email"])
    df["phone"] = normalize_phone(df["phone"])
    df["city"] = normalize_city(df["city"])
    df["state"] = normalize_state(df["state"])
    df["address"] = df["address"].astype("string").str.strip()
    df = enforce_schema(df, SCHEMA)
    return df
