# monitoring/opentelemetry/

Tracing convention for the platform — ARCHITECTURE.md [§17](../../ARCHITECTURE.md#17-layer-14--observability--finops), built in **Sprint 16**. This document is conceptual: the actual `opentelemetry-api`/`opentelemetry-sdk` instrumentation lives inside the code it traces (`api/`, `mcp/`, `agents/`, `lakehouse/`, `ml/` — each owned by its own workstream). What follows is the contract every workstream instruments against, so traces compose into one coherent end-to-end view instead of five disconnected fragments.

## Why this matters

A single user-facing question — *"Is customer X eligible for a refund?"* — crosses five process boundaries: Power BI or a chat UI → `api/` → an `agents/` LangGraph run → one or more `mcp/` tool calls → `lakehouse/`/Snowflake/Cortex data access. Without a shared tracing convention, debugging a slow or wrong answer means grepping five separate log streams by hand. With one, it's a single trace in Grafana (via Prometheus exemplars) or a Jaeger-compatible backend, expandable end-to-end.

## Span naming convention

Format: `{layer}.{component}.{operation}` — lowercase, dot-separated, stable across releases (span names are a query surface, not free text).

| Layer | Example span names |
|---|---|
| `api` | `api.route.get_customer`, `api.middleware.auth` |
| `agent` | `agent.customer_intelligence.run`, `agent.customer_intelligence.tool_selection`, `agent.recommendation.human_approval_wait` |
| `mcp` | `mcp.server.tool_call`, `mcp.client.request` |
| `pipeline` | `pipeline.bronze.ingest`, `pipeline.silver.transform`, `pipeline.gold.build` |
| `dq` | `dq.checkpoint.run`, `dq.suite.validate` |
| `ml` | `ml.churn.predict`, `ml.churn.explain` (SHAP) |
| `llm` | `llm.completion`, `llm.embedding` |
| `warehouse` | `warehouse.snowflake.query`, `warehouse.cortex.analyst` |

Every span sets at minimum: `service.name`, `service.version` (git SHA), and a `customer_intelligence.*` resource attribute namespace (e.g. `customer_intelligence.master_customer_id` when the span is customer-scoped) — never the raw synthetic PII fields themselves (see [governance/pii.md](../../governance/pii.md)).

## Trace-id propagation through MCP calls

MCP transport (JSON-RPC over stdio or HTTP, per the MCP spec) does not natively carry a W3C `traceparent` header the way HTTP-to-HTTP calls do. The convention here:

1. The **calling agent** (LangGraph node) starts or continues a trace and reads the current `traceparent` from its own OTel context.
2. Before invoking an MCP tool, the agent injects `traceparent` (and `tracestate` if present) as an explicit field on the **MCP tool-call request payload** — not a transport header, since stdio has none — following the pattern `{"_meta": {"traceparent": "..."}}` reserved by the MCP spec for out-of-band metadata.
3. The **MCP server** (`mcp/server`), on receiving a tool call, extracts `_meta.traceparent` if present and starts its `mcp.server.tool_call` span as a **child** of that remote context (`opentelemetry.trace.set_span_in_context` with a manually reconstructed `SpanContext`); if absent (e.g. a direct Claude Desktop call with no upstream trace), it starts a new root trace instead of failing.
4. Any downstream call the MCP server makes (Snowflake query, Databricks SQL, Unity Catalog lookup) propagates the same context further, so a single trace can span **UI → API → Agent → MCP → Warehouse** in one waterfall.

This mirrors how Databricks Managed MCP and Power BI MCP behave as black boxes from this platform's point of view (§15) — for those, the custom MCP server's outbound call to them is the trace boundary; anything inside the managed MCP is out of scope for this repo's tracing but still shows up as a single child span with `component=external_mcp`.

## Metrics vs. traces

Traces answer *"why was this one request slow / what did it touch"*; Prometheus metrics (`monitoring/prometheus/prometheus.yml`) answer *"is the system healthy right now, in aggregate."* The OTel SDK is configured with both an OTLP trace exporter (to a Jaeger-compatible collector, documented but not required for local dev) and a Prometheus metrics exporter, so instrumenting once (`with tracer.start_as_current_span(...)`) yields both a trace and, via span duration histograms, the `pipeline_duration` / `agent_latency` / `ml_latency` Prometheus metrics scraped in `prometheus.yml` — one instrumentation call, not two.

## Local dev vs. cloud

Locally, exporting traces is optional (`OTEL_TRACES_EXPORTER=console` or unset/no-op) — the metrics half of instrumentation (Prometheus) is what `docker-compose.yml` actually wires up, matching the local-first principle in ARCHITECTURE.md §1. Full distributed tracing to a collector is a cloud-environment concern, configured via `OTEL_EXPORTER_OTLP_ENDPOINT` in `.env` / Key Vault, documented further once Sprint 16 lands the collector deployment.
