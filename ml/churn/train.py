"""Train, compare, and register churn models — Logistic Regression / Random Forest / Gradient
Boosting — all tracked in MLflow.

Run directly:

    python -m ml.churn.train

Every run (one per candidate model) is logged to the `churn_model` MLflow experiment at
`file:./mlflow/mlruns` — a separate tracking URI folder from `mdm_entity_resolution`'s experiment
inside the same store, so the two agents' runs coexist without colliding (see ARCHITECTURE.md
§10 / `mlflow/README.md`). The run with the highest held-out ROC-AUC is registered to the MLflow
Model Registry as `churn_model` and promoted to the `Staging` stage.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import NamedTuple

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.churn.label import add_churn_label
from ml.features.build_features import OUTPUT_PATH as FEATURES_PATH

logger = logging.getLogger("ml.churn.train")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

MLFLOW_TRACKING_URI = "file:./mlflow/mlruns"
EXPERIMENT_NAME = "churn_model"
REGISTERED_MODEL_NAME = "churn_model"
RANDOM_STATE = 42
TEST_SIZE = 0.25

# The four columns the proxy label is derived from (see `ml/churn/label.py`) are still legitimate
# predictive features here — a churn model is expected to lean on recency/support signals — the
# noise injected into the label at construction time is what keeps this an honest, non-trivial
# learning problem rather than the model memorizing a deterministic rule. `churn_risk_score` is
# excluded: it IS the (noisy) pre-threshold label, so including it would be direct leakage.
FEATURE_COLUMNS: list[str] = [
    "recency_days",
    "frequency",
    "monetary",
    "event_count",
    "distinct_event_types",
    "days_since_last_activity",
    "ticket_count",
    "avg_sentiment_score",
    "unresolved_count",
]


class ModelResult(NamedTuple):
    """One trained candidate's held-out evaluation, enough to rank champions and print a table."""

    name: str
    run_id: str
    roc_auc: float
    f1: float
    pr_auc: float
    brier_score: float
    model: object


def _build_candidates() -> dict[str, Pipeline]:
    """Candidate models, each wrapped in a `StandardScaler` pipeline for a fair, consistent
    preprocessing contract across models (harmless for the two tree ensembles, necessary for
    Logistic Regression's coefficients to be on comparable scales)."""
    return {
        "logistic_regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=200, max_depth=8, random_state=RANDOM_STATE, n_jobs=-1
                    ),
                ),
            ]
        ),
        "gradient_boosting": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", GradientBoostingClassifier(random_state=RANDOM_STATE)),
            ]
        ),
    }


def _evaluate(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float]:
    """Compute ROC-AUC, F1 (at the default 0.5 decision threshold), PR-AUC (average precision),
    and Brier score (a proper calibration metric — lower is better-calibrated) on held-out data.
    """
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    return {
        "roc_auc": roc_auc_score(y_test, proba),
        "f1": f1_score(y_test, pred),
        "pr_auc": average_precision_score(y_test, proba),
        "brier_score": brier_score_loss(y_test, proba),
    }


def train_and_compare(features_path: Path = FEATURES_PATH) -> list[ModelResult]:
    """Train all three candidates, log each to MLflow, and return their held-out results.

    Args:
        features_path: path to the Feature Store output (`ml/features/build_features.py`).

    Returns:
        One `ModelResult` per candidate, in training order.
    """
    features = pd.read_parquet(features_path)
    labeled = add_churn_label(features)

    X = labeled[FEATURE_COLUMNS]
    y = labeled["churned"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    logger.info(
        "Train/test split: %d/%d rows, positive rate train=%.3f test=%.3f",
        len(X_train),
        len(X_test),
        y_train.mean(),
        y_test.mean(),
    )

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    results: list[ModelResult] = []
    for name, pipeline in _build_candidates().items():
        with mlflow.start_run(run_name=name) as run:
            pipeline.fit(X_train, y_train)
            metrics = _evaluate(pipeline, X_test, y_test)

            mlflow.log_param("model_type", name)
            mlflow.log_param("features", ",".join(FEATURE_COLUMNS))
            mlflow.log_param("train_rows", len(X_train))
            mlflow.log_param("test_rows", len(X_test))
            mlflow.log_param("positive_rate", round(float(y.mean()), 4))
            mlflow.log_metrics(metrics)
            mlflow.sklearn.log_model(pipeline, artifact_path="model")

            logger.info(
                "%s: ROC-AUC=%.3f F1=%.3f PR-AUC=%.3f Brier=%.4f",
                name,
                metrics["roc_auc"],
                metrics["f1"],
                metrics["pr_auc"],
                metrics["brier_score"],
            )
            results.append(
                ModelResult(
                    name=name,
                    run_id=run.info.run_id,
                    roc_auc=metrics["roc_auc"],
                    f1=metrics["f1"],
                    pr_auc=metrics["pr_auc"],
                    brier_score=metrics["brier_score"],
                    model=pipeline,
                )
            )

    return results


def register_champion(results: list[ModelResult]) -> str:
    """Register the highest-ROC-AUC candidate to the MLflow Model Registry and promote it to
    `Staging`.

    Args:
        results: output of `train_and_compare`.

    Returns:
        The registered model version string, e.g. `"1"`.
    """
    champion = max(results, key=lambda r: r.roc_auc)
    logger.info("Champion: %s (ROC-AUC=%.3f)", champion.name, champion.roc_auc)

    model_uri = f"runs:/{champion.run_id}/model"
    registered = mlflow.register_model(model_uri=model_uri, name=REGISTERED_MODEL_NAME)

    client = mlflow.MlflowClient()
    client.transition_model_version_stage(
        name=REGISTERED_MODEL_NAME,
        version=registered.version,
        stage="Staging",
        archive_existing_versions=False,
    )
    client.set_model_version_tag(
        REGISTERED_MODEL_NAME, registered.version, "champion_model_type", champion.name
    )
    logger.info(
        "Registered %s v%s as '%s', promoted to Staging",
        champion.name,
        registered.version,
        REGISTERED_MODEL_NAME,
    )
    return registered.version


def print_comparison_table(results: list[ModelResult]) -> None:
    """Print the ROC-AUC/F1/PR-AUC/Brier comparison table across all candidates."""
    header = f"{'Model':<22}{'ROC-AUC':>10}{'F1':>10}{'PR-AUC':>10}{'Brier':>10}"
    print(header)
    print("-" * len(header))
    for r in sorted(results, key=lambda r: r.roc_auc, reverse=True):
        print(f"{r.name:<22}{r.roc_auc:>10.3f}{r.f1:>10.3f}{r.pr_auc:>10.3f}{r.brier_score:>10.4f}")


if __name__ == "__main__":
    all_results = train_and_compare()
    print_comparison_table(all_results)
    register_champion(all_results)
