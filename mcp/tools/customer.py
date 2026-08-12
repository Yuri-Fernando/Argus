"""Customer / Golden Record / Graph tools for the MCP server.

Built in ROADMAP.md Sprint 13, but the data these functions read does not exist yet in this
skeleton — it is produced by earlier sprints owned by other modules:

- Golden Record data (name/email/phone/address/segment, survivorship-resolved) is owned by
  `mdm/golden_record/` (ROADMAP.md Sprint 5). `gold.dim_customer` keyed by `master_customer_id`
  is the canonical read target — see ARCHITECTURE.md §8.
- The relationship subgraph (shared email/phone/address/order clusters) is owned by
  `graph/networkx/` (ROADMAP.md Sprint 6) — see ARCHITECTURE.md §9.

Every function below is a stub with the real, final signature and return shape already decided,
so `mcp/server/server.py` and downstream agents can be built and tested against it today. The
TODOs mark exactly where the real data access layer plugs in — no other part of this function's
contract should need to change when that wiring lands.

Every tool call here is intentionally scoped to read-only, single-customer or bounded-search
access — no tool in this module can list or export the full customer base in one call (see
ADR-007's least-privilege principle).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CustomerSummary:
    """Lightweight customer record used in search results."""

    master_customer_id: str
    name: str
    email: str
    segment: str


@dataclass
class GraphNode:
    """A single node in a customer relationship subgraph."""

    id: str
    type: str  # "Customer" | "Email" | "Phone" | "Address" | "Order" | "Product" | "Seller"
    label: str


@dataclass
class GraphEdge:
    """A single edge in a customer relationship subgraph."""

    source: str
    target: str
    relationship: str  # "HAS_EMAIL" | "HAS_PHONE" | "LIVES_AT" | "PLACED" | "CONTAINS" | "SOLD_BY"


def get_customer(master_customer_id: str) -> dict[str, Any]:
    """Fetch a single customer's Golden Record.

    Args:
        master_customer_id: the MDM-assigned survivor ID from `gold.dim_customer`
            (ARCHITECTURE.md §8) — never a raw source-system `customer_id`.

    Returns:
        dict shape (final, agreed contract):
            {
                "master_customer_id": str,
                "name": str,
                "email": str,
                "phone": str,
                "address": {"city": str, "state": str},
                "segment": str,          # VIP | Loyal | Potential | At Risk | Inactive
                "source_record_count": int,
                "found": bool,
            }
        `found=False` with otherwise-empty fields when the ID does not resolve to a Golden
        Record.
    """
    # TODO(Sprint 5 / mdm/golden_record): replace with a real read against
    # `gold.dim_customer` (Databricks) or its Snowflake CORE mirror, keyed by
    # `master_customer_id`. The access layer should apply the same masking policies described
    # in ARCHITECTURE.md §16 (Snowflake masking on email/phone/document_hash) — this tool must
    # never bypass RBAC by reading a lower-privilege raw table directly.
    return {
        "master_customer_id": master_customer_id,
        "name": None,
        "email": None,
        "phone": None,
        "address": None,
        "segment": None,
        "source_record_count": 0,
        "found": False,
    }


def search_customers(query: str, limit: int = 20) -> dict[str, Any]:
    """Search Golden Records by free-text name/email/phone fragment.

    Args:
        query: free-text search term.
        limit: maximum number of results (capped at 100 server-side to keep results bounded —
            this tool is not a bulk-export path).

    Returns:
        {"results": list[dict] (CustomerSummary-shaped), "total_matches": int}
    """
    limit = min(limit, 100)
    # TODO(Sprint 5 / mdm/golden_record): back this with a real search — e.g. a Snowflake
    # Semantic View or a Databricks SQL query with a trigram/fuzzy index on
    # `gold.dim_customer`. Keep `limit` enforced server-side even if the caller passes a
    # larger value.
    results: list[CustomerSummary] = []
    return {"results": [r.__dict__ for r in results], "total_matches": len(results)}


def get_customer_orders(master_customer_id: str, limit: int = 10) -> dict[str, Any]:
    """List a customer's most recent orders, most recent first.

    Args:
        master_customer_id: the MDM-assigned survivor ID.
        limit: maximum number of orders to return.

    Returns:
        {"orders": list[dict], "total_orders": int}
        Each order dict: {"order_id": str, "status": str, "value": float, "order_date": str}
    """
    # TODO(Sprint 7 / lakehouse/gold): read `gold.fact_orders` joined to `gold.dim_customer` on
    # `master_customer_id`, ordered by `order_date DESC`. See DATA_MODEL.md §3 for the
    # dimensional model this reads from.
    orders: list[dict[str, Any]] = []
    return {"orders": orders, "total_orders": 0}


def get_customer_graph(master_customer_id: str, max_hops: int = 2) -> dict[str, Any]:
    """Return the customer's relationship subgraph rooted at `master_customer_id`.

    Used by the orchestrator agent (agents/orchestrator/) for identity-class questions that a
    flat Golden Record lookup can't answer — e.g. "does this customer share a phone number with
    any other account?" (ARCHITECTURE.md §9).

    Args:
        master_customer_id: root node for the traversal.
        max_hops: maximum traversal depth (default 2, capped at 4 to keep responses bounded for
            an LLM context window).

    Returns:
        {"nodes": list[dict] (GraphNode-shaped), "edges": list[dict] (GraphEdge-shaped)}
    """
    max_hops = min(max_hops, 4)
    # TODO(Sprint 6 / graph/networkx): load the persisted NetworkX graph (or query the optional
    # Neo4j extension) built by `graph/networkx/build_graph.py`, and run a bounded
    # ego_graph(master_customer_id, radius=max_hops) traversal. Convert the result to the
    # GraphNode/GraphEdge shapes above before returning — never return a raw networkx.Graph
    # object across the MCP boundary.
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    return {"nodes": [n.__dict__ for n in nodes], "edges": [e.__dict__ for e in edges]}
