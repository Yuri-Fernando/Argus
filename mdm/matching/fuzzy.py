"""Tier 2 — Probabilistic / fuzzy matching (ARCHITECTURE.md §8).

Jaro-Winkler (name, email) + normalized Levenshtein (address) similarity,
plus exact-match booleans (phone, city, state). This module owns the
similarity-feature computation shared with the ML tier
(`mdm/matching/ml_model.py` imports `compute_features` from here — the ML
classifier is explicitly "a classifier over similarity features",
ARCHITECTURE.md §8 item 3) and a simple weighted-average `fuzzy_match_score`
used both as a standalone probabilistic matcher and as the baseline the ML
model is benchmarked against.

Candidate generation here blocks on `(state, soundex(surname),
first-initial)` — a phonetic key, see `_phonetic_key` — specifically so it
does NOT depend on email/phone/document_hash (that's the deterministic
tier's job). This lets the fuzzy/ML tiers stand on their own for the case
deterministic matching can't help with: two records that are the same
person but do not share any exact key value.
"""
from __future__ import annotations

import itertools
import logging
import unicodedata
from pathlib import Path

import jellyfish
import pandas as pd

logger = logging.getLogger("mdm.matching.fuzzy")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT = Path(__file__).resolve().parents[2]

FEATURE_COLUMNS = [
    "name_similarity",
    "email_similarity",
    "phone_match",
    "address_similarity",
    "city_match",
    "state_match",
]

# Fuzzy blocks bigger than this are collapsed via nearest-neighbor sampling
# rather than compared pairwise, to keep candidate generation tractable.
MAX_FUZZY_BLOCK = 40


def _norm_str(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NA:
        return ""
    return str(v).strip()


def name_similarity(a, b) -> float:
    a, b = _norm_str(a), _norm_str(b)
    if not a or not b:
        return 0.0
    return jellyfish.jaro_winkler_similarity(a.lower(), b.lower())


def email_similarity(a, b) -> float:
    a, b = _norm_str(a), _norm_str(b)
    if not a or not b:
        return 0.0
    return jellyfish.jaro_winkler_similarity(a.lower(), b.lower())


def address_similarity(a, b) -> float:
    a, b = _norm_str(a), _norm_str(b)
    if not a or not b:
        return 0.0
    a, b = a.lower(), b.lower()
    dist = jellyfish.levenshtein_distance(a, b)
    return 1.0 - dist / max(len(a), len(b))


def phone_match(a, b) -> bool:
    a, b = _norm_str(a), _norm_str(b)
    return bool(a) and bool(b) and a == b


def city_match(a, b) -> bool:
    a, b = _norm_str(a).lower(), _norm_str(b).lower()
    return bool(a) and bool(b) and a == b


def state_match(a, b) -> bool:
    a, b = _norm_str(a).lower(), _norm_str(b).lower()
    return bool(a) and bool(b) and a == b


def compute_features(row_a: pd.Series, row_b: pd.Series) -> dict:
    """The 6 similarity features listed in ARCHITECTURE.md §8 item 3."""
    return {
        "name_similarity": name_similarity(row_a.get("name"), row_b.get("name")),
        "email_similarity": email_similarity(row_a.get("email"), row_b.get("email")),
        "phone_match": phone_match(row_a.get("phone"), row_b.get("phone")),
        "address_similarity": address_similarity(row_a.get("address"), row_b.get("address")),
        "city_match": city_match(row_a.get("city"), row_b.get("city")),
        "state_match": state_match(row_a.get("state"), row_b.get("state")),
    }


# Weighted-average heuristic -- the "probabilistic/fuzzy" match score, and
# the baseline the ML classifier (mdm/matching/ml_model.py) is compared
# against. Name and email carry the most identity signal; the three
# boolean/location features are supporting evidence.
FUZZY_WEIGHTS = {
    "name_similarity": 0.40,
    "email_similarity": 0.30,
    "phone_match": 0.10,
    "address_similarity": 0.10,
    "city_match": 0.05,
    "state_match": 0.05,
}


def fuzzy_match_score(features: dict) -> float:
    score = 0.0
    for feat, weight in FUZZY_WEIGHTS.items():
        val = features[feat]
        score += weight * (float(val) if not isinstance(val, bool) else float(val))
    return score


# Faker's pt_BR name provider prefixes ~20% of names with an honorific
# ("Sr. João Silva", "Dra. Ana Costa"). Left in, the honorific becomes the
# blocking key's "first token" for a huge share of rows, collapsing them
# into a handful of giant, useless blocks (measured: max block size 99+
# before stripping). Strip it before computing the phonetic key.
_NAME_TITLES = {"sr.", "sra.", "srta.", "dr.", "dra.", "sr", "sra", "srta", "dr", "dra"}


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _real_name_tokens(name: str) -> list[str]:
    tokens = [t for t in name.split() if t.lower().strip(".") not in {t2.strip(".") for t2 in _NAME_TITLES}]
    return tokens or name.split()


def _phonetic_key(name) -> str:
    """(soundex(last real token), first letter of first real token).

    Empirically the blocking key with the best recall/precision trade-off
    for this dataset's name variants (title-stripped honorific, middle-name
    abbreviation, case swap, accent drop) -- measured 100% blocking recall
    against the 495 ground-truth pairs present in the input, at ~9k total
    within-block pairs (tractable), vs. 84% recall / ~1.8k pairs for a
    first+last NYSIIS composite key, or 100% recall / ~118k pairs for
    last-name soundex alone (too noisy/slow). See mdm/README.md.
    """
    name = _norm_str(name)
    if not name:
        return ""
    tokens = _real_name_tokens(name)
    first, last = tokens[0], tokens[-1]
    try:
        last_key = jellyfish.soundex(last)
    except Exception:
        last_key = last.lower()[:4]
    first_char = _strip_accents(first.lower())[:1] if first else ""
    return f"{last_key}|{first_char}"


def generate_fuzzy_candidates(
    df: pd.DataFrame,
    exclude_pairs: set[tuple[str, str]] | None = None,
    min_score: float = 0.45,
) -> pd.DataFrame:
    """Block on (state, NYSIIS(first name token)), score every within-block
    pair, and keep those at or above `min_score`.

    `exclude_pairs` lets the caller skip pairs already resolved by the
    deterministic tier (recomputing them here would be wasted work).
    """
    exclude_pairs = exclude_pairs or set()
    df = df.copy()
    df["_phonetic"] = df["name"].map(_phonetic_key)
    idx_by_id = df.set_index("crm_customer_id", drop=False)

    rows = []
    n_blocks = 0
    n_pairs_scored = 0
    for (_state, _phon), group in df.groupby(["state", "_phonetic"]):
        if len(group) < 2 or not _phon:
            continue
        ids = group["crm_customer_id"].tolist()
        if len(ids) > MAX_FUZZY_BLOCK:
            logger.warning(
                "Fuzzy block (state=%s, nysiis=%s) has %d rows -- truncating to first %d",
                _state, _phon, len(ids), MAX_FUZZY_BLOCK,
            )
            ids = ids[:MAX_FUZZY_BLOCK]
        n_blocks += 1
        for a, b in itertools.combinations(sorted(ids), 2):
            if (a, b) in exclude_pairs:
                continue
            n_pairs_scored += 1
            row_a, row_b = idx_by_id.loc[a], idx_by_id.loc[b]
            feats = compute_features(row_a, row_b)
            score = fuzzy_match_score(feats)
            if score >= min_score:
                rows.append({"id_1": a, "id_2": b, **feats, "fuzzy_match_score": score})

    result = pd.DataFrame(rows, columns=["id_1", "id_2", *FEATURE_COLUMNS, "fuzzy_match_score"])
    logger.info(
        "Fuzzy tier: %d phonetic blocks, %d pairs scored, %d candidates >= %.2f",
        n_blocks, n_pairs_scored, len(result), min_score,
    )
    return result


def main() -> None:
    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from mdm.matching.deterministic import find_deterministic_pairs, load_customers

    df, source = load_customers()
    det_pairs = find_deterministic_pairs(df)
    exclude = set(zip(det_pairs["id_1"], det_pairs["id_2"]))
    fuzzy_pairs = generate_fuzzy_candidates(df, exclude_pairs=exclude)

    out_dir = ROOT / "data" / "mdm"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "candidate_pairs_fuzzy.parquet"
    fuzzy_pairs.to_parquet(out_path, index=False)
    print(f"Input: {source} ({len(df)} rows)")
    print(f"Fuzzy candidate pairs: {len(fuzzy_pairs)} -> {out_path}")
    if len(fuzzy_pairs):
        print(fuzzy_pairs["fuzzy_match_score"].describe().to_string())


if __name__ == "__main__":
    main()
