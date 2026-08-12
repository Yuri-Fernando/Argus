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
