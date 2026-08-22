"""Bronze ingestion for synthetic Marketing sources: campaigns + interactions."""
from __future__ import annotations

import pandas as pd

from lakehouse.bronze.common import RAW_SYNTHETIC, add_ingestion_columns, read_csv, write_parquet

CAMPAIGNS_PATH = RAW_SYNTHETIC / "marketing" / "campaigns.csv"
INTERACTIONS_PATH = RAW_SYNTHETIC / "marketing" / "campaign_interactions.csv"


def ingest_campaigns() -> pd.DataFrame:
    df = read_csv(
        CAMPAIGNS_PATH,
        dtype={"campaign_id": "string", "name": "string", "channel": "string"},
    )
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce")
    df = add_ingestion_columns(df, source_name="marketing")
    write_parquet(df, table_name="campaigns", source_dir="marketing")
    return df


def ingest_interactions() -> pd.DataFrame:
    df = read_csv(
        INTERACTIONS_PATH,
        dtype={
            "interaction_id": "string",
            "customer_id": "string",
            "campaign_id": "string",
            "channel": "string",
        },
    )
    for col in ("impressions", "clicks", "conversion"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = add_ingestion_columns(df, source_name="marketing")
    write_parquet(df, table_name="campaign_interactions", source_dir="marketing")
    return df


def ingest() -> dict[str, pd.DataFrame]:
    return {
        "campaigns": ingest_campaigns(),
        "campaign_interactions": ingest_interactions(),
    }


if __name__ == "__main__":
    ingest()
