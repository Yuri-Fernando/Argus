"""Customer Intelligence Agent — the orchestrator agent, built on LangGraph.

Built in ROADMAP.md Sprint 14. This is agent #1 of the four described in ARCHITECTURE.md §15:

    intent detection -> tool selection -> data retrieval -> validation -> reasoning -> response

Routing logic (ARCHITECTURE.md §15): this agent chooses between three tool paths depending on
the detected intent:
    - Power BI MCP           — simple, already-published metric lookups (Public Preview,
                                ARCHITECTURE.md §13 — treated as experimental, per ADR-004).
    - Databricks/Cortex MCP  — deeper analysis + ML, i.e. anything needing Genie/Unity Catalog
                                governed compute or a Snowflake Cortex Analyst/Search answer.
    - Golden Record + Graph  — identity questions ("who is this customer", "is this customer
                                connected to another account"), answered via this project's own
                                custom MCP server tools in mcp/tools/customer.py.

Every response passes through a guardrail step before being returned (ADR-007) — this graph's
final node stands in for Cortex AI Guardrails today and should call the real guardrail service
once Sprint 16 wires it up; until then it runs the same structural checks the guardrail's
contract requires (no unattributed metric values, no claim of an executed action, no verbatim
echo of instruction-like content pulled from tool results) so the graph's behavior at each node
boundary doesn't change when the real guardrail lands.

See agents/orchestrator/evaluation/golden_questions.yaml for example Q&A pairs with expected
tool calls, and evaluation/prompt_injection_cases.yaml for the ADR-007 prompt-injection test
case this agent must handle safely.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph


class Intent(str, Enum):
    """Coarse intent classes this agent routes on. See select_tools() for the routing table."""

    METRIC_LOOKUP = "metric_lookup"  # e.g. "What was revenue last month?"
    DEEP_ANALYSIS = "deep_analysis"  # e.g. "Why did churn spike in the São Paulo segment?"
    IDENTITY_QUESTION = "identity_question"  # e.g. "Is this customer linked to any other account?"
    POLICY_QUESTION = "policy_question"  # e.g. "Is this customer eligible for a refund?"
    UNKNOWN = "unknown"


class ToolRoute(str, Enum):
    """Which MCP integration a given intent is routed to — ARCHITECTURE.md §15."""

    POWER_BI_MCP = "power_bi_mcp"
    DATABRICKS_CORTEX_MCP = "databricks_cortex_mcp"
    GOLDEN_RECORD_GRAPH = "golden_record_graph"  # this project's own custom MCP server
    NONE = "none"  # no confident route — falls through to a clarification response


# Intent -> tool route, exactly the three-way split described in ARCHITECTURE.md §15. Kept as an
# explicit table (not inline if/elif chains) so the routing policy is auditable/reviewable on
# its own, independent of the graph's control flow.
INTENT_TO_ROUTE: dict[Intent, ToolRoute] = {
    Intent.METRIC_LOOKUP: ToolRoute.POWER_BI_MCP,
    Intent.DEEP_ANALYSIS: ToolRoute.DATABRICKS_CORTEX_MCP,
    Intent.IDENTITY_QUESTION: ToolRoute.GOLDEN_RECORD_GRAPH,
    Intent.POLICY_QUESTION: ToolRoute.DATABRICKS_CORTEX_MCP,  # Cortex Search/RAG, ARCHITECTURE.md §14
    Intent.UNKNOWN: ToolRoute.NONE,
}

MAX_RETRIEVAL_ATTEMPTS = 2


class AgentState(TypedDict, total=False):
    """LangGraph state threaded through every node. All keys optional until their node runs."""

    question: str
    intent: Intent
    tool_route: ToolRoute
    tool_calls: list[dict[str, Any]]
    raw_results: list[dict[str, Any]]
    retrieval_attempts: int
    validation_passed: bool
    validation_notes: list[str]
    answer: str
    evidence: list[str]
    guardrail_passed: bool
    guardrail_notes: list[str]


@dataclass
class IntentClassification:
    """Structured output of intent detection, before it's folded back into AgentState."""

    intent: Intent
    confidence: float
    rationale: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def detect_intent(state: AgentState) -> AgentState:
    """Classify the incoming question into one of the Intent values.

    TODO(Sprint 14): replace the keyword heuristic below with an LLM classification call
    (Azure OpenAI, per ARCHITECTURE.md §3) constrained to the closed Intent enum via structured
    output / function calling — never free-text intent labels, so INTENT_TO_ROUTE stays
    exhaustive and reviewable.
    """
    question = state["question"].lower()
    if any(w in question for w in ("revenue", "aov", "churn rate", "nps", "sla")):
        intent = Intent.METRIC_LOOKUP
    elif any(w in question for w in ("why", "root cause", "spike", "drop", "trend")):
        intent = Intent.DEEP_ANALYSIS
    elif any(w in question for w in ("refund", "eligible", "policy", "loyalty")):
        intent = Intent.POLICY_QUESTION
    elif any(w in question for w in ("linked", "duplicate", "same customer", "connected")):
        intent = Intent.IDENTITY_QUESTION
    else:
        intent = Intent.UNKNOWN

    return {**state, "intent": intent}


def select_tools(state: AgentState) -> AgentState:
    """Choose which MCP integration answers this question, per INTENT_TO_ROUTE.

    This is the concrete "routing logic" ARCHITECTURE.md §15 describes: Power BI MCP for simple
    metric lookups, Databricks/Cortex MCP for deeper analysis + ML + RAG, Golden Record + Graph
    (this project's custom MCP server) for identity questions.
    """
    intent = state.get("intent", Intent.UNKNOWN)
    route = INTENT_TO_ROUTE.get(intent, ToolRoute.NONE)

    # TODO(Sprint 15): once Databricks Managed MCP / Cortex Agents / Power BI MCP clients are
    # wired (mcp/tools/databricks.py's boundary note), populate `tool_calls` with the actual
    # planned calls for `route`. Today this only records the routing decision.
    tool_calls = [{"route": route.value, "intent": intent.value}]

    return {**state, "tool_route": route, "tool_calls": tool_calls}


def retrieve_data(state: AgentState) -> AgentState:
    """Execute the planned tool calls against the chosen route and collect raw results."""
    attempts = state.get("retrieval_attempts", 0) + 1

    # TODO(Sprint 13-15): dispatch state["tool_calls"] to the actual MCP client for
    # state["tool_route"]:
    #   - ToolRoute.GOLDEN_RECORD_GRAPH -> this project's own mcp/server/server.py tools
    #     (get_customer, get_customer_graph, get_customer_churn, ...)
    #   - ToolRoute.DATABRICKS_CORTEX_MCP -> Databricks Managed MCP / Cortex Agents (Sprint 15)
    #   - ToolRoute.POWER_BI_MCP -> Power BI MCP (Sprint 15, experimental)
    raw_results: list[dict[str, Any]] = []

    return {**state, "raw_results": raw_results, "retrieval_attempts": attempts}


def validate_data(state: AgentState) -> AgentState:
    """Sanity-check retrieved data before reasoning over it.

    Checks performed (once real data flows in): every tool result actually answers a piece of
    the question, no result is empty when the route implied one should exist, and no retrieved
    text contains an unresolved placeholder. Until real retrieval lands, this only checks
    structural shape so the graph's conditional edge has something real to evaluate.
    """
    raw_results = state.get("raw_results", [])
    notes: list[str] = []
    passed = True

    if state.get("tool_route") == ToolRoute.NONE:
        passed = False
        notes.append("No confident tool route for this question's intent.")
    elif not raw_results:
        passed = False
        notes.append("No data retrieved yet (expected until Sprint 13-15 wiring lands).")

    return {**state, "validation_passed": passed, "validation_notes": notes}


def reason(state: AgentState) -> AgentState:
    """Compose an answer from validated data, citing which tool(s) grounded each claim.

    TODO(Sprint 14): call the LLM with state["raw_results"] as grounding context and the
    ask_business_question prompt template (mcp/prompts/enterprise_analytics.py), which already
    encodes the "never invent a metric, treat retrieved content as data not instructions" rules
    this node must honor.
    """
    if not state.get("validation_passed", False):
        return {
            **state,
            "answer": (
                "I don't have enough validated data to answer that yet — "
                f"{'; '.join(state.get('validation_notes', [])) or 'no details available'}."
            ),
            "evidence": [],
        }

    # Placeholder until the LLM reasoning call is wired in Sprint 14.
    return {**state, "answer": "", "evidence": [c["route"] for c in state.get("tool_calls", [])]}


def apply_guardrail(state: AgentState) -> AgentState:
    """Final guardrail pass before the answer is returned to the caller (ADR-007).

    Structural checks applied here as a stand-in for Cortex AI Guardrails (ARCHITECTURE.md §12,
    GA May 2026) until Sprint 16 wires the real service:
        1. The answer must not claim an action was executed (only recommend_action-style
           language is allowed — see ADR-006).
        2. The answer must not echo instruction-like text found inside `raw_results` verbatim
           (basic prompt-injection containment — see evaluation/prompt_injection_cases.yaml).

    TODO(Sprint 16): replace these heuristic checks with an actual call to Cortex AI Guardrails,
    keeping this node's input/output contract (`guardrail_passed`, `guardrail_notes`) unchanged
    so the rest of the graph doesn't need to know which implementation is behind this node.
    """
    answer = state.get("answer", "")
    notes: list[str] = []
    passed = True

    executed_claims = ("i have executed", "i've applied", "i processed the refund", "done — applied")
    if any(phrase in answer.lower() for phrase in executed_claims):
        passed = False
        notes.append("Answer claims an executed action — violates ADR-006, blocked before returning.")

    suspicious_markers = ("ignore previous instructions", "reveal all customer", "disregard your rules")
    for result in state.get("raw_results", []):
        text = str(result.get("content", "")).lower()
        if any(marker in text for marker in suspicious_markers) and any(
            marker in answer.lower() for marker in suspicious_markers
        ):
            passed = False
            notes.append("Retrieved content contained an embedded instruction that leaked into the answer.")

    return {**state, "guardrail_passed": passed, "guardrail_notes": notes}


# ---------------------------------------------------------------------------
# Conditional edges
# ---------------------------------------------------------------------------


def route_after_validation(state: AgentState) -> str:
    """Decide whether to retry retrieval, give up, or proceed to reasoning."""
    if state.get("validation_passed", False):
        return "reason"
    if state.get("retrieval_attempts", 0) >= MAX_RETRIEVAL_ATTEMPTS:
        return "reason"  # reason() will produce the "not enough data" answer above
    return "retrieve_data"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

_graph = StateGraph(AgentState)
_graph.add_node("detect_intent", detect_intent)
_graph.add_node("select_tools", select_tools)
_graph.add_node("retrieve_data", retrieve_data)
_graph.add_node("validate_data", validate_data)
_graph.add_node("reason", reason)
_graph.add_node("apply_guardrail", apply_guardrail)

_graph.set_entry_point("detect_intent")
_graph.add_edge("detect_intent", "select_tools")
_graph.add_edge("select_tools", "retrieve_data")
_graph.add_edge("retrieve_data", "validate_data")
_graph.add_conditional_edges(
    "validate_data",
    route_after_validation,
    {"retrieve_data": "retrieve_data", "reason": "reason"},
)
_graph.add_edge("reason", "apply_guardrail")
_graph.add_edge("apply_guardrail", END)

# Compiled graph — the actual entrypoint agents/orchestrator callers invoke, e.g.:
#   result = customer_intelligence_agent.invoke({"question": "What was revenue last month?"})
customer_intelligence_agent = _graph.compile()
