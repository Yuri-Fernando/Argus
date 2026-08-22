"""
Sprint 8 (Semantic Layer) acceptance criteria, ARCHITECTURE.md §11 / ADR-005 —
partially implemented once the three local semantic-layer artifacts landed
(see BUILD_LOG.md, WP4a/WP4b): `snowflake/local_runner.py` (the executable
implementation), `dbt/models/marts/_metrics.yml` (MetricFlow semantic models),
and `powerbi/dax/measures.md` (DAX measures).

SCOPE NOTE — this is a narrower, honest proxy for the full acceptance
criterion, not the complete thing:

ADR-005's real target is a *live* three-way query fan-out — dbt/MetricFlow
(`mf query`), Unity Catalog Metric Views, and Snowflake Semantic Views (or
Cortex Analyst) — each independently computing the same metric against a real
warehouse and being compared at query time. That requires a live Databricks
workspace and a live Snowflake account, neither of which exists in this
environment (no cloud credentials configured — see BUILD_LOG.md's "Pendências
que só você pode resolver"). Faking that fan-out here would be worse than not
having the test at all.

What THIS test actually verifies, and why it's still meaningful: every one of
the three local semantic-layer implementations documents its *expected*
numeric value in prose, cross-checked by hand when each was written (WP4b's
report: "Metric-value consistency check ... all five headline metrics ...
match the exact values/filters from `snowflake/local_runner.py`"). This test
makes that hand-check a regression test — it runs `local_runner.py` LIVE
(the one implementation that's actually executable without a cloud account)
and asserts its output still matches what's documented in the dbt and DAX
files. If someone changes the underlying data or the local_runner logic
without updating the other two docs, this test catches the divergence — the
literal "Power BI said R$10M, the agent said R$13M" failure mode from
ADR-005's Context section, scoped to what's actually testable locally.

Upgrading this to the full live three-way fan-out is tracked as backlog once
real Databricks + Snowflake credentials are available (BUILD_LOG.md).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DBT_METRICS = REPO_ROOT / "dbt" / "models" / "marts" / "_metrics.yml"
DAX_MEASURES = REPO_ROOT / "powerbi" / "dax" / "measures.md"
SILVER_DIR = REPO_ROOT / "data" / "lakehouse" / "silver"

pytestmark = pytest.mark.skipif(
    not SILVER_DIR.exists() or not any(SILVER_DIR.glob("*.parquet")),
    reason="data/lakehouse/silver/*.parquet missing — run lakehouse/run_pipeline.py first",
)

NUMBER_RE = r"R?\$?\s*([\d,]+\.\d+)"


def _extract_documented_value(text: str, anchor: str) -> float:
    """Finds `anchor` in `text` and parses the first R$-or-bare decimal number
    that appears between it and the start of the next section (`\\n## ` for
    the DAX doc's headings, or end-of-text). Raises (not silently skips) if
    the anchor or the number pattern isn't found — a missing reference value
    is a real problem with the doc, not something to hide."""
    # rfind, not find: some anchors (e.g. "run_metric('churn_rate')") also appear
    # earlier as an incidental mention (e.g. inside a measure's own description);
    # the reference "Matches ... exactly: <value>" sentence is reliably the LAST
    # occurrence of the anchor in each file.
    idx = text.rfind(anchor)
    assert idx != -1, f"Anchor {anchor!r} not found — has the doc been restructured?"
    next_section = text.find("\n## ", idx + len(anchor))
    window = text[idx : next_section if next_section != -1 else idx + 3000]
    match = re.search(r"(?:Expected value|exactly)[^0-9]{0,50}" + NUMBER_RE, window)
    assert match, f"No 'Expected value'/'exactly <number>' pattern found near {anchor!r}"
    return float(match.group(1).replace(",", ""))


@pytest.fixture(scope="module")
def live_metrics() -> dict:
    from snowflake.local_runner import build_warehouse, run_all_metrics

    con = build_warehouse()
    try:
        return run_all_metrics(con)
    finally:
        con.close()


@pytest.fixture(scope="module")
def dbt_text() -> str:
    return DBT_METRICS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dax_text() -> str:
    return DAX_MEASURES.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "metric_key,dbt_anchor,dax_anchor,live_value_fn",
    [
        ("revenue", "run_metric('revenue')", "## Revenue", lambda m: m["revenue"]),
        ("aov", "run_metric('aov')", "## AOV", lambda m: m["aov"]),
        ("churn_rate", "run_metric('churn_rate')", "## Churn Rate", lambda m: m["churn_rate"]),
        ("repeat_rate", "run_metric('repeat_rate')", "## Repeat Rate", lambda m: m["repeat_rate"]),
        ("clv", "run_metric('clv')", "## CLV", lambda m: m["clv"]["avg"]),
    ],
)
def test_metric_parity_across_local_runner_dbt_and_dax(
    metric_key, dbt_anchor, dax_anchor, live_value_fn, live_metrics, dbt_text, dax_text
):
    live_value = live_value_fn(live_metrics)
    dbt_value = _extract_documented_value(dbt_text, dbt_anchor)
    dax_value = _extract_documented_value(dax_text, dax_anchor)

    assert live_value == pytest.approx(dbt_value, rel=1e-3), (
        f"{metric_key}: local_runner.py computed {live_value}, but "
        f"dbt/models/marts/_metrics.yml documents {dbt_value} — semantic layer drift."
    )
    assert live_value == pytest.approx(dax_value, rel=1e-3), (
        f"{metric_key}: local_runner.py computed {live_value}, but "
        f"powerbi/dax/measures.md documents {dax_value} — semantic layer drift."
    )
