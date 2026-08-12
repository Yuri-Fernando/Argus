"""Next-Best-Action contextual bandit — reinforcement learning skeleton, gated by ADR-006.

Built per add2.txt's "Experiência em Machine Learning (aprendizado supervisionado, não
supervisionado e por reforço)". Churn (`ml/churn/`) is supervised; segmentation
(`ml/segmentation/`) is unsupervised; this module is the reinforcement-learning leg — a
contextual bandit choosing the best retention action per customer from the same
`CANDIDATE_ACTIONS` set `agents/recommendation/recommendation_agent.py` already defines, instead
of inventing a parallel action taxonomy.

Explicitly labeled an EXTENSION, not core MVP scope (see `ml/reinforcement/README.md`) — kept
narrow and honestly scoped per ARCHITECTURE.md §1, rather than a full RL training pipeline that
would be disproportionate to what this portfolio needs to prove.

Every action this bandit selects is, like every other consequential recommendation in this
platform, enqueued via `agents/recommendation/approval_queue.py` and NEVER auto-executed — see
ADR-006. A bandit is not exempt from human-in-the-loop just because it is "the ML system deciding"
rather than "the LLM agent deciding": the accountability requirement is about the action being
consequential, not about which technique proposed it.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from agents.recommendation.approval_queue import enqueue_recommendation
from agents.recommendation.recommendation_agent import CANDIDATE_ACTIONS

# Reuse the same closed action set the Recommendation Agent uses, per the module docstring —
# a bandit that could select an action outside this reviewed list would be exactly the
# unauditable "open-ended recommendation" ADR-006 was written to prevent.
ACTIONS: tuple[str, ...] = CANDIDATE_ACTIONS


@dataclass
class ActionStats:
    """Running reward statistics for one action, the state a bandit policy needs to choose."""

    action: str
    pulls: int = 0
    total_reward: float = 0.0

    @property
    def mean_reward(self) -> float:
        return self.total_reward / self.pulls if self.pulls > 0 else 0.0


@dataclass
class BanditDecision:
    """One action selection, with enough context to audit why it was chosen."""

    master_customer_id: str
    action: str
    strategy: str  # "explore" | "exploit"
    estimated_reward: float
    queue_id: str | None = None


class EpsilonGreedyBandit:
    """Epsilon-greedy contextual bandit over `ACTIONS`.

    Deliberately the simplest defensible RL policy, not a deep-RL / Thompson-sampling
    implementation — the point of this module is to demonstrate the *discipline* (reward signal
    definition, explore/exploit trade-off, human-in-the-loop gating), not to out-engineer the
    churn model's rigor. A Thompson-sampling variant is noted as the natural next step in
    `ml/reinforcement/README.md` once there is enough real interaction data to justify a fully
    Bayesian policy over a simpler heuristic.

    "Contextual" here means the per-customer signals from
    `agents/recommendation/recommendation_agent.py`'s `CustomerContext` (churn probability, CLV,
    segment) are expected to condition `estimate_rewards` in a future iteration — this skeleton's
    `select_action` accepts a `context` dict precisely so that wiring point already exists, even
    though the reward estimate itself is currently a flat per-action average, not yet
    context-conditioned (see TODO below).
    """

    def __init__(self, *, epsilon: float = 0.1, seed: int | None = 42) -> None:
        """
        Args:
            epsilon: probability of exploring (choosing a random action) instead of exploiting
                (choosing the current best-estimated action). 0.1 is a conventional starting
                point — tightening it over time as more reward data accumulates is a natural
                extension, not implemented here.
            seed: fixed by default (42, matching this project's `--seed 42` reproducibility
                convention across synthetic data generation and MDM benchmarking, ADR-009) so
                bandit behavior is reproducible across runs during development.
        """
        self.epsilon = epsilon
        self._rng = random.Random(seed)
        self._stats: dict[str, ActionStats] = {action: ActionStats(action=action) for action in ACTIONS}

    def select_action(self, master_customer_id: str, context: dict[str, object] | None = None) -> BanditDecision:
        """Choose an action for one customer, exploring with probability `epsilon`.

        Args:
            master_customer_id: the MDM-assigned survivor ID this decision is for.
            context: per-customer signals (churn probability, CLV, segment, etc.) — accepted
                today for interface stability; not yet used to condition the estimate (see
                class docstring "contextual" note and the TODO below).

        Returns:
            A `BanditDecision` recording which action was chosen and why (explore vs. exploit) —
            this is the audit trail a reviewer needs before approving the recommendation.
        """
        _ = context  # TODO(RL extension): condition action-value estimates on context features
        # (churn_probability, clv, segment) instead of the flat per-action average below — e.g. a
        # small linear model per action (LinUCB) or a feature-conditioned reward regressor. Kept
        # as a flat epsilon-greedy bandit for the initial skeleton per the module's "simplest
        # defensible policy" scope note.

        if self._rng.random() < self.epsilon:
            action = self._rng.choice(ACTIONS)
            strategy = "explore"
        else:
            action = max(self._stats.values(), key=lambda s: s.mean_reward).action
            strategy = "exploit"

        return BanditDecision(
            master_customer_id=master_customer_id,
            action=action,
            strategy=strategy,
            estimated_reward=self._stats[action].mean_reward,
        )

    def update(self, action: str, reward: float) -> None:
        """Record the observed reward for an action after it was (eventually) executed.

        Args:
            action: which action was taken — must be one of `ACTIONS`.
            reward: the observed outcome signal, e.g. `1.0` if the customer did not churn in the
                follow-up window after the action was applied, `0.0` otherwise (a simple binary
                retention-success signal — richer reward shaping, e.g. weighting by CLV retained,
                is a documented next step, not implemented here).

        Note: this is only ever called AFTER a human has approved and the downstream executor has
        applied the action (see `agents/recommendation/approval_queue.py`'s `mark_executed`) — a
        bandit that updated its policy from actions that were never actually approved/executed
        would be learning from counterfactual, not real, outcomes.
        """
        stats = self._stats[action]
        stats.pulls += 1
        stats.total_reward += reward

    def recommend_and_enqueue(self, master_customer_id: str, context: dict[str, object] | None = None) -> BanditDecision:
        """Select an action and enqueue it for human approval — never auto-executed (ADR-006).

        This is the bandit's only externally-visible write path, mirroring
        `agents/recommendation/recommendation_agent.py:generate_recommendation`'s contract: it
        selects, it enqueues, and it stops — approval and execution are separate, human-triggered
        code paths this module has no access to.
        """
        decision = self.select_action(master_customer_id, context)
        queue_id = enqueue_recommendation(
            master_customer_id=master_customer_id,
            recommendation=decision.action,
            confidence=decision.estimated_reward,
            evidence=[f"epsilon-greedy bandit, strategy={decision.strategy}"],
        )
        decision.queue_id = queue_id
        return decision
