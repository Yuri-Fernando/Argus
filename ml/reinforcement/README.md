# ml/reinforcement/

**Reinforcement learning — EXTENSION, not core MVP scope.** Addresses `add2.txt`'s "Experiência em Machine Learning (aprendizado supervisionado, não supervisionado e por reforço)": supervised learning is [`ml/churn/`](../churn/) (ARCHITECTURE.md §10), unsupervised is [`ml/segmentation/`](../segmentation/), and reinforcement learning was genuinely missing until this module.

```
ml/reinforcement/
└── next_best_action.py   # epsilon-greedy contextual bandit choosing the best retention action per customer
```

## Why this is labeled an extension, not core

[ARCHITECTURE.md §1](../../ARCHITECTURE.md#1-design-principles)'s first principle is "every tool solves one named problem" — RL earns its place here because it is a *genuinely different technique* the target job market asks for (not padding), but a full production RL system (online learning infrastructure, a real reward pipeline fed by observed post-action outcomes, A/B-tested exploration policy) is disproportionate to what a portfolio project needs to prove. This module is scoped honestly: **one clearly-bounded skeleton** (an epsilon-greedy contextual bandit), not a claim of a production RL system. It ships alongside [ROADMAP.md](../../ROADMAP.md)'s extended Sprint 14 checklist, not as a new numbered sprint of its own.

## What it does

`EpsilonGreedyBandit` picks the best retention action per customer from the **same** closed action set `agents/recommendation/recommendation_agent.py` already defines (`CANDIDATE_ACTIONS` — `offer_retention_discount`, `assign_customer_success_outreach`, `escalate_to_support_supervisor`, `no_action_recommended`), instead of inventing a second action taxonomy that would fragment the platform's recommendation surface. With probability `epsilon` it explores (tries a random action to keep learning); otherwise it exploits (picks the action with the best observed average reward so far).

This ties directly into [`agents/recommendation/recommendation_agent.py`](../../agents/recommendation/recommendation_agent.py): where that agent's `score_recommendation()` is a rules/weighted-scoring approach over a `CustomerContext`, `EpsilonGreedyBandit` is the reinforcement-learning alternative to the *same* decision — chosen by trial-and-reward instead of hand-tuned rules. Both are legitimate techniques for the same underlying problem (which retention action, if any, for this customer), and documenting both side by side is itself the honest answer to "why does a portfolio project need both a rules-based recommender and a bandit" — it demonstrates the trade-off, it doesn't pretend one replaces the other today.

## Human-in-the-loop gate (ADR-006) — no exception for ML-originated actions

`EpsilonGreedyBandit.recommend_and_enqueue()` selects an action and enqueues it via `agents/recommendation/approval_queue.py` — exactly the same gate every other consequential action in this platform passes through ([ADR-006](../../docs/decisions/ADR-006-human-in-the-loop.md)). The bandit has no code path that calls `approve()` or `mark_executed()` itself. This matters specifically for RL: a bandit whose reward signal came from ever auto-executing its own actions would be indistinguishable from a system that bypasses human review "because the ML decided" — this module makes that structurally impossible, not just documented as a rule.

`EpsilonGreedyBandit.update(action, reward)` is only ever meant to be called **after** a human has approved and a downstream executor has actually applied the action (`approval_queue.mark_executed()`) — see the docstring note in `next_best_action.py`. Learning from an action that was proposed but never approved would train the bandit on a counterfactual outcome, not a real one.

## What "done" would look like if promoted out of extension status

Not attempted here, and explicitly listed as such: a real reward pipeline reading actual post-action churn outcomes from `ml.model_predictions` at a fixed follow-up horizon, an offline policy evaluation step before promoting a new bandit policy (mirroring the MLflow Staging→Production gate in [`versioning/model_versioning.md`](../../versioning/model_versioning.md)), and a Thompson-sampling or LinUCB upgrade once there's enough real interaction volume to justify moving off flat epsilon-greedy. Tracked as a backlog item in [IMPROVEMENTS_AND_RESEARCH.md](../../IMPROVEMENTS_AND_RESEARCH.md).

## Related

- [`ml/churn/`](../churn/) — supervised leg
- [`ml/segmentation/`](../segmentation/) — unsupervised leg
- [`agents/recommendation/recommendation_agent.py`](../../agents/recommendation/recommendation_agent.py) — shares the `CANDIDATE_ACTIONS` set and the approval-queue contract
- [ADR-006 — Human-in-the-loop](../../docs/decisions/ADR-006-human-in-the-loop.md)
- [`versioning/experimentation_pipeline.md`](../../versioning/experimentation_pipeline.md) — the experiment→version→publish discipline this module's future policy-evaluation step would follow
