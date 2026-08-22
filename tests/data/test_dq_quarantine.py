"""
Sprint 3 (Data Quality framework) acceptance criteria, ARCHITECTURE.md §7 /
data_quality/README.md — implemented for real once `lakehouse/run_pipeline.py`
and `data_quality/validators/` landed (see BUILD_LOG.md, WP1).

Verifies the exact acceptance criterion stated in ROADMAP.md Sprint 3:
*"intentionally corrupting a field in the synthetic generator causes the
Checkpoint to fail and the row to land in quarantine/."*

The synthetic CRM generator already deterministically corrupts phone numbers
for ~1% of rows (`data/synthetic/config.yaml`'s `dirty_rates.invalid_phone`,
truncated to <=4 digits — see `data/synthetic/generators/crm.py`), and
`valid_phone` is registered as a HARD rule in `data_quality/expectations/`, so
this test does not need to mutate config or regenerate data to get a
deterministic breach — it runs the real pipeline against the data that's
already checked in and asserts on the real, already-corrupted rows.

Requires `data/synthetic/crm/crm_customers.csv` to exist (`make seed`).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CRM_SOURCE = REPO_ROOT / "data" / "synthetic" / "crm" / "crm_customers.csv"

pytestmark = pytest.mark.skipif(
    not CRM_SOURCE.exists(),
    reason="data/synthetic/crm/crm_customers.csv missing — run `make seed` first",
)


@pytest.fixture(scope="module")
def pipeline_reports():
    """Runs the real Bronze->Silver->DQ pipeline once and shares the result
    across assertions in this module (the pipeline is not free — every
    `data_quality/expectations` HARD rule check runs against ~10k+ rows)."""
    from lakehouse.run_pipeline import run

    return {r.table_name: r for r in run()}


def test_corrupted_field_fails_checkpoint_and_lands_in_quarantine(pipeline_reports):
    report = pipeline_reports["crm_customer"]

    # 1. The Checkpoint reports failure for the breached rule (not a silent pass).
    phone_rule = next(r for r in report.rule_results if r.rule.column == "phone")
    assert phone_rule.failed_count > 0, (
        "Expected data/synthetic/config.yaml's ~1% invalid_phone dirty rate to "
        "produce at least one valid_phone failure — got 0. Either the synthetic "
        "data changed, or the rule stopped catching truncated phone numbers."
    )
    assert phone_rule.score < 1.0

    # 2. Quarantine parquet exists, and every quarantined row really is invalid.
    quarantine_path = REPO_ROOT / "data" / "lakehouse" / "quarantine" / "crm_customer.parquet"
    assert quarantine_path.exists(), f"Expected quarantine output at {quarantine_path}"
    quarantined = pd.read_parquet(quarantine_path)
    assert len(quarantined) == report.quarantined_count > 0
    digit_counts = quarantined["phone"].astype(str).str.replace(r"\D", "", regex=True).str.len()
    assert (digit_counts < 8).all(), "Every quarantined row should fail the same hard rule it was flagged for"

    # 3. No row silently disappears — quarantined + passing accounts for every input row.
    silver_path = REPO_ROOT / "data" / "lakehouse" / "silver" / "crm_customer.parquet"
    passing = pd.read_parquet(silver_path)
    assert len(quarantined) + len(passing) == report.total_rows

    # 4. Quarantined IDs are absent from Silver output for this run.
    assert set(quarantined["crm_customer_id"]) & set(passing["crm_customer_id"]) == set()

    # 5. dq_report.json reflects the breach (score dropped below 1.0).
    import json

    dq_report = json.loads((REPO_ROOT / "data_quality" / "reports" / "dq_report.json").read_text(encoding="utf-8"))
    table_entry = next(t for t in dq_report["tables"] if t["table_name"] == "crm_customer")
    assert table_entry["score"] < 1.0
    assert table_entry["quarantined_count"] == report.quarantined_count
