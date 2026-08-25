"""Bronze ingestion for the synthetic Support source (`support_tickets.csv`)."""
from __future__ import annotations

import pandas as pd

from lakehouse.bronze.common import RAW_SYNTHETIC, add_ingestion_columns, read_csv, write_parquet

SOURCE_PATH = RAW_SYNTHETIC / "support" / "support_tickets.csv"

DTYPES = {
    "ticket_id": "string",
    "customer_id": "string",
    "category": "string",
    "priority": "string",
    "sentiment": "string",
    "resolution_status": "string",
}
TS_COLS = ["created_at", "resolved_at"]


def ingest() -> pd.DataFrame:
    df = read_csv(SOURCE_PATH, dtype=DTYPES)
    for col in TS_COLS:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df = add_ingestion_columns(df, source_name="support")
    write_parquet(df, table_name="support_tickets", source_dir="support")
    return df


if __name__ == "__main__":
    ingest()
