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

# Candidate actions this agent can recommend. Kept as a closed set (not free text) so that every
# downstream executor only ever has to handle a known, reviewed list of consequential actions —
# an open-ended "recommendation" string would make the eventual execution step unauditable.
CANDIDATE_ACTIONS = (
    "offer_retention_discount",
    "assign_customer_success_outreach",
    "escalate_to_support_supervisor",
    "no_action_recommended",
)


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
    """Assemble the four input signals for one customer.

    Returns:
        A CustomerContext with all fields populated (or None where a signal is unavailable).
    """
    # TODO(Sprint 10-14 wiring): call the MCP tools directly (or the underlying functions in
    # mcp/tools/ml.py, mcp/tools/quality.py) plus:
    #   - CLV: ml/features/ (RFM-derived, ARCHITECTURE.md §10)
    #   - support_ticket_count_90d / support_sentiment_avg: data/synthetic/support ->
    #     AI_SENTIMENT (ARCHITECTURE.md §12)
    #   - segment: ml/segmentation/ (ROADMAP.md Sprint 11)
    # This function intentionally has the final signature already — only the TODO'd data reads
    # are missing.
    return CustomerContext(
        master_customer_id=master_customer_id,
        churn=ChurnSignal(churn_probability=None, risk_band=None, top_features=[]),
        clv=None,
        support_ticket_count_90d=None,
        support_sentiment_avg=None,
        segment=None,
    )


def score_recommendation(context: CustomerContext) -> Recommendation:
    """Turn a CustomerContext into a single prioritized recommendation.

    This is pure decision logic (no I/O), so it is fully unit-testable against synthetic
    CustomerContext fixtures without needing live data — see
    agents/recommendation/evaluation/golden_questions.yaml for example cases once real scoring
    logic replaces the placeholder below.

    Args:
        context: the four combined signals for one customer.

    Returns:
        A Recommendation with `action` drawn from CANDIDATE_ACTIONS.
    """
    # TODO(Sprint 14): implement the actual weighted-scoring / rules logic combining
    # churn_probability, clv, support_sentiment_avg and segment into a priority + action choice
    # (e.g. high churn risk + high CLV + negative sentiment => "offer_retention_discount" at
    # "high" priority). Until then this returns the safe default: no action, zero confidence,
    # so nothing downstream mistakes an unimplemented scorer for a real recommendation.
    evidence: list[str] = []
    if context.churn.churn_probability is None:
        evidence.append("churn score unavailable — see mcp/tools/ml.py TODO")

    return Recommendation(
        master_customer_id=context.master_customer_id,
        action="no_action_recommended",
        confidence=0.0,
        evidence=evidence,
        priority="low",
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
