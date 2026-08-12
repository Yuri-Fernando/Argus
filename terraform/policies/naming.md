# Naming convention

All Terraform-managed resources follow one pattern:

```
<project>-<env>-<resource>-<region>
```

| Token | Values | Example |
|---|---|---|
| `project` | `eci` (Enterprise Customer Intelligence) — see `tagging.tf` `var.project` | `eci` |
| `env` | `dev` \| `staging` \| `prod` | `dev` |
| `resource` | short resource-type slug (`rg`, `adls`, `adf`, `evh`, `kv`, `vnet`, `law`, `oai`, `dbx`, `sfwh`) | `adls` |
| `region` | Azure short region code (`brs` = Brazil South, `eus2` = East US 2) or `global` for region-less resources (Snowflake account objects, Unity Catalog) | `brs` |

## Examples

| Resource | Name |
|---|---|
| Resource Group (dev, Brazil South) | `eci-dev-rg-brs` |
| ADLS Gen2 storage account | `ecidevadlsbrs` (storage accounts: no hyphens, ≤24 chars, lowercase — see `modules/azure/adls/README.md`) |
| Data Factory | `eci-dev-adf-brs` |
| Event Hubs namespace | `eci-dev-evh-brs` |
| Key Vault | `eci-dev-kv-brs` |
| Azure OpenAI account | `eci-dev-oai-eus2` (Azure OpenAI not available in all regions) |
| Databricks workspace | `eci-dev-dbx-brs` |
| Snowflake warehouse | `ECI_DEV_WH` (Snowflake identifiers: uppercase, underscores, no hyphens) |
| Snowflake database | `CUSTOMER_INTELLIGENCE` (business-name, not env-suffixed — env isolation happens at the Snowflake **account** level, one account per environment tier in a real deployment; this portfolio uses schema-level isolation instead, see `modules/snowflake/databases/README.md`) |

## Exceptions

- **Storage accounts** (Azure) cannot contain hyphens and must be ≤24 characters — the pattern collapses to `<project><env>adls<region>` with no separators.
- **Snowflake identifiers** are uppercase with underscores, never hyphens, per Snowflake SQL identifier conventions.
- **Unity Catalog** objects (`customer_intelligence` catalog, `bronze/silver/gold/ml/monitoring` schemas) follow the data-domain naming from [ARCHITECTURE.md §6](../../ARCHITECTURE.md#6-layer-3--lakehouse-azure-databricks), not the infra naming pattern, since they are logical data objects rather than cloud infrastructure.

## Tags

Every resource that supports tagging carries the standard tag set defined in [`tagging.tf`](tagging.tf): `project`, `environment`, `cost_center`, `managed_by`.
