"""Shared helpers for the Silver layer: dedup, casting, standardization.

Silver responsibilities (lakehouse/README.md): structural exact-duplicate
removal, dtype casting, standardization (name/email casing, phone digits-only,
city/state normalization), and schema enforcement. Business-rule data-quality
validation and quarantine live in `data_quality/` — Silver produces a
*candidate* standardized table; `lakehouse/run_pipeline.py` runs the DQ
engine against it and only the rows that pass hard rules land in the final
`data/lakehouse/silver/<table>.parquet` file (failing rows go to
`data/lakehouse/quarantine/<table>.parquet`).
"""
from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

import pandas as pd

logger = logging.getLogger("lakehouse.silver")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT = Path(__file__).resolve().parents[2]
SILVER_ROOT = ROOT / "data" / "lakehouse" / "silver"

# Brazilian UF codes — used to standardize/validate the `state` column.
VALID_UF = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
}


def drop_exact_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
    """Structural exact-duplicate removal (Silver's dedup responsibility).

    This is NOT fuzzy/near-duplicate entity resolution (that's MDM's job on
    `crm_customer` — see DATA_MODEL.md §4); this only removes rows that are
    byte-identical across `subset` (or all columns if None).
    """
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
    removed = before - len(df)
    if removed:
        logger.info("Silver: dropped %d exact-duplicate rows (subset=%s)", removed, subset)
    return df


def normalize_name(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip()
    s = s.str.replace(r"\s+", " ", regex=True)
    return s.str.title()


def normalize_email(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip().str.lower()
    return s.replace({"": pd.NA, "nan": pd.NA})


def normalize_phone(series: pd.Series) -> pd.Series:
    """Digits-only phone format, e.g. '+55 51 8196 0013' -> '555181960013'."""
    s = series.astype("string")
    return s.str.replace(r"\D", "", regex=True).replace({"": pd.NA})


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def normalize_city(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip()
    s = s.str.replace(r"\s+", " ", regex=True)
    return s.str.title()


def normalize_state(series: pd.Series) -> pd.Series:
    s = series.astype("string").str.strip().str.upper()
    return s


def enforce_schema(df: pd.DataFrame, schema: dict[str, str]) -> pd.DataFrame:
    """Keep/order columns per `schema` ({col: pandas dtype}); cast where safe."""
    missing = [c for c in schema if c not in df.columns]
    if missing:
        raise ValueError(f"Silver schema enforcement: missing columns {missing}")
    df = df[list(schema.keys())].copy()
    for col, dtype in schema.items():
        try:
            if dtype == "string":
                df[col] = df[col].astype("string")
            elif dtype.startswith("datetime"):
                df[col] = pd.to_datetime(df[col], errors="coerce")
            else:
                df[col] = df[col].astype(dtype)
        except (TypeError, ValueError) as exc:
            logger.warning("Silver: could not cast column %s to %s (%s) — leaving as-is", col, dtype, exc)
    return df


def write_silver_parquet(df: pd.DataFrame, table_name: str) -> Path:
    SILVER_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = SILVER_ROOT / f"{table_name}.parquet"
    df.to_parquet(out_path, engine="pyarrow", index=False)
    logger.info("Wrote Silver %s: %d rows -> %s", table_name, len(df), out_path)
    return out_path
