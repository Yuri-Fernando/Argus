"""Connected components -> duplicate candidate clusters (ARCHITECTURE.md §9).

Any connected component containing 2+ `Customer` nodes means those
customers share at least one Email/Phone/Address node (possibly transitively:
A and B share an email, B and C share a phone -> A/B/C all one component
even if A and C share nothing directly). That is precisely a
duplicate-candidate cluster, independent of and complementary to the MDM
matcher in `mdm/entity_resolution/run.py` -- see
`graph/queries/duplicate_clusters.md` for the actual finding from comparing
the two.
"""
from __future__ import annotations

import logging

import networkx as nx

logger = logging.getLogger("graph.algorithms.components")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def customer_clusters_from_components(g: nx.Graph) -> list[dict]:
    """One row per connected component that contains >=2 Customer nodes.

    `shared_identifiers` is restricted to identifier nodes with degree >= 2
    *within the component* -- i.e. actually connecting more than one
    customer -- not merely every Email/Phone/Address node any member
    happens to touch (a component can contain an unshared Phone node just
    because one member has a phone; that is not evidence of duplication).
    """
    clusters = []
    for component in nx.connected_components(g):
        customer_nodes = [n for n in component if g.nodes[n].get("type") == "Customer"]
        if len(customer_nodes) < 2:
            continue
        shared_identifiers = sorted(
            n for n in component
            if g.nodes[n].get("type") in {"Email", "Phone", "Address"} and g.degree[n] >= 2
        )
        clusters.append(
            {
                "customer_ids": sorted(g.nodes[n]["crm_customer_id"] for n in customer_nodes),
                "size": len(customer_nodes),
                "shared_identifiers": shared_identifiers,
                "shared_identifier_types": sorted({g.nodes[n]["type"] for n in shared_identifiers}),
            }
        )
    clusters.sort(key=lambda c: -c["size"])
    return clusters


def component_size_distribution(g: nx.Graph) -> dict[int, int]:
    dist: dict[int, int] = {}
    for component in nx.connected_components(g):
        customer_nodes = sum(1 for n in component if g.nodes[n].get("type") == "Customer")
        if customer_nodes == 0:
            continue
        dist[customer_nodes] = dist.get(customer_nodes, 0) + 1
    return dict(sorted(dist.items()))


def main() -> None:
    import sys
    from pathlib import Path

    import pandas as pd

    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from graph.networkx.build_graph import build_graph  # noqa: E402
    from mdm.matching.deterministic import load_customers  # noqa: E402

    df, _ = load_customers()
    g = build_graph(df)

    dist = component_size_distribution(g)
    print(f"Customer-node component size distribution (size -> count): {dist}")
    n_singletons = dist.get(1, 0)
    n_multi = sum(c for size, c in dist.items() if size > 1)
    print(f"{n_multi} multi-customer components (duplicate-candidate clusters); {n_singletons} singleton customers")

    clusters = customer_clusters_from_components(g)
    print(f"\nTop 10 largest duplicate-candidate clusters:")
    for c in clusters[:10]:
        print(f"  size={c['size']} via={c['shared_identifier_types']} customers={c['customer_ids']}")

    out_dir = root / "data" / "graph"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "duplicate_candidate_clusters.csv"
    rows = [
        {
            "size": c["size"],
            "customer_ids": ";".join(c["customer_ids"]),
            "shared_identifier_types": ";".join(c["shared_identifier_types"]),
            "shared_identifiers": ";".join(c["shared_identifiers"]),
        }
        for c in clusters
    ]
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"\nWrote {len(rows)} duplicate-candidate clusters -> {out_path}")


if __name__ == "__main__":
    main()
