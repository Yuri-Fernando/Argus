"""AgentCard builders — one per existing agent (orchestrator/quality/recommendation/monitoring).

Built in Sprint 17 (ROADMAP.md) to close the A2A gap identified in
IMPROVEMENTS_AND_RESEARCH.md §5: the four agents in `agents/` (orchestrator, quality,
recommendation, monitoring) talk to each other today only via direct Python calls / LangGraph
internals — never through a standardized inter-agent protocol. This module does NOT reimplement
any of those agents; it describes them, per the Agent2Agent (A2A) protocol's discovery model
(https://a2a-protocol.org/latest/specification/ — "Agent Card").

An AgentCard is the JSON document an A2A client fetches from
`GET /agents/{agent_id}/.well-known/agent.json` (see `server.py`) to learn what an agent can do
before sending it a task — the A2A analogue of an OpenAPI spec, but agent-capability-shaped
(skills, not endpoints) rather than route-shaped.

Deviation from the spec, documented rather than hidden: the A2A spec assumes one agent per host,
serving its card at the host root's `/.well-known/agent.json`. This project runs all four agents
behind one local FastAPI process for a testable-without-infrastructure Sprint 17 demo, so each
agent gets its own path prefix (`/agents/{agent_id}/...`) instead of its own host. A real
multi-service deployment (e.g. one Pod per agent, see `k8s/`) would give each agent its own origin
and could serve `/.well-known/agent.json` at that origin's root unmodified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

A2A_PROTOCOL_VERSION = "0.2"  # version of the A2A spec this module targets


@dataclass
class AgentSkill:
    """One entry in an AgentCard's `skills` list — a discrete capability an agent exposes,
    per the A2A spec's Skill object (id/name/description/tags/examples)."""

    id: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "examples": self.examples,
        }


@dataclass
class AgentCard:
    """The discovery document for one agent — A2A spec's Agent Card shape.

    `url` is filled in by `server.py` at request time (it depends on the host the client used to
    reach the server), not hard-coded here — an AgentCard should describe the agent it was
    fetched from, not a guessed deployment URL.
    """

    id: str
    name: str
    description: str
    version: str
    skills: list[AgentSkill]
    input_modes: list[str] = field(default_factory=lambda: ["text/plain"])
    output_modes: list[str] = field(default_factory=lambda: ["application/json"])
    streaming: bool = False

    def to_dict(self, *, url: str) -> dict[str, Any]:
        """Render as the JSON shape `GET .well-known/agent.json` returns.

        Args:
            url: the fully-qualified base URL this agent is reachable at (e.g.
                "http://localhost:8020/agents/quality") — filled in by the caller (server.py),
                which knows the request's actual host:port.
        """
        return {
            "protocolVersion": A2A_PROTOCOL_VERSION,
            "name": self.name,
            "description": self.description,
            "url": url,
            "version": self.version,
            "provider": {
                "organization": "Enterprise Customer Intelligence Data Platform",
                "url": "https://github.com",  # placeholder — portfolio project, no real org URL
            },
            "capabilities": {
                "streaming": self.streaming,
                "pushNotifications": False,
                "stateTransitionHistory": False,
            },
            "defaultInputModes": self.input_modes,
            "defaultOutputModes": self.output_modes,
            "skills": [s.to_dict() for s in self.skills],
        }


# ---------------------------------------------------------------------------
# One AgentCard per existing agent — wrapping, never reimplementing, ARCHITECTURE.md §15's four
# agents. See server.py for how each card's skill maps to the underlying agent function call.
# ---------------------------------------------------------------------------


ORCHESTRATOR_CARD = AgentCard(
    id="orchestrator",
    name="Customer Intelligence Agent",
    description=(
        "Answers natural-language business questions by routing to Power BI MCP, Databricks/"
        "Cortex MCP, or this platform's own Golden Record + Graph MCP tools, depending on "
        "detected intent (metric lookup / deep analysis / identity question / policy question). "
        "Wraps agents/orchestrator/customer_intelligence_agent.py — the compiled LangGraph graph "
        "is the actual handler; this card never reimplements its logic."
    ),
    version="0.1.0",
    skills=[
        AgentSkill(
            id="ask_business_question",
            name="Ask a business question",
            description=(
                "Classify intent, select a tool route, retrieve and validate data, reason over "
                "it, and return a guardrail-checked answer (ADR-007)."
            ),
            tags=["customer-intelligence", "orchestration", "langgraph"],
            examples=["What was revenue last month?", "Is this customer linked to any other account?"],
        )
    ],
)

QUALITY_CARD = AgentCard(
    id="quality",
    name="Data Quality Agent",
    description=(
        "Diagnoses a data quality score drop for a given dataset: main cause (worst-scoring DQ "
        "dimension), affected row count, and a recommended action — never triggers a pipeline "
        "re-run itself. Wraps agents/quality/data_quality_agent.py:diagnose_quality_drop()."
    ),
    version="0.1.0",
    skills=[
        AgentSkill(
            id="diagnose_quality_drop",
            name="Diagnose a data quality drop",
            description="Root-cause a DQ score drop for one dataset, per ARCHITECTURE.md §15's example format.",
            tags=["data-quality", "diagnosis"],
            examples=["Why did silver.crm_customers' DQ score drop?"],
        )
    ],
)

RECOMMENDATION_CARD = AgentCard(
    id="recommendation",
    name="Recommendation Agent",
    description=(
        "Combines churn score, CLV, support history and sentiment into one prioritized "
        "retention/engagement recommendation. NEVER executes it — always enqueues via "
        "agents/recommendation/approval_queue.py for human approval (ADR-006). Wraps "
        "agents/recommendation/recommendation_agent.py:generate_recommendation()."
    ),
    version="0.1.0",
    skills=[
        AgentSkill(
            id="generate_recommendation",
            name="Generate a customer recommendation",
            description="Score a customer and enqueue a PENDING recommendation for human review.",
            tags=["recommendation", "human-in-the-loop"],
            examples=["What should we do about customer C-12345's churn risk?"],
        )
    ],
)

MONITORING_CARD = AgentCard(
    id="monitoring",
    name="Monitoring Agent",
    description=(
        "Watches pipeline/model/LLM health signals against thresholds and raises structured "
        "alerts — read-only, never restarts a job or rolls back a deployment. Wraps "
        "agents/monitoring/monitoring_agent.py:run_monitoring_cycle()."
    ),
    version="0.1.0",
    skills=[
        AgentSkill(
            id="run_monitoring_cycle",
            name="Run one monitoring cycle",
            description="Fetch current health signals and evaluate them against DEFAULT_THRESHOLDS.",
            tags=["monitoring", "observability"],
            examples=["Is anything currently breaching a health threshold?"],
        )
    ],
)


# Registry keyed by agent_id — the single source of truth server.py and client.py both read from,
# so adding a fifth agent later means adding one entry here, not editing routing logic elsewhere.
AGENT_CARDS: dict[str, AgentCard] = {
    "orchestrator": ORCHESTRATOR_CARD,
    "quality": QUALITY_CARD,
    "recommendation": RECOMMENDATION_CARD,
    "monitoring": MONITORING_CARD,
}
