# ml/

Feature engineering, model training and explainability — ARCHITECTURE.md §10, built in **Sprints 10-11**. Every experiment is tracked in [`../mlflow/`](../mlflow/).

```
ml/
├── features/          # RFM, engagement, support, and graph-derived features (reads mdm/ + graph/ outputs)
├── churn/               # Logistic Regression / Random Forest / Gradient Boosting, compared on ROC-AUC/F1/PR-AUC/calibration
├── segmentation/         # KMeans over RFM+engagement → VIP/Loyal/Potential/At Risk/Inactive
├── matching/               # shared with mdm/matching/ml_model.py (imported, not duplicated)
├── training/                # training pipeline entrypoints, parameterized by MLflow run config
├── evaluation/                # held-out test set metrics, model comparison reports
└── explainability/             # SHAP value computation, attached to every churn prediction
```

## Champion model criterion

The model promoted to `Staging` in the MLflow Model Registry is the one with the best PR-AUC on the held-out set (chosen over raw ROC-AUC because churn is a moderately imbalanced label) — see Sprint 10 acceptance criteria in [ROADMAP.md](../ROADMAP.md).
