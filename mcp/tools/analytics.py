"""Sales/revenue analytics tool for the MCP server.

Built in ROADMAP.md Sprint 13. The metric values this tool returns must come from the governed
semantic layer (ARCHITECTURE.md §11), never from a raw Gold/CORE table computed ad hoc — that is
the exact discipline ADR-005 (semantic layer) exists to enforce: one metric, one definition,
whether it's answered by dbt/MetricFlow, a Unity Catalog Metric View, or a Snowflake Semantic
View. An agent asking "what was Revenue last month?" must get the same number Power BI would
show for the same question.

WIRED (this session): routes to `snowflake/local_runner.py`'s `build_warehouse()` +
`run_metric()` — the local-dev DuckDB stand-in for the three cloud semantic-layer
implementations named above (dbt/MetricFlow, Unity Catalog Metric View, Snowflake Semantic
View), all three of which are cross-checked against this same `local_runner.py` output in
`tests/data/test_metric_parity.py`. See `_METRIC_NAME_MAP` / `SKIPPED_NOTE_MAP` below for how
this tool's `KNOWN_METRICS` names map onto `local_runner.py`'s metric names, several of which it
explicitly `SKIPPED_METRICS`s (no fabricated numbers for those — `value` stays `None`).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import duckdb

from snowflake.local_runner import SKIPPED_METRICS, build_warehouse, run_metric

# Canonical metric names this tool accepts — must stay in sync with
# docs/semantic-dictionary.md (owned by the Sprint 8 semantic layer work). Kept as a constant
# here so an unknown metric name fails fast instead of silently falling back to a raw column.
KNOWN_METRICS = frozenset(
    {
        "revenue",
        "aov",  # average order value
        "order_count",
        "churn_rate",
        "clv",  # customer lifetime value
        "nps",
        "delivery_sla",
    }
)

# This tool's canonical metric name -> snowflake/local_runner.py's metric name. Identical for
# most; `order_count` maps to local_runner's `orders`, which it explicitly SKIPs (no
# fact_orders/Olist data in this build).
_METRIC_NAME_MAP: dict[str, str] = {
    "revenue": "revenue",
    "aov": "aov",
    "order_count": "orders",
    "churn_rate": "churn_rate",
    "clv": "clv",
    "nps": "nps",
    "delivery_sla": "delivery_sla",
}

_UNIT_MAP: dict[str, str] = {
    "revenue": "BRL",
    "aov": "BRL",
    "order_count": "count",
    "churn_rate": "percent",
    "clv": "BRL",
    "nps": "score",
    "delivery_sla": "percent",
}

_SOURCE = "snowflake_local_runner"
_PERIOD_SEGMENT_CAVEAT = (
    "snowflake/local_runner.py — full-dataset snapshot, period/segment filtering not yet "
    "implemented (its metrics are computed over the whole warehouse, not broken down by date "
    "range or segment)."
)


@lru_cache(maxsize=1)
def _connection() -> duckdb.DuckDBPyConnection:
    """Build (once per process) the same local DuckDB warehouse `snowflake/local_runner.py`'s
    CLI and `api/services/metrics_service.py` use — never recomputed per MCP call."""
    return build_warehouse(rebuild=True)


def get_sales_metrics(
    metric: str,
    period: str = "last_30_days",
    segment: str | None = None,
) -> dict[str, Any]:
    """Fetch a governed metric value for a given period and optional segment filter.

    Args:
        metric: canonical metric name (must be one of KNOWN_METRICS — see
            docs/semantic-dictionary.md for the full definitions table).
        period: semantic-layer period string, e.g. "last_30_days", "mtd", "ytd", "qtd".
        segment: optional customer segment filter (VIP/Loyal/Potential/At Risk/Inactive from
            ml/segmentation/, ROADMAP.md Sprint 11).

    Returns:
        {
            "metric": str,
            "period": str,
            "segment": str | None,
            "value": float | None,
            "unit": str,             # e.g. "BRL", "count", "percent"
            "source": str,           # which semantic-layer implementation answered
            "valid": bool,           # False if `metric` is not a recognized canonical metric
        }
    """
    if metric not in KNOWN_METRICS:
        return {
            "metric": metric,
            "period": period,
            "segment": segment,
            "value": None,
            "unit": None,
            "source": None,
            "valid": False,
        }

    # TODO(Sprint 8 / semantic layer): route this call to one of the three governed
    # implementations described in ARCHITECTURE.md §11:
    #   - dbt / MetricFlow (via its query interface), or
    #   - Databricks SQL against a Unity Catalog Metric View, or
    #   - a Snowflake Semantic View query (the same source Cortex Analyst is grounded on).
    # Whichever is chosen as this tool's default, log which one answered in `source` so the
    # regression test in tests/data/test_metric_parity.py (Sprint 8 acceptance criteria) can be
    # cross-checked against Power BI and the other two implementations.
    # Local-dev wiring: routed to `snowflake/local_runner.py`, the local DuckDB stand-in for all
    # three cloud implementations above (see module docstring). `source` always reports which
    # implementation actually answered, honestly, per the TODO's own instruction.
    local_metric_name = _METRIC_NAME_MAP[metric]
    con = _connection()

    try:
        value = run_metric(con, local_metric_name)
    except NotImplementedError:
        # local_runner.py's own SKIPPED_METRICS guard — e.g. order_count/nps/delivery_sla have
        # no supporting data in this build (no Olist orders, no NPS survey source). Never
        # fabricate a number here; say so honestly instead.
        reason = SKIPPED_METRICS.get(local_metric_name, "not implemented in snowflake/local_runner.py")
        return {
            "metric": metric,
            "period": period,
            "segment": segment,
            "value": None,
            "unit": _UNIT_MAP.get(metric),
            "source": f"{_SOURCE} — SKIPPED: {reason} {_PERIOD_SEGMENT_CAVEAT}",
            "valid": True,
        }

    # `clv` returns a dict (avg/min/max/median) from run_metric — every other metric is a float.
    # The contract's `value` field is documented as `float | None`; for `clv` the average is
    # surfaced as `value` (matching what `dim_customer.lifetime_value`'s AVG represents in
    # `powerbi/dax/measures.md`), with the fuller breakdown folded into `source` for transparency
    # rather than silently dropping min/max/median on the floor.
    if isinstance(value, dict):
        numeric_value = value.get("avg")
        source_note = f"{_SOURCE} (avg of clv.min={value.get('min')}, clv.max={value.get('max')}, clv.median={value.get('median')}). {_PERIOD_SEGMENT_CAVEAT}"
    else:
        numeric_value = float(value)
        source_note = f"{_SOURCE}. {_PERIOD_SEGMENT_CAVEAT}"

    return {
        "metric": metric,
        "period": period,
        "segment": segment,
        "value": numeric_value,
        "unit": _UNIT_MAP.get(metric),
        "source": source_note,
        "valid": True,
    }
