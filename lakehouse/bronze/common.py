"""Shared helpers for the Bronze layer.

Bronze rule (see lakehouse/README.md): near-verbatim copy of raw data, minimal
transform only (dtype casting, `_ingested_at` timestamping, format conversion
to Parquet). No filtering, no deduplication, no business logic here — that is
Silver's job.

Engine note: this module uses pandas + pyarrow, which always works on a
laptop with no cluster. The exact same logical steps (read -> cast ->
add _ingested_at -> write partitioned Parquet/Delta) map 1:1 onto a PySpark
`DataFrameReader`/`DataFrameWriter` pipeline for the Databricks/`PROFILE=cloud`
path described in ADR-010; swapping the engine does not change this module's
contract, so a `spark.py` variant could be dropped in later without touching
Silver or Data Quality.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger("lakehouse.bronze")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT = Path(__file__).resolve().parents[2]
RAW_SYNTHETIC = ROOT / "data" / "synthetic"
RAW_OLIST = ROOT / "data" / "raw" / "olist"
BRONZE_ROOT = ROOT / "data" / "lakehouse" / "bronze"


def ingested_at() -> pd.Timestamp:
    """Single ingestion timestamp shared by all rows written in one run."""
    return pd.Timestamp(datetime.now(timezone.utc)).tz_localize(None)


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Expected source CSV not found: {path}")
    logger.info("Reading %s", path)
    return pd.read_csv(path, **kwargs)


def add_ingestion_columns(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    df = df.copy()
    df["_ingested_at"] = ingested_at()
    df["_source_system"] = source_name
    return df


def write_parquet(df: pd.DataFrame, table_name: str, source_dir: str) -> Path:
    out_dir = BRONZE_ROOT / source_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{table_name}.parquet"
    df.to_parquet(out_path, engine="pyarrow", index=False)
    logger.info("Wrote %s rows -> %s", len(df), out_path)
    return out_path


def source_missing_warning(source_name: str, path: Path) -> None:
    logger.warning(
        "Bronze[%s]: source path %s not found — skipping this source. "
        "Downstream Silver/DQ steps must degrade gracefully (see DATA_MODEL.md §1.1).",
        source_name,
        path,
    )
