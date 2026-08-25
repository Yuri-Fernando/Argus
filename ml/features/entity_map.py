"""CRM customer id -> MDM golden-record id mapping.

`mdm/golden_record/build.py` writes `data/mdm/golden_record.parquet` with one row per resolved
entity and a `source_customer_ids` column holding the raw `crm_customer_id`s that were merged
into it, semicolon-delimited (e.g. `"CRM00000017;CRM00010248"`). Every other Silver table
(`support_ticket`, `web_event`, `payment_finance`, `campaign_interaction`) still keys its
`customer_id` column on the raw, pre-resolution `crm_customer_id`. This module builds the
lookup that lets feature builders roll all of those tables up to `master_customer_id`.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

GOLDEN_RECORD_PATH = Path("data/mdm/golden_record.parquet")


def load_customer_id_map(golden_record_path: Path = GOLDEN_RECORD_PATH) -> pd.DataFrame:
    """Return a flat `crm_customer_id -> master_customer_id` lookup table.

    Args:
        golden_record_path: path to the MDM golden record produced by
            `mdm/golden_record/build.py`.

    Returns:
        DataFrame with columns `["crm_customer_id", "master_customer_id"]`, one row per raw CRM
        id (a golden record whose `source_customer_ids` merged N raw ids expands to N rows here).
    """
    golden = pd.read_parquet(golden_record_path)
    exploded = golden.assign(
        crm_customer_id=golden["source_customer_ids"].str.split(";")
    ).explode("crm_customer_id")
    return exploded[["crm_customer_id", "master_customer_id"]].reset_index(drop=True)


def map_to_master_id(df: pd.DataFrame, customer_id_col: str, id_map: pd.DataFrame) -> pd.DataFrame:
    """Attach `master_customer_id` to `df` by joining on its raw CRM customer id column.

    Rows whose `customer_id` is not found in the golden record (should not happen — the golden
    record is built from the same CRM table every Silver table's `customer_id` references — but
    checked defensively) are dropped, since they cannot be attributed to a resolved customer.

    Args:
        df: any Silver table with a raw `crm_customer_id`-valued column.
        customer_id_col: name of that column in `df`.
        id_map: output of `load_customer_id_map`.

    Returns:
        `df` with an added `master_customer_id` column, unresolvable rows dropped.
    """
    merged = df.merge(
        id_map, left_on=customer_id_col, right_on="crm_customer_id", how="inner"
    )
    return merged.drop(columns=["crm_customer_id"]) if customer_id_col != "crm_customer_id" else merged
