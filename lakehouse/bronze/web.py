"""Bronze ingestion for the synthetic Web Analytics source (`web_events.csv`)."""
from __future__ import annotations

import pandas as pd

from lakehouse.bronze.common import RAW_SYNTHETIC, add_ingestion_columns, read_csv, write_parquet

SOURCE_PATH = RAW_SYNTHETIC / "web" / "web_events.csv"

DTYPES = {
    "session_id": "string",
    "customer_id": "string",
    "event_type": "string",
    "product_id": "string",
    "device": "string",
    "browser": "string",
    "source": "string",
    "campaign": "string",
}


def ingest() -> pd.DataFrame:
    df = read_csv(SOURCE_PATH, dtype=DTYPES)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = add_ingestion_columns(df, source_name="web")
    write_parquet(df, table_name="web_events", source_dir="web")
    return df


if __name__ == "__main__":
    ingest()
