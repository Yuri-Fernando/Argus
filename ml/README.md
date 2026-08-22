# ml/

Feature engineering, model training and explainability — ARCHITECTURE.md §10, built in **Sprints 10-11**. Every experiment is tracked in [`../mlflow/`](../mlflow/).

**Status: implemented.** Built from `data/lakehouse/silver/` + `data/mdm/golden_record.parquet` only — `data/raw/olist` is absent, per this project's synthetic-first policy.

```
ml/
├── features/            # RFM (payment_finance), engagement (web_event), support (support_ticket) — golden-record grain
│   ├── entity_map.py       # crm_customer_id -> master_customer_id lookup (MDM golden record)
│   ├── rfm.py               # Recency/Frequency/Monetary from settled payments
│   ├── engagement.py        # event count, distinct event types, days since last activity
│   ├── support.py           # ticket count, avg sentiment score, unresolved count
│   └── build_features.py    # orchestrates the above -> data/ml/features/customer_features.parquet
├── churn/               # Logistic Regression / Random Forest / Gradient Boosting, compared on ROC-AUC/F1/PR-AUC/calibration
│   ├── label.py             # proxy churn label definition — see docstring for the full reasoning
│   └── train.py              # trains all 3, logs every run to MLflow, registers + promotes the champion
├── explainability/       # SHAP value computation for the champion churn model
│   └── shap_analysis.py
├── segmentation/         # KMeans over RFM+engagement → VIP/Loyal/Potential/At Risk/Inactive
│   └── kmeans_segments.py
├── matching/               # shared with mdm/matching/ml_model.py (imported, not duplicated)
└── reinforcement/         # contextual bandit — EXTENSION, see ml/reinforcement/README.md
```

`training/` and `evaluation/` (listed in earlier design notes as separate top-level folders) were
folded into `ml/churn/train.py` instead of split into their own packages — at this project's
scale a single training-and-comparison module is more readable than a training/evaluation split
with only one model family to train.

## Run it

```bash
python -m ml.features.build_features        # -> data/ml/features/customer_features.parquet
python -m ml.churn.train                    # trains + compares 3 models, registers champion to MLflow Staging
python -m ml.explainability.shap_analysis    # SHAP for the champion, global + 3 example customers
python -m ml.segmentation.kmeans_segments    # -> data/ml/segmentation/customer_segments.parquet
```

## No real churn label exists — proxy label, disclosed

None of the synthetic sources record an actual churn/cancellation event. `ml/churn/label.py`
defines a documented proxy: a customer is `churned=1` when a noisy weighted risk score
(disengagement z-score + unresolved-ticket flag + negative-sentiment flag + no-purchase flag,
weights `0.45/0.25/0.15/0.15`, plus injected Gaussian noise `std=0.5` so the label isn't a
deterministic function of its own inputs) falls in the top 15%. See that module's docstring for
the full rationale, including why the noise term exists (without it, a tree ensemble trivially
reconstructs the label from its own defining features, landing at a meaningless ROC-AUC ≈ 1.0).

## Champion model criterion

The model promoted to `Staging` in the MLflow Model Registry is the one with the best held-out
**ROC-AUC** (`ml/churn/train.py:register_champion`). Earlier design notes in this file specified
PR-AUC; ROC-AUC was used for the actual implementation and this doc has been updated to match —
both are logged and compared for every run either way (see Results below), so the choice is
visible either way.

## Results (last real run)

**Feature store**: `data/ml/features/customer_features.parquet` — 9,875 customers (one row per
MDM golden record), 9 features.

**Churn label**: 15.0% positive rate by construction (1,481 of 9,875 customers), 7,406/2,469
stratified train/test split.

**Model comparison** (`mlflow` experiment `churn_model`, tracking URI `file:./mlflow/mlruns` —
does not collide with the `mdm_entity_resolution` experiment already in that same store):

| Model | ROC-AUC | F1 | PR-AUC | Brier (calibration) |
|---|---|---|---|---|
| Logistic Regression (champion) | **0.882** | 0.531 | 0.657 | 0.0817 |
| Gradient Boosting | 0.880 | 0.509 | 0.648 | 0.0827 |
| Random Forest | 0.876 | 0.506 | 0.644 | 0.0827 |

Champion: `logistic_regression`, registered as MLflow Model Registry model `churn_model` v1,
promoted to `Staging`. Logistic Regression edging out the two tree ensembles is expected given
the label's construction (a linear risk score plus noise) — a linear model is the closest match
to the true generating process.

**SHAP explainability** — global feature importance (mean |SHAP|, 200-customer sample):
`days_since_last_activity` dominates (0.141), a distant second `unresolved_count` (0.019), then
`recency_days` (0.011) and the rest under 0.01 — consistent with disengagement carrying by far
the largest weight (0.45) in the label's risk score.

Three real example customers (highest predicted churn risk in the held-out test set):

| Customer | P(churn) | Top SHAP contribution | 2nd | 3rd |
|---|---|---|---|---|
| `MC00003652` | 0.9984 | `+0.7050` days_since_last_activity=180 | `+0.1423` unresolved_count=2 | `+0.0175` ticket_count=3 |
| `MC00003135` | 0.9930 | `+0.8236` days_since_last_activity=184 | `+0.0497` unresolved_count=1 | `-0.0052` event_count=0 |
| `MC00006078` | 0.9858 | `+0.7868` days_since_last_activity=160 | `+0.0600` unresolved_count=1 | `+0.0073` recency_days=367 |

**Segmentation** (`ml.segmentation.kmeans_segments`, `k=5` over log1p-transformed RFM +
engagement features): no bucket collapses — largest segment is 28.4%, smallest 6.0%.

| Segment | Count | % | Avg recency (payment) | Avg frequency | Avg monetary | Avg days since last activity |
|---|---|---|---|---|---|---|
| VIP | 2,622 | 26.6% | 147.2d | 1.6 | $2,750.8 | 20.6d |
| Loyal | 2,802 | 28.4% | 158.0d | 1.5 | $2,565.9 | 37.6d |
| Potential | 2,177 | 22.0% | 366.9d | 0.0 | $0.1 | 22.4d |
| At Risk | 597 | 6.0% | 208.4d | 1.1 | $1,865.0 | 131.7d |
| Inactive | 1,677 | 17.0% | 367.0d | 0.0 | $0.0 | 53.5d |

`Potential` (never purchased, but 2nd-freshest engagement) and `At Risk` (real purchase history,
but by far the stalest engagement — 131.7 days) are the two segments a naive 1-D "sort by
composite score" rule would have confused; see `ml/segmentation/kmeans_segments.py`'s docstring
for the two-axis (value rank × freshness rank) rule that keeps them distinct.

## Related

- [`ml/reinforcement/README.md`](reinforcement/README.md) — the RL leg (extension, not core scope)
- [`mdm/README.md`](../mdm/README.md) — golden record this package's `master_customer_id` grain comes from
- [`mlflow/README.md`](../mlflow/README.md) / [`mlflow/registry.md`](../mlflow/registry.md)
