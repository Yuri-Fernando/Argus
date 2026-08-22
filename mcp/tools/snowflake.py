"""Parameterized, read-only Snowflake query tool for the MCP server.

Built in ROADMAP.md Sprint 13. This tool exists so an agent can answer ad hoc analytical
questions the fixed tool set (`get_sales_metrics`, etc.) doesn't cover, without falling back to
"let the LLM write and run arbitrary SQL" — the exact anti-pattern ADR-004 rejects.

Why this tool is read-only, and always will be
--------------------------------------------
ADR-007 (AI guardrails) requires every MCP tool to be scoped to the minimum permission needed.
For a query tool reachable by an LLM-driven agent, the minimum permission is SELECT — never
INSERT/UPDATE/DELETE/MERGE/CREATE/DROP. This is enforced at three layers, deliberately
redundant:

    1. Statement-shape validation in `_is_select_only()` below, rejecting any statement that
       doesn't parse as a single read-only SELECT.
    2. The Snowflake role this tool authenticates as (TODO below) is provisioned via Terraform
       with SELECT-only grants on the ANALYTICS/SEMANTIC schemas — see
       terraform/modules/snowflake/ (ROADMAP.md Sprint 7) and ARCHITECTURE.md §16. Even a bug in
       layer 1 cannot escalate past what the warehouse role itself is allowed to do.
    3. Snowflake masking policies on PII columns (ARCHITECTURE.md §16) apply regardless of which
       layer executes the query, so even an approved SELECT never returns raw email/phone/
       document_hash to a role that isn't entitled to see it unmasked.

A write-capable variant of this tool is intentionally not offered, not even behind a flag —
adding one would require a new ADR superseding ADR-007's least-privilege principle, not just a
parameter.
"""

from __future__ import annotations

import re
from typing import Any

import duckdb

# Reuse the exact same process-cached DuckDB connection `mcp/tools/analytics.py` builds, rather
# than each module independently calling `build_warehouse(rebuild=True)` — DuckDB locks the
# warehouse file for the lifetime of an open connection, so two independent rebuilds in the same
# process (one per module) fail: the second rebuild's `DB_PATH.unlink()` cannot remove a file the
# first connection still has open. Sharing one `@lru_cache`-wrapped connection avoids that.
from mcp.tools.analytics import _connection

# Extremely conservative allow-list check: the statement must start with SELECT (after
# stripping leading whitespace/comments) and must not contain any DML/DDL keyword anywhere,
# including inside CTEs. This is a defense-in-depth guard, not the only guard — see the module
# docstring's three-layer explanation above.
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|DROP|ALTER|GRANT|REVOKE|TRUNCATE|CALL|COPY)\b",
    re.IGNORECASE,
)
_SELECT_PREFIX = re.compile(r"^\s*(--.*\n\s*)*SELECT\b", re.IGNORECASE)


def _is_select_only(sql: str) -> bool:
    """Return True only if `sql` looks like a single read-only SELECT statement."""
    if not _SELECT_PREFIX.match(sql):
        return False
    if _FORBIDDEN_KEYWORDS.search(sql):
        return False
    if ";" in sql.strip().rstrip(";"):
        # Reject statement chaining (`SELECT ...; DROP ...`).
        return False
    return True


def query_snowflake(sql: str, params: dict[str, Any] | None = None, limit: int = 500) -> dict[str, Any]:
    """Run a parameterized, read-only SELECT query against Snowflake.

    Args:
        sql: a parameterized SELECT statement. Use Snowflake bind-parameter syntax
            (`%(name)s`) for any value — never interpolate untrusted values into the string.
            NOTE (local-dev wiring): this executes against the local DuckDB warehouse (see
            below), whose Python driver expects its own named-parameter syntax (`$name`), not
            Snowflake's `%(name)s` — a real difference between the two backends, documented
            here rather than silently papered over. `sql` is passed through to
            `duckdb.execute()` unmodified either way.
        params: bind parameters referenced by `sql`.
        limit: hard row cap enforced server-side (default 500), independent of any LIMIT clause
            already present in `sql`.

    Returns:
        {
            "rows": list[dict],
            "row_count": int,
            "truncated": bool,   # True if more rows existed than `limit`
            "rejected": bool,    # True if `sql` failed the read-only validation and was not run
            "reason": str | None,
        }
    """
    if not _is_select_only(sql):
        return {
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "rejected": True,
            "reason": "Only single, read-only SELECT statements are permitted (ADR-007).",
        }

    # TODO(Sprint 7 / snowflake): open a connection using the SELECT-only Terraform-provisioned
    # role (terraform/modules/snowflake/roles/) via Key Vault-sourced credentials (never
    # hardcoded), bind `params`, apply `LIMIT {limit}` server-side if the statement doesn't
    # already have a tighter one, and map the cursor result to list[dict]. Recommended library:
    # the official `snowflake-connector-python` (not yet in pyproject.toml — add it alongside
    # this wiring, scoped to the read-only role only).
    #
    # LOCAL-DEV WIRING (this session): the TODO above describes the real Snowflake read-only
    # role — that still does not exist as a live account in this environment. What's wired here
    # instead is the exact same local-dev equivalent every other governed-metric tool in this
    # repo already stands on: `snowflake/local_runner.py::build_warehouse()`, the local DuckDB
    # warehouse built from the same DDL in `snowflake/ddl/*.sql` (portable ANSI SQL that also
    # runs unmodified on a real Snowflake account per that module's own docstring). The
    # three-layer guardrail above is unaffected — `_is_select_only()` still runs first, and this
    # path only ever issues the validated, parameterized SELECT it approved.
    con = _connection()
    try:
        cursor = con.execute(sql, params or {})
        column_names = [d[0] for d in cursor.description] if cursor.description else []
        fetched = cursor.fetchall()
    except duckdb.Error as exc:
        return {
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "rejected": True,
            "reason": f"Query failed against the local DuckDB warehouse: {exc}",
        }

    truncated = len(fetched) > limit
    limited_rows = fetched[:limit]
    rows = [dict(zip(column_names, row)) for row in limited_rows]

    return {
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "rejected": False,
        "reason": None,
    }
