"""Customer / Golden Record / churn / duplicates business logic.

Reads the parquet outputs other workstreams already produced (`data/mdm/`, `data/ml/`) directly
with pandas — this project's `data/` products are the source of truth, not a live database, so
each service function is a thin, cached parquet read + lookup, mirroring the query logic
`mcp/tools/customer.py`'s stub contracts describe for the equivalent MCP tools.

`register_customer` is the one write path: it appends to an in-process intake list (not a
parquet file — this API layer doesn't own the MDM pipeline's input format) so `POST /customer`
has somewhere real to write to and `GET` immediately after a `POST` in the same process reflects
it, without reaching into `mdm/`'s (read-only, out-of-scope) ingestion path.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
MDM_DIR = REPO_ROOT / "data" / "mdm"
ML_FEATURES_DIR = REPO_ROOT / "data" / "ml" / "features"
ML_SEGMENTS_DIR = REPO_ROOT / "data" / "ml" / "segmentation"

# In-process intake store for POST /customer — see module docstring for why this isn't a parquet
# write. Cleared on process restart, which is fine for a demo/local-dev API surface.
_REGISTERED_CUSTOMERS: list[dict] = []


@lru_cache(maxsize=1)
def _golden_record_df() -> pd.DataFrame:
    return pd.read_parquet(MDM_DIR / "golden_record.parquet")


@lru_cache(maxsize=1)
def _features_df() -> pd.DataFrame:
    return pd.read_parquet(ML_FEATURES_DIR / "customer_features.parquet")


@lru_cache(maxsize=1)
def _segments_df() -> pd.DataFrame:
    return pd.read_parquet(ML_SEGMENTS_DIR / "customer_segments.parquet")


@lru_cache(maxsize=1)
def _duplicate_pairs_df() -> pd.DataFrame:
    # candidate_pairs_deterministic.parquet carries a `decision` column distinguishing confirmed
    # matches (AUTO_MATCH) from pairs still needing review (PENDING_FUZZY_ML) — exactly the
    # "candidate/confirmed duplicate pairs" this endpoint is meant to expose, per mdm/matching/.
    return pd.read_parquet(MDM_DIR / "candidate_pairs_deterministic.parquet")


def register_customer(name: str, email: str, phone: str, city: str | None, state: str | None) -> dict:
    """Append a new source-system customer record to the intake list.

    Returns the stored record, including a generated `source_customer_id` (this API layer's own
    id namespace — `API` prefix, distinct from `mdm/`'s `CRM*` source ids and `MC*` Golden Record
    ids, so it's never mistaken for either).
    """
    record = {
        "source_customer_id": f"API{uuid.uuid4().hex[:10].upper()}",
        "name": name,
        "email": email,
        "phone": phone,
        "city": city,
        "state": state,
        "registered_at": datetime.now(timezone.utc),
    }
    _REGISTERED_CUSTOMERS.append(record)
    return record


def list_registered_customers() -> list[dict]:
    """Return every customer registered via `POST /customer` this process has seen."""
    return list(_REGISTERED_CUSTOMERS)


def get_golden_record(master_customer_id: str) -> dict:
    """Look up one customer's Golden Record by `master_customer_id`."""
    df = _golden_record_df()
    match = df[df["master_customer_id"] == master_customer_id]
    if match.empty:
        return {
            "master_customer_id": master_customer_id,
            "canonical_name": None,
            "canonical_email": None,
            "canonical_phone": None,
            "city": None,
            "state": None,
            "source_record_count": None,
            "created_at": None,
            "updated_at": None,
            "found": False,
        }
    row = match.iloc[0]
    return {
        "master_customer_id": row["master_customer_id"],
        "canonical_name": row["canonical_name"],
        "canonical_email": row["canonical_email"],
        "canonical_phone": row["canonical_phone"],
        "city": row.get("city"),
        "state": row.get("state"),
        "source_record_count": int(row["source_record_count"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "found": True,
    }


def get_churn_score(master_customer_id: str) -> dict:
    """Compute one customer's churn score + segment.

    `churn_score` mirrors the recency-based proxy formula used in
    `snowflake/local_runner.py::build_warehouse` (`min(recency_days / 365, 1.0)`) — there is no
    `ml/churn/` model-output parquet in this snapshot, so both this endpoint and `GET /metrics`
    (via `churn_rate`) derive from the same documented proxy rather than two different numbers
    claiming to answer the same question.
    """
    features = _features_df()
    segments = _segments_df()

    feat_match = features[features["master_customer_id"] == master_customer_id]
    seg_match = segments[segments["master_customer_id"] == master_customer_id]

    if feat_match.empty:
        return {"master_customer_id": master_customer_id, "found": False}

    feat_row = feat_match.iloc[0]
    # `local_runner.py::build_warehouse()` fills a missing recency_days with 365 (a full year —
    # i.e. treated as maximally stale) before dividing; this endpoint previously skipped that
    # `fillna` step, which a code-review pass flagged two ways: (1) the formulas silently diverge
    # for any customer with a null recency_days, and (2) worse, `int(float("nan"))` raises
    # ValueError — so this endpoint would 500 for exactly the customers whose churn score matters
    # most to compute (no settled-payment activity at all). Matching the fillna fixes both.
    raw_recency = feat_row["recency_days"]
    recency_days = int(raw_recency) if pd.notna(raw_recency) else 365
    churn_score = round(min(recency_days / 365.0, 1.0), 4)

    result = {
        "master_customer_id": master_customer_id,
        "found": True,
        "churn_score": churn_score,
        "recency_days": recency_days,
        "frequency": int(feat_row["frequency"]),
        "monetary": float(feat_row["monetary"]),
        "segment": None,
        "cluster": None,
    }
    if not seg_match.empty:
        seg_row = seg_match.iloc[0]
        result["segment"] = seg_row["segment"]
        result["cluster"] = int(seg_row["cluster"])
    return result


def get_duplicate_pairs(decision: str | None = None, limit: int = 50) -> dict:
    """Return MDM candidate/confirmed duplicate pairs, optionally filtered by `decision`.

    Args:
        decision: filter to one decision value (e.g. `AUTO_MATCH` for confirmed duplicates,
            `PENDING_FUZZY_ML` for candidates still needing human/ML review). `None` returns both.
        limit: maximum pairs returned (bounded server-side, same least-privilege spirit as
            `mcp/tools/customer.py::search_customers`).
    """
    df = _duplicate_pairs_df()
    if decision:
        df = df[df["decision"] == decision]

    total = len(df)
    limit = min(limit, 200)
    subset = df.head(limit)

    pairs = [
        {
            "id_1": row["id_1"],
            "id_2": row["id_2"],
            "decision": row["decision"],
            "n_keys": int(row["n_keys"]) if pd.notna(row.get("n_keys")) else None,
            "match_probability": float(row["match_probability"]) if pd.notna(row.get("match_probability")) else None,
            "strong": bool(row["strong"]) if pd.notna(row.get("strong")) else None,
            "tier": row.get("tier"),
        }
        for _, row in subset.iterrows()
    ]
    return {"total": total, "returned": len(pairs), "pairs": pairs}
