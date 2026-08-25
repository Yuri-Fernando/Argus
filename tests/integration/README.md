# tests/integration/

Like `tests/unit/`, this directory intentionally stays near-empty. Real integration tests — the ones that spin up or reach into the local Docker stack (`docker-compose.yml`: MinIO, Postgres, MLflow) or call a real MCP server end-to-end — land **alongside the code they test**, e.g. `lakehouse/bronze/test_ingest_integration.py`, `mcp/server/test_tools_integration.py`, `mdm/entity_resolution/test_run_integration.py`.

Convention: any test file with `_integration` in its name (or marked `@pytest.mark.integration`) is assumed to require the local stack to be up (`make up`) and is skipped/xfailed gracefully when it isn't reachable, so `make test` never hard-fails an environment that hasn't run `docker compose up` — the same "don't punish an unset-up environment" principle applied in `tests/data/test_no_real_pii.py`.

Centralized here only when a test genuinely spans multiple top-level modules with no single natural home (e.g. "ingestion → Bronze → Silver end-to-end" touching both `ingestion/` and `lakehouse/`); the default is still co-location. See [tests/README.md](../README.md).
