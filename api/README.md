# api/

A **FastAPI** service exposing the same customer-intelligence data surface as REST/JSON, for
consumers that aren't MCP-aware — [ARCHITECTURE.md §20](../ARCHITECTURE.md#20-repository-structure).
Built with `fastapi` + `uvicorn` (already declared in [`pyproject.toml`](../pyproject.toml)).

```
api/
├── routes/       # one router module per resource group (see below)
├── schemas/       # Pydantic request/response models — the REST contract
├── services/        # business logic, shared with mcp/tools/ where the underlying query is identical
└── middleware/         # auth, request logging, rate limiting
```

## Route groups

Mirrors the MCP tool list in [ARCHITECTURE.md §15](../ARCHITECTURE.md#15-layer-12--mcp--agentic-ai) —
same underlying queries, plain HTTP/JSON instead of MCP tool calls:

| Route | Mirrors MCP tool |
|---|---|
| `GET /customers`, `GET /customers/{id}` | `search_customers`, `get_customer` |
| `GET /customers/{id}/churn` | `get_customer_churn` |
| `GET /customers/{id}/quality` | `get_customer_quality` |
| `GET /metrics` | `get_sales_metrics` |
| `GET /data-quality` | `get_data_quality` |
| `GET /pipeline-status` | `get_pipeline_status` |

## Why this duplicates `mcp/` — on purpose

[`mcp/`](../mcp/) (owned by another workstream — see [`mcp/README.md`](../mcp/README.md) and
[ADR-004](../docs/decisions/ADR-004-mcp-strategy.md)) exposes this same data as typed MCP tools,
for LLM agents. `api/` exposes it as plain REST, for everything that is **not** an agent: a future
hosted demo UI (backlog item 1 in [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md)),
a curl call, a non-Claude client. This is **intentional duplication of the data surface, not
accidental drift** — the two layers speak different protocols to different audiences, and both
should be free to evolve their own request/response shape without one blocking the other. Where
the underlying query logic is identical (e.g. "what's this customer's churn score"), it lives once
in `api/services/` (or a shared internal module) and is imported by both, so the duplication is at
the protocol boundary, not in the query logic itself.

## Related

- [ARCHITECTURE.md §15 — Layer 12: MCP & Agentic AI](../ARCHITECTURE.md#15-layer-12--mcp--agentic-ai) — the tool list this mirrors
- [`mcp/`](../mcp/) — the MCP-native equivalent of this surface (separate workstream, referenced not duplicated here)
- [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) — backlog item 1, hosted demo UI as the primary consumer of this API
