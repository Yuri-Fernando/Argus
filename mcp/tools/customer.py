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

WIRED (this session): `get_customer` and `search_customers` now read the real
`data/mdm/golden_record.parquet`, reusing `api/services/customer_service.py`'s
`get_golden_record()` / `_golden_record_df()` (this project has no live Databricks/Snowflake to
apply the masking policies the TODO below describes — that TODO is left in place, unmasked local
parquet reads are the documented local-dev equivalent, same posture as `snowflake/local_runner.py`
standing in for a real Snowflake account). `get_customer_graph` now loads the real customer graph
— see its own docstring for why that's an in-memory rebuild rather than a load of the persisted
pickle.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import networkx as nx
import pandas as pd

from api.services.customer_service import _golden_record_df, _segments_df, get_golden_record


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
    # Local-dev wiring: `data/mdm/golden_record.parquet` is the closest available stand-in for
    # `gold.dim_customer` in this build; masking is not applied here (no Snowflake/Databricks
    # role exists in this environment) — see module docstring.
    record = get_golden_record(master_customer_id)
    if not record["found"]:
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

    segs = _segments_df()
    seg_match = segs[segs["master_customer_id"] == master_customer_id]
    segment = seg_match.iloc[0]["segment"] if not seg_match.empty else None

    return {
        "master_customer_id": record["master_customer_id"],
        "name": record["canonical_name"],
        "email": record["canonical_email"],
        "phone": record["canonical_phone"],
        "address": {"city": record["city"], "state": record["state"]},
        "segment": segment,
        "source_record_count": record["source_record_count"],
        "found": True,
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
    # Local-dev wiring: substring (case-insensitive) search over the same
    # `golden_record.parquet` `get_customer()` reads, via `api/services/customer_service.py`'s
    # cached loader — no separate parquet read implemented here.
    query = (query or "").strip().lower()
    if not query:
        return {"results": [], "total_matches": 0}

    df = _golden_record_df()
    mask = (
        df["canonical_name"].astype(str).str.lower().str.contains(query, na=False, regex=False)
        | df["canonical_email"].astype(str).str.lower().str.contains(query, na=False, regex=False)
        | df["canonical_phone"].astype(str).str.lower().str.contains(query, na=False, regex=False)
    )
    matched = df[mask]
    total_matches = len(matched)

    segs = _segments_df()[["master_customer_id", "segment"]]
    subset = matched.head(limit).merge(segs, on="master_customer_id", how="left")

    results: list[CustomerSummary] = [
        CustomerSummary(
            master_customer_id=row.master_customer_id,
            name=row.canonical_name,
            email=row.canonical_email,
            segment=row.segment if pd.notna(row.segment) else None,
        )
        for row in subset.itertuples(index=False)
    ]
    return {"results": [r.__dict__ for r in results], "total_matches": total_matches}


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
    # Left as-is per task scope: no Olist order data in this build (CONFIRMED ABSENT, see
    # BUILD_LOG.md) — there is no `fact_orders`-equivalent parquet to read yet.
    orders: list[dict[str, Any]] = []
    return {"orders": orders, "total_orders": 0}


# ---------------------------------------------------------------------------
# get_customer_graph wiring
# ---------------------------------------------------------------------------

_RELATIONSHIP_LOOKUP = {"HAS_EMAIL", "HAS_PHONE", "LIVES_AT", "PLACED", "CONTAINS", "SOLD_BY"}


@lru_cache(maxsize=1)
def _load_customer_graph() -> nx.Graph:
    """Return the customer relationship graph.

    `graph/networkx/build_graph.py` already persists this to
    `data/graph/customer_graph.gpickle` via `save_graph()`/`load_graph()` — the intended reuse
    path. In THIS environment that pickle fails to unpickle (`AttributeError:
    'Graph' object has no attribute '_adj'`), a networkx version-skew issue between whatever
    environment wrote the pickle and this session's installed networkx (2.6.3) — a real,
    reproducible failure, not a hypothetical one (confirmed by direct `pickle.load()` before
    writing this). Per the task brief's fallback instruction, this rebuilds the identical graph
    in-memory by calling the real `graph.networkx.build_graph.build_graph()` against
    `mdm.matching.deterministic.load_customers()` — the exact same two functions
    `graph/networkx/build_graph.py::main()` calls before persisting — so the graph shape/content
    is identical to what the (unreadable) pickle would have held. Rebuilding costs well under a
    second (10,384 CRM rows -> ~39k nodes / ~31k edges) and is cached per-process so it only
    happens once.
    """
    from graph.networkx.build_graph import build_graph
    from mdm.matching.deterministic import load_customers

    customers, _source = load_customers()
    return build_graph(customers)


def _node_label(node_id: str, data: dict[str, Any]) -> str:
    node_type = data.get("type", "")
    if node_type == "Customer":
        return str(data.get("name") or node_id)
    if node_type in ("Email", "Phone"):
        return str(data.get("value") or node_id)
    if node_type == "Address":
        return f"{data.get('address', '')}, {data.get('city', '')} - {data.get('state', '')}"
    return node_id


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
    # Local-dev wiring: see `_load_customer_graph()` above for why this is an in-memory rebuild
    # rather than a load of the persisted pickle. The graph is keyed by CRM source customer id
    # (`Customer:{crm_customer_id}`), not `master_customer_id` — this MDM survivor id is resolved
    # to its `source_customer_ids` via `golden_record.parquet` first, and the ego graphs for each
    # merged source id are unioned (a merged Golden Record can have >1 source CRM id).
    record = get_golden_record(master_customer_id)
    if not record["found"]:
        return {"nodes": [], "edges": []}

    graph = _load_customer_graph()
    gr_row = _golden_record_df()
    gr_row = gr_row[gr_row["master_customer_id"] == master_customer_id].iloc[0]
    source_ids = [s.strip() for s in str(gr_row["source_customer_ids"]).split(";") if s.strip()]

    nodes_by_id: dict[str, GraphNode] = {}
    edges_seen: set[tuple[str, str, str]] = set()
    edges: list[GraphEdge] = []

    for crm_id in source_ids:
        root = f"Customer:{crm_id}"
        if root not in graph:
            continue
        ego = nx.ego_graph(graph, root, radius=max_hops)
        for node_id, data in ego.nodes(data=True):
            if node_id not in nodes_by_id:
                nodes_by_id[node_id] = GraphNode(
                    id=node_id, type=data.get("type", "unknown"), label=_node_label(node_id, data)
                )
        for u, v, data in ego.edges(data=True):
            rel = data.get("type", "unknown")
            key = (u, v, rel)
            if key in edges_seen:
                continue
            edges_seen.add(key)
            edges.append(GraphEdge(source=u, target=v, relationship=rel))

    return {
        "nodes": [n.__dict__ for n in nodes_by_id.values()],
        "edges": [e.__dict__ for e in edges],
    }
