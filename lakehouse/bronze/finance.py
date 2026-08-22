"""Bronze ingestion for the synthetic Finance source (`customer_payments.csv`)."""
from __future__ import annotations

import pandas as pd

from lakehouse.bronze.common import RAW_SYNTHETIC, add_ingestion_columns, read_csv, write_parquet

SOURCE_PATH = RAW_SYNTHETIC / "finance" / "customer_payments.csv"

DTYPES = {
    "payment_id": "string",
    "customer_id": "string",
    "method": "string",
    "status": "string",
}


def ingest() -> pd.DataFrame:
    df = read_csv(SOURCE_PATH, dtype=DTYPES)
    for col in ("gross_amount", "fee_amount", "net_amount"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["settled_at"] = pd.to_datetime(df["settled_at"], errors="coerce")
    df = add_ingestion_columns(df, source_name="finance")
    write_parquet(df, table_name="customer_payments", source_dir="finance")
    return df


if __name__ == "__main__":
    ingest()
