"""`/metrics` route — reuses `snowflake/local_runner.py::run_all_metrics()`, per this task's
scope note to not recompute platform metrics in the API layer.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas.metrics import MetricsResponse
from api.services import metrics_service

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(rebuild: bool = Query(False, description="Force a warehouse rebuild before computing")) -> MetricsResponse:
    """All canonical platform metrics (revenue, AOV, churn_rate, repeat_rate, CLV, ...)."""
    return MetricsResponse(metrics=metrics_service.get_all_metrics(rebuild=rebuild))
