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

## How to actually apply this for real

This is documentation only — nothing below is run as part of validation work in this repo. It is the sequence someone (including a future you) would follow to stand `environments/dev` up against a real Azure/Databricks/Snowflake sandbox.

### 1. Prerequisites

- Terraform >= 1.9.0 (`terraform version`).
- An Azure subscription with rights to create resource groups, and the Azure CLI installed.
- A Databricks workspace host reachable once the Azure resources exist (the workspace itself is provisioned by `modules/databricks/workspace`, but a Databricks *account* and Azure subscription linkage must already exist).
- A Snowflake account with a user that has rights to create warehouses/databases/roles (typically `SYSADMIN` or an equivalent custom role).

### 2. Authenticate to each provider

```bash
# Azure — az login opens a browser; azurerm then uses your logged-in identity
az login
az account set --subscription "<subscription-id>"

# Databricks — prefer Entra ID / az login-based auth over a long-lived PAT;
# if a PAT is unavoidable for a personal sandbox, generate one from the
# workspace UI (User Settings -> Developer -> Access tokens) and treat it
# like any other secret (never commit it).

# Snowflake — the snowflake and snowflakelabs providers both authenticate
# via the variables below (account/user/password/role); for anything beyond
# a personal sandbox, prefer key-pair auth over a plaintext password.
```

### 3. Configure variables

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Fill in `terraform.tfvars` with real values — `azure_subscription_id`, `azure_tenant_id`, `databricks_host`, `snowflake_account`, etc. (see the file's own comments). **Never commit `terraform.tfvars`** — it's already covered by `.gitignore`. Secrets (`databricks_token`, `snowflake_password`) are better injected as `TF_VAR_*` environment variables in CI than left in the file at all:

```bash
export TF_VAR_databricks_token="<token>"
export TF_VAR_snowflake_password="<password>"
```

### 4. Plan and apply

```bash
terraform init
terraform plan    # review before applying anything against real cloud billing
terraform apply
```

### 5. Tear down when done

Cloud resources here are provisioned on demand and torn down between demo sessions to control cost (see [docs/deployment.md](../docs/deployment.md) and [ARCHITECTURE.md §21](../ARCHITECTURE.md#21-production-readiness--honesty-note)):

```bash
terraform destroy
```

### Remote state (optional)

By default `dev/main.tf` uses local state (`terraform.tfstate`, gitignored) so `terraform init` works with zero setup. To use a real Azure Storage-backed remote state, provision a storage account/container out-of-band first (a backend config can't create the backend it depends on), then uncomment and fill in the `backend "azurerm"` block at the top of `dev/main.tf` and re-run `terraform init -migrate-state`.
