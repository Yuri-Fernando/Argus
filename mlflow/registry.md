# MLflow Model Registry log

Human-readable record of what is currently in `Staging`/`Production` in the MLflow Model Registry and why — the audit trail [`versioning/model_versioning.md`](../versioning/model_versioning.md) promises for every promotion/rollback decision. Updated by hand (or by `.github/workflows/ml.yml`) whenever a model's stage changes; the MLflow UI (`make mlflow-ui`) is the source of truth for metrics, this file is the source of truth for *why* a decision was made.

| Date | Model | Version | Stage | Metric (vs. previous) | Decision by | Notes |
|---|---|---|---|---|---|---|
| — | `churn` | — | `None` | — | — | No training run registered yet — lands in Sprint 10 |
| — | `segmentation` | — | `None` | — | — | Lands in Sprint 11 |
| — | `mdm_match` | — | `None` | — | — | Lands in Sprint 5 |
| — | `next_best_action` | — | `None` | — | — | Extension (`ml/reinforcement/`) — see [ADR list](../docs/decisions/) and [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) |

No promotions have happened yet — this table is genuinely empty because implementation hasn't started (see [ROADMAP.md](../ROADMAP.md)), not because the audit trail was skipped. Each row is filled in the moment a model is registered, per [`versioning/model_versioning.md`](../versioning/model_versioning.md)'s `None → Staging → Production → Archived` policy — never retroactively.
