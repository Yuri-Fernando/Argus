"""Custom MCP server — the platform's tool/resource/prompt surface for agents.

Built in ROADMAP.md Sprint 13 ("Custom MCP server"). Implements the tool list from
ARCHITECTURE.md §15 (Layer 12 — MCP & Agentic AI) using the official `mcp` Python SDK's
FastMCP interface. Design rationale for using MCP instead of letting an LLM emit raw SQL is in
docs/decisions/ADR-004-mcp-strategy.md.

This module is intentionally a thin registration layer: every tool's actual logic lives in
`mcp/tools/*.py` and is imported here, so tools stay independently unit-testable without a live
MCP session. `server.py` should never grow business logic of its own — if a tool needs new
behaviour, it goes in its `mcp/tools/*.py` module, not here.

Sprint 13 acceptance criteria (ROADMAP.md): `get_customer_churn(customer_id)` and
`get_data_quality()` return correct live data end-to-end through MCP, once the underlying data
sources are wired (see the TODOs in `mcp/tools/*.py` — most of that wiring belongs to earlier
sprints' modules: mdm/, graph/, ml/, data_quality/, snowflake/).

Known constraint: this package is named `mcp/`, which collides with the third-party `mcp` SDK
package if the repo root ends up first on `sys.path`. See mcp/README.md "Known constraint"
section before changing how this file is invoked.

Run:
    python mcp/server/server.py
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from mcp.tools.analytics import get_sales_metrics as _get_sales_metrics
from mcp.tools.customer import (
    get_customer as _get_customer,
    get_customer_graph as _get_customer_graph,
    get_customer_orders as _get_customer_orders,
    search_customers as _search_customers,
)
from mcp.tools.fiscal import (
    get_fiscal_document as _get_fiscal_document,
    get_fiscal_quality as _get_fiscal_quality,
)
from mcp.tools.ml import (
    get_customer_churn as _get_customer_churn,
    get_model_metrics as _get_model_metrics,
    recommend_action as _recommend_action,
)
from mcp.tools.quality import (
    get_customer_quality as _get_customer_quality,
    get_data_quality as _get_data_quality,
    get_pipeline_status as _get_pipeline_status,
)
from mcp.tools.snowflake import query_snowflake as _query_snowflake

logger = logging.getLogger("mcp.server")

# Server name/version surfaced to MCP clients (Claude Desktop / Claude Code) on connect.
mcp = FastMCP(
    name="enterprise-customer-intelligence",
    instructions=(
        "Tools for querying customer 360, data quality, churn/ML and sales metrics for the "
        "Argus, the enterprise customer data platform. All tools are read-only except "
        "recommend_action, which never executes anything directly — it always enqueues a "
        "recommendation for human approval (see ADR-006)."
    ),
)


# ---------------------------------------------------------------------------
# Customer / Golden Record / Graph tools — mcp/tools/customer.py
# ---------------------------------------------------------------------------


@mcp.tool()
def get_customer(master_customer_id: str) -> dict:
    """Fetch a single customer's Golden Record by master_customer_id.

    Args:
        master_customer_id: the MDM-assigned survivor ID (see ARCHITECTURE.md §8), not a raw
            source-system customer_id.

    Returns:
        A dict with the Golden Record's survived fields (name, email, phone, address, segment,
        master_customer_id, source_record_count) or a not-found error shape. See
        mcp/tools/customer.py for the exact schema.
    """
    return _get_customer(master_customer_id)


@mcp.tool()
def search_customers(query: str, limit: int = 20) -> dict:
    """Search customers by free-text (name, email or phone fragment).

    Args:
        query: free-text search term.
        limit: maximum number of results to return (default 20, capped at 100).

    Returns:
        A dict with `results` (list of lightweight customer summaries) and `total_matches`.
    """
    return _search_customers(query, limit=limit)


@mcp.tool()
def get_customer_orders(master_customer_id: str, limit: int = 10) -> dict:
    """List a customer's most recent orders.

    Args:
        master_customer_id: the MDM-assigned survivor ID.
        limit: maximum number of orders to return, most recent first (default 10).

    Returns:
        A dict with `orders` (list of order summaries: order_id, status, value, order_date) and
        `total_orders`.
    """
    return _get_customer_orders(master_customer_id, limit=limit)


@mcp.tool()
def get_customer_graph(master_customer_id: str, max_hops: int = 2) -> dict:
    """Return the customer's relationship subgraph (shared email/phone/address/orders).

    Used for identity questions the Golden Record alone can't answer, e.g. "is this customer
    connected to any other flagged account?" — see ARCHITECTURE.md §9 (Customer Graph).

    Args:
        master_customer_id: the MDM-assigned survivor ID, used as the graph traversal root.
        max_hops: maximum traversal depth from the root node (default 2).

    Returns:
        A dict with `nodes` and `edges` (see mcp/tools/customer.py for the exact shape) suitable
        for an agent to reason over without needing to understand NetworkX directly.
    """
    return _get_customer_graph(master_customer_id, max_hops=max_hops)


# ---------------------------------------------------------------------------
# Analytics tool — mcp/tools/analytics.py
# ---------------------------------------------------------------------------


@mcp.tool()
def get_sales_metrics(
    metric: str,
    period: str = "last_30_days",
    segment: str | None = None,
) -> dict:
    """Fetch a governed sales/revenue metric from the semantic layer.

    Args:
        metric: canonical metric name as defined in docs/semantic-dictionary.md (e.g.
            "revenue", "aov", "order_count"). Never a raw column name — see ARCHITECTURE.md §11.
        period: a semantic-layer-recognized period string (e.g. "last_30_days", "mtd", "ytd").
        segment: optional customer segment filter (e.g. "VIP", "At Risk").

    Returns:
        A dict with `metric`, `period`, `value`, `unit` and `source` (which semantic-layer
        implementation answered — dbt/MetricFlow, UC Metric View, or Snowflake Semantic View).
    """
    return _get_sales_metrics(metric, period=period, segment=segment)


# ---------------------------------------------------------------------------
# Data quality / pipeline tools — mcp/tools/quality.py
# ---------------------------------------------------------------------------


@mcp.tool()
def get_customer_quality(master_customer_id: str) -> dict:
    """Fetch the data quality profile for a single customer's Golden Record.

    Args:
        master_customer_id: the MDM-assigned survivor ID.

    Returns:
        A dict with per-field completeness/validity flags and an overall `dq_score` in [0, 1].
    """
    return _get_customer_quality(master_customer_id)


@mcp.tool()
def get_data_quality(dataset: str | None = None) -> dict:
    """Fetch the platform's current data quality score(s).

    Args:
        dataset: optional dataset name (e.g. "silver.customer"). If omitted, returns the overall
            platform-level rollup score (ARCHITECTURE.md §7).

    Returns:
        A dict with `dq_score`, `dimension_scores` (completeness/validity/uniqueness/
        referential_integrity/freshness/schema/volume) and `as_of` timestamp.
    """
    return _get_data_quality(dataset)


@mcp.tool()
def get_pipeline_status(pipeline: str | None = None) -> dict:
    """Fetch the last-run status of a data pipeline (Bronze/Silver/Gold job, DQ checkpoint, etc.).

    Args:
        pipeline: optional pipeline/job name. If omitted, returns a summary across all tracked
            pipelines.

    Returns:
        A dict with `status` (e.g. "success", "failed", "running"), `last_run_at`,
        `duration_seconds` and `rows_processed`.
    """
    return _get_pipeline_status(pipeline)


# ---------------------------------------------------------------------------
# ML tools — mcp/tools/ml.py
# ---------------------------------------------------------------------------


@mcp.tool()
def get_customer_churn(master_customer_id: str) -> dict:
    """Fetch a customer's churn risk score and its top SHAP contributing features.

    Args:
        master_customer_id: the MDM-assigned survivor ID.

    Returns:
        A dict with `churn_probability`, `risk_band` ("low"/"medium"/"high"),
        `top_features` (list of {feature, shap_value}) and `model_version`.
    """
    return _get_customer_churn(master_customer_id)


@mcp.tool()
def get_model_metrics(model_name: str = "churn") -> dict:
    """Fetch the registered model's held-out evaluation metrics from the MLflow Model Registry.

    Args:
        model_name: one of "churn", "segmentation", "match" (see ARCHITECTURE.md §10).

    Returns:
        A dict with `roc_auc`, `f1`, `pr_auc`, `precision`, `recall`, `stage` (e.g. "Staging",
        "Production") and `run_id`.
    """
    return _get_model_metrics(model_name)


@mcp.tool()
def recommend_action(master_customer_id: str) -> dict:
    """Generate a prioritized retention/engagement recommendation for a customer.

    IMPORTANT — per ADR-006 (human-in-the-loop), this tool NEVER executes anything. It always
    returns a recommendation object with `requires_human_approval: true` and enqueues it in
    agents/recommendation/approval_queue.py for a human to approve or reject. No downstream
    system is ever mutated by this call.

    Args:
        master_customer_id: the MDM-assigned survivor ID.

    Returns:
        A dict: {recommendation, confidence, evidence, requires_human_approval: True,
        queue_id}. See mcp/tools/ml.py for the exact schema.
    """
    return _recommend_action(master_customer_id)


# ---------------------------------------------------------------------------
# Snowflake tool — mcp/tools/snowflake.py
# ---------------------------------------------------------------------------


@mcp.tool()
def query_snowflake(sql: str, params: dict | None = None, limit: int = 500) -> dict:
    """Run a parameterized, read-only SELECT query against Snowflake.

    Only SELECT statements against approved schemas (ANALYTICS/SEMANTIC) are permitted — see the
    explicit least-privilege comment in mcp/tools/snowflake.py (ADR-007). This tool will never
    accept INSERT/UPDATE/DELETE/MERGE/DDL, by design, not just by convention.

    Args:
        sql: a parameterized SELECT statement (use `%(name)s`-style bind params, never
            string-interpolated values).
        params: bind parameters referenced by `sql`.
        limit: hard row cap applied server-side regardless of the query's own LIMIT (default
            500).

    Returns:
        A dict with `rows` (list of dicts), `row_count` and `truncated` (bool).
    """
    return _query_snowflake(sql, params=params, limit=limit)


# ---------------------------------------------------------------------------
# Fiscal / tributário tools (ADR-015) — mcp/tools/fiscal.py
# ---------------------------------------------------------------------------


@mcp.tool()
def get_fiscal_quality() -> dict:
    """Fetch the synthetic fiscal_document dataset's current data quality score.

    Returns:
        A dict with `dataset`, `dq_score`, `as_of` and `worst_rule` (the lowest-scoring
        individual rule — real description text, e.g. "NCM code must be in the platform's
        catalog"). See mcp/tools/fiscal.py for the exact schema.
    """
    return _get_fiscal_quality()


@mcp.tool()
def get_fiscal_document(fiscal_document_id: str) -> dict:
    """Fetch one synthetic fiscal document plus its ground-truth tax discrepancy, if any.

    Args:
        fiscal_document_id: e.g. "NFE00000042".

    Returns:
        A dict with the document's NCM/CFOP/CST codes, `calculated_tax_total` (what the document
        shows), `correct_tax_total` (the ground-truth reference figure), `discrepancy_amount` and
        `discrepancy_reason`. See mcp/tools/fiscal.py for the exact schema.
    """
    return _get_fiscal_document(fiscal_document_id)


def main() -> None:
    """Entrypoint used by `python mcp/server/server.py`."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting enterprise-customer-intelligence MCP server (Sprint 13 skeleton)")
    mcp.run()


if __name__ == "__main__":
    main()
