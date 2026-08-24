"""Data quality and pipeline health tools for the MCP server.

Built in ROADMAP.md Sprint 13. Reads from `data_quality/reports/` (ROADMAP.md Sprint 3 — GX
Core suites publish `quality_report.json` + GX Data Docs + a `dq_score` per dataset, rolled up
into an overall platform score — ARCHITECTURE.md §7). These tools are what
`agents/quality/data_quality_agent.py` calls when it needs to diagnose a quality drop.

WIRED (this session): both tools below now read the real
`data_quality/reports/dq_report.json` produced by `data_quality/validators/report.py` via
`lakehouse/run_pipeline.py`, plus (for `get_customer_quality`) the real
`data/mdm/golden_record.parquet` and `data/lakehouse/quarantine/*.parquet` outputs. No new
module was created for this — the report's shape is simple enough that a couple of small,
locally-cached loader functions were enough; see `_load_dq_report()` / `_golden_record_df()` /
`_quarantine_df()` below.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DQ_REPORT_PATH = REPO_ROOT / "data_quality" / "reports" / "dq_report.json"
MDM_DIR = REPO_ROOT / "data" / "mdm"
QUARANTINE_DIR = REPO_ROOT / "data" / "lakehouse" / "quarantine"

# Quarantine parquet file -> the column that carries the CRM source customer id in that file.
# `crm_customer.parquet` uses its own primary key column; every downstream table quarantines on
# a foreign `customer_id` that (per data_quality/validators/engine.py's referential_integrity
# rule) always points back to a `crm_customer_id`.
_QUARANTINE_ID_COLUMNS: dict[str, str] = {
    "crm_customer.parquet": "crm_customer_id",
    "support_ticket.parquet": "customer_id",
    "web_event.parquet": "customer_id",
    "campaign_interaction.parquet": "customer_id",
    "payment_finance.parquet": "customer_id",
}

# rule.type -> which dq_report "dimension" bucket(s) it rolls up into, per the mapping the task
# brief specifies. `schema_check` deliberately counts toward both `completeness` (a missing/
# renamed column makes the row incomplete) and `schema` (it *is* the schema dimension).
_RULE_TYPE_TO_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "schema_check": ("completeness", "schema"),
    "not_null": ("completeness",),
    "valid_email": ("validity",),
    "valid_phone": ("validity",),
    "valid_date": ("validity",),
    "range_check": ("validity",),
    "unique": ("uniqueness",),
    "duplicate_rate": ("uniqueness",),
    "referential_integrity": ("referential_integrity",),
    "freshness": ("freshness",),
}

_EMPTY_DIMENSION_SCORES: dict[str, float | None] = {
    "completeness": None,
    "validity": None,
    "uniqueness": None,
    "referential_integrity": None,
    "freshness": None,
    "schema": None,
    "volume_anomaly": None,  # no rule type in data_quality/validators/engine.py maps here yet
}


@lru_cache(maxsize=1)
def _load_dq_report() -> dict[str, Any]:
    with open(DQ_REPORT_PATH, encoding="utf-8") as f:
        return json.load(f)


def _find_table(tables: list[dict[str, Any]], dataset: str) -> dict[str, Any] | None:
    """Resolve a `dataset` argument (e.g. "crm_customer", "silver.crm_customer",
    "silver.crm_customers") to one entry in the report's `tables` list.

    Registered table names are singular ("crm_customer") throughout the real pipeline
    (`lakehouse/run_pipeline.py::TABLE_ORDER`), but several docs/examples/golden-question fixtures
    written before the naming was finalized use the plural "crm_customers" — a code-review pass
    caught this breaking the Data Quality Agent's own canonical example end-to-end
    (`diagnose_quality_drop("silver.crm_customers")` silently returning no scores). Rather than
    hunt down and edit every doc reference, this resolver accepts the plural form defensively so
    the mismatch can never silently break a caller again, whichever form they use.
    """
    dataset_norm = dataset.strip().lower()
    # Accept a dotted qualifier ("silver.crm_customer") by matching on the last segment.
    short_name = dataset_norm.rsplit(".", 1)[-1]
    candidates = {dataset_norm, short_name}
    candidates |= {c[:-1] for c in candidates if c.endswith("s") and not c.endswith("ss")}
    for table in tables:
        name = str(table.get("table_name", "")).lower()
        if name in candidates:
            return table
    return None


def _worst_rule(rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The lowest-scoring individual rule (not a dimension bucket average) — the specific,
    real-description signal `agents/quality/root_cause_classifier.py` was actually trained on
    (rule-level text like "Non-null emails must be well-formed"), as opposed to the coarse
    "{dataset} {dimension}." string `data_quality_agent.py::_infer_main_cause` builds for display.
    A code-review pass caught the two being conflated — the classifier was silently fed the coarse
    string, far outside its training distribution. `get_data_quality()` now surfaces this
    separately so a caller can classify on the real thing."""
    scored = [r for r in rules if r.get("score") is not None]
    if not scored:
        return None
    return min(scored, key=lambda r: r["score"])


def _bucket_dimension_scores(rules: list[dict[str, Any]]) -> dict[str, float | None]:
    """Average each rule's `score` into the dimension bucket(s) its `type` maps to."""
    buckets: dict[str, list[float]] = {
        "completeness": [],
        "validity": [],
        "uniqueness": [],
        "referential_integrity": [],
        "freshness": [],
        "schema": [],
    }
    for rule in rules:
        for dim in _RULE_TYPE_TO_DIMENSIONS.get(rule.get("type"), ()):
            score = rule.get("score")
            if score is not None:
                buckets[dim].append(float(score))

    dims: dict[str, float | None] = {
        dim: (round(sum(scores) / len(scores), 4) if scores else None) for dim, scores in buckets.items()
    }
    dims["volume_anomaly"] = None
    return dims


@lru_cache(maxsize=1)
def _golden_record_df() -> pd.DataFrame:
    return pd.read_parquet(MDM_DIR / "golden_record.parquet")


@lru_cache(maxsize=None)
def _quarantine_df(filename: str) -> pd.DataFrame | None:
    path = QUARANTINE_DIR / filename
    if not path.exists():
        return None
    return pd.read_parquet(path)


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
    gr = _golden_record_df()
    match = gr[gr["master_customer_id"] == master_customer_id]
    if match.empty:
        return {
            "master_customer_id": master_customer_id,
            "dq_score": None,
            "field_flags": {},
            "found": False,
        }

    source_ids = [s.strip() for s in str(match.iloc[0]["source_customer_ids"]).split(";") if s.strip()]

    field_flags: dict[str, bool] = {}
    any_hit = False
    for filename, id_col in _QUARANTINE_ID_COLUMNS.items():
        q_df = _quarantine_df(filename)
        if q_df is None or q_df.empty:
            continue
        hits = q_df[q_df[id_col].isin(source_ids)]
        if hits.empty:
            continue
        any_hit = True
        for reasons in hits["_dq_failure_reasons"].dropna():
            # reason strings look like "valid_phone:phone" or "referential_integrity:customer_id"
            for reason in str(reasons).split(","):
                field = reason.strip().split(":")[-1] or reason.strip()
                field_flags[field] = True

    # Best-effort scoring, per the task brief: a hit in quarantine (this customer's own source
    # record, or a source record for one of its child tables, failed a hard DQ rule and was
    # quarantined) drags the per-customer score down; no hit means every source row that fed
    # this Golden Record passed every hard rule at ingestion time, so 1.0 is honest, not assumed.
    # NOTE (documented, not hidden): in this build no Golden Record actually has a hit — a
    # quarantined `crm_customer` row never survives into Silver, so it can never have been
    # merged into `golden_record.parquet` in the first place, and the four downstream
    # quarantine tables are 100% referential_integrity cascades from already-quarantined CRM
    # rows (see BUILD_LOG.md's WP1 entry). The join logic below is still real and will correctly
    # score a customer down for real if that data-shape assumption ever changes.
    dq_score = 0.5 if any_hit else 1.0

    return {
        "master_customer_id": master_customer_id,
        "dq_score": dq_score,
        "field_flags": field_flags,
        "found": True,
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
            "worst_rule": dict | None,  # the lowest-scoring individual rule — real rule.description
                                          # text, type, column, score — see _worst_rule()'s docstring
                                          # for why this exists separately from dimension_scores.
        }
    """
    report = _load_dq_report()
    as_of = report.get("generated_at")
    tables: list[dict[str, Any]] = report.get("tables", [])

    if dataset is None:
        all_rules = [rule for table in tables for rule in table.get("rules", [])]
        return {
            "dataset": None,
            "dq_score": report.get("overall_score"),
            "dimension_scores": _bucket_dimension_scores(all_rules),
            "as_of": as_of,
            "worst_rule": _worst_rule(all_rules),
        }

    table = _find_table(tables, dataset)
    if table is None:
        return {
            "dataset": dataset,
            "dq_score": None,
            "dimension_scores": dict(_EMPTY_DIMENSION_SCORES),
            "as_of": as_of,
            "worst_rule": None,
        }

    return {
        "dataset": dataset,
        "dq_score": table.get("score"),
        "dimension_scores": _bucket_dimension_scores(table.get("rules", [])),
        "as_of": as_of,
        "worst_rule": _worst_rule(table.get("rules", [])),
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
    # Left as-is per task scope: no live OTel/Prometheus source exists in this build.
    return {
        "pipeline": pipeline,
        "status": "unknown",
        "last_run_at": None,
        "duration_seconds": None,
        "rows_processed": None,
    }
