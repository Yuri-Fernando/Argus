# dbt/

One of the three semantic layer implementations (dbt/MetricFlow) — see [ADR-005](../docs/decisions/ADR-005-semantic-layer.md) and ARCHITECTURE.md §11, built in **Sprint 8**. MetricFlow is Apache-2.0 open source as of late 2025 — see [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md).

```
dbt/
├── dbt_project.yml
├── models/
│   ├── staging/        # 1:1 light cleanup views over Silver/Gold sources
│   ├── intermediate/    # joins/business logic building blocks
│   └── marts/             # final marts + MetricFlow semantic models (metrics: Revenue, Orders, AOV, Churn, CLV, NPS...)
├── tests/                  # dbt tests (schema + custom SQL)
├── macros/
├── snapshots/               # SCD tracking where relevant (e.g. customer_segment history)
└── seeds/                    # small static reference tables (e.g. state/region mapping)
```

## Canonical metric source

Every metric defined here traces back to exactly one definition in [`../docs/semantic-dictionary.md`](../docs/semantic-dictionary.md) — the same definition is mirrored into Unity Catalog Metric Views and Snowflake Semantic Views, with an automated parity test (`tests/data/test_metric_parity.py`, Sprint 8 acceptance criteria).

## Target warehouses

Configured to run against both `dbt-databricks` and `dbt-snowflake` adapters (see `pyproject.toml` `[dbt]` extra) — models are adapter-agnostic SQL wherever possible.
