"""Self-contained DQ runner for the fiscal/tributário extension (ADR-015).

Deliberately NOT wired into `lakehouse/run_pipeline.py::TABLE_ORDER` — `fiscal_document` is a
bolt-on domain extension (`data/synthetic/generators/fiscal.py`), conceptually a different table
family from the CRM/support/web/campaign/finance e-commerce pipeline, so it gets its own small
runner instead of forcing it through Bronze/Silver staging it doesn't need. It still reuses the
exact same `DQEngine` (`data_quality/validators/engine.py`) and writes a report in the same shape
as `data_quality/validators/report.py::write_reports` (so `mcp/tools/fiscal.py` can read it with
the identical parsing logic `mcp/tools/quality.py` already uses) — just to its own file, so it
never collides with the main pipeline's `dq_report.json`.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from data_quality.expectations.fiscal_document import get_rules
from data_quality.validators.engine import DQEngine, TableReport, quarantine_reasons

ROOT = Path(__file__).resolve().parents[2]
FISCAL_CSV_PATH = ROOT / "data" / "synthetic" / "fiscal" / "fiscal_documents.csv"
FISCAL_GROUND_TRUTH_PATH = ROOT / "data" / "synthetic" / "fiscal" / "fiscal_documents_ground_truth.csv"
FISCAL_QUARANTINE_PATH = ROOT / "data" / "lakehouse" / "quarantine" / "fiscal_document.parquet"
FISCAL_REPORT_PATH = ROOT / "data_quality" / "reports" / "fiscal_dq_report.json"
CRM_CSV_PATH = ROOT / "data" / "synthetic" / "crm" / "crm_customers.csv"

# NCM/CFOP/CST are real-world codes that legitimately carry leading zeros (e.g. "07019000") —
# `pd.read_csv` without an explicit dtype infers these all-digit columns as int64 and silently
# drops the leading zero, which then makes a perfectly valid code fail the NCM catalog check for
# no real reason. Force string dtype on every read of this CSV, here and in mcp/tools/fiscal.py.
FISCAL_CSV_DTYPE = {"ncm_code": str, "cfop_code": str, "cst_code": str}


def run_fiscal_dq() -> TableReport:
    """Loads the synthetic fiscal documents, validates them with the same `DQEngine` the main
    pipeline uses, writes the quarantined rows + a JSON report, and returns the `TableReport`.

    Raises:
        FileNotFoundError: if `data/synthetic/fiscal/fiscal_documents.csv` doesn't exist yet —
            run `python data/synthetic/generate_all.py --only fiscal` first.
    """
    df = pd.read_csv(FISCAL_CSV_PATH, dtype=FISCAL_CSV_DTYPE)

    crm_customer_ids: set = set()
    if CRM_CSV_PATH.exists():
        crm_customer_ids = set(pd.read_csv(CRM_CSV_PATH)["crm_customer_id"].dropna())

    rules = get_rules(crm_customer_ids)
    engine = DQEngine()
    report = engine.validate("fiscal_document", df, rules)

    if report.quarantined_count > 0:
        FISCAL_QUARANTINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        quarantined_df = df[report.quarantine_mask].copy()
        quarantined_df["_dq_failure_reasons"] = quarantine_reasons(report)
        quarantined_df.to_parquet(FISCAL_QUARANTINE_PATH, index=False)

    _write_fiscal_report(report)
    return report


def _write_fiscal_report(report: TableReport) -> Path:
    FISCAL_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_score": round(report.score, 4),
        "overall_score_pct": round(report.score * 100, 2),
        "tables": [report.to_dict()],
        "notes": {"domain": "fiscal (ADR-015)", "reason": "self-contained extension, not part of TABLE_ORDER"},
    }
    FISCAL_REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return FISCAL_REPORT_PATH


if __name__ == "__main__":
    result = run_fiscal_dq()
    print(
        f"fiscal_document DQ score={result.score:.2%} rows={result.total_rows} "
        f"quarantined={result.quarantined_count}"
    )
    print(f"Report written to {FISCAL_REPORT_PATH}")
