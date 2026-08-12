# ML benchmarks

What this measures and why: held-out set performance of the champion churn model —
[ARCHITECTURE.md §10](../ARCHITECTURE.md#10-layer-7--machine-learning). PR-AUC is the champion
selection criterion (churn is moderately imbalanced — see [`ml/README.md`](../ml/README.md)), but
all standard classification metrics are recorded here so the comparison against the runner-up
models (Logistic Regression / Random Forest / Gradient Boosting) stays auditable.

| Metric | Value | Date measured | Sprint | Notes |
|---|---|---|---|---|
| ROC-AUC | | | | |
| F1 | | | | |
| precision | | | | |
| recall | | | | |
| calibration | | | | |

## Related

[ARCHITECTURE.md §17](../ARCHITECTURE.md#17-layer-14--observability--finops) ·
[IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) backlog item 5 (FinOps cost guardrails)
