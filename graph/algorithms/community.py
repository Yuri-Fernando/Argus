"""Community detection over the customer graph (ARCHITECTURE.md §9).

Uses NetworkX's Louvain implementation (`nx.algorithms.community.louvain_communities`,
available in NetworkX >= 3.0) -- near-linear runtime, good default for a
graph this size and sparsity. Falls back to greedy modularity maximization
if Louvain isn't available in the installed NetworkX version.

On this graph (Customer/Email/Phone/Address, no Order/Product/Seller since
Olist is absent), communities largely mirror the connected components
found by `graph/algorithms/components.py` -- customers only link to each
other transitively through shared identifiers, so there's little extra
structure for modularity to exploit beyond "which identifiers are shared."
It's included per the Sprint 6 deliverable list and reported honestly.
"""
from __future__ import annotations

import logging

import networkx as nx

logger = logging.getLogger("graph.algorithms.community")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

RANDOM_STATE = 42


def detect_communities(g: nx.Graph) -> list[set]:
    try:
        return list(nx.algorithms.community.louvain_communities(g, seed=RANDOM_STATE))
    except AttributeError:  # pragma: no cover - older networkx
        logger.warning("louvain_communities unavailable -- falling back to greedy_modularity_communities")
        return list(nx.algorithms.community.greedy_modularity_communities(g))


def community_report(g: nx.Graph, communities: list[set]) -> dict:
    modularity = nx.algorithms.community.modularity(g, communities)
    sizes = sorted((len(c) for c in communities), reverse=True)
    customer_counts = []
    for c in communities:
        n_customers = sum(1 for n in c if g.nodes[n].get("type") == "Customer")
        if n_customers:
            customer_counts.append(n_customers)
    return {
        "n_communities": len(communities),
        "modularity": modularity,
        "size_distribution_top10": sizes[:10],
        "communities_with_customers": len(customer_counts),
        "avg_customers_per_community": sum(customer_counts) / len(customer_counts) if customer_counts else 0.0,
    }


def main() -> None:
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from graph.networkx.build_graph import build_graph, graph_stats  # noqa: E402
    from mdm.matching.deterministic import load_customers  # noqa: E402

    df, _ = load_customers()
    g = build_graph(df)
    print(f"Graph: {graph_stats(g)}")

    communities = detect_communities(g)
    report = community_report(g, communities)
    print(f"\nCommunities: {report['n_communities']}  modularity={report['modularity']:.4f}")
    print(f"Top-10 community sizes (nodes): {report['size_distribution_top10']}")
    print(f"Communities containing >=1 customer: {report['communities_with_customers']}, "
          f"avg customers/community: {report['avg_customers_per_community']:.2f}")


if __name__ == "__main__":
    main()
