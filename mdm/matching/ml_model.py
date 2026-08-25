"""Tier 3 — ML-based matching (ARCHITECTURE.md §8 item 3).

RandomForest classifier over the 6 similarity features
(`mdm/matching/fuzzy.py:compute_features`) -> `match_probability`, tracked
in MLflow with a local file store (no server required).

Dataset construction (labeled from `crm_customers_ground_truth.csv`):
- Positives: the ~495 ground-truth duplicate pairs actually present in the
  loaded customer table (some of the 500 are absent because Silver dropped
  a handful of byte-identical ingestion duplicates upstream -- see
  mdm/README.md).
- Negatives, three kinds, to make the training/test distribution look like
  the real candidate pool the pipeline will score at inference time:
    1. "hard" negatives -- pairs from the fuzzy phonetic blocking step
       (same state + surname-soundex + first-initial block, different
       people). These are the near-misses the fuzzy tier's own blocking
       surfaces.
    2. "email-collision" negatives -- the deterministic tier's email-only
       matches. Empirically **100% of these are false positives** in this
       dataset (Faker's `pt_BR` email provider collides at n=10.5k rows);
       they are an excellent hard-negative source and a real test of
       whether the model has learned to require more than one weak signal.
    3. "random" easy negatives -- uniformly sampled pairs sharing no block,
       for class balance and to keep the model honest on obviously-distinct
       pairs.

Train/test is a stratified split; the "fuzzy-only baseline" is
`fuzzy_match_score >= threshold`, with `threshold` chosen on the TRAIN
split (best F1) and then applied, unchanged, to the held-out TEST split --
exactly like the RandomForest, so the two are compared fairly.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mdm.matching.deterministic import find_deterministic_pairs, load_customers  # noqa: E402
from mdm.matching.fuzzy import FEATURE_COLUMNS, compute_features, fuzzy_match_score, generate_fuzzy_candidates  # noqa: E402

logger = logging.getLogger("mdm.matching.ml_model")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

RANDOM_STATE = 42
MLFLOW_TRACKING_URI = f"file:{(ROOT / 'mlflow' / 'mlruns').as_posix()}"
MLFLOW_EXPERIMENT = "mdm_entity_resolution"


def _load_ground_truth() -> pd.DataFrame:
    path = ROOT / "data" / "synthetic" / "crm" / "crm_customers_ground_truth.csv"
    return pd.read_csv(path, dtype=str)


def build_labeled_dataset(
    df: pd.DataFrame,
    n_hard_negatives: int = 2000,
    n_random_negatives: int = 800,
) -> pd.DataFrame:
    """Assemble the {features..., label} training table described above."""
    idx_by_id = df.set_index("crm_customer_id", drop=False)
    ids_present = set(idx_by_id.index)

    gt = _load_ground_truth()
    positive_pairs = [
        tuple(sorted((r.customer_id, r.duplicate_of_customer_id)))
        for r in gt.itertuples()
        if r.customer_id in ids_present and r.duplicate_of_customer_id in ids_present
    ]
    positive_set = set(positive_pairs)
    logger.info("Positives: %d ground-truth pairs present in input (of %d total)", len(positive_pairs), len(gt))

    det_pairs = find_deterministic_pairs(df)
    email_only_pairs = [
        (a, b) for a, b in zip(det_pairs.loc[~det_pairs["strong"], "id_1"], det_pairs.loc[~det_pairs["strong"], "id_2"])
        if (a, b) not in positive_set
    ]
    logger.info("Hard negatives (email-collision): %d", len(email_only_pairs))

    exclude = positive_set | set(zip(det_pairs["id_1"], det_pairs["id_2"]))
    fuzzy_candidates = generate_fuzzy_candidates(df, exclude_pairs=exclude, min_score=0.0)
    fuzzy_neg_pairs = list(zip(fuzzy_candidates["id_1"], fuzzy_candidates["id_2"]))
    fuzzy_neg_pairs = [p for p in fuzzy_neg_pairs if p not in positive_set]
    rng = np.random.RandomState(RANDOM_STATE)
    if len(fuzzy_neg_pairs) > n_hard_negatives:
        sel = rng.choice(len(fuzzy_neg_pairs), size=n_hard_negatives, replace=False)
        fuzzy_neg_pairs = [fuzzy_neg_pairs[i] for i in sel]
    logger.info("Hard negatives (fuzzy phonetic blocking, non-match): %d", len(fuzzy_neg_pairs))

    all_ids = list(ids_present)
    random_neg_pairs: set[tuple[str, str]] = set()
    exclude_all = positive_set | set(email_only_pairs) | set(fuzzy_neg_pairs)
    attempts = 0
    while len(random_neg_pairs) < n_random_negatives and attempts < n_random_negatives * 20:
        attempts += 1
        a, b = rng.choice(all_ids, size=2, replace=False)
        pair = tuple(sorted((a, b)))
        if pair in exclude_all or pair in random_neg_pairs:
            continue
        random_neg_pairs.add(pair)
    logger.info("Easy negatives (random, no shared block): %d", len(random_neg_pairs))

    rows = []
    for pairs, label, source in [
        (positive_pairs, 1, "ground_truth"),
        (email_only_pairs, 0, "email_collision"),
        (fuzzy_neg_pairs, 0, "fuzzy_block_nonmatch"),
        (list(random_neg_pairs), 0, "random"),
    ]:
        for a, b in pairs:
            feats = compute_features(idx_by_id.loc[a], idx_by_id.loc[b])
            rows.append({"id_1": a, "id_2": b, **feats, "label": label, "negative_source": source})

    out = pd.DataFrame(rows)
    for col in ["phone_match", "city_match", "state_match"]:
        out[col] = out[col].astype(float)
    return out


def train_and_evaluate(
    dataset: pd.DataFrame,
    test_size: float = 0.3,
    feature_columns: list[str] | None = None,
    run_name: str = "rf_match_classifier",
):
    """Train the RandomForest, evaluate it and the fuzzy-only baseline on
    the same held-out split, and log everything to a local MLflow file store.

    `feature_columns` defaults to the full 6-feature set
    (`mdm.matching.fuzzy.FEATURE_COLUMNS`); pass a subset to run an
    ablation (see `main()` for the name+email-only ablation, which
    simulates matching without a shared phone/address join key).

    Returns (model, metrics_dict).
    """
    import mlflow
    import mlflow.sklearn

    feature_columns = feature_columns or FEATURE_COLUMNS
    X = dataset[feature_columns].astype(float)
    y = dataset["label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_STATE, stratify=y
    )

    # --- Fuzzy-only baseline: pick the F1-maximizing threshold on TRAIN, apply to TEST ---
    # Baseline score always uses the full weighted formula; features not in
    # `feature_columns` are treated as neutral (0) so the ablation run's
    # baseline is comparably handicapped, the same way the ML model is.
    def _score_row(row: pd.Series) -> float:
        feats = {f: (row[f] if f in feature_columns else 0.0) for f in FEATURE_COLUMNS}
        return fuzzy_match_score(feats)

    train_scores = X_train.apply(_score_row, axis=1)
    best_threshold, best_f1 = 0.5, -1.0
    for t in np.arange(0.10, 0.95, 0.01):
        preds = (train_scores >= t).astype(int)
        p, r, f1, _ = precision_recall_fscore_support(y_train, preds, average="binary", zero_division=0)
        if f1 > best_f1:
            best_f1, best_threshold = f1, t

    test_scores = X_test.apply(_score_row, axis=1)
    baseline_preds = (test_scores >= best_threshold).astype(int)
    b_p, b_r, b_f1, _ = precision_recall_fscore_support(y_test, baseline_preds, average="binary", zero_division=0)

    # --- RandomForest ---
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )
    model.fit(X_train, y_train)
    ml_preds = model.predict(X_test)
    m_p, m_r, m_f1, _ = precision_recall_fscore_support(y_test, ml_preds, average="binary", zero_division=0)

    feature_importances = dict(zip(feature_columns, model.feature_importances_.tolist()))

    metrics = {
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_positive_total": int(y.sum()),
        "n_negative_total": int((y == 0).sum()),
        "features_used": feature_columns,
        "baseline_threshold": float(best_threshold),
        "baseline_precision": float(b_p),
        "baseline_recall": float(b_r),
        "baseline_f1": float(b_f1),
        "ml_precision": float(m_p),
        "ml_recall": float(m_r),
        "ml_f1": float(m_f1),
        "feature_importances": feature_importances,
    }

    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(MLFLOW_EXPERIMENT)
        with mlflow.start_run(run_name=run_name):
            mlflow.log_params(
                {
                    "n_estimators": 200,
                    "max_depth": 6,
                    "min_samples_leaf": 3,
                    "class_weight": "balanced",
                    "test_size": test_size,
                    "random_state": RANDOM_STATE,
                    "baseline_threshold": round(best_threshold, 2),
                    "features_used": ",".join(feature_columns),
                }
            )
            mlflow.log_metrics(
                {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
            )
            for feat, imp in feature_importances.items():
                mlflow.log_metric(f"feature_importance_{feat}", imp)
            mlflow.sklearn.log_model(model, name="model")
        logger.info("Logged run '%s' to MLflow (%s, experiment=%s)", run_name, MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT)
    except Exception as exc:  # pragma: no cover - MLflow is best-effort, never blocks the pipeline
        logger.warning("MLflow logging failed (%s) -- continuing without tracking", exc)

    return model, metrics


def main() -> None:
    df, source = load_customers()
    print(f"Input: {source} ({len(df)} rows)")

    dataset = build_labeled_dataset(df)
    print(f"Labeled dataset: {len(dataset)} rows ({dataset['label'].sum()} positive, {(dataset['label']==0).sum()} negative)")
    print(dataset["negative_source"].value_counts(dropna=False).to_string())

    model, metrics = train_and_evaluate(dataset, run_name="rf_match_classifier_full")

    # Ablation: name+email only -- simulates matching across sources that
    # don't share a reliable phone/address join key (the scenario
    # ARCHITECTURE.md §8 actually motivates the ML tier for). address/phone
    # are near-deterministic signals for true dupes in THIS synthetic set
    # (never modified by the duplicate generator), so the full-feature model
    # separates perfectly -- this ablation is the more honest read of how
    # the ML tier compares to the fuzzy baseline on weak/ambiguous signal.
    ablation_model, ablation_metrics = train_and_evaluate(
        dataset, feature_columns=["name_similarity", "email_similarity"], run_name="rf_match_classifier_name_email_only"
    )

    out_dir = ROOT / "data" / "mdm"
    out_dir.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(out_dir / "ml_training_dataset.parquet", index=False)

    def _report(label: str, m: dict) -> None:
        print(f"\n=== {label} (held-out test set, n_test={m['n_test']}) ===")
        print(f"Baseline (fuzzy_match_score >= {m['baseline_threshold']:.2f}):")
        print(f"  precision={m['baseline_precision']:.4f}  recall={m['baseline_recall']:.4f}  f1={m['baseline_f1']:.4f}")
        print("RandomForest:")
        print(f"  precision={m['ml_precision']:.4f}  recall={m['ml_recall']:.4f}  f1={m['ml_f1']:.4f}")
        print("Feature importances:")
        for feat, imp in sorted(m["feature_importances"].items(), key=lambda kv: -kv[1]):
            print(f"  {feat}: {imp:.4f}")

    _report("Full 6-feature model", metrics)
    _report("Ablation: name+email only (no phone/address/city/state signal)", ablation_metrics)


if __name__ == "__main__":
    main()
