"""Entity Resolution orchestration -- `make mdm` / `python mdm/entity_resolution/run.py`.

Wires the three matching tiers + golden record together:

1. **Deterministic** (`mdm/matching/deterministic.py`) -- exact match on
   email/phone/document_hash. `strong` pairs (phone or document_hash) are
   trusted as AUTO_MATCH directly. `email`-only pairs are demoted to
   candidates for tier 2/3 -- see that module's docstring for why (Faker
   email collisions are 100% false positives in this dataset).
2. **Fuzzy** (`mdm/matching/fuzzy.py`) -- phonetic-blocked near-miss
   candidates that share no exact key at all.
3. **ML** (`mdm/matching/ml_model.py`) -- RandomForest scores every
   tier-1-weak and tier-2 candidate pair; decision bands from
   ARCHITECTURE.md §8 (`>=0.90 AUTO_MATCH`, `0.55-0.90 HUMAN_REVIEW`,
   `<0.55 DISTINCT`).
4. **Union-find** merges every AUTO_MATCH pair (tier 1 strong + tier 3)
   into clusters; singleton customers become 1-member clusters.
5. **Golden Record** (`mdm/golden_record/build.py`) applies survivorship
   rules per cluster and writes the audit log.
6. **Evaluation** (`mdm/entity_resolution/evaluation/evaluate.py`) scores
   the resulting clusters against the labeled ground truth.

Outputs under `data/mdm/`:
  - `candidate_pairs_deterministic.parquet`
  - `candidate_pairs_fuzzy.parquet`
  - `scored_candidates_ml.parquet`
  - `human_review_queue.parquet`
  - `clusters.parquet` (crm_customer_id -> master_customer_id)
  - `golden_record.parquet`
And `mdm/golden_record/survivorship_log/survivorship_log.csv`.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mdm.entity_resolution.evaluation.evaluate import evaluate_clusters, print_report  # noqa: E402
from mdm.golden_record.build import build_golden_records, write_survivorship_log  # noqa: E402
from mdm.matching.deterministic import find_deterministic_pairs, load_customers  # noqa: E402
from mdm.matching.fuzzy import compute_features, generate_fuzzy_candidates  # noqa: E402
from mdm.matching.ml_model import build_labeled_dataset, train_and_evaluate  # noqa: E402

logger = logging.getLogger("mdm.entity_resolution.run")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

OUT_DIR = ROOT / "data" / "mdm"

AUTO_MATCH_THRESHOLD = 0.90
HUMAN_REVIEW_THRESHOLD = 0.55


class UnionFind:
    def __init__(self, ids: list[str]):
        self.parent = {i: i for i in ids}

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # Deterministic tie-break so cluster IDs are stable across runs.
            if ra < rb:
                self.parent[rb] = ra
            else:
                self.parent[ra] = rb


def run() -> dict:
    logger.info("=== Entity Resolution: loading customers ===")
    df, source = load_customers()
    logger.info("Input: %s (%d rows)", source, len(df))

    # --- Tier 1: deterministic ---
    det_pairs = find_deterministic_pairs(df)
    strong_pairs = det_pairs[det_pairs["strong"]]
    weak_pairs = det_pairs[~det_pairs["strong"]]

    # --- Tier 2: fuzzy candidate generation (excludes all deterministic pairs) ---
    exclude = set(zip(det_pairs["id_1"], det_pairs["id_2"]))
    fuzzy_pairs = generate_fuzzy_candidates(df, exclude_pairs=exclude, min_score=0.45)

    # --- Tier 3: ML scoring of (deterministic-weak + fuzzy) candidates ---
    logger.info("=== Training ML classifier (tracked in MLflow) ===")
    training_dataset = build_labeled_dataset(df)
    model, ml_metrics = train_and_evaluate(training_dataset, run_name="rf_match_classifier_pipeline_run")

    idx = df.set_index("crm_customer_id", drop=False)
    ml_candidates = pd.concat(
        [
            weak_pairs[["id_1", "id_2"]],
            fuzzy_pairs[["id_1", "id_2"]] if len(fuzzy_pairs) else pd.DataFrame(columns=["id_1", "id_2"]),
        ],
        ignore_index=True,
    ).drop_duplicates()

    from mdm.matching.fuzzy import FEATURE_COLUMNS as _FEATURE_COLUMNS

    feat_rows = [
        {"id_1": row.id_1, "id_2": row.id_2, **compute_features(idx.loc[row.id_1], idx.loc[row.id_2])}
        for row in ml_candidates.itertuples(index=False)
    ]
    scored_ml = pd.DataFrame(feat_rows, columns=["id_1", "id_2", *_FEATURE_COLUMNS])
    if len(scored_ml):
        proba = model.predict_proba(scored_ml[_FEATURE_COLUMNS].astype(float))[:, 1]
        scored_ml["match_probability"] = proba
        scored_ml["tier"] = "ml"
        scored_ml["decision"] = pd.cut(
            proba,
            bins=[-1, HUMAN_REVIEW_THRESHOLD, AUTO_MATCH_THRESHOLD, 2],
            labels=["DISTINCT", "HUMAN_REVIEW", "AUTO_MATCH"],
            right=False,
        ).astype(str)
    else:
        scored_ml["match_probability"] = pd.Series(dtype=float)
        scored_ml["tier"] = pd.Series(dtype=str)
        scored_ml["decision"] = pd.Series(dtype=str)

    ml_auto_match = scored_ml[scored_ml["decision"] == "AUTO_MATCH"] if len(scored_ml) else pd.DataFrame(columns=["id_1", "id_2"])
    human_review = scored_ml[scored_ml["decision"] == "HUMAN_REVIEW"] if len(scored_ml) else pd.DataFrame(columns=["id_1", "id_2"])
    logger.info(
        "ML tier: %d candidates scored -> %d AUTO_MATCH, %d HUMAN_REVIEW, %d DISTINCT",
        len(scored_ml), len(ml_auto_match), len(human_review), len(scored_ml) - len(ml_auto_match) - len(human_review),
    )

    # --- Union-find merge: deterministic-strong + ML AUTO_MATCH ---
    uf = UnionFind(df["crm_customer_id"].tolist())
    for row in strong_pairs.itertuples(index=False):
        uf.union(row.id_1, row.id_2)
    for row in ml_auto_match.itertuples(index=False):
        uf.union(row.id_1, row.id_2)

    clusters: dict[str, list[str]] = {}
    for cid in df["crm_customer_id"]:
        root = uf.find(cid)
        clusters.setdefault(root, []).append(cid)
    # Stable, readable master IDs instead of raw root crm_customer_id.
    master_id_map = {root: f"MC{i:08d}" for i, root in enumerate(sorted(clusters))}
    clusters = {master_id_map[root]: members for root, members in clusters.items()}

    n_multi = sum(1 for m in clusters.values() if len(m) > 1)
    logger.info("Clusters: %d total (%d multi-record, %d singletons)", len(clusters), n_multi, len(clusters) - n_multi)

    # --- Golden Record ---
    golden_df, survivorship_log_df = build_golden_records(df, clusters)
    write_survivorship_log(survivorship_log_df)

    # --- Evaluation vs. ground truth ---
    metrics = evaluate_clusters(clusters, ids_present=set(df["crm_customer_id"]))
    print_report(metrics)

    # --- Persist outputs ---
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    det_pairs.to_parquet(OUT_DIR / "candidate_pairs_deterministic.parquet", index=False)
    fuzzy_pairs.to_parquet(OUT_DIR / "candidate_pairs_fuzzy.parquet", index=False)
    scored_ml.to_parquet(OUT_DIR / "scored_candidates_ml.parquet", index=False)
    human_review.to_parquet(OUT_DIR / "human_review_queue.parquet", index=False)
    clusters_df = pd.DataFrame(
        [{"crm_customer_id": cid, "master_customer_id": mid} for mid, members in clusters.items() for cid in members]
    )
    clusters_df.to_parquet(OUT_DIR / "clusters.parquet", index=False)
    golden_df.to_parquet(OUT_DIR / "golden_record.parquet", index=False)

    logger.info("Golden record: %d master_customer_id rows -> %s", len(golden_df), OUT_DIR / "golden_record.parquet")

    return {
        "n_input_rows": len(df),
        "n_clusters": len(clusters),
        "n_multi_record_clusters": n_multi,
        "n_deterministic_strong_pairs": len(strong_pairs),
        "n_deterministic_weak_pairs": len(weak_pairs),
        "n_fuzzy_candidates": len(fuzzy_pairs),
        "n_ml_auto_match": len(ml_auto_match),
        "n_ml_human_review": len(human_review),
        "ml_metrics": ml_metrics,
        "evaluation": metrics,
        "clusters": clusters,
    }


def main() -> None:
    result = run()
    print("\n=== Pipeline summary ===")
    print(f"Input rows: {result['n_input_rows']}")
    print(f"Clusters: {result['n_clusters']} ({result['n_multi_record_clusters']} multi-record)")
    print(f"Deterministic: {result['n_deterministic_strong_pairs']} strong AUTO_MATCH, "
          f"{result['n_deterministic_weak_pairs']} email-only deferred")
    print(f"Fuzzy candidates generated: {result['n_fuzzy_candidates']}")
    print(f"ML: {result['n_ml_auto_match']} AUTO_MATCH, {result['n_ml_human_review']} HUMAN_REVIEW")


if __name__ == "__main__":
    main()
