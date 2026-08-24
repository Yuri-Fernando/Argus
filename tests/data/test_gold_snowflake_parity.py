"""
STUB — Sprint 7 (Gold dimensional model + Snowflake DWH) acceptance
criteria, ARCHITECTURE.md §12 / ROADMAP.md Sprint 7. Not yet implemented:
the Databricks Gold tables and the Snowflake Streams/Tasks incremental sync
this test depends on don't exist yet. Raises `pytest.skip` until Sprint 7
lands.

---

Once implemented, this test will verify the exact acceptance criterion
stated in ROADMAP.md Sprint 7: *"a row inserted in Databricks Gold appears
in Snowflake CORE within one Task cycle, values matching exactly."*

1. **Arrange** — construct one fully-formed synthetic row for a Gold
   dimensional table (e.g. `gold.dim_customer` or `gold.fact_orders`) with
   a sentinel/test-only key (a `master_customer_id` or `order_id` prefixed
   e.g. `TESTPARITY-`) so it can be found and cleaned up without touching
   real synthetic fixtures.

2. **Act**:
   - Insert the row into the Databricks Gold Delta table
     (`customer_intelligence.gold.<table>`), via the same write path
     `lakehouse/gold/` uses in production (not a raw SQL `INSERT` bypassing
     the pipeline's own validation).
   - Wait for one Snowflake Task cycle to complete — either by polling
     `INFORMATION_SCHEMA.TASK_HISTORY` for the sync task's next completed
     run after the insert timestamp, or by manually triggering the task
     (`EXECUTE TASK`) if the test needs to be deterministic rather than
     wall-clock-bound in CI.

3. **Assert**:
   - The row (matched by primary key) exists in the corresponding
     Snowflake `CUSTOMER_INTELLIGENCE.CORE.<table>` table.
   - Every column value matches exactly between the Databricks Gold row and
     the Snowflake CORE row — this is a field-by-field diff, not just a
     row-count check, since a sync bug that silently drops or truncates a
     column would otherwise pass a naive "row exists" assertion.
   - The sync latency (Gold insert timestamp -> Snowflake row visible
     timestamp) is recorded and asserted below a documented ceiling (e.g.
     the configured Task schedule interval plus a grace margin), so a
     silently-degraded sync doesn't quietly turn "one Task cycle" into "one
     hour."

4. **Cleanup** — deletes the sentinel row from both Databricks Gold and
   Snowflake CORE afterward so repeated CI runs stay idempotent.

Requires live Databricks + Snowflake credentials (unlike the fully local
`tests/data/test_no_real_pii.py` and `test_dq_quarantine.py`), so once
implemented this test is expected to skip gracefully — same pattern as
`.github/workflows/dbt.yml`'s secrets-check step — in any environment
without `DATABRICKS_HOST`/`DATABRICKS_TOKEN` and `SNOWFLAKE_ACCOUNT`
configured, rather than fail CI runs that can't reach cloud infrastructure
(e.g. forked-repo PRs).

---

STATUS (see BUILD_LOG.md): every other layer of this platform now has a real,
local, runnable implementation — this is the one test in the suite that
genuinely cannot be satisfied locally, because "Databricks Gold" and
"Snowflake CORE" as two separate synced systems don't both exist in this
environment (there's one local DuckDB stand-in — `snowflake/local_runner.py`
— not two systems with a sync job between them). The `skipif` marker below is
conditioned on `DATABRICKS_HOST`/`DATABRICKS_TOKEN`/`SNOWFLAKE_ACCOUNT` rather
than an unconditional skip, so it correctly reports *why* the test is skipped
in this environment specifically (credentials missing) instead of a generic
"not implemented."

Correction (a code-review pass caught this overclaim in an earlier version of
this paragraph): configuring those three credentials does NOT make this test
"start actually running" in any meaningful sense — the function body below is
still the unimplemented Sprint 7 stub and calls `pytest.skip()` itself
unconditionally, so even with credentials present the test collects, runs,
and reports skipped, asserting nothing. Two separate gates exist here: the
`skipif` marker (now credential-conditioned) and the stub body (still always
skips). Implementing the real Delta-write + Task-poll + field-by-field diff
described above — which needs live credentials to develop against, exactly
what's missing here — is the only thing that removes the second gate.
"""
import os

import pytest

_REQUIRED_ENV_VARS = ("DATABRICKS_HOST", "DATABRICKS_TOKEN", "SNOWFLAKE_ACCOUNT")


@pytest.mark.skipif(
    not all(os.environ.get(v) for v in _REQUIRED_ENV_VARS),
    reason=(
        f"Requires live Databricks + Snowflake credentials ({', '.join(_REQUIRED_ENV_VARS)}) — "
        "none configured in this environment. See BUILD_LOG.md's 'Pendências que só você pode "
        "resolver'. This is the one acceptance test in the suite that cannot be satisfied by a "
        "local-only build (ADR-010) since it verifies sync between two separate cloud systems."
    ),
)
def test_databricks_gold_row_appears_in_snowflake_core():
    pytest.skip(
        "Credentials are present but the Delta-write + Task-poll + field-by-field-diff "
        "implementation (Sprint 7 body) is still a stub — see the docstring's numbered plan."
    )
