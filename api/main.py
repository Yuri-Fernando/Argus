"""api/main.py — FastAPI app entrypoint.

Run locally:
    uvicorn api.main:app --reload --port 8010

See `api/README.md` for the full route table and why this REST surface intentionally duplicates
`mcp/`'s tool set at the protocol boundary rather than sharing it.
"""

from __future__ import annotations

from fastapi import FastAPI

from api.routes import customer, health, metrics

app = FastAPI(
    title="Enterprise Customer Intelligence Data Platform API",
    description=(
        "REST/JSON surface over the same customer-intelligence data mcp/tools/ exposes as MCP "
        "tools -- golden records, churn scores, MDM duplicates, and platform metrics."
    ),
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(customer.router)
app.include_router(metrics.router)
