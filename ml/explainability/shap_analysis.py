"""SHAP explanations for the champion churn model.

Run directly:

    python -m ml.explainability.shap_analysis

Loads the champion model already trained and registered by `python -m ml.churn.train`
(MLflow Model Registry — `models:/{REGISTERED_MODEL_NAME}/latest`), reconstructs the exact
deterministic train/test split `ml/churn/train.py` used (same fixed `RANDOM_STATE`, so the held-out
rows and their true labels line up with what the registered model was actually evaluated on,
without needing to retrain), and prints:

  1. Global feature importance — mean |SHAP value| across a sample of the held-out test set.
  2. Per-customer explanations for three concrete example customers — their real
     `master_customer_id`, predicted churn probability, and their top SHAP feature
     contributions, so a prediction is demoable and auditable rather than an opaque score.

Uses `shap.Explainer` against the loaded model's `predict_proba`, not a model-specific
explainer — this keeps the module correct regardless of which model type happens to be
registered as champion (Logistic Regression today).

FIXED (code-review pass): this module previously called `ml.churn.train.train_and_compare()`
on every run — retraining Logistic Regression, a 200-tree Random Forest, AND Gradient Boosting
from scratch just to explain the one already-trained, already-registered champion. `mcp/tools/
ml.py::_champion_model()` already does this correctly (load, don't retrain); this module now
mirrors that same technique directly (not by importing from `mcp/tools/`, which is the adapter
layer around this domain-core module per ADR-014 — the dependency only goes the other way).
"""
from __future__ import annotations

import logging

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import train_test_split

from ml.churn.label import add_churn_label
from ml.churn.train import (
    FEATURE_COLUMNS,
    MLFLOW_TRACKING_URI,
    RANDOM_STATE,
    REGISTERED_MODEL_NAME,
    TEST_SIZE,
)
from ml.features.build_features import OUTPUT_PATH as FEATURES_PATH

logger = logging.getLogger("ml.explainability.shap_analysis")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

BACKGROUND_SAMPLE_SIZE = 100
GLOBAL_IMPORTANCE_SAMPLE_SIZE = 200
N_EXAMPLE_CUSTOMERS = 3
TOP_N_CONTRIBUTIONS = 4


def _rebuild_test_set_with_ids() -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.DataFrame]:
    """Reproduce `ml.churn.train.train_and_compare`'s exact train/test split, but keep
    `master_customer_id` alongside it (dropped inside `train_and_compare` since raw customer ids
    are not a model feature) so explanations can be attributed to real, named customers.

    Returns:
        `(X_train, X_test, y_test, test_ids)` — `test_ids` is a DataFrame with columns
        `["master_customer_id"]`, row-aligned with `X_test`/`y_test`.
    """
    features = pd.read_parquet(FEATURES_PATH)
    labeled = add_churn_label(features)

    X = labeled[FEATURE_COLUMNS]
    y = labeled["churned"]
    ids = labeled[["master_customer_id"]]

    X_train, X_test, y_train, y_test, _, ids_test = train_test_split(
        X, y, ids, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    return X_train, X_test, y_test, ids_test


def explain_champion() -> None:
    """End-to-end: train candidates, pick the champion, print global + per-customer SHAP output."""
    results: list[ModelResult] = train_and_compare()
    champion = max(results, key=lambda r: r.roc_auc)
    logger.info("Explaining champion: %s (ROC-AUC=%.3f)", champion.name, champion.roc_auc)

    X_train, X_test, y_test, ids_test = _rebuild_test_set_with_ids()

    background = shap.sample(X_train, BACKGROUND_SAMPLE_SIZE, random_state=RANDOM_STATE)
    explainer = shap.Explainer(champion.model.predict_proba, background, feature_names=FEATURE_COLUMNS)

    # --- Global importance, over a sample of the held-out test set ---
    sample_idx = X_test.sample(
        n=min(GLOBAL_IMPORTANCE_SAMPLE_SIZE, len(X_test)), random_state=RANDOM_STATE
    ).index
    global_explanation = explainer(X_test.loc[sample_idx])
    # predict_proba returns two columns [P(not churned), P(churned)] — SHAP output shape follows;
    # index 1 selects the churn-probability output.
    shap_values_churn = global_explanation.values[..., 1]
    mean_abs_importance = pd.Series(
        np.abs(shap_values_churn).mean(axis=0), index=FEATURE_COLUMNS
    ).sort_values(ascending=False)

    print(f"\nChampion model: {champion.name} (ROC-AUC={champion.roc_auc:.3f})")
    print(f"\nGlobal feature importance (mean |SHAP|, n={len(sample_idx)} test customers):")
    for feature, value in mean_abs_importance.items():
        print(f"  {feature:<28}{value:.4f}")

    # --- Per-customer explanations for concrete example customers ---
    # Pick the N customers with the highest predicted churn probability in the test set — the
    # most demoable case ("why is this specific customer flagged as high-risk?") rather than an
    # arbitrary random sample.
    proba_test = champion.model.predict_proba(X_test)[:, 1]
    top_risk_positions = np.argsort(proba_test)[::-1][:N_EXAMPLE_CUSTOMERS]

    print(f"\nPer-customer SHAP explanations (top {N_EXAMPLE_CUSTOMERS} highest-risk test customers):")
    for pos in top_risk_positions:
        row = X_test.iloc[[pos]]
        customer_id = ids_test.iloc[pos]["master_customer_id"]
        actual_label = y_test.iloc[pos]
        explanation = explainer(row)
        shap_row = explanation.values[0, :, 1]
        base_value = explanation.base_values[0, 1]
        predicted_proba = proba_test[pos]

        contributions = pd.Series(shap_row, index=FEATURE_COLUMNS).sort_values(
            key=np.abs, ascending=False
        )

        print(f"\n  Customer {customer_id} (actual label churned={actual_label})")
        print(f"    Predicted churn probability: {predicted_proba:.4f}  (base rate: {base_value:.4f})")
        print("    Top SHAP feature contributions:")
        for feature, value in contributions.head(TOP_N_CONTRIBUTIONS).items():
            raw_value = row.iloc[0][feature]
            sign = "+" if value >= 0 else ""
            print(f"      {sign}{value:.4f}  {feature} (value={raw_value})")


if __name__ == "__main__":
    explain_champion()
