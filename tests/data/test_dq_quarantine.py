"""
STUB — Sprint 3 (Data Quality framework) acceptance criteria,
ARCHITECTURE.md §7 / data_quality/README.md. Not yet implemented: the GX
Checkpoints and quarantine-routing job this test depends on don't exist yet.
Raises `pytest.skip` until Sprint 3 lands.

---

Once implemented, this test will verify the exact acceptance criterion
stated in ROADMAP.md Sprint 3 and data_quality/README.md: *"intentionally
corrupting a field via `data/synthetic/config.yaml`'s `dirty_rates` causes
the relevant Checkpoint to fail and the affected rows to land in
`quarantine/`."*

1. **Arrange** — override `data/synthetic/config.yaml`'s `dirty_rates` (e.g.
   temporarily push `invalid_phone` or `missing_email` well above its
   default 0.01/0.02, or add a new deliberately-invalid field not currently
   modeled) and regenerate a small CRM sample via
   `data/synthetic/generate_all.py --only crm --profile local`, so the
   corruption rate is high enough to guarantee at least one row breaches
   the relevant GX Expectation deterministically (not a flaky, seed-
   dependent maybe).

2. **Act** — run the Bronze->Silver GX Checkpoint that owns the corrupted
   field's Expectation (`data_quality/validators/`, invoked the same way
   `make dq` does: `python data_quality/run_checkpoint.py --suite
   customer_suite`).

3. **Assert**:
   - The Checkpoint's `run_results` report `success: False` for the
     breached Expectation (not a silent pass).
   - The corrupted row(s) — identified by `crm_customer_id` — are present
     in `data/quarantine/` (or the ADLS-equivalent `adls/quarantine/`
     prefix locally via MinIO) and are **absent** from the corresponding
     Silver table output for that run.
   - The row count in quarantine plus the row count that passed equals the
     total input row count (no row silently disappears — every input row
     is accounted for in exactly one of "passed" or "quarantined").
   - `quality_report.json`'s `dq_score` for the affected dataset reflects
     the breach (drops below 1.0 by roughly the corrupted fraction).

4. **Cleanup** — restores `data/synthetic/config.yaml` to its committed
   dirty_rates afterward (via a fixture using `tmp_path`/monkeypatch on the
   config loader, not by mutating the repo's actual config.yaml on disk) so
   the test is hermetic and repeatable in CI.

Wired into CI via `.github/workflows/data-quality.yml` once implemented —
that workflow already runs `make dq` on every PR touching `lakehouse/**` or
`data_quality/**`; this test adds the "and quarantine actually happens"
assertion GX's own checkpoint success/failure alone doesn't prove.
"""
import pytest


def test_corrupted_field_fails_checkpoint_and_lands_in_quarantine():
    pytest.skip("Sprint 3 — data quality quarantine pipeline not yet implemented")
