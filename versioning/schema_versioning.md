# Schema Versioning Policy

Applies to Bronze/Silver/Gold Delta tables (Databricks), Snowflake CORE tables, and the Golden Record (`gold.dim_customer`).

## Rules

1. **Additive changes are always safe and require no version bump**: new nullable column, new table, new partition. Delta/Unity Catalog and Snowflake both support schema evolution for additive changes natively.
2. **Breaking changes** (column rename, type narrowing, column removal, changing a grain) require:
   - A migration script under `lakehouse/{bronze,silver,gold}/migrations/NNN_description.py` (Databricks side) or `snowflake/tables/migrations/NNN_description.sql` (Snowflake side), numbered sequentially.
   - A dual-write or backfill window documented in the migration script's docstring — never a silent in-place breaking change to a table an agent or dashboard already depends on.
   - A bump of the relevant table's `schema_version` tag (Unity Catalog table property / Snowflake table tag) — consumers (agents, dbt models, Power BI) can read this tag to detect drift before it breaks them.
3. **The Golden Record schema** (`gold.dim_customer`) is the most sensitive — any breaking change here requires updating [`DATA_MODEL.md §3`](../DATA_MODEL.md#3-gold-layer--dimensional-model) and re-running the MDM benchmark (`mdm/entity_resolution/evaluation/`) to confirm match quality didn't regress.

## Enforcement

`data_quality/expectations/` includes a schema-check Expectation per table (ARCHITECTURE.md §7) — an unplanned schema drift fails the Checkpoint and quarantines the batch, rather than silently propagating downstream. See [`../data_quality/README.md`](../data_quality/README.md).
