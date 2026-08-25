# data_quality/

A self-contained **pandas-based** rule engine (ARCHITECTURE.md §7, built in **Sprint 3**). This is the primary/default path — it has no hard dependency on Great Expectations. GX Core (Great Expectations 1.0+) Checkpoints wired to the same `expectations/` rule catalog remain a documented, optional alternative engine (see `validators/__init__.py`), not what actually runs by default.

```
data_quality/
├── expectations/    # rule catalog per Silver table: not_null, unique, valid_email, valid_phone,
│                     # valid_date, referential_integrity, range_check, duplicate_rate, schema_check, freshness
├── validators/       # engine.py (DQEngine — the rule evaluator), quarantine.py, report.py
└── reports/          # generated dq_report.json + dq_report.md — regenerated on every pipeline run
```

`monitoring/` (native Databricks statistical drift monitoring, complementary to these declarative rules) is a future Databricks-cloud-path addition, not implemented locally.

## Run it

```bash
/c/Users/Yuri_/AppData/Local/Programs/Python/Python310/python.exe lakehouse/run_pipeline.py
```

This runs Bronze → Silver → Data Quality end to end (there is no separate `run_checkpoint.py` — the DQ engine is invoked directly from `lakehouse/run_pipeline.py` against each candidate Silver table). It prints a per-table + overall DQ score summary and writes `data_quality/reports/dq_report.json` / `dq_report.md`.

## What "done" looks like (Sprint 3 acceptance criteria)

Intentionally corrupting a field via `data/synthetic/config.yaml`'s `dirty_rates` causes the relevant HARD rule to fail and the affected rows to land in `data/lakehouse/quarantine/<table>.parquet` instead of `data/lakehouse/silver/<table>.parquet` — verified in practice: the CRM's deliberate 1% invalid-phone rate quarantines those rows via the `valid_phone` HARD rule, and every downstream table (support/web/marketing/finance) cascades a `referential_integrity` HARD failure for rows pointing at a quarantined `customer_id`, proving the wiring end to end.
