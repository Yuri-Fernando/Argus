"""A2A client — minimal, dependency-light client that discovers an AgentCard and sends a task.

Built in Sprint 17 (ROADMAP.md). Uses only `urllib` (stdlib) so this module has zero new runtime
dependency beyond what the rest of the platform already installs — appropriate for a thin client
used mostly from scripts/tests/other agents, not a full A2A SDK.

Usage:
    from agents.a2a.client import A2AClient

    client = A2AClient(base_url="http://localhost:8020")
    card = client.discover("quality")
    task = client.send_task("quality", text="silver.crm_customers")
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from uuid import uuid4


class A2AClientError(RuntimeError):
    """Raised when discovery or a task send fails (network error or non-2xx response)."""


@dataclass
class A2AClient:
    """Talks to one A2A server (agents/a2a/server.py) hosting one or more agents."""

    base_url: str
    timeout_seconds: float = 10.0

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}{path}"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout_seconds) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise A2AClientError(f"GET {url} failed: {exc}") from exc

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise A2AClientError(f"POST {url} failed: HTTP {exc.code} — {body}") from exc
        except urllib.error.URLError as exc:
            raise A2AClientError(f"POST {url} failed: {exc}") from exc

    def list_agents(self) -> list[dict[str, Any]]:
        """List every agent this server hosts (id/name/description) — not part of the A2A spec,
        a convenience the server exposes for browsing before discovery."""
        return self._get("/agents")["agents"]

    def discover(self, agent_id: str) -> dict[str, Any]:
        """Fetch an agent's AgentCard from its `.well-known/agent.json` — the A2A discovery step
        a real client should perform before sending any task, to confirm the agent exists and
        learn its skills/capabilities."""
        return self._get(f"/agents/{agent_id}/.well-known/agent.json")

    def send_task(
        self,
        agent_id: str,
        *,
        text: str | None = None,
        metadata: dict[str, Any] | None = None,
        task_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a task to `agent_id` via `POST /tasks/send` and return the resulting Task object.

        Args:
            agent_id: which agent to send to (see AGENT_CARDS in agent_card.py).
            text: the task's plain-text message content — most handlers accept either this or a
                structured `metadata` key (see agents/a2a/server.py's per-agent `_handle_*`
                docstrings for which key each agent prefers).
            metadata: structured extra parameters (e.g. {"master_customer_id": "C-123"}).
            task_id: client-generated task id; a random UUID is used if omitted.
            session_id: optional session id grouping multiple tasks together.
        """
        payload: dict[str, Any] = {
            "id": task_id or str(uuid4()),
            "sessionId": session_id,
            "message": {"role": "user", "parts": [{"type": "text", "text": text}] if text else []},
            "metadata": metadata or {},
        }
        return self._post(f"/agents/{agent_id}/tasks/send", payload)


def main() -> None:
    """CLI smoke-test: `python -m agents.a2a.client [base_url] [agent_id] [text]`."""
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8020"
    agent_id = sys.argv[2] if len(sys.argv) > 2 else "monitoring"
    text = sys.argv[3] if len(sys.argv) > 3 else ""

    client = A2AClient(base_url=base_url)
    print("Agents:", json.dumps(client.list_agents(), indent=2))
    print("Card:", json.dumps(client.discover(agent_id), indent=2))
    print("Task result:", json.dumps(client.send_task(agent_id, text=text or None), indent=2))


if __name__ == "__main__":
    main()
