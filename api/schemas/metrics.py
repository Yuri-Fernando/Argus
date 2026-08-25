"""Pydantic response model for `GET /metrics`."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class MetricsResponse(BaseModel):
    """Response for `GET /metrics` — one entry per canonical metric in
    `docs/semantic-dictionary.md`, as computed by `snowflake/local_runner.py::run_all_metrics`.
    A metric's value is either a number, a dict (e.g. CLV's avg/min/max/median), or the string
    `"SKIPPED: <reason>"` when the underlying data isn't available locally (see
    `snowflake/local_runner.py::SKIPPED_METRICS`) — surfaced as-is rather than hidden, so this
    endpoint never silently claims a metric exists when it doesn't.
    """

    metrics: dict[str, Any]
