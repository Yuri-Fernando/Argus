# modules/databricks/clusters

Provisions a workspace-level **cluster policy** (node types, DBR version, autotermination, mandatory tags) that every job cluster must comply with, plus one shared interactive cluster for notebook exploration. The job clusters that actually run the Bronze→Silver→Gold pipeline are declared inside the Databricks Asset Bundle (`databricks/workflows/`, deployed via `databricks bundle deploy`) as `job_clusters` blocks referencing this policy — Terraform owns the guardrail, DABs own the job body, per [ARCHITECTURE.md §6](../../../../ARCHITECTURE.md#6-layer-3--lakehouse-azure-databricks).

Built in **Sprint 2** ([ROADMAP.md](../../../../ROADMAP.md)).
