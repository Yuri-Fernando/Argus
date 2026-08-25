# Duplicate clusters: graph vs. the MDM matcher

Sprint 6 acceptance criteria deliverable (graph/README.md). Ran the full
chain for real against the Silver CRM table
(`data/lakehouse/silver/crm_customer.parquet`, 10,384 rows) on
2026-08-14: `mdm/entity_resolution/run.py`, then
`graph/networkx/build_graph.py` + `graph/algorithms/components.py`
independently, then compared the two.

## The question this doc was scoped to answer

> Does the graph flag >=1 duplicate cluster the ML matcher missed?

**Short answer: no — not on the labeled ground truth.** The
deterministic+fuzzy+ML pipeline (`mdm/entity_resolution/run.py`) achieves
**100% recall** (495/495 ground-truth pairs present in the input, 0 false
negatives) in this run — see `mdm/entity_resolution/evaluation/`. Verified
directly two ways:

1. Every pair of customers sharing **both** `phone` and `address` (the
   strongest signal the graph can see, short of an exact Email match) ends
   up in the *same* `master_customer_id` cluster — checked exhaustively,
   0 exceptions.
2. Every one of the 495 ground-truth duplicate pairs shares at least the
   `Address` node in the graph (the synthetic generator never mutates
   `address`/`phone` for an injected duplicate — see
   `data/synthetic/generators/crm.py`), so there is no true duplicate this
   graph's node/edge model is structurally blind to.

**The graph's real, honest finding runs the other way**: naive connected-components
over undifferentiated `HAS_EMAIL`/`HAS_PHONE`/`LIVES_AT` edges *over-clusters* —
it groups genuinely distinct customers together through Faker's low-cardinality
`pt_BR` email pool, in a way the tiered matcher correctly avoids. That is
arguably the more useful result for a portfolio demo: it's evidence for
*why* the pipeline treats deterministic keys unequally
(`mdm/matching/deterministic.py`) rather than trusting every shared
identifier the same amount.

## The numbers

Built from the same Silver input as the MDM run. Every connected component
containing >=2 `Customer` nodes (script: `graph/algorithms/components.py`,
output: `data/graph/duplicate_candidate_clusters.csv`):

| Component size (customers) | Count |
|---|---|
| 1 (no cluster) | 8,588 |
| 2 | 804 |
| 3 | 56 |
| 4 | 5 |
| **Total multi-customer components** | **865** |

Broken down by which identifier(s) actually connect >1 customer inside the
component (`shared_identifiers`, degree >= 2 within the component — not
just "an Email/Phone/Address node someone in the component happens to
have"):

| Shared via | Components | What it actually is |
|---|---|---|
| `Address` + `Email` + `Phone` | 485 | Genuine duplicate pairs — full corroborating signal |
| `Email` only | 368 | **Coincidental collisions between unrelated people** (see below) |
| `Address` + `Phone` (no Email) | 10 | Genuine duplicates where `email` was null (2% `missing_email` dirty rate hit both source and copy) |
| `Address` only | 2 | Coincidental — two unrelated people, one shared fake street address (see below) |

The 368 "Email only" components are the same phenomenon flagged in
`mdm/matching/deterministic.py`: Faker's `pt_BR` email provider draws from
too small a pool at n=10,384 rows, so ~500 pairs of *completely unrelated*
customers end up with the same email by chance. Measured directly: **0 of
505 raw email-only-collision pairs are true duplicates** per the ground
truth. The pipeline's deterministic tier already treats these as weak/unconfirmed
signal rather than an auto-match; the graph, with no such tiering, cannot
tell them apart from a real match without extra logic.

40 of the 865 components mix a genuine duplicate pair with one extra,
unrelated customer attached only via that same weak email edge — one is
detailed below with real IDs.

## Concrete example (real customer IDs, from this run)

```
CRM00000049  Caroline Peixoto  |  kcassiano@example.org | 09002706537 | doc_hash ec455c1... | Praia de Martins, 96, Caxias Do Sul, RS
CRM00010058  Caroline Peixoto  |  kcassiano@example.org | 09002706537 | doc_hash ec455c1... | Praia de Martins, 96, Caxias Do Sul, RS
CRM00004213  Clarice Ferreira  |  kcassiano@example.org | 2151328994  | doc_hash 3edc513... | Recanto de Rezende, 42, Rio De Janeiro, RJ
```

`CRM00000049` and `CRM00010058` are the same person — an injected
ground-truth duplicate (`crm_customers_ground_truth.csv` row 58:
`CRM00010058 -> CRM00000049`), identical on every field including
`document_hash`. `CRM00004213` is a different, unrelated person: different
name, phone, document_hash, city, and state — the *only* thing she shares
with the other two is the literal email string `kcassiano@example.org`,
which Faker independently generated for both people.

- **Graph**: connects all three into one component (the `Email` node
  `kcassiano@example.org` has degree 3), because it has no way to prefer
  a document_hash/phone match over an email-only match.
- **MDM pipeline**: correctly builds two golden records —
  `MC00000049` = `{CRM00000049, CRM00010058}` (the real pair, merged via
  `document_hash` in the deterministic tier — see
  `mdm/golden_record/survivorship_log/survivorship_log.csv`,
  `master_customer_id=MC00000049`) and a separate cluster for
  `CRM00004213` alone. `Clarice Ferreira`'s record is never touched by
  `Caroline Peixoto`'s golden record.

If the golden record had been built off the naive graph clustering instead
of the tiered matcher, `Clarice Ferreira`'s phone number and address would
have had a chance of being overwritten by survivorship rules pulling from
`Caroline Peixoto`'s records (or vice versa) — a real, LGPD-relevant data
quality failure this comparison caught in review rather than in production.

The second coincidental case: `CRM00000777` (Vinícius Carvalho) and
`CRM00002724` (Ayla Peixoto) — two unrelated people, different names,
emails, phones, and document_hashes — share only the literal fake street
address `"Lago de Ribeiro, São Paulo, SP"`. Same root cause (Faker's street
name pool is small enough to collide at this row count), same conclusion:
the pipeline correctly leaves them as separate customers.

## Takeaway

- Pipeline recall on labeled ground truth: **1.0** (see
  `mdm/entity_resolution/evaluation/`). No graph-only duplicate cluster
  was found that the pipeline missed.
- Pipeline precision: **0.9687** (16 false-positive merges, all from rare
  `document_hash` coincidental collisions — see mdm/README.md for that
  number's derivation). Checked directly: **all 16** share neither `phone`
  nor `address` with their wrongly-merged partner in the graph — the graph
  would have flagged every one of these 16 AUTO_MATCHes as suspicious (single
  weak/coincidental signal, no corroboration), a good candidate follow-up
  check (not implemented here) for an automated "does the graph disagree
  with an AUTO_MATCH?" sanity gate.
- The graph's real value demonstrated here is **precision QA on the
  matcher's own assumptions**, not incremental recall: it makes visible,
  with an explicit shared-node trail, exactly which candidate merges rest
  on a single weak signal (email) vs. multiple corroborating ones
  (address + phone), which a purely pairwise ML score does not surface as
  legibly.
