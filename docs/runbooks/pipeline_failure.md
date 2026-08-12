# Runbook: Bronze → Silver Job Failure

**Scope:** a scheduled Databricks Workflow (deployed via DABs — [ARCHITECTURE.md §6](../../ARCHITECTURE.md#6-layer-3--lakehouse-azure-databricks)) that transforms a Bronze Delta table into its Silver counterpart fails to complete, is flagged in `monitoring.pipeline_run_log`, and the Monitoring Agent raises an alert.

## Symptoms

- Monitoring Agent alert (or Grafana panel on `pipeline_duration` / job status) shows a failed run for a `bronze.* → silver.*` job — e.g. `crm_customers` or `olist_orders`.
- Downstream Silver-dependent jobs (MDM, DQ checkpoints, Gold materialization) either skip the run or operate on stale data, silently widening the gap between what Power BI/agents report and what actually landed.
- Data Quality Agent may separately report a **freshness** violation on the affected Silver table before anyone notices the job itself failed — see [`dq_score_drop.md`](dq_score_drop.md) if that's the entry point instead.

## Diagnosis steps

1. **Confirm the failure and scope it.**
   - Check `monitoring.pipeline_run_log` (or the Databricks Workflow run UI) for the failed run's `run_id`, `job_name`, `start_time`, `error_message`.
   - Identify which source table(s) were in flight — a single job failure on `crm_customers` does not necessarily mean `olist_orders` is also affected.

2. **Read the actual Spark error, not just the job status.**
   - Databricks Workflow run page → failed task → stderr/stdout logs. Common causes at this stage of the pipeline:
     | Cause | Signature |
     |---|---|
     | Schema drift in the source | `AnalysisException: cannot resolve column` or a new/renamed column not in the Bronze schema |
     | Bad data violating a Silver-stage assumption (e.g. a null in a NOT-NULL-typed cast) | `NullPointerException` or a cast failure on a specific column |
     | Cluster/compute issue (spot eviction, OOM) | `SparkException: Job aborted` with an executor-lost or out-of-memory message, unrelated to any specific column |
     | Upstream Bronze table itself incomplete (ingestion job failed earlier) | Row count anomaly warning preceding the Silver job, or the Bronze table's own `updated_at` is stale |
     | Delta table version conflict (concurrent write) | `ConcurrentAppendException` / `ConcurrentDeleteReadException` |

3. **Check whether the source is upstream-broken, not Silver-broken.**
   - If the Bronze table itself wasn't refreshed (ADF/Event Hubs ingestion issue), the Silver job is failing on stale or incomplete input — the fix belongs in ingestion, not the Silver transform. Cross-check `adls/raw/<source>/` landing timestamps.

4. **Reproduce locally if the cause isn't obvious from logs.**
   - Pull the same Bronze partition against the local docker-compose stack ([`docs/deployment.md`](../deployment.md)) and re-run the Silver transform (`lakehouse/silver/`) against it with `pyspark` locally — reproducing outside the cluster isolates whether this is a data problem or a cluster/environment problem.

## Resolution

| Root cause | Fix |
|---|---|
| Schema drift | Update the Silver transform's expected schema (`lakehouse/silver/`) to handle the new/renamed column deliberately — never silently `.drop()` an unexpected column without a corresponding GX Core schema expectation update ([ARCHITECTURE.md §7](../../ARCHITECTURE.md#7-layer-4--data-quality)) |
| Bad data breaking a cast/assumption | Route the offending rows to `adls/quarantine/` per the existing quarantine pattern instead of failing the whole job — if quarantine logic wasn't already handling this case, that's the actual gap to close |
| Cluster/compute issue | Re-run the job (transient spot eviction/OOM is often not reproducible); if it recurs, adjust the DABs job cluster sizing/policy, not the transform code |
| Upstream Bronze incomplete | Fix/re-run the ingestion job first (ADF pipeline or Event Hubs consumer), then re-trigger the dependent Silver job — do not patch around missing data at the Silver layer |
| Delta concurrent write conflict | Confirm no manual/ad-hoc write is racing the scheduled job against the same table; re-run — Delta's optimistic concurrency will succeed once the conflicting writer is gone |

After resolution:

1. Re-run the specific failed job (not the full DAG) via the Databricks Workflow UI or `databricks jobs run-now`.
2. Confirm the Silver table's `updated_at`/row count moved as expected, and that downstream MDM/DQ/Gold jobs that were skipped or ran on stale data are re-triggered.
3. Verify the platform Data Quality Score ([`docs/semantic-dictionary.md`](../semantic-dictionary.md)) recovers on the next GX Core checkpoint run — if it doesn't, follow [`dq_score_drop.md`](dq_score_drop.md) next.
4. If the root cause was a code/config gap (missing quarantine handling, missing schema expectation), file it as a follow-up — a runbook resolves the incident, it doesn't replace fixing the underlying gap.

## Related

- [`dq_score_drop.md`](dq_score_drop.md) — companion runbook when the entry point is a DQ score drop rather than an explicit job failure.
- [ARCHITECTURE.md §6](../../ARCHITECTURE.md#6-layer-3--lakehouse-azure-databricks) — Bronze/Silver/Gold layer definitions.
- [ARCHITECTURE.md §7](../../ARCHITECTURE.md#7-layer-4--data-quality) — GX Core dimensions and quarantine pattern.
- [ARCHITECTURE.md §15](../../ARCHITECTURE.md#15-layer-12--mcp--agentic-ai) — Monitoring Agent, the usual alert source for this runbook.
