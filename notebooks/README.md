# notebooks/

Runnable Jupyter notebooks that exercise the platform's layers **locally, over pandas/scikit-learn**, so results are visible without provisioning Databricks/Snowflake/Power BI — the fastest way for a recruiter (or you, mid-development) to see the pipeline actually produce something.

This is distinct from [`../databricks/notebooks/`](../databricks/notebooks/), which holds the production Databricks-hosted notebooks (PySpark, Unity Catalog, real cluster) built out sprint-by-sprint. These local notebooks are a **demonstration/validation layer**, not what runs in production — they intentionally use pandas instead of PySpark so they open and run in plain Jupyter/VS Code/Colab with no cluster.

## Prerequisites

```bash
make seed              # downloads Olist + generates all synthetic data — see DATA_MODEL.md
pip install -e ".[dev]"
pip install jupyter matplotlib seaborn
jupyter lab notebooks/
```

Every notebook checks for its required input files at the top and prints a clear `make seed` reminder instead of a confusing traceback if they're missing.

## Notebooks

| # | Notebook | What it shows | Mirrors |
|---|---|---|---|
| 01 | [`01_data_quality_overview.ipynb`](01_data_quality_overview.ipynb) | Completeness/validity/uniqueness checks across Olist + synthetic sources, an overall DQ score, and where the deliberately-injected dirty data shows up | [`data_quality/`](../data_quality/) (Sprint 3), the Power BI "Data Quality" page (ARCHITECTURE.md §13) |
| 02 | [`02_entity_resolution_golden_record.ipynb`](02_entity_resolution_golden_record.ipynb) | Deterministic → fuzzy → ML entity resolution on the synthetic CRM data, scored against the ground-truth duplicates, building a Golden Record | [`mdm/`](../mdm/) (Sprints 4-5) |
| 03 | [`03_churn_model_explainability.ipynb`](03_churn_model_explainability.ipynb) | Feature engineering, a trained churn classifier, ROC/PR curves, and SHAP explainability for individual customers | [`ml/churn/`](../ml/README.md) (Sprint 10) |
| 04 | [`04_customer_segmentation.ipynb`](04_customer_segmentation.ipynb) | RFM feature build + KMeans segmentation into VIP/Loyal/Potential/At Risk/Inactive | [`ml/segmentation/`](../ml/README.md) (Sprint 11) |
| 05 | [`05_customer_graph_analysis.ipynb`](05_customer_graph_analysis.ipynb) | NetworkX customer relationship graph, centrality/community detection, duplicate clusters the ML matcher alone would miss | [`graph/`](../graph/) (Sprint 6) |
| 06 | [`06_platform_kpis_dashboard.ipynb`](06_platform_kpis_dashboard.ipynb) | An in-notebook Executive Overview — Revenue, Orders, AOV, Churn, DQ score, all in one page — the same KPI set as the Power BI page, rendered with matplotlib for anyone without Power BI access | [`powerbi/`](../powerbi/README.md) (Sprint 9), ARCHITECTURE.md §13 |

## Convention

Every notebook is self-contained (imports its own deps, no shared `utils.py` state to keep the "open and Run All" experience frictionless), reads directly from `data/raw/` and `data/synthetic/` via relative paths (run `jupyter lab` from the repo root), and ends with a short "what this maps to in the real pipeline" markdown cell linking back to the corresponding sprint and module.
