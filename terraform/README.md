# terraform/

Infrastructure as Code for the platform, across **three provider domains** — `azurerm`, `databricks`, and Snowflake (two providers, see below) — structured as `environments/{dev,staging,prod}` consuming reusable `modules/{azure,databricks,snowflake}`. This is [Layer 15 in ARCHITECTURE.md §18](../ARCHITECTURE.md#18-layer-15--infrastructure-as-code).

```
terraform/
├── environments/
│   ├── dev/          # full HCL — real provider/module wiring, applied against a personal-budget sandbox
│   ├── staging/       # README only — mirrors dev/ with stricter approval gates, see below
│   └── prod/           # README only — same pattern, environment-gated apply
├── modules/
│   ├── azure/          # resource_group, adls, data_factory, event_hubs, key_vault, networking, monitoring, openai
│   ├── databricks/       # workspace, clusters, jobs, unity_catalog, permissions
│   └── snowflake/         # warehouse, databases, schemas, roles, grants, stages, semantic
└── policies/
    ├── tagging.tf          # standard tag set applied across every taggable resource
    └── naming.md            # <project>-<env>-<resource>-<region> naming convention
```

## Why three provider domains

| Provider | Scope | Rationale |
|---|---|---|
| `hashicorp/azurerm` | Resource groups, ADLS Gen2, Data Factory, Event Hubs, Key Vault, networking, Azure Monitor, Azure OpenAI | Azure is the primary cloud — [ADR-001](../docs/decisions/ADR-001-cloud-strategy.md) |
| `databricks/databricks` | Workspace-level objects: clusters, cluster policies, Unity Catalog, permissions | Official provider; job **bodies** are declared via Databricks Asset Bundles in `databricks/workflows/`, not here — Terraform only owns what DABs don't |
| `snowflakedb/snowflake` (primary) + `Snowflake-Labs/snowflake` v1 (fallback) | Warehouses, databases, schemas, roles, grants, stages, semantic objects | Per [ADR-008](../docs/decisions/ADR-008-terraform-providers.md): use the newer official `snowflakedb/snowflake` provider wherever it already covers a resource; fall back to `Snowflake-Labs/snowflake` v1 with `preview_features_enabled` declared explicitly for anything not yet migrated. Every module under `modules/snowflake/` documents which provider it uses and why in its own README |

## Environments

Only `environments/dev/` ships full HCL in this repo — it is the environment actually applied against a personal-budget Azure/Databricks/Snowflake sandbox and torn down between demos (see [ARCHITECTURE.md §21](../ARCHITECTURE.md#21-production-readiness--honesty-note)). `staging/` and `prod/` are documented as the same module graph with different `.tfvars` and progressively stricter approval gates — see their own READMEs.

## State & CI/CD

- `dev/main.tf` declares (commented-out by default) an `azurerm` remote backend — this portfolio does not ship a live backend, so `terraform init` defaults to local state unless you configure your own storage account.
- Plan/apply is wired into `.github/workflows/terraform.yml` (owned by the CI/CD workstream, not this directory): lint → `terraform plan` on PR → `terraform apply` on merge, environment-gated for staging/prod.
- [ROADMAP.md](../ROADMAP.md) Sprint 1 provisions the ADLS module standalone; Sprint 7 provisions the Snowflake modules; Sprint 16 is when the full `dev` environment is required to `terraform destroy && terraform apply` unattended end-to-end.

## Local-first note

Per [ARCHITECTURE.md §1](../ARCHITECTURE.md#1-design-principles) (local-first development), none of this is required to run the pipeline locally against MinIO/Postgres. It exists to demonstrate IaC competence and is provisioned on demand.
