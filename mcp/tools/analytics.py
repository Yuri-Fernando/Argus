"""Sales/revenue analytics tool for the MCP server.

Built in ROADMAP.md Sprint 13. The metric values this tool returns must come from the governed
semantic layer (ARCHITECTURE.md §11), never from a raw Gold/CORE table computed ad hoc — that is
the exact discipline ADR-005 (semantic layer) exists to enforce: one metric, one definition,
whether it's answered by dbt/MetricFlow, a Unity Catalog Metric View, or a Snowflake Semantic
View. An agent asking "what was Revenue last month?" must get the same number Power BI would
show for the same question.
"""

from __future__ import annotations

from typing import Any

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
    return {
        "metric": metric,
        "period": period,
        "segment": segment,
        "value": None,
        "unit": None,
        "source": None,
        "valid": True,
    }
