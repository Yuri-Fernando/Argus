"""Human-in-the-loop approval gate — the concrete mechanism behind ADR-006.

Built in ROADMAP.md Sprint 14 ("Agents (LangGraph) + human-in-the-loop"). ADR-006 states the
policy ("no agent auto-executes a consequential action"); this module is the code that actually
enforces it. Every recommendation produced anywhere in this platform (currently:
`mcp/tools/ml.py:recommend_action`, called from `agents/recommendation/recommendation_agent.py`)
must pass through this queue, and the state machine below makes it structurally impossible for
an item to reach EXECUTED without first being explicitly APPROVED by a human — this is enforced
by an assertion in `mark_executed()`, not merely by convention or by every caller "remembering"
to check first.

State machine
-------------
    PENDING --approve()--> APPROVED --mark_executed()--> EXECUTED
    PENDING --reject()--->  REJECTED

There is no transition from PENDING or REJECTED directly to EXECUTED, and no transition out of
EXECUTED or REJECTED at all (both are terminal). `mark_executed()` raises if called on anything
other than an APPROVED item.

Persistence: this Sprint 14 skeleton uses an in-memory store (`ApprovalQueue`) so the state
machine and its guard can be demoed/tested without a database. A later sprint should back this
with a real table (e.g. `gold.recommendation_queue` or a Postgres table in `api/`) so the queue
survives process restarts and gives the audit trail ADR-006 promises — the public API below
(`enqueue`, `approve`, `reject`, `mark_executed`, `get`, `list_pending`) is designed to stay
stable across that swap.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class RecommendationStatus(str, Enum):
    """The four states a queued recommendation can be in. See module docstring for transitions."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"


@dataclass
class RecommendationItem:
    """A single recommendation's full lifecycle record — the audit trail unit for ADR-006."""

    queue_id: str
    master_customer_id: str
    recommendation: str | None
    confidence: float | None
    evidence: list[str]
    status: RecommendationStatus = RecommendationStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decided_by: str | None = None
    decided_at: datetime | None = None
    decision_reason: str | None = None
    executed_at: datetime | None = None


class ApprovalQueueError(RuntimeError):
    """Raised when a caller attempts an invalid state transition (e.g. executing without approval)."""


class ApprovalQueue:
    """In-memory PENDING/APPROVED/REJECTED/EXECUTED queue with a guarded execution transition."""

    def __init__(self) -> None:
        self._items: dict[str, RecommendationItem] = {}

    def enqueue(
        self,
        *,
        master_customer_id: str,
        recommendation: str | None,
        confidence: float | None,
        evidence: list[str],
    ) -> str:
        """Add a new PENDING recommendation to the queue and return its queue_id.

        This is the only way a `RecommendationItem` comes into existence — there is no
        constructor path that creates one already APPROVED or EXECUTED.
        """
        queue_id = str(uuid.uuid4())
        self._items[queue_id] = RecommendationItem(
            queue_id=queue_id,
            master_customer_id=master_customer_id,
            recommendation=recommendation,
            confidence=confidence,
            evidence=list(evidence),
        )
        return queue_id

    def get(self, queue_id: str) -> RecommendationItem:
        """Fetch a queue item by id, raising KeyError if unknown."""
        return self._items[queue_id]

    def list_pending(self) -> list[RecommendationItem]:
        """List all items still awaiting a human decision, oldest first."""
        pending = [i for i in self._items.values() if i.status is RecommendationStatus.PENDING]
        return sorted(pending, key=lambda i: i.created_at)

    def approve(self, queue_id: str, *, approved_by: str, reason: str | None = None) -> RecommendationItem:
        """Transition a PENDING item to APPROVED. This is the ONLY human-triggered action that
        makes an item eligible for execution — nothing else in this codebase may set APPROVED.

        Args:
            queue_id: the item to approve.
            approved_by: identifier of the human approver (e.g. an employee/user id). Required —
                an anonymous approval is not an audit trail.
            reason: optional free-text justification.

        Raises:
            ApprovalQueueError: if the item is not currently PENDING.
        """
        item = self.get(queue_id)
        if item.status is not RecommendationStatus.PENDING:
            raise ApprovalQueueError(
                f"Cannot approve item {queue_id} in status {item.status}; only PENDING items "
                "may be approved."
            )
        if not approved_by:
            raise ApprovalQueueError("approved_by is required — approvals must be attributable to a human.")
        item.status = RecommendationStatus.APPROVED
        item.decided_by = approved_by
        item.decided_at = datetime.now(timezone.utc)
        item.decision_reason = reason
        return item

    def reject(self, queue_id: str, *, rejected_by: str, reason: str | None = None) -> RecommendationItem:
        """Transition a PENDING item to REJECTED (terminal — cannot later be executed)."""
        item = self.get(queue_id)
        if item.status is not RecommendationStatus.PENDING:
            raise ApprovalQueueError(
                f"Cannot reject item {queue_id} in status {item.status}; only PENDING items "
                "may be rejected."
            )
        if not rejected_by:
            raise ApprovalQueueError("rejected_by is required — rejections must be attributable to a human.")
        item.status = RecommendationStatus.REJECTED
        item.decided_by = rejected_by
        item.decided_at = datetime.now(timezone.utc)
        item.decision_reason = reason
        return item

    def mark_executed(self, queue_id: str) -> RecommendationItem:
        """Transition an APPROVED item to EXECUTED.

        This is the concrete guard ADR-006 requires: it is structurally impossible to reach
        EXECUTED from PENDING or REJECTED. Any downstream system that performs the actual write
        (refund, retention offer, Golden Record merge) MUST call this only after its own action
        succeeded, and MUST call `approve()`'s result — never bypass this queue to write
        directly.

        Raises:
            ApprovalQueueError: if the item is not currently APPROVED. This is the assertion
                that makes the human-in-the-loop guarantee real rather than aspirational.
        """
        item = self.get(queue_id)
        if item.status is not RecommendationStatus.APPROVED:
            raise ApprovalQueueError(
                f"Refusing to execute item {queue_id} in status {item.status}: only items that "
                "have passed through approve() may be marked EXECUTED. This guard is the "
                "concrete mechanism behind ADR-006 — do not bypass it."
            )
        item.status = RecommendationStatus.EXECUTED
        item.executed_at = datetime.now(timezone.utc)
        return item


# Module-level default queue, shared by mcp/tools/ml.py:recommend_action and
# agents/recommendation/recommendation_agent.py so both talk to the same in-memory state during
# local development. TODO(later sprint): once this queue is backed by a real table, replace
# this singleton with a proper dependency-injected client (e.g. constructed once in api/ and
# passed to callers) instead of a module-global.
_default_queue = ApprovalQueue()


def get_queue() -> ApprovalQueue:
    """Return the shared default ApprovalQueue instance."""
    return _default_queue


def enqueue_recommendation(
    *,
    master_customer_id: str,
    recommendation: str | None,
    confidence: float | None,
    evidence: list[str],
) -> str:
    """Convenience wrapper around `get_queue().enqueue(...)` — used by mcp/tools/ml.py."""
    return _default_queue.enqueue(
        master_customer_id=master_customer_id,
        recommendation=recommendation,
        confidence=confidence,
        evidence=evidence,
    )
