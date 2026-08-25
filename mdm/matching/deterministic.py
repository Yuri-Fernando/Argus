"""Tier 1 — Deterministic matching (ARCHITECTURE.md §8 / mdm/README.md).

Exact match on `email`, `phone`, or `document_hash`, blocked (grouped) per
key so we never do an O(n^2) full scan.

Also owns loading the matching input table: prefers the cleaner Silver
output produced by `lakehouse/silver/crm_customer.py`
(`data/lakehouse/silver/crm_customer.parquet`) and falls back to the raw
synthetic CSV (`data/synthetic/crm/crm_customers.csv`) if Silver hasn't been
built yet.

Empirical finding from running this on the synthetic data (see
mdm/entity_resolution/evaluation/ report and mdm/README.md): treating an
exact-match on all three keys as equally trustworthy is WRONG for this
dataset. Faker's `pt_BR` email provider draws from a small pool at n=10.5k
rows, so plain email collisions between two otherwise-unrelated customers
are common (measured: 505 of 990 raw email-collision pairs — *all* of them
— are false positives with zero ground-truth overlap). `phone` and
`document_hash` collisions are the reliable signal (measured: union of the
two gives 99% recall against the labeled ground truth at 97% precision).
So this module tags every candidate pair with which key(s) it matched on
and a `strong` flag (`phone` or `document_hash`), and leaves the
AUTO_MATCH/HUMAN_REVIEW decision on `email`-only pairs to the
fuzzy+ML tiers instead of trusting the raw key match.
"""
from __future__ import annotations

import itertools
import logging
from collections import defaultdict
from pathlib import Path

import pandas as pd

logger = logging.getLogger("mdm.matching.deterministic")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT = Path(__file__).resolve().parents[2]
SILVER_PARQUET = ROOT / "data" / "lakehouse" / "silver" / "crm_customer.parquet"
RAW_CSV = ROOT / "data" / "synthetic" / "crm" / "crm_customers.csv"

DETERMINISTIC_KEYS = ["email", "phone", "document_hash"]
# phone/document_hash collisions are near-certain true matches in this
# dataset (measured precision 97-100%); email-alone collisions are noise
# (measured precision 0%) — see module docstring.
STRONG_KEYS = {"phone", "document_hash"}

# Groups larger than this are almost certainly a low-cardinality key
# collision (e.g. a shared placeholder value) rather than genuine
# duplicate customers. Skip them so one bad block doesn't emit O(n^2) junk.
MAX_BLOCK_SIZE = 8


def load_customers() -> tuple[pd.DataFrame, str]:
    """Load the CRM customer table for matching.

    Returns (dataframe, source_label) so downstream reporting can say which
    input was actually used.
    """
    if SILVER_PARQUET.exists():
        df = pd.read_parquet(SILVER_PARQUET)
        source = "silver:crm_customer.parquet"
        logger.info("Loaded %d rows from Silver (%s)", len(df), SILVER_PARQUET)
    elif RAW_CSV.exists():
        df = pd.read_csv(RAW_CSV, dtype=str)
        df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
        # Mirror Silver's standardization so deterministic/fuzzy features are
        # computed the same way regardless of which input was available.
        df["email"] = df["email"].str.strip().str.lower().replace({"": None, "nan": None})
        df["phone"] = df["phone"].str.replace(r"\D", "", regex=True).replace({"": None})
        df["name"] = df["name"].str.strip().str.replace(r"\s+", " ", regex=True).str.title()
        df["city"] = df["city"].str.strip().str.replace(r"\s+", " ", regex=True).str.title()
        df["state"] = df["state"].str.strip().str.upper()
        source = "raw:crm_customers.csv (Silver not found -- degraded fallback)"
        logger.warning("Silver parquet not found at %s -- falling back to raw CSV", SILVER_PARQUET)
    else:
        raise FileNotFoundError(
            f"Neither {SILVER_PARQUET} nor {RAW_CSV} exist -- no CRM input data available."
        )
    df = df.reset_index(drop=True)
    df["crm_customer_id"] = df["crm_customer_id"].astype(str)
    return df, source


def _pairs_from_blocks(df: pd.DataFrame, key: str) -> set[tuple[str, str]]:
    """All (id_1, id_2) combinations within each non-null value of `key`."""
    pairs: set[tuple[str, str]] = set()
    valid = df[df[key].notna() & (df[key].astype(str).str.len() > 0)]
    for value, group in valid.groupby(key):
        ids = group["crm_customer_id"].tolist()
        if len(ids) < 2:
            continue
        if len(ids) > MAX_BLOCK_SIZE:
            logger.warning(
                "Skipping oversized deterministic block on %s=%r (%d rows) -- likely a bad key, not real duplicates",
                key, value, len(ids),
            )
            continue
        for a, b in itertools.combinations(sorted(ids), 2):
            pairs.add((a, b))
    return pairs


def find_deterministic_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """Exact-match candidate pairs on email / phone / document_hash.

    Returns a DataFrame with one row per unique (id_1, id_2) pair and
    columns: `id_1, id_2, match_keys, n_keys, strong, tier,
    match_probability, decision`. `strong=True` pairs (matched via phone
    and/or document_hash) are decided AUTO_MATCH here. `strong=False`
    pairs (email-only) are marked HUMAN_REVIEW-eligible/PENDING and left
    for the fuzzy+ML tiers to actually score.
    """
    keys_by_pair: dict[tuple[str, str], set[str]] = defaultdict(set)
    per_key_counts: dict[str, int] = {}
    for key in DETERMINISTIC_KEYS:
        found = _pairs_from_blocks(df, key)
        per_key_counts[key] = len(found)
        for pair in found:
            keys_by_pair[pair].add(key)

    rows = []
    for (a, b), keys in sorted(keys_by_pair.items()):
        strong = bool(keys & STRONG_KEYS)
        rows.append(
            {
                "id_1": a,
                "id_2": b,
                "match_keys": ",".join(sorted(keys)),
                "n_keys": len(keys),
                "strong": strong,
                "tier": "deterministic",
                "match_probability": 1.0 if strong else float("nan"),
                "decision": "AUTO_MATCH" if strong else "PENDING_FUZZY_ML",
            }
        )
    result = pd.DataFrame(
        rows,
        columns=["id_1", "id_2", "match_keys", "n_keys", "strong", "tier", "match_probability", "decision"],
    )
    n_strong = int(result["strong"].sum()) if len(result) else 0
    logger.info(
        "Deterministic tier: %d unique candidate pairs (raw per-key: email=%d, phone=%d, document_hash=%d) "
        "-- %d strong (AUTO_MATCH), %d email-only (deferred to fuzzy+ML)",
        len(result), per_key_counts.get("email", 0), per_key_counts.get("phone", 0),
        per_key_counts.get("document_hash", 0), n_strong, len(result) - n_strong,
    )
    return result


def main() -> None:
    df, source = load_customers()
    pairs = find_deterministic_pairs(df)
    out_dir = ROOT / "data" / "mdm"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "candidate_pairs_deterministic.parquet"
    pairs.to_parquet(out_path, index=False)
    print(f"Input: {source} ({len(df)} rows)")
    print(f"Deterministic candidate pairs: {len(pairs)} -> {out_path}")
    print(f"  strong (AUTO_MATCH, phone/document_hash): {int(pairs['strong'].sum())}")
    print(f"  email-only (deferred to fuzzy+ML): {int((~pairs['strong']).sum())}")


if __name__ == "__main__":
    main()
