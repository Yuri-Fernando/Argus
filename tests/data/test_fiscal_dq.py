"""
ADR-015 acceptance criteria for the fiscal/tributário extension — same shape as
tests/data/test_dq_quarantine.py's Sprint 3 acceptance test, applied to the self-contained
`fiscal_document` domain (data_quality/validators/fiscal_report.py::run_fiscal_dq()) instead of
the main lakehouse pipeline.

The synthetic fiscal generator deterministically injects three discrepancy categories
(data/synthetic/config.yaml's `dirty_rates_fiscal`, ~3%/2%/1% — see
data/synthetic/generators/fiscal.py's FiscalDirtyRates), so this test does not need to mutate
config or regenerate data to get a deterministic breach — it runs the real DQ engine against the
data that's already checked in and asserts on the real, already-corrupted rows.

Requires `data/synthetic/fiscal/fiscal_documents.csv` to exist
(`python data/synthetic/generate_all.py --only fiscal`).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FISCAL_SOURCE = REPO_ROOT / "data" / "synthetic" / "fiscal" / "fiscal_documents.csv"

pytestmark = pytest.mark.skipif(
    not FISCAL_SOURCE.exists(),
    reason="data/synthetic/fiscal/fiscal_documents.csv missing — run "
           "`python data/synthetic/generate_all.py --only fiscal` first",
)


@pytest.fixture(scope="module")
def fiscal_report():
    from data_quality.validators.fiscal_report import run_fiscal_dq

    return run_fiscal_dq()


def test_injected_discrepancies_fail_checkpoint_and_land_in_quarantine(fiscal_report):
    from data_quality.validators.fiscal_report import FISCAL_GROUND_TRUTH_PATH, FISCAL_QUARANTINE_PATH, FISCAL_REPORT_PATH

    ground_truth = pd.read_csv(FISCAL_GROUND_TRUTH_PATH)
    n_dirty = int((ground_truth["discrepancy_reason"] != "none").sum())

    # 1. The engine reports failures for the breached rules (not a silent pass).
    assert fiscal_report.score < 1.0
    failing_rules = [r for r in fiscal_report.rule_results if r.failed_count > 0]
    assert failing_rules, "Expected at least one DQ rule to catch the injected fiscal discrepancies"

    # 2. Quarantine parquet exists (only if there's at least one dirty row — same "hard rules
    # cause quarantine" contract as test_dq_quarantine.py), and quarantined count matches the
    # engine's own count.
    if n_dirty > 0:
        assert FISCAL_QUARANTINE_PATH.exists(), f"Expected quarantine output at {FISCAL_QUARANTINE_PATH}"
        quarantined = pd.read_parquet(FISCAL_QUARANTINE_PATH)
        assert len(quarantined) == fiscal_report.quarantined_count > 0

    # 3. No row silently disappears — quarantined count never exceeds total rows.
    assert 0 <= fiscal_report.quarantined_count <= fiscal_report.total_rows == len(ground_truth)

    # 4. fiscal_dq_report.json reflects the breach (score dropped below 1.0) and is readable by
    # mcp/tools/fiscal.py's exact parsing logic.
    report_payload = json.loads(FISCAL_REPORT_PATH.read_text(encoding="utf-8"))
    table_entry = report_payload["tables"][0]
    assert table_entry["table_name"] == "fiscal_document"
    assert table_entry["score"] < 1.0
    assert table_entry["quarantined_count"] == fiscal_report.quarantined_count


def test_clean_documents_are_not_quarantined(fiscal_report):
    """The flip side of the acceptance criterion above — a document with
    discrepancy_reason == "none" must never end up in quarantine, or the DQ rules would be
    over-triggering on data that's actually fine."""
    from data_quality.validators.fiscal_report import FISCAL_CSV_DTYPE, FISCAL_CSV_PATH, FISCAL_GROUND_TRUTH_PATH

    docs = pd.read_csv(FISCAL_CSV_PATH, dtype=FISCAL_CSV_DTYPE)
    ground_truth = pd.read_csv(FISCAL_GROUND_TRUTH_PATH)
    clean_ids = set(ground_truth[ground_truth["discrepancy_reason"] == "none"]["fiscal_document_id"])

    quarantined_mask = fiscal_report.quarantine_mask
    quarantined_ids = set(docs.loc[quarantined_mask, "fiscal_document_id"])

    assert not (clean_ids & quarantined_ids), (
        "A document with no injected discrepancy ended up quarantined — DQ rules are "
        "over-triggering on genuinely clean fiscal data."
    )
