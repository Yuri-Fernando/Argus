"""Quarantine writer — rows failing a HARD DQ rule land here instead of Silver."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger("data_quality.quarantine")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT = Path(__file__).resolve().parents[2]
QUARANTINE_ROOT = ROOT / "data" / "lakehouse" / "quarantine"


def write_quarantine(df: pd.DataFrame, table_name: str, reasons: pd.Series | None = None) -> Path | None:
    if df.empty:
        logger.info("Quarantine[%s]: no rows to quarantine", table_name)
        return None
    df = df.copy()
    if reasons is not None:
        df["_dq_failure_reasons"] = reasons.values
    QUARANTINE_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = QUARANTINE_ROOT / f"{table_name}.parquet"
    df.to_parquet(out_path, engine="pyarrow", index=False)
    logger.warning("Quarantine[%s]: wrote %d rows -> %s", table_name, len(df), out_path)
    return out_path
