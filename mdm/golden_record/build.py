"""Golden Record construction: clusters -> dim_customer + survivorship_log.

Consumes the entity-resolution clusters produced by
`mdm/entity_resolution/run.py` (a mapping of `master_customer_id ->
[crm_customer_id, ...]`, singletons included) and the source CRM rows, and
produces:

1. A `dim_customer`-shaped golden table (DATA_MODEL.md §2 -- columns
   `master_customer_id, canonical_name, canonical_email, canonical_phone,
   city, state, created_at, updated_at, source_customer_ids,
   source_record_count`).
2. An auditable survivorship log written to
   `mdm/golden_record/survivorship_log/` with one row per
   `{master_customer_id, field, winning_source, losing_sources,
   rule_applied, timestamp}` (DATA_MODEL.md §4), for every field-level
   decision made -- including trivial single-record clusters, so "why does
   the platform think this is the email?" always has an answer.

Field-level rules live in `mdm/survivorship/rules.py`.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from mdm.survivorship.rules import SURVIVORSHIP_RULES

logger = logging.getLogger("mdm.golden_record.build")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT = Path(__file__).resolve().parents[2]
SURVIVORSHIP_LOG_DIR = Path(__file__).resolve().parent / "survivorship_log"


def build_golden_records(
    customers: pd.DataFrame, clusters: dict[str, list[str]]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (golden_df, survivorship_log_df)."""
    idx = customers.set_index("crm_customer_id", drop=False)
    run_ts = datetime.now(timezone.utc).isoformat()

    golden_rows = []
    log_rows = []
    for master_id, member_ids in clusters.items():
        members = [idx.loc[mid] for mid in member_ids if mid in idx.index]
        if not members:
            continue

        decisions = {field: rule(members) for field, rule in SURVIVORSHIP_RULES.items()}

        created_at = min((m.get("created_at") for m in members if pd.notna(m.get("created_at"))), default=pd.NaT)
        updated_at = max((m.get("updated_at") for m in members if pd.notna(m.get("updated_at"))), default=pd.NaT)

        golden_rows.append(
            {
                "master_customer_id": master_id,
                "canonical_name": decisions["canonical_name"].winning_value,
                "canonical_email": decisions["canonical_email"].winning_value,
                "canonical_phone": decisions["canonical_phone"].winning_value,
                "city": decisions["city"].winning_value,
                "state": decisions["state"].winning_value,
                "created_at": created_at,
                "updated_at": updated_at,
                "source_customer_ids": ";".join(sorted(member_ids)),
                "source_record_count": len(members),
            }
        )

        for field, decision in decisions.items():
            log_rows.append(
                {
                    "master_customer_id": master_id,
                    "field": field,
                    "winning_value": decision.winning_value,
                    "winning_source": decision.winning_record_id,
                    "losing_sources": ";".join(decision.losing_record_ids) if decision.losing_record_ids else "",
                    "rule_applied": decision.rule_applied,
                    "rationale": decision.rationale,
                    "cluster_size": len(members),
                    "timestamp": run_ts,
                }
            )

    golden_df = pd.DataFrame(golden_rows)
    log_df = pd.DataFrame(log_rows)
    return golden_df, log_df


def write_survivorship_log(log_df: pd.DataFrame) -> Path:
    SURVIVORSHIP_LOG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SURVIVORSHIP_LOG_DIR / "survivorship_log.csv"
    log_df.to_csv(out_path, index=False)
    logger.info("Wrote %d survivorship decisions -> %s", len(log_df), out_path)
    return out_path
