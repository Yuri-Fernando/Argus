# lakehouse/

Transformation code for the Medallion architecture (ARCHITECTURE.md §6). This is the *code*; the *deployed jobs* that run it (when Databricks is in the loop) live in [`../databricks/`](../databricks/).

```
lakehouse/
├── bronze/          # Sprint 2 — near-verbatim copy of raw, minimal transform, Parquet
├── silver/          # Sprint 2/3 — dedup, casting, standardization, schema enforcement
├── run_pipeline.py  # single entrypoint: bronze -> silver -> data quality
└── gold/            # Sprint 7 — dimensional model build (see DATA_MODEL.md §3), not yet implemented
```

## Engine: pandas is the default, PySpark is an equivalent alternative

The implementation in `bronze/` and `silver/` uses **pandas + pyarrow** as the always-works local default — every module runs on a laptop with no cluster and no MinIO/Spark session required. Each module reads CSV -> casts dtypes -> writes Parquet with the exact same logical steps (read → cast → add `_ingested_at` → write) that a PySpark `DataFrameReader`/`DataFrameWriter` job would use for the `PROFILE=cloud` / Databricks path described in [ADR-010](../docs/decisions/ADR-010-local-first-development.md); a `spark.py` variant implementing the same contract can be added later without touching Silver or Data Quality.

## Rule: Bronze never destroys information

Bronze transformations are limited to: format conversion (CSV → Parquet), dtype casting, and adding `_ingested_at`/`_source_system` columns. No filtering, no deduplication happens in Bronze — that's Silver's job. Rows that fail a **hard** Data Quality rule (checked against the candidate Silver table) are quarantined to `data/lakehouse/quarantine/<table>.parquet` instead of landing in `data/lakehouse/silver/<table>.parquet` — see `data_quality/README.md`.

## Local execution

```bash
/c/Users/Yuri_/AppData/Local/Programs/Python/Python310/python.exe lakehouse/run_pipeline.py
```

Runs Bronze → Silver → Data Quality end to end against the local `data/` tree and prints a per-table + overall DQ score summary. Olist-derived Bronze/Silver/Gold tables are skipped with a warning when `data/raw/olist` is absent (see `lakehouse/bronze/olist.py`).
