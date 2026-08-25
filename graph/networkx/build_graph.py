"""Customer relationship graph (ARCHITECTURE.md §9 / graph/README.md).

Nodes: `Customer, Email, Phone, Address`. Edges: `HAS_EMAIL, HAS_PHONE,
LIVES_AT`. `Order/Product/Seller` nodes and `PLACED/CONTAINS/SOLD_BY` edges
are documented in ARCHITECTURE.md §9 but require the Olist dataset, which
is confirmed absent for this environment (see mdm/README.md /
CLAUDE.md task brief) -- degraded gracefully to the CRM-only subset.

A customer connects to an Email/Phone/Address node whenever it has a
non-null value for that field; two customers that share an Email, Phone,
or Address node are therefore connected via that shared node, one hop
apart -- exactly the signal `graph/queries/duplicate_clusters.md` uses to
cross-check the MDM matcher (mdm/entity_resolution/run.py).
"""
from __future__ import annotations

import logging
import pickle
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mdm.matching.deterministic import load_customers  # noqa: E402

logger = logging.getLogger("graph.networkx.build_graph")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

OUT_DIR = ROOT / "data" / "graph"


def _node_id(prefix: str, value: str) -> str:
    return f"{prefix}:{value}"


def build_graph(customers: pd.DataFrame) -> nx.Graph:
    g = nx.Graph()

    for row in customers.itertuples(index=False):
        cust_node = _node_id("Customer", row.crm_customer_id)
        g.add_node(cust_node, type="Customer", crm_customer_id=row.crm_customer_id, name=row.name)

        email = getattr(row, "email", None)
        if pd.notna(email) and str(email).strip():
            email_node = _node_id("Email", str(email).strip().lower())
            g.add_node(email_node, type="Email", value=str(email).strip().lower())
            g.add_edge(cust_node, email_node, type="HAS_EMAIL")

        phone = getattr(row, "phone", None)
        if pd.notna(phone) and str(phone).strip():
            phone_node = _node_id("Phone", str(phone).strip())
            g.add_node(phone_node, type="Phone", value=str(phone).strip())
            g.add_edge(cust_node, phone_node, type="HAS_PHONE")

        address, city, state = getattr(row, "address", None), getattr(row, "city", None), getattr(row, "state", None)
        if pd.notna(address) and str(address).strip():
            addr_key = f"{str(address).strip().lower()}|{str(city or '').strip().lower()}|{str(state or '').strip().lower()}"
            addr_node = _node_id("Address", addr_key)
            g.add_node(addr_node, type="Address", address=address, city=city, state=state)
            g.add_edge(cust_node, addr_node, type="LIVES_AT")

    return g


def graph_stats(g: nx.Graph) -> dict:
    node_types: dict[str, int] = {}
    for _, data in g.nodes(data=True):
        node_types[data.get("type", "unknown")] = node_types.get(data.get("type", "unknown"), 0) + 1
    edge_types: dict[str, int] = {}
    for _, _, data in g.edges(data=True):
        edge_types[data.get("type", "unknown")] = edge_types.get(data.get("type", "unknown"), 0) + 1
    return {
        "n_nodes": g.number_of_nodes(),
        "n_edges": g.number_of_edges(),
        "nodes_by_type": node_types,
        "edges_by_type": edge_types,
    }


def save_graph(g: nx.Graph, path: Path | None = None) -> Path:
    path = path or (OUT_DIR / "customer_graph.gpickle")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(g, f, protocol=pickle.HIGHEST_PROTOCOL)
    logger.info("Saved graph (%d nodes, %d edges) -> %s", g.number_of_nodes(), g.number_of_edges(), path)
    return path


def load_graph(path: Path | None = None) -> nx.Graph:
    path = path or (OUT_DIR / "customer_graph.gpickle")
    with open(path, "rb") as f:
        return pickle.load(f)


def main() -> None:
    df, source = load_customers()
    print(f"Input: {source} ({len(df)} rows)")
    g = build_graph(df)
    stats = graph_stats(g)
    print(f"Graph: {stats['n_nodes']} nodes, {stats['n_edges']} edges")
    print(f"  nodes by type: {stats['nodes_by_type']}")
    print(f"  edges by type: {stats['edges_by_type']}")
    save_graph(g)


if __name__ == "__main__":
    main()
