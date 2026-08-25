# mcp/

Custom **Model Context Protocol (MCP)** server: the platform's own tool + resource + prompt
surface for agents — [ARCHITECTURE.md §15](../ARCHITECTURE.md#15-layer-12--mcp--agentic-ai),
built in **[ROADMAP.md Sprint 13](../ROADMAP.md)**. Design rationale (why MCP instead of
letting an LLM generate SQL directly) is in
[ADR-004](../docs/decisions/ADR-004-mcp-strategy.md).

```
mcp/
├── server/
│   └── server.py           # FastMCP app — registers every tool below
├── tools/
│   ├── customer.py          # get_customer, search_customers, get_customer_orders, get_customer_graph
│   ├── analytics.py         # get_sales_metrics
│   ├── quality.py           # get_customer_quality, get_data_quality, get_pipeline_status
│   ├── ml.py                 # get_customer_churn, get_model_metrics, recommend_action
│   ├── snowflake.py           # query_snowflake (parameterized, read-only by design)
│   └── databricks.py           # boundary note — see "Why no databricks.py tools" below
├── resources/
│   ├── catalog.py            # Unity Catalog / Snowflake catalog structure as an MCP resource
│   └── documentation.py       # semantic dictionary + access control docs as MCP resources
└── prompts/
    └── enterprise_analytics.py # reusable "ask a business question" prompt templates
```

## Why MCP instead of direct SQL from the LLM

Full reasoning in [ADR-004](../docs/decisions/ADR-004-mcp-strategy.md). Short version: a
custom MCP server gives every agent-to-data interaction a **named, typed tool contract**
(explicit input/output schema, independently testable, independently scoped) instead of a
"chatbot that writes SQL" pattern with no permission boundary. This is the differentiator the
project is built to demonstrate, not an implementation detail.

## Tool list (ARCHITECTURE.md §15)

`get_customer` · `search_customers` · `get_customer_quality` · `get_customer_churn` ·
`get_customer_orders` · `get_customer_graph` · `get_sales_metrics` · `get_data_quality` ·
`get_model_metrics` · `get_pipeline_status` · `query_snowflake` · `recommend_action`

Every tool function lives in `mcp/tools/`, is imported into `mcp/server/server.py`, and is
registered there with `@mcp.tool()`. `mcp/server/server.py` itself contains no business logic —
it is a thin registration layer, so tools stay unit-testable without spinning up an MCP session.

## Why no `databricks.py` tools

`mcp/tools/databricks.py` exists but intentionally registers nothing. Databricks access for
this project goes through the **Databricks Managed MCP server** directly (GA since early 2026 —
ARCHITECTURE.md §15), which inherits the caller's Unity Catalog permissions natively. Re-wrapping
that as a custom tool here would duplicate a governed integration instead of reusing it — see
the module docstring in that file for the full boundary note, and
[ROADMAP.md Sprint 15](../ROADMAP.md) for where it gets wired up and benchmarked against the
custom server and Cortex Agents.

## Guardrails (ADR-007)

- Every tool call is scoped to the **minimum permission** needed for that call — no tool
  authenticates as a generic admin role. See each tool module for the specific scoping note.
- `query_snowflake` is **read-only by design** — see the comment in `mcp/tools/snowflake.py`.
- `recommend_action` **never executes anything**. It returns a recommendation object and
  enqueues it via [`agents/recommendation/approval_queue.py`](../agents/recommendation/approval_queue.py)
  per [ADR-006](../docs/decisions/ADR-006-human-in-the-loop.md).

## Known constraint: package name collision

This module's own top-level package is named `mcp/`, matching the repo's "one directory per
architecture layer" convention — and that collides with the third-party `mcp` SDK package
(`pip install mcp`, used for `FastMCP` itself) if the repository root ends up on `sys.path[0]`
(e.g. running `python -m mcp.server.server` from the repo root inserts the repo root first,
so `import mcp` resolves to this local package instead of site-packages). Until the repo adopts
a `src/` layout (tracked as a later-sprint cleanup, not required for Sprint 13's acceptance
criteria), run the server either as a script (`python mcp/server/server.py`, which puts the
script's own directory — not the repo root — on `sys.path[0]`) or via an editable install
(`pip install -e .`) invoked from outside the repo root.

## Run it

```bash
# Sprint 13 acceptance criteria: connect from Claude Desktop / Claude Code and call
# get_customer_churn(customer_id) / get_data_quality() end-to-end.
python mcp/server/server.py
```

## Related

- [ARCHITECTURE.md §15 — Layer 12: MCP & Agentic AI](../ARCHITECTURE.md#15-layer-12--mcp--agentic-ai)
- [ADR-004 — MCP strategy](../docs/decisions/ADR-004-mcp-strategy.md)
- [ADR-006 — Human-in-the-loop](../docs/decisions/ADR-006-human-in-the-loop.md)
- [ADR-007 — AI guardrails](../docs/decisions/ADR-007-ai-guardrails.md)
- [agents/README.md](../agents/README.md) — the consumers of these tools
