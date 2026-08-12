# databricks/

Databricks workspace artifacts: notebooks, job/workflow definitions, SQL, and Unity Catalog object definitions. Built across **Sprint 2** (Bronze/Silver) and referenced by every later sprint that runs on the Lakehouse.

```
databricks/
├── notebooks/         # exploratory + productionized notebooks (paired with .py source via Databricks Repos)
├── jobs/               # job definitions (JSON/YAML), deployed via the Databricks Asset Bundle in workflows/
├── workflows/           # databricks.yml (Asset Bundle root) — declarative job/pipeline/cluster config,
│                         # deployed with `databricks bundle deploy` from CI (see .github/workflows/ci.yml)
├── sql/                  # Databricks SQL warehouse queries/dashboards definitions
└── unity_catalog/         # catalog/schema/grant definitions (mirrors terraform/modules/databricks/unity_catalog,
                            # but as the human-readable SQL DDL equivalent for local review)
```

## Why Databricks Asset Bundles (DABs)

Reached GA in 2024 and renamed *Declarative Automation Bundles* in Mar/2026 (see [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md)) — used here so jobs/clusters/pipelines are **defined in git**, code-reviewed, and deployed identically across `dev`/`staging`/`prod`, instead of being clicked together in the workspace UI.

## Catalog structure (see ARCHITECTURE.md §6)

`customer_intelligence` catalog → `bronze` / `silver` / `gold` / `ml` / `monitoring` schemas.
