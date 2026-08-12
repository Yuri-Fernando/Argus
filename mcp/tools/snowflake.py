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
    return {
        "rows": [],
        "row_count": 0,
        "truncated": False,
        "rejected": False,
        "reason": None,
    }
