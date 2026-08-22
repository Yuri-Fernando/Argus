"""Bronze ingestion for the synthetic CRM source (`crm_customers.csv`)."""
from __future__ import annotations

import pandas as pd

from lakehouse.bronze.common import RAW_SYNTHETIC, add_ingestion_columns, read_csv, write_parquet

SOURCE_PATH = RAW_SYNTHETIC / "crm" / "crm_customers.csv"

DTYPES = {
    "crm_customer_id": "string",
    "name": "string",
    "email": "string",
    "phone": "string",
    "document_hash": "string",
    "address": "string",
    "city": "string",
    "state": "string",
}
DATE_COLS = ["birth_date"]
TS_COLS = ["created_at", "updated_at"]


def ingest() -> pd.DataFrame:
    df = read_csv(SOURCE_PATH, dtype=DTYPES)
    for col in DATE_COLS + TS_COLS:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df = add_ingestion_columns(df, source_name="crm")
    write_parquet(df, table_name="crm_customers", source_dir="crm")
    return df


if __name__ == "__main__":
    ingest()
