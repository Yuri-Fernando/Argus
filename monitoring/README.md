# monitoring/

Observability & FinOps stack — ARCHITECTURE.md [§17](../ARCHITECTURE.md#17-layer-14--observability--finops), built in **Sprint 16**. OpenTelemetry traces spanning pipeline → ML → LLM → MCP → API calls, exported to Prometheus, visualized in Grafana.

```
monitoring/
├── prometheus/
│   └── prometheus.yml          # scrape config — mounted by docker-compose.yml at repo root
├── grafana/
│   └── dashboards/
│       └── platform_observability.json   # Platform Observability dashboard (mirrors the Power BI page of the same name)
└── opentelemetry/
    └── README.md                # tracing convention: span naming, trace-id propagation through MCP
```

## Local stack

`docker compose up` (root `docker-compose.yml`) brings up `prometheus` (port `9090`) and `grafana` (port `3000`, `admin`/`admin`) pre-wired to this directory. Prometheus scrapes `/metrics` endpoints exposed by the platform's own services (API, MCP server, pipeline exporter — see `prometheus/prometheus.yml`); Grafana is provisioned manually with the dashboard JSON in `grafana/dashboards/` until Sprint 16 adds datasource/dashboard provisioning files.

## Metrics tracked

Matches the metric list in [ARCHITECTURE.md §17](../ARCHITECTURE.md#17-layer-14--observability--finops): `pipeline_duration`, `rows_processed`, `dq_score`, `ml_latency`, `agent_latency`, `mcp_calls`, `llm_tokens`. FinOps metrics (Databricks DBU, Snowflake credits, LLM token cost, cost-per-1M-records, cost-per-agent-request) are layered on top of the same Prometheus/Grafana stack rather than a separate tool.

## Instrumentation ownership

The metrics/traces themselves are emitted by code owned by other workstreams (`api/`, `mcp/`, `agents/`, `lakehouse/`, `ml/`) using the `opentelemetry-api`/`opentelemetry-sdk`/`prometheus-client` dependencies already declared in `pyproject.toml`. This directory owns the **collection and visualization config**, not the instrumentation itself — see `opentelemetry/README.md` for the convention every workstream instruments against.
