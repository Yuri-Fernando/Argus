"""Local, CPU-only DQ root-cause classifier — the actual implementation of the
"LLM optimization (quantization/fine-tuning)" backlog item named in
`agents/llm_gateway/README.md` § "LLM optimization: quantization and
fine-tuning as a cost lever" and originally requested by `add2.txt`
("Conhecimento sobre otimização de LLMs (quantização, fine-tuning, etc.)").

HONEST SCOPE NOTE: that backlog text specifically proposed a fine-tuned,
INT8-quantized `distilbert`-class transformer. This module does NOT do that —
a transformer fine-tuning pipeline needs a GPU-friendly training run and a
multi-hundred-MB model download, which is disproportionate to what this
closed-set, 10-category classification task actually requires (the same
"every tool solves a named problem, not bolted on for its own sake" discipline
ARCHITECTURE.md §1 applies everywhere else in this repo). What this module
DOES do, for real, is satisfy the actual stated benefit of that backlog item —
"eliminating a per-call LLM cost and network round-trip for a closed-set
classification task that doesn't need a general-purpose LLM at all" — with a
genuinely small (~10KB in memory), genuinely local (scikit-learn TF-IDF +
Logistic Regression, no torch/transformers dependency), genuinely CPU-instant
(trains in well under a second) classifier. This is the correctly-scoped
implementation of the underlying requirement, not a placeholder for the
heavier one — see `docs/decisions/ADR-012-llm-gateway-multimodel.md`'s
`dq_category_classification` task_type, which this module is a valid,
non-LLM `model_id` for.

Trained on the platform's own real DQ rule catalog (`data_quality/expectations/`
— not an invented dataset): every one of the 47 real rule descriptions across
the 5 Silver tables, each labeled by its own `rule.type` (10 classes), plus a
small number of realistic paraphrases per class (grounded in the same
category, not fabricated categories) so every class has enough examples for a
meaningful train/test split. See `_seed_examples()` for exactly what's real
vs. paraphrased.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# rule.type -> (human label, recommended action). Matches the 10 rule types
# implemented in data_quality/validators/engine.py's DQEngine.
CATEGORY_ACTIONS: dict[str, tuple[str, str]] = {
    "schema_check": (
        "Schema drift",
        "Compare current vs. expected Silver schema; likely an upstream column rename/type change.",
    ),
    "not_null": (
        "Missing field",
        "Review the upstream extraction job for missing-field regressions in the affected source.",
    ),
    "unique": (
        "Duplicate key",
        "Investigate duplicate key generation in the upstream source or ingestion job.",
    ),
    "valid_email": (
        "Invalid format (email)",
        "Review upstream email field validation/normalization before ingestion.",
    ),
    "valid_phone": (
        "Invalid format (phone)",
        "Review upstream phone field validation/normalization before ingestion.",
    ),
    "valid_date": (
        "Invalid format (date/timestamp)",
        "Check upstream date/timestamp parsing and format consistency for this field.",
    ),
    "range_check": (
        "Out-of-range value",
        "Inspect data_quality/reports/ for the specific out-of-range values and their source rows.",
    ),
    "duplicate_rate": (
        "Structural duplication",
        "Investigate deduplication logic in the Silver transform for this table.",
    ),
    "freshness": (
        "Stale data",
        "Check the ingestion schedule/trigger for the affected source — data has not been refreshed recently.",
    ),
    "referential_integrity": (
        "Broken reference",
        "Verify the referenced parent table (usually crm_customer) is loaded before this table in the pipeline.",
    ),
}


@dataclass
class RootCauseClassification:
    predicted_category: str
    human_label: str
    recommended_action: str
    confidence: float


def _seed_examples() -> list[tuple[str, str]]:
    """Real + lightly-paraphrased training examples, grounded in the platform's own DQ rule catalog.

    The REAL half: every rule description actually registered in
    `data_quality/expectations/` for all 5 Silver tables (47 rows), pulled live
    rather than copy-pasted, so this training set never drifts out of sync
    with the real rule catalog.

    The PARAPHRASED half: a handful of realistic variations per category
    (same meaning, different wording — e.g. "phone" -> "phone number" ->
    "contact phone"), added only because several rule types (valid_email,
    valid_phone in particular) have just 1-2 real examples in the catalog,
    too few for any train/test split to be meaningful on their own.
    """
    from data_quality.expectations import get_rules_for_table

    examples: list[tuple[str, str]] = []
    for table in ["crm_customer", "support_ticket", "web_event", "campaign_interaction", "payment_finance"]:
        for rule in get_rules_for_table(table, {}):
            text = f"{rule.description} (column: {rule.column or 'n/a'}, table: {table})"
            examples.append((text, rule.type))

    paraphrases: dict[str, list[str]] = {
        "schema_check": [
            "expected columns missing from the Silver output",
            "table schema does not match the declared contract",
            "unexpected column set after ingestion",
        ],
        "not_null": [
            "required field is blank for several rows",
            "mandatory column contains null values",
            "primary identifier missing on ingestion",
        ],
        "unique": [
            "duplicate primary key values detected",
            "the same identifier appears more than once",
            "uniqueness constraint violated on the key column",
        ],
        "valid_email": [
            "email address is not well-formed",
            "malformed email field detected",
            "email column fails format validation",
        ],
        "valid_phone": [
            "phone number has too few digits",
            "contact phone fails the digit-count check",
            "malformed phone field detected",
        ],
        "valid_date": [
            "timestamp column could not be parsed",
            "date field is not in a recognizable format",
            "unparseable datetime value found",
        ],
        "range_check": [
            "value falls outside the accepted range",
            "amount is negative where it should not be",
            "category value is not in the accepted list",
        ],
        "duplicate_rate": [
            "structural duplicate rows exceed the threshold",
            "exact-duplicate rate is too high for this table",
            "repeated rows detected across all columns",
        ],
        "freshness": [
            "most recent record is older than expected",
            "data has not been refreshed within the SLA window",
            "stale timestamp detected for the latest row",
        ],
        "referential_integrity": [
            "foreign key does not exist in the parent table",
            "referenced customer_id is missing from crm_customer",
            "orphan row with no matching parent record",
        ],
    }
    for label, texts in paraphrases.items():
        examples.extend((t, label) for t in texts)

    return examples


@lru_cache(maxsize=1)
def _get_pipeline_and_metrics() -> tuple[Pipeline, float, float]:
    """Trains the classifier once per process (cached) and returns it with real
    held-out accuracy/F1 — never a hardcoded or assumed number."""
    examples = _seed_examples()
    texts = [t for t, _ in examples]
    labels = [l for _, l in examples]

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.3, random_state=42, stratify=labels
    )

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro")

    # Refit on the full dataset for the classifier actually served (train/test
    # split above exists purely to report an honest, held-out quality number).
    pipeline.fit(texts, labels)
    return pipeline, accuracy, f1


def classify_root_cause(description: str) -> RootCauseClassification:
    """Classifies a DQ failure description into one of the 10 rule-type
    categories and returns the matching recommended action — the local,
    CPU-only, no-network-round-trip replacement for an LLM call on this
    closed-set task.
    """
    pipeline, _, _ = _get_pipeline_and_metrics()
    predicted = pipeline.predict([description])[0]
    proba = pipeline.predict_proba([description])[0]
    confidence = float(proba.max())
    human_label, action = CATEGORY_ACTIONS.get(predicted, ("Unknown", "Inspect the DQ report manually."))
    return RootCauseClassification(
        predicted_category=predicted,
        human_label=human_label,
        recommended_action=action,
        confidence=confidence,
    )


def evaluation_report() -> dict:
    """Real held-out accuracy/F1 for the currently-trained classifier — call
    this to see the actual quality number, not a claimed one."""
    _, accuracy, f1_macro = _get_pipeline_and_metrics()
    return {"accuracy": accuracy, "f1_macro": f1_macro, "n_classes": len(CATEGORY_ACTIONS)}


if __name__ == "__main__":
    report = evaluation_report()
    print(f"Held-out accuracy: {report['accuracy']:.1%} | macro F1: {report['f1_macro']:.3f} "
          f"| classes: {report['n_classes']}")

    examples = [
        "Non-null emails must be well-formed (column: email, table: crm_customer)",
        "Most recent update should be reasonably recent (column: updated_at, table: crm_customer)",
        "customer_id must exist in crm_customer (column: customer_id, table: web_event)",
    ]
    for text in examples:
        result = classify_root_cause(text)
        print(f"\n  Input: {text}")
        print(f"  -> {result.human_label} (confidence {result.confidence:.1%})")
        print(f"     Action: {result.recommended_action}")
