"""Entity Resolution pipeline evaluation vs. the labeled ground truth.

Pair-level precision/recall/F1: every cluster with >=2 members contributes
all its pairwise combinations as "predicted duplicate pairs"; these are
compared against the true pair set derived from
`crm_customers_ground_truth.csv` (`customer_id, duplicate_of_customer_id`).

This is a different (and stricter/more end-to-end) metric than the
train/test classification metrics in `mdm/matching/ml_model.py` -- it
scores the *whole pipeline's clustering decision* (deterministic auto-match
+ ML auto-match -> union-find merge), not just the classifier in isolation.

Target: recall >= 0.85 (mdm/README.md / task brief). Reported honestly
either way.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
GROUND_TRUTH_PATH = ROOT / "data" / "synthetic" / "crm" / "crm_customers_ground_truth.csv"


def load_true_pairs(ids_present: set[str] | None = None) -> tuple[set[tuple[str, str]], int]:
    """Returns (true_pair_set, n_excluded_missing_from_input)."""
    gt = pd.read_csv(GROUND_TRUTH_PATH, dtype=str)
    excluded = 0
    pairs = set()
    for row in gt.itertuples():
        a, b = row.customer_id, row.duplicate_of_customer_id
        if ids_present is not None and (a not in ids_present or b not in ids_present):
            excluded += 1
            continue
        pairs.add(tuple(sorted((a, b))))
    return pairs, excluded


def predicted_pairs_from_clusters(clusters: dict[str, list[str]]) -> set[tuple[str, str]]:
    pairs = set()
    for member_ids in clusters.values():
        if len(member_ids) < 2:
            continue
        for a, b in itertools.combinations(sorted(member_ids), 2):
            pairs.add((a, b))
    return pairs


def evaluate_clusters(
    clusters: dict[str, list[str]], ids_present: set[str] | None = None
) -> dict:
    true_pairs, n_excluded = load_true_pairs(ids_present)
    predicted_pairs = predicted_pairs_from_clusters(clusters)

    tp = predicted_pairs & true_pairs
    fp = predicted_pairs - true_pairs
    fn = true_pairs - predicted_pairs

    precision = len(tp) / len(predicted_pairs) if predicted_pairs else 0.0
    recall = len(tp) / len(true_pairs) if true_pairs else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "n_true_pairs": len(true_pairs),
        "n_true_pairs_excluded_missing_from_input": n_excluded,
        "n_predicted_pairs": len(predicted_pairs),
        "true_positive_pairs": len(tp),
        "false_positive_pairs": len(fp),
        "false_negative_pairs": len(fn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "meets_recall_target_0.85": recall >= 0.85,
        "false_negative_examples": sorted(fn)[:20],
        "false_positive_examples": sorted(fp)[:20],
    }


def print_report(metrics: dict) -> None:
    print("\n=== Entity Resolution pipeline vs. ground truth (pair-level) ===")
    print(f"True pairs in ground truth: {metrics['n_true_pairs']} "
          f"(+{metrics['n_true_pairs_excluded_missing_from_input']} excluded -- not present in input data)")
    print(f"Predicted pairs (from merged clusters): {metrics['n_predicted_pairs']}")
    print(f"TP={metrics['true_positive_pairs']}  FP={metrics['false_positive_pairs']}  FN={metrics['false_negative_pairs']}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}  (target >= 0.85 -> {'MET' if metrics['meets_recall_target_0.85'] else 'NOT MET'})")
    print(f"F1:        {metrics['f1']:.4f}")
    if metrics["false_negative_examples"]:
        print(f"Sample false negatives (missed true dupes): {metrics['false_negative_examples'][:5]}")
    if metrics["false_positive_examples"]:
        print(f"Sample false positives (wrongly merged): {metrics['false_positive_examples'][:5]}")
