"""Machine learning tools for the MCP server: churn scoring, model metrics, recommendations.

Built in ROADMAP.md Sprint 13. `get_customer_churn` and `get_model_metrics` read from the
champion models tracked in MLflow (`ml/churn/`, ROADMAP.md Sprint 10 — ARCHITECTURE.md §10).

`recommend_action` is the tool most tightly constrained by governance: per ADR-006
(human-in-the-loop) and ADR-007 (AI guardrails), a recommendation-generating tool must never be
able to also be the thing that executes the recommendation. That separation is enforced here at
the type level, not just by convention — this function's return type has no field or code path
that results in a downstream mutation. Execution, if it ever happens, happens only after a human
calls `approve()` in agents/recommendation/approval_queue.py, from a completely separate code
path this tool cannot reach.

WIRED (this session):
  - `get_customer_churn` loads the real registered `churn_model` (MLflow Model Registry —
    `mlflow.sklearn.load_model`, no retraining) and scores the customer's real feature row from
    `data/ml/features/customer_features.parquet`. SHAP attribution reuses the same technique
    `ml/explainability/shap_analysis.py` uses (`shap.Explainer` against `predict_proba`) — that
    module itself has no importable single-customer function (it is a `print`-only CLI script
    that retrains 3 models every run), so the explainer is built here directly against the
    already-loaded champion model instead of shelling out to that script. See
    `_shap_explainer()`.
  - `get_model_metrics` queries the real local MLflow Model Registry / tracking store.
  - `recommend_action` now delegates to `agents.recommendation.recommendation_agent
    .generate_recommendation()`, which composes a real recommendation from `get_customer_churn`
    (this module) + CLV + segment + support signals. It previously duplicated that logic inline
    because `recommendation_agent.py`'s own scorer was still a stub — since fixed (second wiring
    pass), so this tool is back to being a thin MCP-shaped adapter over the real agent, matching
    the separation of concerns that module's docstring always intended.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import mlflow
import mlflow.sklearn
import pandas as pd
import shap

from api.services.customer_service import _features_df
from ml.churn.train import FEATURE_COLUMNS, MLFLOW_TRACKING_URI, REGISTERED_MODEL_NAME

RISK_BAND_LOW_MAX = 0.3  # < 0.3 -> "low"
RISK_BAND_HIGH_MIN = 0.7  # >= 0.7 -> "high"; in between -> "medium". Documented, not tuned.

SHAP_BACKGROUND_SIZE = 100
TOP_N_SHAP_FEATURES = 4


@dataclass
class ShapFeature:
    """A single SHAP-attributed feature contributing to a churn prediction."""

    feature: str
    shap_value: float


def _risk_band(probability: float) -> str:
    if probability < RISK_BAND_LOW_MAX:
        return "low"
    if probability >= RISK_BAND_HIGH_MIN:
        return "high"
    return "medium"


@lru_cache(maxsize=1)
def _champion_model_version():
    """Latest registered version of `churn_model` in the local MLflow Model Registry, or
    `None` if nothing is registered (e.g. `python -m ml.churn.train` was never run in this
    environment)."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = mlflow.MlflowClient()
    versions = client.search_model_versions(f"name='{REGISTERED_MODEL_NAME}'")
    if not versions:
        return None
    return max(versions, key=lambda v: int(v.version))


@lru_cache(maxsize=1)
def _champion_model():
    """Load the registered champion model's artifact once per process — never retrained here,
    per this tool's original TODO ("do not recompute SHAP per-request if a cached explanation
    already exists — SHAP is not free"), extended to "don't retrain the model per-request"
    either."""
    version = _champion_model_version()
    if version is None:
        return None
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    return mlflow.sklearn.load_model(f"models:/{REGISTERED_MODEL_NAME}/{version.version}")


@lru_cache(maxsize=1)
def _shap_explainer():
    """SHAP explainer against the champion model's `predict_proba`, background-sampled from the
    real feature store — same technique as `ml/explainability/shap_analysis.py::explain_champion`
    (see module docstring for why that script itself isn't called directly)."""
    model = _champion_model()
    if model is None:
        return None
    features = _features_df()[FEATURE_COLUMNS]
    background = shap.sample(features, min(SHAP_BACKGROUND_SIZE, len(features)), random_state=42)
    return shap.Explainer(model.predict_proba, background, feature_names=FEATURE_COLUMNS)


def get_customer_churn(master_customer_id: str) -> dict[str, Any]:
    """Fetch a customer's churn risk score with its top SHAP contributing features.

    Args:
        master_customer_id: the MDM-assigned survivor ID.

    Returns:
        {
            "master_customer_id": str,
            "churn_probability": float | None,   # 0.0-1.0
            "risk_band": str | None,               # "low" | "medium" | "high"
            "top_features": list[dict],             # ShapFeature-shaped, highest |shap_value| first
            "model_version": str | None,             # MLflow Model Registry version tag
            "found": bool,
        }
    """
    # TODO(Sprint 10 / ml/churn + ml/explainability): load the champion model from the MLflow
    # Model Registry (Staging/Production alias — see ml/README.md "Champion model criterion"),
    # score this customer's current feature vector from ml/features/, and attach the
    # precomputed SHAP values from ml/explainability/. Do not recompute SHAP per-request if a
    # cached explanation already exists — SHAP is not free.
    # Wired: see module docstring. `_champion_model()` / `_shap_explainer()` are process-cached
    # so the model is loaded and the SHAP background sampled exactly once, not per call.
    model = _champion_model()
    version = _champion_model_version()
    if model is None:
        return {
            "master_customer_id": master_customer_id,
            "churn_probability": None,
            "risk_band": None,
            "top_features": [],
            "model_version": None,
            "found": False,
        }

    features = _features_df()
    match = features[features["master_customer_id"] == master_customer_id]
    if match.empty:
        return {
            "master_customer_id": master_customer_id,
            "churn_probability": None,
            "risk_band": None,
            "top_features": [],
            "model_version": str(version.version) if version else None,
            "found": False,
        }

    row = match[FEATURE_COLUMNS]
    probability = float(model.predict_proba(row)[:, 1][0])

    top_features: list[dict[str, Any]] = []
    explainer = _shap_explainer()
    if explainer is not None:
        explanation = explainer(row)
        # predict_proba -> two output columns [P(not churned), P(churned)]; index 1 selects the
        # churn-probability output, matching ml/explainability/shap_analysis.py's convention.
        shap_row = explanation.values[0, :, 1]
        contributions = pd.Series(shap_row, index=FEATURE_COLUMNS).sort_values(key=lambda s: s.abs(), ascending=False)
        top_features = [
            ShapFeature(feature=feature, shap_value=float(value)).__dict__
            for feature, value in contributions.head(TOP_N_SHAP_FEATURES).items()
        ]

    return {
        "master_customer_id": master_customer_id,
        "churn_probability": round(probability, 4),
        "risk_band": _risk_band(probability),
        "top_features": top_features,
        "model_version": str(version.version) if version else None,
        "found": True,
    }


def get_model_metrics(model_name: str = "churn") -> dict[str, Any]:
    """Fetch a registered model's held-out evaluation metrics from the MLflow Model Registry.

    Args:
        model_name: one of "churn", "segmentation", "match" (ARCHITECTURE.md §10).

    Returns:
        {
            "model_name": str,
            "roc_auc": float | None,
            "f1": float | None,
            "pr_auc": float | None,
            "precision": float | None,
            "recall": float | None,
            "stage": str | None,        # e.g. "Staging", "Production"
            "run_id": str | None,
            "found": bool,
        }
    """
    # TODO(Sprint 10-11 / ml/evaluation, mlflow/): query the MLflow tracking server / Model
    # Registry for the given model's latest evaluated run. Champion selection criterion for
    # "churn" is PR-AUC on the held-out set — see ml/README.md.
    # Wired for "churn" (the only model actually registered in this build's MLflow Model
    # Registry — verified live: `search_registered_models()` returns only `churn_model`.
    # `ml/segmentation/kmeans_segments.py` (KMeans) and `mdm/matching/ml_model.py` (the MDM
    # matcher) both track runs under their own MLflow experiments but neither registers a
    # Model Registry entry, so "segmentation"/"match" honestly return found=False rather than
    # fabricating a registry entry that doesn't exist.
    if model_name != "churn":
        return {
            "model_name": model_name,
            "roc_auc": None,
            "f1": None,
            "pr_auc": None,
            "precision": None,
            "recall": None,
            "stage": None,
            "run_id": None,
            "found": False,
        }

    version = _champion_model_version()
    if version is None:
        return {
            "model_name": model_name,
            "roc_auc": None,
            "f1": None,
            "pr_auc": None,
            "precision": None,
            "recall": None,
            "stage": None,
            "run_id": None,
            "found": False,
        }

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = mlflow.MlflowClient()
    run = client.get_run(version.run_id)
    metrics = run.data.metrics

    return {
        "model_name": model_name,
        "roc_auc": metrics.get("roc_auc"),
        "f1": metrics.get("f1"),
        "pr_auc": metrics.get("pr_auc"),
        # ml/churn/train.py::_evaluate() logs roc_auc/f1/pr_auc/brier_score only — precision and
        # recall at the 0.5 threshold are not separately logged. Left honestly None rather than
        # recomputed from a different threshold than what f1 was scored at.
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "stage": version.current_stage,
        "run_id": version.run_id,
        "found": True,
    }


def recommend_action(master_customer_id: str) -> dict[str, Any]:
    """Generate a prioritized retention/engagement recommendation for a customer.

    This function NEVER executes anything. It always returns
    `requires_human_approval: True` and enqueues the recommendation via
    `agents.recommendation.approval_queue.enqueue_recommendation`, per ADR-006. There is no
    parameter, flag, or code path in this function that results in a downstream write — approval
    and execution live entirely in agents/recommendation/, in a different call stack triggered
    only by an explicit human action.

    Args:
        master_customer_id: the MDM-assigned survivor ID.

    Returns:
        {
            "master_customer_id": str,
            "recommendation": str | None,      # e.g. "offer_retention_discount"
            "confidence": float | None,          # 0.0-1.0
            "evidence": list[str],                 # human-readable evidence bullets
            "requires_human_approval": True,        # always True — see docstring
            "queue_id": str,                          # id of the enqueued PENDING approval item
        }
    """
    # Wired (this session, second pass): agents/recommendation/recommendation_agent.py's
    # gather_customer_context()/score_recommendation() are now real — this MCP tool delegates to
    # generate_recommendation() (which itself enqueues via approval_queue) instead of duplicating
    # the composite scoring logic inline, per the agent module's own stated design intent
    # ("the composite scoring logic itself lives here so it can be unit tested independently of
    # the MCP transport"). This closes the duplication the previous wiring pass had to introduce
    # because recommendation_agent.py was still a stub at the time.
    from agents.recommendation.recommendation_agent import generate_recommendation

    item = generate_recommendation(master_customer_id)

    return {
        "master_customer_id": master_customer_id,
        "recommendation": item.recommendation,
        "confidence": item.confidence,
        "evidence": item.evidence,
        "requires_human_approval": True,
        "queue_id": item.queue_id,
    }
