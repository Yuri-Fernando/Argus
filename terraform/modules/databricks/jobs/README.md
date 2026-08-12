# modules/databricks/jobs

Provisions only the workspace-level resources job runs depend on — an instance pool for faster/cheaper job-cluster starts, and a dedicated service principal jobs run as — **not** the job bodies themselves. Task graphs, schedules, and job-cluster specs for the Bronze→Silver→Gold pipeline are declared in `databricks/workflows/databricks.yml` (a Databricks Asset Bundle) and deployed via `databricks bundle deploy` from CI, per [`databricks/README.md`](../../../../databricks/README.md). Keeping job bodies out of Terraform avoids two systems fighting over the same ownership.

Built in **Sprint 2** ([ROADMAP.md](../../../../ROADMAP.md)).
