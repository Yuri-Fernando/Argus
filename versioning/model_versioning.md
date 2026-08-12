# ML Model Versioning Policy

Applies to the churn model, segmentation model, and MDM match model (`ml/`, `mdm/matching/ml_model.py`).

## MLflow Model Registry stages

```
None ──(training run registered)──▶ Staging ──(passes evaluation gate)──▶ Production ──(superseded)──▶ Archived
```

- **None** — every training run is logged (params/metrics/artifacts), but not registered as a named model version.
- **Staging** — the run with the best PR-AUC (churn) / silhouette score (segmentation) / F1 (matching) on the held-out set is registered and promoted here automatically at the end of the training job.
- **Production** — promoted manually (or via CI gate in `.github/workflows/ml.yml`) only after the [`ml/evaluation/`](../ml/README.md) report confirms no metric regression vs. the current Production model, on the same held-out set.
- **Archived** — the previous Production model, kept for rollback and for audit (LGPD accountability — a customer's churn score must be traceable to the exact model version that produced it).

## Versioning scheme

Each registered model version is tagged with: `{model_name}-v{MAJOR}.{MINOR}` where `MAJOR` bumps on a feature-set or algorithm change, `MINOR` bumps on a retrain with the same feature set. The Delta table `ml.model_predictions` (or Snowflake equivalent) always stores the `model_version` alongside every prediction — this is what makes the SHAP explanation for any customer reproducible after the fact.

## Rollback

`mlflow models serve` / the batch scoring job reads the model version pinned in `ml/training/config.yaml`, not always-latest — rolling back is a one-line config change plus a redeploy, not a retrain.
