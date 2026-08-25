# modules/databricks/permissions

Provisions the three workspace groups (`data-engineers`, `data-analysts`, `ml-engineers`) and grants them least-privilege access to the Unity Catalog catalog and job-cluster policy — group-based, never per-user, matching the RBAC model in [ARCHITECTURE.md §16](../../../../ARCHITECTURE.md#16-layer-13--governance--security) that every MCP tool call also inherits from (ARCHITECTURE.md §15).

Built in **Sprint 16** ([ROADMAP.md](../../../../ROADMAP.md)) as part of the governance hardening pass.
