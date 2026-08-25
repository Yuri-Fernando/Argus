# environments/prod/

Mirrors [`environments/dev/`](../dev/) and [`environments/staging/`](../staging/) — same module graph, same `main.tf` shape, different `terraform.tfvars` (production-sized SKUs, `eci-prod-*` naming per [`../../policies/naming.md`](../../policies/naming.md)) and the strictest approval path in [`.github/workflows/terraform.yml`](../../../.github/workflows/terraform.yml) (owned by the CI/CD workstream):

- `terraform plan` runs on PR, output posted as a PR comment for review.
- `terraform apply` requires **two** required reviewers on the `production` GitHub Environment, plus a passing `security.yml` scan (`tfsec`/`checkov`-class static analysis) before the gate unlocks.
- No direct `terraform apply` from a developer machine against prod state — only the pipeline's OIDC-federated identity holds apply credentials.

## Honesty note

This is a portfolio project — there is no real "production" customer base behind this environment. It exists to demonstrate that the module graph and naming/tagging conventions are environment-parameterized correctly, not because a third live environment is actually being run continuously. See [ARCHITECTURE.md §21](../../../ARCHITECTURE.md#21-production-readiness--honesty-note).

## Provisioning

```bash
cd terraform/environments/prod
terraform init
terraform plan -var-file=terraform.tfvars
# apply is pipeline-only in practice — see .github/workflows/terraform.yml
```
