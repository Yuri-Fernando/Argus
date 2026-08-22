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

## Scope note: CRM-only

`data/raw/olist/` is confirmed absent in this environment, so the graph is
built from the CRM customer table only: `Customer, Email, Phone, Address`
nodes and `HAS_EMAIL, HAS_PHONE, LIVES_AT` edges. The `Order, Product,
Seller` nodes and `PLACED, CONTAINS, SOLD_BY` edges ARCHITECTURE.md §9
describes need Olist and are not built — degraded gracefully rather than
faked.

## Run it

```bash
python graph/networkx/build_graph.py     # builds + saves data/graph/customer_graph.gpickle
python graph/algorithms/centrality.py    # degree + approximate betweenness centrality
python graph/algorithms/components.py    # connected components -> data/graph/duplicate_candidate_clusters.csv
python graph/algorithms/community.py     # Louvain community detection
```

## Results (last real run, 10,384 customers)

Graph: 39,394 nodes (10,384 Customer / 9,234 Email / 9,889 Phone / 9,887
Address), 30,921 edges. 865 connected components contain 2+ Customer nodes
(a duplicate-candidate cluster); see `graph/queries/duplicate_clusters.md`
for what those actually are (485 genuine duplicate clusters, 368
coincidental email-only collisions, 10 genuine clusters with a null email,
2 coincidental address-only collisions) and how they compare to
`mdm/entity_resolution/run.py`'s actual merge decisions, with real customer
IDs.
