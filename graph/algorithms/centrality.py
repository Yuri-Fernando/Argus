"""Degree + betweenness centrality over the customer graph (ARCHITECTURE.md §9).

Betweenness centrality is exact-computed as O(V*E), which is too slow to
run on the full graph (~10k customers + ~30k identifier nodes) inside a
portfolio-demo runtime, so it uses NetworkX's k-sample approximation
(`k=BETWEENNESS_SAMPLE_K` pivots, seeded for reproducibility) -- standard
practice for graphs at this scale. Degree centrality is exact (cheap).
"""
from __future__ import annotations

import logging

import networkx as nx

logger = logging.getLogger("graph.algorithms.centrality")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

BETWEENNESS_SAMPLE_K = 300
RANDOM_STATE = 42


def degree_centrality_report(g: nx.Graph, top_n: int = 15) -> list[dict]:
    """Highest-degree nodes -- an Email/Phone/Address node with degree > 2
    means more than 2 customers share that identifier (a duplicate-cluster
    signal on its own)."""
    dc = nx.degree_centrality(g)
    ranked = sorted(dc.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    return [
        {
            "node": node,
            "type": g.nodes[node].get("type"),
            "degree": g.degree[node],
            "degree_centrality": score,
        }
        for node, score in ranked
    ]


def betweenness_centrality_report(g: nx.Graph, top_n: int = 15, k: int = BETWEENNESS_SAMPLE_K) -> list[dict]:
    """Approximate betweenness centrality (k-sample pivots).

    High-betweenness Customer nodes sit "between" many other nodes' shortest
    paths -- in this graph's structure that means a customer connected to
    identifiers that are themselves shared with other customers, i.e. a
    plausible duplicate-cluster hub.
    """
    k_eff = min(k, g.number_of_nodes())
    bc = nx.betweenness_centrality(g, k=k_eff, seed=RANDOM_STATE, normalized=True)
    ranked = sorted(bc.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    return [
        {
            "node": node,
            "type": g.nodes[node].get("type"),
            "betweenness_centrality": score,
        }
        for node, score in ranked
    ]


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

    print("\nTop-15 by degree centrality:")
    for row in degree_centrality_report(g):
        print(f"  {row['node']} ({row['type']}) degree={row['degree']} centrality={row['degree_centrality']:.5f}")

    print(f"\nTop-15 by (approximate, k={BETWEENNESS_SAMPLE_K}) betweenness centrality:")
    for row in betweenness_centrality_report(g):
        print(f"  {row['node']} ({row['type']}) betweenness={row['betweenness_centrality']:.6f}")


if __name__ == "__main__":
    main()
