# modules/databricks/unity_catalog

Provisions the `customer_intelligence` catalog and its five schemas — `bronze`, `silver`, `gold`, `ml`, `monitoring` — backed by a storage credential/external location pointing at the ADLS Gen2 `gold` container, matching [ARCHITECTURE.md §6](../../../../ARCHITECTURE.md#6-layer-3--lakehouse-azure-databricks) exactly. This is the Terraform-managed mirror of the human-readable SQL DDL in [`databricks/unity_catalog/`](../../../../databricks/unity_catalog/) — the SQL is for local review/onboarding, this module is what actually applies in CI.

Built in **Sprint 2** ([ROADMAP.md](../../../../ROADMAP.md)), extended with masking/RBAC in **Sprint 16**.
