"""Recommendation Agent — combines churn, CLV, support history and sentiment into one action.

Built in ROADMAP.md Sprint 14. This is agent #3 of the four described in ARCHITECTURE.md §15.
It is the agent that ultimately drives `mcp/tools/ml.py:recommend_action`, but the composite
scoring logic itself lives here so it can be unit tested independently of the MCP transport.

Per ADR-006, this agent's public entrypoint (`generate_recommendation`) returns a recommendation
object and ALWAYS enqueues it via `agents/recommendation/approval_queue.py` — it has no code
path that results in a downstream write. Execution only happens after a human calls
`approval_queue.approve()` followed by whatever downstream action-executor later calls
`approval_queue.mark_executed()` (that executor is out of scope for Sprint 14 — see the TODO at
the bottom of this file).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agents.recommendation.approval_queue import RecommendationItem, enqueue_recommendation
from ml.segmentation.kmeans_segments import SEGMENT_LOYAL, SEGMENT_VIP

# Candidate actions this agent can recommend. Kept as a closed set (not free text) so that every
# downstream executor only ever has to handle a known, reviewed list of consequential actions —
# an open-ended "recommendation" string would make the eventual execution step unauditable.
CANDIDATE_ACTIONS = (
    "offer_retention_discount",
    "assign_customer_success_outreach",
    "escalate_to_support_supervisor",
    "no_action_recommended",
)

# CLV threshold (BRL) above which a customer counts as "high value" for the retention-discount
# branch even outside the VIP/Loyal segments. Named here (was an inline `1000` literal — a
# code-review pass flagged it alongside the SEGMENT_VIP/SEGMENT_LOYAL literals it sat next to)
# so it's a single, greppable source of truth rather than a magic number.
HIGH_VALUE_CLV_THRESHOLD = 1000


@dataclass
class ChurnSignal:
    """Subset of mcp/tools/ml.py:get_customer_churn's output this agent consumes."""

    churn_probability: float | None
    risk_band: str | None
    top_features: list[dict] = field(default_factory=list)


@dataclass
class CustomerContext:
    """The four inputs this agent combines, per ARCHITECTURE.md §15's Recommendation Agent line."""

    master_customer_id: str
    churn: ChurnSignal
    clv: float | None  # customer lifetime value, from ml/features/ RFM-derived features
    support_ticket_count_90d: int | None
    support_sentiment_avg: float | None  # AI_SENTIMENT score, -1.0 (negative) to 1.0 (positive)
    segment: str | None  # VIP | Loyal | Potential | At Risk | Inactive, from ml/segmentation/


@dataclass
class Recommendation:
    """The agent's output before it is handed to the approval queue."""

    master_customer_id: str
    action: str
    confidence: float
    evidence: list[str]
    priority: str  # "low" | "medium" | "high"


def gather_customer_context(master_customer_id: str) -> CustomerContext:
    """Assemble the four input signals for one customer, from the real local artifacts built
    across this session — no live LLM or cloud call needed for any of it.

    Sources (all real, all local):
        - churn: `mcp.tools.ml.get_customer_churn()` — champion model + SHAP, MLflow Model Registry.
        - clv: same proxy formula as `snowflake/local_runner.py::build_warehouse()` and
          `mcp/tools/ml.py::recommend_action()` (documented reuse, not re-derived independently —
          `data/ml/features/customer_features.parquet` has no persisted CLV column of its own):
          AOV(monetary/frequency) * frequency * (1 - churn_probability).
        - support_ticket_count_90d / support_sentiment_avg: `customer_features.parquet`'s
          `unresolved_count`/`avg_sentiment_score` columns (built by `ml/features/support.py`).
        - segment: `data/ml/segmentation/customer_segments.parquet`.

    Returns:
        A CustomerContext with all fields populated (or None where the customer/feature row
        genuinely isn't found — never a guessed value).
    """
    from api.services.customer_service import _features_df, _segments_df
    from mcp.tools.ml import get_customer_churn

    churn_raw = get_customer_churn(master_customer_id)
    churn = ChurnSignal(
        churn_probability=churn_raw["churn_probability"],
        risk_band=churn_raw["risk_band"],
        top_features=churn_raw["top_features"],
    )

    features = _features_df()
    feat_match = features[features["master_customer_id"] == master_customer_id]
    segments = _segments_df()
    seg_match = segments[segments["master_customer_id"] == master_customer_id]

    clv: float | None = None
    support_ticket_count_90d: int | None = None
    support_sentiment_avg: float | None = None
    if not feat_match.empty:
        row = feat_match.iloc[0]
        # Support/sentiment signals have no dependency on churn score — a code-review pass caught
        # them previously being gated on `churn.churn_probability is not None` alongside CLV
        # (which genuinely needs it), so a customer with real ticket/sentiment data but no
        # registered churn model (e.g. `python -m ml.churn.train` never run) silently got these
        # reported as unavailable even though the real values were sitting right there.
        support_ticket_count_90d = int(row["unresolved_count"])
        support_sentiment_avg = float(row["avg_sentiment_score"])
        if churn.churn_probability is not None:
            monetary, frequency = float(row["monetary"]), float(row["frequency"])
            avg_order_value = (monetary / frequency) if frequency else 0.0
            clv = round(avg_order_value * frequency * (1 - churn.churn_probability), 2)

    segment = seg_match.iloc[0]["segment"] if not seg_match.empty else None

    return CustomerContext(
        master_customer_id=master_customer_id,
        churn=churn,
        clv=clv,
        support_ticket_count_90d=support_ticket_count_90d,
        support_sentiment_avg=support_sentiment_avg,
        segment=segment,
    )


def score_recommendation(context: CustomerContext) -> Recommendation:
    """Turn a CustomerContext into a single prioritized recommendation.

    This is pure decision logic (no I/O), so it is fully unit-testable against synthetic
    CustomerContext fixtures without needing live data — see
    agents/recommendation/evaluation/golden_questions.yaml for example cases.

    Rules (documented, not tuned against a labeled outcome set — there is no real "did the
    customer actually churn after this action" ground truth in a synthetic dataset, so this is a
    reasonable, explainable heuristic rather than a claimed-optimal policy; `ml/reinforcement/
    next_best_action.py` is the explicitly-labeled extension for learning this from outcomes):
        - high churn risk + high value (VIP/Loyal segment or CLV >= R$1,000) -> retention discount
        - high churn risk + negative support signal -> escalate to a human supervisor
        - high/medium churn risk + negative support signal, or high risk alone -> CS outreach
        - otherwise -> no action

    Args:
        context: the four combined signals for one customer.

    Returns:
        A Recommendation with `action` drawn from CANDIDATE_ACTIONS.
    """
    evidence: list[str] = []
    probability = context.churn.churn_probability

    if probability is None:
        evidence.append(f"No churn score available for {context.master_customer_id} (not found in ml/features/).")
        return Recommendation(
            master_customer_id=context.master_customer_id,
            action="no_action_recommended",
            confidence=0.0,
            evidence=evidence,
            priority="low",
        )

    risk_band = context.churn.risk_band
    evidence.append(f"Churn probability {probability:.2f} ({risk_band} risk).")
    if context.churn.top_features:
        top = context.churn.top_features[0]
        evidence.append(f"Top SHAP driver: {top['feature']} ({top['shap_value']:+.4f}).")
    if context.segment:
        evidence.append(f"Segment: {context.segment}.")
    if context.clv is not None:
        evidence.append(f"Estimated CLV: R$ {context.clv:,.2f}.")
    if context.support_ticket_count_90d:
        evidence.append(f"{context.support_ticket_count_90d} unresolved support ticket(s).")
    if context.support_sentiment_avg is not None:
        evidence.append(f"Average support sentiment: {context.support_sentiment_avg:+.2f}.")

    high_value = context.segment in (SEGMENT_VIP, SEGMENT_LOYAL) or (
        context.clv is not None and context.clv >= HIGH_VALUE_CLV_THRESHOLD
    )
    negative_support_signal = (context.support_ticket_count_90d or 0) > 0 or (
        context.support_sentiment_avg is not None and context.support_sentiment_avg < 0
    )

    if risk_band == "high" and high_value:
        action, confidence, priority = "offer_retention_discount", round(min(0.95, 0.5 + probability / 2), 2), "high"
    elif risk_band == "high" and negative_support_signal:
        action, confidence, priority = "escalate_to_support_supervisor", round(min(0.9, 0.45 + probability / 2), 2), "high"
    elif risk_band in ("high", "medium") and negative_support_signal:
        action, confidence, priority = "assign_customer_success_outreach", round(0.3 + probability / 2, 2), "medium"
    elif risk_band == "high":
        action, confidence, priority = "assign_customer_success_outreach", round(0.3 + probability / 2, 2), "medium"
    else:
        action, confidence, priority = "no_action_recommended", round(1 - probability, 2), "low"

    # A real check, not `assert` — code-review pass caught that `assert` is stripped entirely
    # under `python -O`/`PYTHONOPTIMIZE`, silently losing the one guarantee that keeps `action`
    # inside the closed, auditable CANDIDATE_ACTIONS set (see this module's docstring on why that
    # closure matters for the human-in-the-loop boundary).
    if action not in CANDIDATE_ACTIONS:
        raise ValueError(f"{action!r} not in CANDIDATE_ACTIONS — this is a bug in score_recommendation's branches.")

    return Recommendation(
        master_customer_id=context.master_customer_id,
        action=action,
        confidence=confidence,
        evidence=evidence,
        priority=priority,
    )


def generate_recommendation(master_customer_id: str) -> RecommendationItem:
    """Full pipeline: gather context, score it, and enqueue the result for human approval.

    This function NEVER calls `approval_queue.approve()` or `approval_queue.mark_executed()` —
    those are exclusively human-triggered actions from a separate code path (e.g. a review UI or
    CLI operated by a person), per ADR-006.

    Args:
        master_customer_id: the MDM-assigned survivor ID to generate a recommendation for.

    Returns:
        The `RecommendationItem` as stored in the approval queue, status PENDING.
    """
    context = gather_customer_context(master_customer_id)
    recommendation = score_recommendation(context)

    queue_id = enqueue_recommendation(
        master_customer_id=recommendation.master_customer_id,
        recommendation=recommendation.action,
        confidence=recommendation.confidence,
        evidence=recommendation.evidence,
    )

    from agents.recommendation.approval_queue import get_queue

    return get_queue().get(queue_id)


# TODO(later sprint, out of Sprint 14 scope): build the actual action-executor that, given an
# APPROVED RecommendationItem, performs the real side effect (e.g. calls a CRM API to apply a
# retention discount) and then — only after that side effect succeeds — calls
# `agents.recommendation.approval_queue.get_queue().mark_executed(queue_id)`. That executor is
# deliberately not part of this file: keeping "decide" and "act" in separate modules makes the
# human-in-the-loop boundary a module boundary, not just a runtime check.
