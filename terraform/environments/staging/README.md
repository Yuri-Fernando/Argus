# environments/staging/

Mirrors [`environments/dev/`](../dev/) — the same module graph (`modules/azure`, `modules/databricks`, `modules/snowflake`), wired together the same way in a `main.tf` of identical shape. Only two things differ, deliberately kept out of this portfolio to stay demo-sized rather than duplicating ~500 lines of near-identical HCL:

1. **`terraform.tfvars`** — staging-sized SKUs (e.g. `Standard_LRS` → `Standard_ZRS`, larger Databricks cluster autoscale ceiling, a dedicated Snowflake warehouse sized `SMALL` instead of `XSMALL`), staging-specific naming (`eci-staging-*`, see [`../../policies/naming.md`](../../policies/naming.md)), and its own resource group / Key Vault / catalog names so `dev` and `staging` never collide.
2. **Approval gates** — `terraform plan` still runs automatically on every PR touching `terraform/`, but `terraform apply` against staging requires a manual approval step in [`.github/workflows/terraform.yml`](../../../.github/workflows/terraform.yml) (owned by the CI/CD workstream, not `terraform/`) — a GitHub Environment protection rule with one required reviewer.

## Provisioning

```bash
cd terraform/environments/staging
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars   # requires the CI approval gate in practice
```

See [ARCHITECTURE.md §18](../../../ARCHITECTURE.md#18-layer-15--infrastructure-as-code) and [ADR-008](../../../docs/decisions/ADR-008-terraform-providers.md) for the underlying provider strategy shared by every environment.
