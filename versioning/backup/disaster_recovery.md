# Backup & Disaster Recovery Strategy

This document was created specifically to close a gap: **none of the three original design conversations (`rascunho.md`) mentioned backup or disaster recovery at all.** See [IMPROVEMENTS_AND_RESEARCH.md §2 item 9](../../IMPROVEMENTS_AND_RESEARCH.md).

## Principle

Every layer already has a *native* recovery mechanism provided by the platform it runs on — the job here is to **configure and document** those mechanisms with explicit RPO (Recovery Point Objective) / RTO (Recovery Time Objective) targets, not to build a custom backup system from scratch.

## RPO / RTO targets by component

| Component | Native mechanism | RPO target | RTO target | Notes |
|---|---|---|---|---|
| **ADLS Gen2** (Data Lake) | Soft delete (blobs + containers) + versioning + geo-redundant storage (GRS) | 15 min (GRS replication lag) | < 1 h (failover to secondary region) | Configured in `terraform/modules/azure/adls` |
| **Databricks Delta tables** (Bronze/Silver/Gold) | Delta transaction log — `VERSION AS OF` / `TIMESTAMP AS OF` time travel; `VACUUM` retention set to 30 days (never the default 7) so accidental bad writes are recoverable for a full month | 0 (every write is a new immutable version) | Minutes (restore = re-point to prior version, not a data copy) | `RESTORE TABLE ... TO VERSION AS OF N` |
| **Unity Catalog metastore** | Metastore backup is managed by Databricks; catalog/schema/grant definitions are *also* fully reproducible from `terraform/modules/databricks/unity_catalog` (infrastructure-as-code doubles as a config backup) | N/A (managed) | Terraform re-apply: < 30 min | IaC is the real backup here — see [ADR-010](../../docs/decisions/ADR-010-local-first-development.md) |
| **Snowflake** | Time Travel (default 1 day, raised to 90 days on `CUSTOMER_INTELLIGENCE.CORE` — Snowflake Enterprise edition feature) + Fail-safe (7 additional days, Snowflake-managed, non-configurable) | 0 (Time Travel) | Minutes (`UNDROP` / `AT`/`BEFORE` clause query) | Configured via `terraform/modules/snowflake/databases` |
| **MLflow Model Registry / artifacts** | Backing Postgres (metadata) + artifact store (MinIO locally / ADLS in cloud) — both already covered by their own backup lines above | Same as backing store | Same as backing store | No separate mechanism needed |
| **Terraform state** | Remote backend (`azurerm` backend with blob versioning enabled) — never local state | 0 (every `apply` is a new blob version) | Minutes (`terraform state pull` from a prior version) | See `terraform/environments/dev/main.tf` backend block |
| **Secrets (Key Vault)** | Soft-delete + purge protection enabled | N/A (soft-delete window: 90 days) | Minutes (recover, not regenerate) | Configured via `terraform/modules/azure/key_vault` |
| **Golden Record survivorship log** | Append-only by design (`mdm/golden_record/survivorship_log/`), itself stored as a Delta table — inherits Delta's own recovery guarantees above | 0 | Minutes | Never overwritten, only appended — see [DATA_MODEL.md §4](../../DATA_MODEL.md#4-golden-record--survivorship-rules) |

## What this project deliberately does NOT implement

- **Cross-cloud DR** (e.g., a hot standby in AWS) — out of scope for a portfolio project's budget; documented as a natural extension given [ADR-001](../../docs/decisions/ADR-001-cloud-strategy.md)'s AWS-portability groundwork, not implemented.
- **Automated failover testing / chaos engineering** — the RTO targets above are the platform vendors' documented SLAs, not independently verified by a game-day exercise in this repo. Stated honestly rather than implied as tested.

## Recovery runbook

For an actual incident walkthrough (not just the policy table above), see [`../../docs/runbooks/`](../../docs/runbooks/) — e.g. a Bronze→Silver job failure or a DQ score drop, which are the *operational* counterpart to this document's *infrastructure* recovery guarantees.
