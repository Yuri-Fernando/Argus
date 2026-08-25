# Runbook: Data Quality Score Drop

**Scope:** the platform-level Data Quality Score ([`docs/semantic-dictionary.md`](../semantic-dictionary.md)) or a per-dataset `dq_score` from a GX Core checkpoint run ([ARCHITECTURE.md §7](../../ARCHITECTURE.md#7-layer-4--data-quality)) drops below its expected baseline. This runbook mirrors the diagnostic flow the **Data Quality Agent** itself follows ([ARCHITECTURE.md §15](../../ARCHITECTURE.md#15-layer-12--mcp--agentic-ai)) — root cause → affected row count → recommended action — so a human can reproduce the agent's reasoning manually, or pick up where an agent-flagged incident left off.

## Symptoms

- The Power BI Data Quality dashboard, Grafana `dq_score` panel, or a Data Quality Agent alert shows the rollup score (or a specific dataset's score) below its rolling baseline.
- Downstream signal: MDM entity resolution producing an unusual number of `HUMAN_REVIEW` matches, or a Gold table's row count deviating from its normal range — both are often *symptoms* of the same underlying DQ regression, not separate problems.

## Diagnosis steps — following the Data Quality Agent's flow

1. **Identify which dimension regressed.** The Data Quality Score is a weighted rollup across datasets ([`docs/semantic-dictionary.md`](../semantic-dictionary.md#data-quality-score)); each dataset's own `dq_score` breaks down by GX Core dimension ([ARCHITECTURE.md §7](../../ARCHITECTURE.md#7-layer-4--data-quality)): completeness, validity, uniqueness, referential integrity, freshness, schema, volume anomaly. Pull the latest `quality_report.json` / GX Data Docs for the affected dataset and identify which dimension(s) actually dropped — a rollup drop is often driven by one dimension on one dataset, not a broad regression.

2. **Quantify the affected row count.** Cross-reference the failed Expectation(s) against the checkpoint's row-level results to get an exact count and, where possible, the specific rows/partitions affected — "12% of `crm_customers` rows ingested in the last run failed the `email` validity Expectation" is the shape of finding this step should produce, not "email quality looks worse."

3. **Root-cause the dimension that regressed:**

   | Dimension regressed | Likely root cause | Where to look |
   |---|---|---|
   | Completeness | Upstream source stopped populating a field, or an ingestion bug started dropping it | Compare the affected partition's null-rate against the historical baseline; check the ingestion job's own logs for the same time window |
   | Validity | A source system changed its format (e.g. phone numbers now include country code), or a genuinely dirtier batch landed | Sample the failing rows directly; compare against the synthetic generator's configured dirty-rate if this is a synthetic source ([DATA_MODEL.md §5](../../DATA_MODEL.md#5-synthetic-data-generation-strategy)) — a `--dirty-rate` change is a legitimate, expected cause in this demo environment |
   | Uniqueness | Upstream started emitting duplicate rows (retry without idempotency, or a genuine spike in near-duplicate customers) | Check whether this correlates with an MDM `HUMAN_REVIEW` spike — the same underlying duplication often shows up in both places |
   | Referential integrity | A parent table's Bronze→Silver job failed or ran late relative to a child table's ([`pipeline_failure.md`](pipeline_failure.md)) | Check the parent table's own last successful run timestamp |
   | Freshness | The Bronze→Silver job for this source didn't run, or ran on stale input — likely the same root cause covered by [`pipeline_failure.md`](pipeline_failure.md) | Check `monitoring.pipeline_run_log` for the source table's last successful run |
   | Schema | Column added/removed/retyped upstream without a corresponding Expectation update | Diff the current Bronze schema against the GX Expectation Suite's expected schema |
   | Volume anomaly | Row count deviates sharply from the rolling baseline (either a stalled/partial ingestion, or a genuine one-off event like a promotional spike) | Compare against the rolling baseline window, not just yesterday's count — a real promotional spike is a false positive, not an incident |

4. **Rule out a Bronze→Silver pipeline failure as the actual cause.** If the freshness or referential-integrity dimension is what regressed, this may simply be an unresolved case of [`pipeline_failure.md`](pipeline_failure.md) rather than a data quality problem in its own right — check `monitoring.pipeline_run_log` before investigating further as a DQ issue specifically.

## Resolution

| Root cause | Action |
|---|---|
| Genuine upstream data problem (format change, dropped field) | Fix the ingestion/Silver transform to handle the new reality, or escalate to the owning source-system team if this platform doesn't control the source |
| Expected synthetic dirty-rate change (demo/testing) | No action needed if the drop matches an intentional `--dirty-rate` change ([DATA_MODEL.md §5](../../DATA_MODEL.md#5-synthetic-data-generation-strategy)) — confirm this is the case before treating it as an incident |
| Upstream pipeline failure (freshness/referential integrity) | Resolve via [`pipeline_failure.md`](pipeline_failure.md), then re-run the GX Core checkpoint |
| Rows genuinely fail an Expectation and should be excluded from downstream processing | Confirm they're routed to `adls/quarantine/` correctly rather than silently passing through to Silver/Gold |
| Expectation itself is miscalibrated (too strict/stale threshold) | Update the Expectation Suite deliberately, with the change reviewed — do not loosen a threshold silently just to make the score look better |

After resolution:

1. Re-run the GX Core checkpoint (`make dq`) for the affected dataset and confirm the dimension-level and rollup scores recover.
2. If the regression triggered downstream effects (MDM `HUMAN_REVIEW` spike, Gold row-count anomaly), confirm those recover too on the next scheduled run.
3. Log the finding (root cause, affected row count, resolution) the same way the Data Quality Agent's recommendation would be logged — this is the same accountability trail referenced in [`governance/lgpd.md`](../../governance/lgpd.md) and [ADR-006](../decisions/ADR-006-human-in-the-loop.md).

## Related

- [`pipeline_failure.md`](pipeline_failure.md) — companion runbook when the root cause is a job failure, not a data-content problem.
- [ARCHITECTURE.md §7](../../ARCHITECTURE.md#7-layer-4--data-quality) — GX Core dimensions and quarantine mechanism.
- [ARCHITECTURE.md §15](../../ARCHITECTURE.md#15-layer-12--mcp--agentic-ai) — the Data Quality Agent this runbook mirrors.
- [`docs/semantic-dictionary.md`](../semantic-dictionary.md#data-quality-score) — the Data Quality Score metric definition.
