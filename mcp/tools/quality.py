"""Data quality and pipeline health tools for the MCP server.

Built in ROADMAP.md Sprint 13. Reads from `data_quality/reports/` (ROADMAP.md Sprint 3 — GX
Core suites publish `quality_report.json` + GX Data Docs + a `dq_score` per dataset, rolled up
into an overall platform score — ARCHITECTURE.md §7). These tools are what
`agents/quality/data_quality_agent.py` calls when it needs to diagnose a quality drop.
"""

from __future__ import annotations

from typing import Any


def get_customer_quality(master_customer_id: str) -> dict[str, Any]:
    """Fetch the data quality profile for a single customer's Golden Record.

    Args:
        master_customer_id: the MDM-assigned survivor ID.

    Returns:
        {
            "master_customer_id": str,
            "dq_score": float | None,       # 0.0-1.0
            "field_flags": dict[str, bool],  # e.g. {"email": True, "phone": False, ...}
            "found": bool,
        }
    """
    # TODO(Sprint 3 / data_quality): join `data_quality/reports/` row-level results (or the
    # Databricks Data Quality Monitoring profiling output, ARCHITECTURE.md §7) back to this
    # customer's source records via `mdm/golden_record/` survivorship log, so the score
    # reflects the specific rows that survived into this Golden Record.
    return {
        "master_customer_id": master_customer_id,
        "dq_score": None,
        "field_flags": {},
        "found": False,
    }


def get_data_quality(dataset: str | None = None) -> dict[str, Any]:
    """Fetch the platform's current data quality score(s).

    Args:
        dataset: optional dataset name (e.g. "silver.customer"). Omit for the overall
            platform-level rollup.

    Returns:
        {
            "dataset": str | None,
            "dq_score": float | None,
            "dimension_scores": {
                "completeness": float | None,
                "validity": float | None,
                "uniqueness": float | None,
                "referential_integrity": float | None,
                "freshness": float | None,
                "schema": float | None,
                "volume_anomaly": float | None,
            },
            "as_of": str | None,   # ISO-8601 timestamp of the report this was read from
        }
    """
    # TODO(Sprint 3 / data_quality): read the latest `quality_report.json` from
    # `data_quality/reports/` (per-dataset when `dataset` is given, else the platform rollup).
    # This is the same source the "Data Quality" Power BI page reads (ARCHITECTURE.md §13), so
    # an agent's answer and the dashboard should never disagree.
    return {
        "dataset": dataset,
        "dq_score": None,
        "dimension_scores": {
            "completeness": None,
            "validity": None,
            "uniqueness": None,
            "referential_integrity": None,
            "freshness": None,
            "schema": None,
            "volume_anomaly": None,
        },
        "as_of": None,
    }


def get_pipeline_status(pipeline: str | None = None) -> dict[str, Any]:
    """Fetch the last-run status of a data pipeline / job / DQ checkpoint.

    Args:
        pipeline: optional pipeline/job name (e.g. "bronze_to_silver_crm"). Omit for a summary
            across all tracked pipelines.

    Returns:
        {
            "pipeline": str | None,
            "status": str | None,          # "success" | "failed" | "running" | "unknown"
            "last_run_at": str | None,     # ISO-8601
            "duration_seconds": float | None,
            "rows_processed": int | None,
        }
    """
    # TODO(Sprint 16 / monitoring): read from the OpenTelemetry-instrumented pipeline run log
    # exported to Prometheus (ARCHITECTURE.md §17), or, if that's not yet wired, from
    # Databricks Workflows / Asset Bundle job run history directly. Monitoring Agent
    # (agents/monitoring/monitoring_agent.py) is the primary consumer of this tool.
    return {
        "pipeline": pipeline,
        "status": "unknown",
        "last_run_at": None,
        "duration_seconds": None,
        "rows_processed": None,
    }
