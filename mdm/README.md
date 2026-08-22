# mdm/

Master Data Management: Entity Resolution + Golden Record — ARCHITECTURE.md §8, built in **Sprints 4-5**. See [ADR-003](../docs/decisions/ADR-003-mdm-build-vs-buy.md) for why this is built in-house rather than bought.

```
mdm/
├── entity_resolution/
│   └── evaluation/        # precision/recall/F1 vs. data/synthetic/crm/crm_customers_ground_truth.csv
├── golden_record/
│   └── survivorship_log/  # auditable {master_customer_id, field, winning_source, rule_applied} records — DATA_MODEL.md §4
├── matching/
│   ├── deterministic.py   # Sprint 4 — exact match on email/phone/document_hash
│   ├── fuzzy.py            # Sprint 4 — Jaro-Winkler + Levenshtein (jellyfish)
│   └── ml_model.py          # Sprint 5 — Random Forest/XGBoost classifier, tracked in MLflow
└── survivorship/            # field-level survivorship rule definitions (DATA_MODEL.md §4 table, as code)
```

## Run it

```bash
make mdm   # = python mdm/entity_resolution/run.py
```

## Decision bands

`match_probability ≥ 0.90 → AUTO_MATCH` · `0.55–0.90 → HUMAN_REVIEW` · `< 0.55 → DISTINCT` — see ARCHITECTURE.md §8.

## Results (last real run, `data/lakehouse/silver/crm_customer.parquet`, 10,384 rows)

Pipeline vs. `crm_customers_ground_truth.csv` (495 of 500 pairs present in
the input — 5 dropped upstream by Silver's exact-ID dedup):

| Metric | Value |
|---|---|
| Recall | **1.0000** (0 false negatives — target ≥0.85 MET) |
| Precision | 0.9687 (16 false-positive merges) |
| F1 | 0.9841 |

RandomForest vs. fuzzy-only baseline (`mdm/matching/ml_model.py`, held-out
test split, tracked in MLflow at `mlflow/mlruns`, experiment
`mdm_entity_resolution`):

| Feature set | Baseline P/R/F1 | RandomForest P/R/F1 |
|---|---|---|
| Full 6 features | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 |
| name+email only (ablation) | 0.974 / 1.000 / 0.987 | 0.980 / 1.000 / 0.990 |

**Why the full-feature model is a perfect, uninteresting 1.0/1.0/1.0**: this
synthetic dataset's injected duplicates (`data/synthetic/generators/crm.py`)
never mutate `phone`/`address` — only `name` gets a cosmetic variant — so
`phone_match`/`address_similarity` are near-deterministic keys on their own
and any reasonable classifier separates the classes trivially. The
name+email-only ablation (dropping those two features, simulating matching
without a shared phone/address join key — the actual scenario the ML tier
is meant for across less-aligned sources) is the more honest read of the ML
model's contribution over the fuzzy heuristic.

**A finding that reshaped the deterministic tier**: exact-matching on
`email` alone is unreliable at this row count — Faker's `pt_BR` email
provider collides often enough that **0 of 505** raw email-only-collision
pairs turned out to be true duplicates, while `phone`/`document_hash`
matches were 495/511 correct (97%). `mdm/matching/deterministic.py` treats
email-only matches as weak signal deferred to the fuzzy/ML tiers rather
than an automatic match — see that module's docstring for the full
breakdown.

Cross-checked against an independent signal in `graph/queries/duplicate_clusters.md`:
the graph finds no true duplicate this pipeline missed, but does show where
a naive "same email" merge would have been wrong — real customer IDs
included.
