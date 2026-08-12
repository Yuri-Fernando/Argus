"""Boundary note: Databricks access does NOT go through this custom MCP server.

Built (as a documentation boundary, not an implementation) in ROADMAP.md Sprint 13, formalized
against the Databricks Managed MCP server in Sprint 15.

Why this file registers no tools
---------------------------------
ARCHITECTURE.md §15 lists the **Databricks Managed MCP server** (Genie + Unity Catalog + AI
Search + custom functions) as GA since early 2026, separate from this project's custom MCP
server (`mcp/server/`). The Managed MCP server's defining property — and the reason it is used
directly instead of being re-wrapped here — is that every tool call made through it **inherits
the caller's Unity Catalog permissions natively**. Re-implementing a `query_databricks`-style
tool in this file would mean re-deriving that permission inheritance ourselves (essentially
reimplementing Unity Catalog RBAC checks in application code), which is both redundant and a
strictly worse security posture than delegating to the platform's own governed integration — the
same reasoning ADR-004 applies to why this project uses MCP at all instead of raw SQL access.

Where Databricks tool access actually happens
----------------------------------------------
- Agents that need Databricks/Genie/Unity-Catalog-governed data connect an MCP client directly
  to the **Databricks Managed MCP** endpoint, alongside (not instead of) this custom server.
  Wiring and evaluation of that connection is ROADMAP.md Sprint 15's scope, benchmarked in
  `benchmarks/` against the custom server and Snowflake Cortex Agents for the same 10 questions.
- `agents/orchestrator/customer_intelligence_agent.py`'s tool-routing node is where the choice
  between "custom MCP server", "Databricks Managed MCP", "Power BI MCP" and "Golden Record +
  Graph" is made per-intent — see that module's `select_tools` node.

What belongs in this file, if anything, later
------------------------------------------------
If a future sprint identifies platform-specific glue that the Managed MCP server genuinely
cannot express (e.g. translating an intent into the specific Genie space/AI Search index to
target), that glue would live here as a thin routing helper — never as a reimplementation of
Databricks data access itself. As of Sprint 13/15 no such gap has been identified, so this
module intentionally contains no tool functions.
"""

from __future__ import annotations

# Intentionally no `@mcp.tool()` registrations in this module — see module docstring.
