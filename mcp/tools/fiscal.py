"""Fiscal/tributário tools for the MCP server (ADR-015).

Reads from `data_quality/reports/fiscal_dq_report.json` (produced by
`data_quality/validators/fiscal_report.py::run_fiscal_dq()`) and the synthetic fiscal
documents/ground-truth CSVs — same shape and caching discipline as `mcp/tools/quality.py`, so
`agents/fiscal/root_cause_agent.py` can call this exactly the way
`agents/quality/data_quality_agent.py` calls `mcp/tools/quality.py`.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from data_quality.validators.fiscal_report import (
    FISCAL_CSV_DTYPE,
    FISCAL_CSV_PATH,
    FISCAL_GROUND_TRUTH_PATH,
    FISCAL_REPORT_PATH,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _load_fiscal_report() -> dict[str, Any]:
    import json

    with open(FISCAL_REPORT_PATH, encoding="utf-8") as f:
        return json.load(f)


def _worst_rule(rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Same technique as `mcp/tools/quality.py::_worst_rule` — the lowest-scoring individual rule,
    not a dimension average, so a caller can classify root cause on real rule-description text."""
    scored = [r for r in rules if r.get("score") is not None]
    if not scored:
        return None
    return min(scored, key=lambda r: r["score"])


@lru_cache(maxsize=1)
def _fiscal_documents_df() -> pd.DataFrame:
    return pd.read_csv(FISCAL_CSV_PATH, dtype=FISCAL_CSV_DTYPE)


@lru_cache(maxsize=1)
def _fiscal_ground_truth_df() -> pd.DataFrame:
    return pd.read_csv(FISCAL_GROUND_TRUTH_PATH)


def get_fiscal_quality() -> dict[str, Any]:
    """Fetch the fiscal_document dataset's current data quality score.

    Returns:
        {
            "dataset": "fiscal_document",
            "dq_score": float | None,
            "as_of": str | None,           # ISO-8601 timestamp of the report this was read from
            "worst_rule": dict | None,     # lowest-scoring individual rule — real description text
        }
    """
    report = _load_fiscal_report()
    table = report.get("tables", [{}])[0] if report.get("tables") else {}
    return {
        "dataset": "fiscal_document",
        "dq_score": table.get("score"),
        "as_of": report.get("generated_at"),
        "worst_rule": _worst_rule(table.get("rules", [])),
    }


def get_fiscal_document(fiscal_document_id: str) -> dict[str, Any]:
    """Fetch one fiscal document plus its ground-truth tax discrepancy, if any.

    Args:
        fiscal_document_id: e.g. "NFE00000042".

    Returns:
        {
            "fiscal_document_id": str,
            "found": bool,
            "crm_customer_id": str | None,
            "ncm_code": str | None,
            "cfop_code": str | None,
            "cst_code": str | None,
            "cst_cfop_valid": bool | None,
            "calculated_tax_total": float | None,
            "correct_tax_total": float | None,   # from the ground-truth file — the reference figure
            "discrepancy_amount": float | None,  # calculated_tax_total - correct_tax_total
            "discrepancy_reason": str | None,    # "none" | "invalid_ncm" | "cst_cfop_mismatch" | "rate_out_of_range"
        }
    """
    docs = _fiscal_documents_df()
    match = docs[docs["fiscal_document_id"] == fiscal_document_id]
    if match.empty:
        return {"fiscal_document_id": fiscal_document_id, "found": False}

    row = match.iloc[0]
    gt = _fiscal_ground_truth_df()
    gt_match = gt[gt["fiscal_document_id"] == fiscal_document_id]
    gt_row = gt_match.iloc[0] if not gt_match.empty else None

    return {
        "fiscal_document_id": fiscal_document_id,
        "found": True,
        "crm_customer_id": row["crm_customer_id"],
        "ncm_code": row["ncm_code"],
        "cfop_code": row["cfop_code"],
        "cst_code": row["cst_code"],
        "cst_cfop_valid": bool(row["cst_cfop_valid"]),
        "calculated_tax_total": float(row["calculated_tax_total"]),
        "correct_tax_total": float(gt_row["correct_tax_total"]) if gt_row is not None else None,
        "discrepancy_amount": float(gt_row["discrepancy_amount"]) if gt_row is not None else None,
        "discrepancy_reason": str(gt_row["discrepancy_reason"]) if gt_row is not None else None,
    }
