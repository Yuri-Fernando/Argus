# lakehouse/

PySpark transformation code for the Medallion architecture (ARCHITECTURE.md §6). This is the *code*; the *deployed jobs* that run it live in [`../databricks/`](../databricks/).

```
lakehouse/
├── bronze/     # Sprint 2 — near-verbatim copy of raw, Delta-ified, minimal transform
├── silver/     # Sprint 2/3 — dedup, casting, standardization, schema enforcement, DQ hooks
└── gold/       # Sprint 7 — dimensional model build (see DATA_MODEL.md §3)
```

## Rule: Bronze never destroys information

Bronze transformations are limited to: format conversion (CSV/JSON → Delta), partitioning, and column renaming for consistency. Any row that fails a Bronze-level structural check goes to `data/quarantine/`, never silently dropped.

## Local execution

`lakehouse/*` runs against a local Spark session (`pyspark` extra in `pyproject.toml`) reading/writing the MinIO-backed `data/` tree when `PROFILE=local`; the same code targets `abfss://` + a real Databricks cluster when `PROFILE=cloud` — see [ADR-010](../docs/decisions/ADR-010-local-first-development.md).
