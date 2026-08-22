"""Platform metrics — thin wrapper around `snowflake/local_runner.py`.

Reuses `build_warehouse()` / `run_all_metrics()` as-is rather than recomputing metric logic in
the API layer: `snowflake/local_runner.py` already implements the canonical metric definitions
from `docs/semantic-dictionary.md` against the local DuckDB warehouse, and duplicating that SQL
here would be exactly the kind of drift ARCHITECTURE.md §1 warns against.

The warehouse build reads several-thousand-row parquet files and is not free — it is built once
per process (module-level cache) and reused across requests, rebuilt only if a caller explicitly
asks for a refresh.
"""

from __future__ import annotations

import duckdb

from snowflake.local_runner import build_warehouse, run_all_metrics

_connection: duckdb.DuckDBPyConnection | None = None


def _get_connection(*, rebuild: bool = False) -> duckdb.DuckDBPyConnection:
    global _connection
    if _connection is None or rebuild:
        _connection = build_warehouse(rebuild=True)
    return _connection


def get_all_metrics(*, rebuild: bool = False) -> dict:
    """Return every canonical platform metric, via `snowflake.local_runner.run_all_metrics`."""
    con = _get_connection(rebuild=rebuild)
    return run_all_metrics(con)
