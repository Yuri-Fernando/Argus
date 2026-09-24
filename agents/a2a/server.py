"""A2A protocol server — exposes the four existing agents (orchestrator/quality/recommendation/
monitoring) as A2A-discoverable, A2A-callable agents.

Built in Sprint 17 (ROADMAP.md) — see agent_card.py's module docstring for the gap this closes
and the deliberate deviation from the spec's one-agent-per-host assumption.

This module WRAPS, never reimplements, the four agents:
    - agents/orchestrator/customer_intelligence_agent.py (compiled LangGraph graph)
    - agents/quality/data_quality_agent.py:diagnose_quality_drop()
    - agents/recommendation/recommendation_agent.py:generate_recommendation()
    - agents/monitoring/monitoring_agent.py:run_monitoring_cycle()
Every `_handle_*` function below is a thin adapter: parse the A2A task's input, call the existing
function unmodified, serialize its existing return type. No agent logic lives in this file — see
ADR-014 (Ports & Adapters): this server is exactly a third adapter around the same domain core
that `mcp/tools/*.py` (MCP) and `api/services/*.py` (REST) already wrap.

Endpoints (per agent_id in agent_card.AGENT_CARDS):
    GET  /agents/{agent_id}/.well-known/agent.json   -- AgentCard discovery
    POST /agents/{agent_id}/tasks/send                -- send a task, get a completed Task back
    GET  /agents                                       -- convenience: list every agent_id + name

Run locally:
    uvicorn agents.a2a.server:app --port 8020

See agents/a2a/README.md for the actual discovery + tasks/send output captured from a real local
run (booted, curled, and stopped as part of Sprint 17's verification step).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from langgraph.types import Command

from agents.a2a.agent_card import AGENT_CARDS
from agents.monitoring.monitoring_agent import run_monitoring_cycle
from agents.orchestrator.customer_intelligence_agent import customer_intelligence_agent
from agents.quality.data_quality_agent import diagnose_quality_drop
from agents.recommendation.approval_queue import RecommendationStatus
from agents.recommendation.recommendation_agent import generate_recommendation

logger = logging.getLogger("agents.a2a.server")

app = FastAPI(
    title="Argus — A2A Agent Server",
    description=(
        "Agent2Agent (A2A) protocol layer wrapping the four existing agents/ LangGraph/plain-"
        "Python agents. See agents/a2a/agent_card.py and docs/decisions/ADR-014 for design notes."
    ),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# A2A wire types (the subset of the spec's Task/Message/Part shapes this server needs)
# ---------------------------------------------------------------------------


class MessagePart(BaseModel):
    type: str = "text"
    text: str | None = None


class A2AMessage(BaseModel):
    role: str = "user"
    parts: list[MessagePart] = Field(default_factory=list)


class TaskSendRequest(BaseModel):
    """POST /tasks/send body — A2A spec's `tasks/send` request shape (JSON-RPC envelope elided;
    this server takes the params object directly at a REST-style path instead of JSON-RPC's
    single `/` endpoint with a `method` field — documented simplification for a local demo
    server, same spirit as agent_card.py's per-agent-path deviation)."""

    id: str | None = None
    sessionId: str | None = None
    message: A2AMessage
    metadata: dict[str, Any] = Field(default_factory=dict)


def _text_of(message: A2AMessage) -> str:
    """Concatenate every text part of a message — the plain-text input most handlers need."""
    return " ".join(p.text for p in message.parts if p.type == "text" and p.text)


def _to_jsonable(value: Any) -> Any:
    """Best-effort conversion of dataclasses/enums/datetimes into JSON-safe primitives, so every
    handler below can return whatever native type the wrapped agent already returns (a dataclass,
    an AgentState dict, a list of dataclasses) without each handler hand-rolling serialization."""
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value") and hasattr(value, "name") and not isinstance(value, (int, str)):
        # Enum instance (RecommendationStatus, AlertSeverity, Intent, ToolRoute, ...)
        return value.value
    return value


# ---------------------------------------------------------------------------
# Handlers — one per agent_id, each a thin call into the real, existing agent entrypoint
# ---------------------------------------------------------------------------


def _handle_orchestrator(text: str, metadata: dict[str, Any], thread_id: str) -> dict[str, Any]:
    """`thread_id` is required now that the graph is compiled with a checkpointer (ADR-006
    human-in-the-loop gate, see customer_intelligence_agent.py) — LangGraph keys paused/resumable
    state to it. `send_task` passes `body.sessionId or task_id`, so a client that wants to resume
    a paused (`input-required`) task must send the same `sessionId` on its follow-up call.

    `metadata.resume`, when present, resumes a paused task instead of starting a new question —
    the *value* of `resume` is never trusted for authorization (see
    customer_intelligence_agent.py::require_human_approval's docstring): it only tells LangGraph
    which interrupted node to re-enter; the actual approve/reject decision is read back out of
    agents/recommendation/approval_queue.py, which a human must have updated out-of-band (e.g. via
    a separate internal review endpoint/CLI — not built here, out of this scope, same as
    approval_queue.py's own `mark_executed()` executor).
    """
    config = {"configurable": {"thread_id": thread_id}}
    if "resume" in metadata:
        result_state = customer_intelligence_agent.invoke(Command(resume=metadata["resume"]), config)
        return _to_jsonable(dict(result_state))

    question = metadata.get("question") or text
    if not question:
        raise HTTPException(status_code=400, detail="orchestrator requires a question (message text or metadata.question).")
    result_state = customer_intelligence_agent.invoke({"question": question}, config)
    return _to_jsonable(dict(result_state))


def _handle_quality(text: str, metadata: dict[str, Any], thread_id: str) -> dict[str, Any]:
    _ = thread_id  # quality has no multi-turn/paused state — stateless per call
    dataset = metadata.get("dataset") or text
    if not dataset:
        raise HTTPException(status_code=400, detail="quality requires a dataset (message text or metadata.dataset).")
    previous_score = metadata.get("previous_score")
    diagnosis = diagnose_quality_drop(dataset, previous_score=previous_score)
    payload = _to_jsonable(diagnosis)
    payload["text"] = diagnosis.as_text()
    return payload


def _handle_recommendation(text: str, metadata: dict[str, Any], thread_id: str) -> dict[str, Any]:
    _ = thread_id  # this agent's own ADR-006 gate (approval_queue.py) isn't thread/session-scoped
    master_customer_id = metadata.get("master_customer_id") or text
    if not master_customer_id:
        raise HTTPException(
            status_code=400,
            detail="recommendation requires master_customer_id (message text or metadata.master_customer_id).",
        )
    item = generate_recommendation(master_customer_id)
    payload = _to_jsonable(item)
    payload["requires_human_approval"] = item.status == RecommendationStatus.PENDING
    return payload


def _handle_monitoring(text: str, metadata: dict[str, Any], thread_id: str) -> dict[str, Any]:
    _ = (text, metadata, thread_id)  # monitoring takes no input — evaluates current platform-wide signals
    alerts = run_monitoring_cycle()
    return {"alerts": _to_jsonable(alerts), "alert_count": len(alerts)}


_HANDLERS = {
    "orchestrator": _handle_orchestrator,
    "quality": _handle_quality,
    "recommendation": _handle_recommendation,
    "monitoring": _handle_monitoring,
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/agents")
def list_agents() -> dict[str, Any]:
    """Convenience index — not part of the A2A spec, useful for a human/client browsing this
    multi-agent host before hitting a specific agent's `.well-known/agent.json`."""
    return {
        "agents": [
            {"id": agent_id, "name": card.name, "description": card.description}
            for agent_id, card in AGENT_CARDS.items()
        ]
    }


@app.get("/agents/{agent_id}/.well-known/agent.json")
def get_agent_card(agent_id: str, request: Request) -> dict[str, Any]:
    """A2A discovery endpoint — returns the requested agent's AgentCard."""
    card = AGENT_CARDS.get(agent_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent_id={agent_id!r}. See GET /agents.")
    base = str(request.base_url).rstrip("/")
    return card.to_dict(url=f"{base}/agents/{agent_id}")


@app.post("/agents/{agent_id}/tasks/send")
def send_task(agent_id: str, body: TaskSendRequest) -> dict[str, Any]:
    """A2A `tasks/send` endpoint — routes the task to the matching agent's real entrypoint and
    returns a completed A2A Task object.

    This never queues or backgrounds work (no polling/streaming needed for these four agents'
    call latency) — the response is always the final `completed` (or `failed`) state.
    """
    handler = _HANDLERS.get(agent_id)
    if handler is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent_id={agent_id!r}. See GET /agents.")

    task_id = body.id or str(uuid4())
    text = _text_of(body.message)
    # LangGraph checkpoints (customer_intelligence_agent's ADR-006 gate) key paused state to this
    # thread_id — a client resuming a paused task MUST send the same sessionId it got back below.
    thread_id = body.sessionId or task_id

    try:
        result = handler(text, body.metadata, thread_id)
        # "__interrupt__" is LangGraph's own marker for a paused-not-failed run (see
        # customer_intelligence_agent.py's require_human_approval) — surfaced as the A2A spec's
        # "input-required" state, not "completed", since the answer isn't final yet: it's pending
        # a human approve()/reject() call against agents/recommendation/approval_queue.py.
        state = "input-required" if isinstance(result, dict) and "__interrupt__" in result else "completed"
        error = None
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 — surfaced to the caller as a failed A2A Task, not a 500
        logger.exception("agent_id=%s task_id=%s handler raised", agent_id, task_id)
        result = None
        state = "failed"
        error = str(exc)

    task: dict[str, Any] = {
        "id": task_id,
        "sessionId": body.sessionId,
        "status": {"state": state, "timestamp": datetime.now(timezone.utc).isoformat()},
        "artifacts": (
            [{"name": f"{agent_id}_result", "parts": [{"type": "data", "data": result}]}]
            if result is not None
            else []
        ),
    }
    if error:
        task["status"]["error"] = error
    return task
