"""Local, CPU-only tax-discrepancy root-cause classifier — the fiscal-domain sibling of
`agents/quality/root_cause_classifier.py`, same technique and same "HONEST SCOPE NOTE" discipline
(see that module's docstring for the full rationale on why TF-IDF + Logistic Regression, not a
fine-tuned transformer, is the correctly-scoped implementation of the `add2.txt`/`tributario.txt`
"otimização de LLMs" backlog item for a closed-set classification task).

Trained on the platform's own real fiscal DQ rule catalog
(`data_quality/expectations/fiscal_document.py::get_rules()` — not an invented dataset), the same
three categories `data/synthetic/generators/fiscal.py::FiscalDirtyRates` injects, each mapped to
the specific rule(s) whose description would fire for that category, plus a small number of
realistic paraphrases per class (there are only 1-3 real rule descriptions per category in a
7-rule catalog — too few on their own for a meaningful train/test split, the same problem
`root_cause_classifier.py`'s `valid_email`/`valid_phone` classes had).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# discrepancy_reason -> (human label, recommended action). Matches the three categories
# data/synthetic/generators/fiscal.py::FiscalDirtyRates injects.
CATEGORY_ACTIONS: dict[str, tuple[str, str]] = {
    "invalid_ncm": (
        "NCM fora do catálogo",
        "Revisar a classificação fiscal do item — o código NCM não consta no catálogo de produtos "
        "esperado; provável erro de digitação ou item não cadastrado.",
    ),
    "cst_cfop_mismatch": (
        "CST/CFOP incompatível",
        "Revisar a combinação de CST e CFOP do documento — uma operação marcada como imune/isenta "
        "não deveria estar associada a um CFOP de venda tributada integral.",
    ),
    "rate_out_of_range": (
        "Alíquota fora da faixa",
        "Verificar a alíquota (IBS/CBS/Imposto Seletivo) aplicada ao documento — um valor negativo "
        "ou acima de 100% indica um erro de digitação/sinal na origem do dado.",
    ),
}


@dataclass
class TaxDiscrepancyClassification:
    predicted_category: str
    human_label: str
    recommended_action: str
    confidence: float


def _seed_examples() -> list[tuple[str, str]]:
    """Real (pulled live from `fiscal_document.get_rules()`, never copy-pasted) + paraphrased
    training examples, grouped by which of the three injected discrepancy categories each DQ rule
    actually detects — see this module's docstring for why paraphrases are needed at all."""
    from data_quality.expectations.fiscal_document import get_rules

    rule_to_category = {
        "ncm_code": "invalid_ncm",
        "cst_cfop_valid": "cst_cfop_mismatch",
        "ibs_rate": "rate_out_of_range",
        "cbs_rate": "rate_out_of_range",
        "imposto_seletivo_rate": "rate_out_of_range",
    }

    examples: list[tuple[str, str]] = []
    for rule in get_rules(crm_customer_ids=None):
        category = rule_to_category.get(rule.column)
        if category:
            examples.append((rule.description, category))

    paraphrases: dict[str, list[str]] = {
        "invalid_ncm": [
            "código NCM não encontrado no catálogo de produtos",
            "classificação fiscal do item é inválida",
            "NCM informado não corresponde a nenhum produto cadastrado",
        ],
        "cst_cfop_mismatch": [
            "situação tributária não compatível com o tipo de operação",
            "CST de isenção usado numa venda tributada integralmente",
            "combinação de CST e CFOP logicamente inconsistente",
        ],
        "rate_out_of_range": [
            "alíquota de imposto está negativa",
            "percentual de tributo acima de 100%",
            "valor de alíquota fora do intervalo permitido",
        ],
    }
    for label, texts in paraphrases.items():
        examples.extend((t, label) for t in texts)

    return examples


@lru_cache(maxsize=1)
def _get_pipeline_and_metrics() -> tuple[Pipeline, float, float]:
    """Trains the classifier once per process (cached) and returns it with real held-out
    accuracy/F1 — never a hardcoded or assumed number."""
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

    # Refit on the full dataset for the classifier actually served (train/test split above exists
    # purely to report an honest, held-out quality number).
    pipeline.fit(texts, labels)
    return pipeline, accuracy, f1


def classify_discrepancy(description: str) -> TaxDiscrepancyClassification:
    """Classifies a tax discrepancy description into one of the three injected fiscal DQ
    categories and returns the matching recommended action — the local, CPU-only, no-network
    replacement for an LLM call on this closed-set task."""
    pipeline, _, _ = _get_pipeline_and_metrics()
    predicted = pipeline.predict([description])[0]
    proba = pipeline.predict_proba([description])[0]
    confidence = float(proba.max())
    human_label, action = CATEGORY_ACTIONS.get(predicted, ("Desconhecido", "Inspecionar o relatório de DQ manualmente."))
    return TaxDiscrepancyClassification(
        predicted_category=predicted,
        human_label=human_label,
        recommended_action=action,
        confidence=confidence,
    )


def evaluation_report() -> dict:
    """Real held-out accuracy/F1 for the currently-trained classifier — call this to see the
    actual quality number, not a claimed one."""
    _, accuracy, f1_macro = _get_pipeline_and_metrics()
    return {"accuracy": accuracy, "f1_macro": f1_macro, "n_classes": len(CATEGORY_ACTIONS)}


if __name__ == "__main__":
    report = evaluation_report()
    print(f"Held-out accuracy: {report['accuracy']:.1%} | macro F1: {report['f1_macro']:.3f} "
          f"| classes: {report['n_classes']}")

    examples = [
        "NCM code must be in the platform's (synthetic) product catalog",
        "cst_cfop_valid must be True",
        "IBS rate must be within [0, 1]",
    ]
    for text in examples:
        result = classify_discrepancy(text)
        print(f"\n  Input: {text}")
        print(f"  -> {result.human_label} (confidence {result.confidence:.1%})")
        print(f"     Action: {result.recommended_action}")
