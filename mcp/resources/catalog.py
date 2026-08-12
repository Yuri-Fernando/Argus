"""MCP resource: read-only catalog structure (Unity Catalog + Snowflake).

Built in ROADMAP.md Sprint 13. Exposes the catalog/schema/table topology as an MCP *resource*
(not a tool) — resources are for grounding an agent's understanding of what data exists and how
it's organized, distinct from tools, which fetch specific values. An agent reads this resource
once at the start of a session (or when it's unsure a table exists) rather than guessing table
names.

This module only lists structure (catalog → schema → table → column names/comments) — it never
returns row data. Listing structure at the Unity Catalog / Snowflake INFORMATION_SCHEMA level is
itself governed by the same RBAC the underlying platforms enforce (ARCHITECTURE.md §16): a
caller only sees objects their role is granted USAGE/SELECT on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mcp.server.fastmcp import FastMCP


@dataclass
class ColumnInfo:
    """A single column's catalog metadata."""

    name: str
    data_type: str
    comment: str | None = None


@dataclass
class TableInfo:
    """A single table/view's catalog metadata."""

    name: str
    kind: str  # "table" | "view" | "metric_view" | "semantic_view"
    columns: list[ColumnInfo] = field(default_factory=list)
    comment: str | None = None


def get_unity_catalog_structure(catalog: str = "customer_intelligence") -> dict[str, Any]:
    """List the Unity Catalog schema/table topology for `catalog`.

    Args:
        catalog: Unity Catalog name (default: this project's catalog — ARCHITECTURE.md §6:
            `customer_intelligence` with schemas `bronze`, `silver`, `gold`, `ml`, `monitoring`).

    Returns:
        {"catalog": str, "schemas": {schema_name: {"tables": list[dict] (TableInfo-shaped)}}}
    """
    # TODO(Sprint 2-7 / databricks/unity_catalog): query
    # `information_schema.tables` / `information_schema.columns` (or the Databricks SDK's
    # catalog client) scoped to the caller's own USAGE grants — never a service-principal with
    # catalog-wide admin rights for this read path.
    return {"catalog": catalog, "schemas": {}}


def get_snowflake_catalog_structure(database: str = "CUSTOMER_INTELLIGENCE") -> dict[str, Any]:
    """List the Snowflake database/schema/table topology for `database`.

    Args:
        database: Snowflake database name (default: this project's DWH — ARCHITECTURE.md §12:
            `CUSTOMER_INTELLIGENCE` with schemas `RAW`, `STAGING`, `CORE`, `ANALYTICS`,
            `SEMANTIC`, `AI`).

    Returns:
        {"database": str, "schemas": {schema_name: {"tables": list[dict] (TableInfo-shaped)}}}
    """
    # TODO(Sprint 7-8 / snowflake): query `INFORMATION_SCHEMA.TABLES` /
    # `INFORMATION_SCHEMA.COLUMNS`, scoped to the same read-only role `query_snowflake`
    # authenticates as (mcp/tools/snowflake.py) — one governed identity for both structure
    # discovery and data reads.
    return {"database": database, "schemas": {}}


def register(mcp: FastMCP) -> None:
    """Register this module's resources on the given FastMCP server instance.

    Kept as an explicit `register()` function (rather than importing `mcp` from
    `mcp/server/server.py`) so this module has no import-time dependency on the server module —
    it can be unit tested by calling `get_unity_catalog_structure()` /
    `get_snowflake_catalog_structure()` directly.
    """

    @mcp.resource("catalog://unity-catalog/{catalog}")
    def unity_catalog_resource(catalog: str = "customer_intelligence") -> dict[str, Any]:
        """Unity Catalog structure resource — see get_unity_catalog_structure()."""
        return get_unity_catalog_structure(catalog)

    @mcp.resource("catalog://snowflake/{database}")
    def snowflake_catalog_resource(database: str = "CUSTOMER_INTELLIGENCE") -> dict[str, Any]:
        """Snowflake catalog structure resource — see get_snowflake_catalog_structure()."""
        return get_snowflake_catalog_structure(database)
