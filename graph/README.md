# graph/

Customer relationship graph — ARCHITECTURE.md §9, built in **Sprint 6**. Surfaces duplicate clusters and relationship structure that row-by-row matching in `mdm/` alone would miss.

```
graph/
├── networkx/    # build_graph.py — Customer/Email/Phone/Address/Order/Product/Seller nodes and edges
├── algorithms/   # degree, betweenness centrality, connected components, community detection
└── queries/       # saved analyses, e.g. duplicate_clusters.md (Sprint 6 acceptance criteria deliverable)
```

## Why NetworkX first, Neo4j optional

NetworkX runs in-process with no extra infrastructure, which is enough to demonstrate the graph-analysis technique at this project's data volume. A Neo4j extension is documented as backlog (see [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) item 6) for when graph query language (Cypher) itself needs to be demonstrated.
