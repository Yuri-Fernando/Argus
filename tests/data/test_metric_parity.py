"""
STUB — Sprint 8 (Semantic Layer) acceptance criteria, ARCHITECTURE.md §11 /
ADR-005. Not yet implemented: the dbt/MetricFlow marts, Unity Catalog Metric
Views, and Snowflake Semantic Views this test depends on don't exist yet.
Raises `pytest.skip` until Sprint 8 lands; kept in the repo now (rather than
added later) so the acceptance criterion is visible and trackable from
Sprint 0 onward, and so CI has a named, discoverable check to eventually
stop skipping.

---

Once implemented, this test will assert semantic-layer parity across all
three implementations described in ARCHITECTURE.md §11 — the concrete,
automated version of ADR-005's decision ("one canonical metric definition,
three implementations, one automated parity test that fails CI if they
diverge"):

1. **Golden question set** — a fixed list of (question, expected_metric,
   grain, filters) tuples, sourced from `docs/semantic-dictionary.md`'s
   canonical definitions (Revenue, Orders, AOV, Churn, CLV, NPS, Delivery
   SLA, ...). At minimum: "What was Revenue last month?", "What is AOV by
   region this quarter?", "What is the churn rate for VIP segment?".

2. **Three query paths, one question each**:
   - **dbt/MetricFlow** — `mf query --metrics <metric> --group-by <dims>`
     (or the MetricFlow Python API) against `dbt/models/marts/`.
   - **Unity Catalog Metric Views** — a SQL query against the Databricks
     Metric View object mirroring the same metric definition.
   - **Snowflake Semantic Views** — a query through the Semantic View (the
     same grounding source Cortex Analyst uses), either via `SELECT`
     against the semantic view or via the Cortex Analyst REST API with a
     structured query matching the same metric/grain/filters.

3. **Assertion** — for every question in the golden set, the three
   implementations MUST return **numerically identical results** (exact
   match for counts/integers; a documented epsilon, e.g. 1e-6 relative
   tolerance, for floating-point aggregates to allow for warehouse-level
   rounding differences). Any divergence fails the test with a diff showing
   question, all three values, and which pair(s) disagreed — this is
   exactly the *"Power BI said R$10M, the agent said R$13M"* failure mode
   from the original design draft (see ADR-005's Context section) made
   impossible to ship silently.

4. **Freshness assumption** — the test assumes all three targets are
   refreshed from the same Gold snapshot at test time (Databricks Gold is
   the source of truth; Snowflake CORE is synced via Streams/Tasks per
   Sprint 7 — see `test_gold_snowflake_parity.py`). A metric comparison
   across stale targets is a false failure, not a real parity break, so the
   real implementation will pin or wait for a sync checkpoint before
   querying.

Wired into CI via `.github/workflows/dbt.yml` (or a dedicated
`semantic-parity.yml` if the three-way query fan-out needs credentials
beyond what `dbt.yml` already provisions) once implemented.
"""
import pytest


def test_metric_parity_across_dbt_uc_snowflake():
    pytest.skip("Sprint 8 — semantic layer not yet implemented")
