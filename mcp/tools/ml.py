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
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.recommendation.approval_queue import enqueue_recommendation


@dataclass
class ShapFeature:
    """A single SHAP-attributed feature contributing to a churn prediction."""

    feature: str
    shap_value: float


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
    return {
        "master_customer_id": master_customer_id,
        "churn_probability": None,
        "risk_band": None,
        "top_features": [],
        "model_version": None,
        "found": False,
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
    # TODO(Sprint 14 / agents/recommendation): replace the placeholder evidence/confidence
    # below with the real composite computed by
    # agents/recommendation/recommendation_agent.py, which combines:
    #   - churn score + SHAP evidence (this module, get_customer_churn)
    #   - CLV (ml/features/, RFM-derived)
    #   - support ticket sentiment (data/synthetic/support -> AI_SENTIMENT, ARCHITECTURE.md §12)
    #   - segment (ml/segmentation/)
    recommendation: str | None = None
    confidence: float | None = None
    evidence: list[str] = []

    queue_id = enqueue_recommendation(
        master_customer_id=master_customer_id,
        recommendation=recommendation,
        confidence=confidence,
        evidence=evidence,
    )

    return {
        "master_customer_id": master_customer_id,
        "recommendation": recommendation,
        "confidence": confidence,
        "evidence": evidence,
        "requires_human_approval": True,
        "queue_id": queue_id,
    }
