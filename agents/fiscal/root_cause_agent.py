"""Fiscal Root-Cause Agent (ADR-015) — diagnoses why a synthetic fiscal document's printed tax
total (`calculated_tax_total`) diverges from the reference figure (`correct_tax_total`), with a
root cause and a recommended action.

Structurally the same shape as `agents/quality/data_quality_agent.py` (function returning a
dataclass with `.as_text()`, backed by a local TF-IDF+LogReg classifier with a keyword-matching
fallback) rather than the Agno multi-tool pattern of `agents/knowledge_ingestion/agent.py` — this
agent's job is a fixed, four-part diagnosis over already-structured data, not autonomous tool
selection across heterogeneous sources. See ADR-011's "LangChain vs. Agno vs. LangGraph" section
for the decision rule this follows.

Read/diagnose-only, same human-in-the-loop discipline as the Data Quality Agent (ADR-006): this
agent never corrects a fiscal document itself, it only surfaces a recommendation for a human.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from mcp.tools.fiscal import get_fiscal_document, get_fiscal_quality

logger = logging.getLogger(__name__)


@dataclass
class TaxDiagnosis:
    """The four-part diagnosis this agent always produces, same shape as
    `agents/quality/data_quality_agent.py::QualityDiagnosis`."""

    fiscal_document_id: str
    calculated_tax_total: float | None
    correct_tax_total: float | None
    discrepancy_amount: float | None
    main_cause: str
    recommended_action: str

    def as_text(self) -> str:
        calc = f"R$ {self.calculated_tax_total:.2f}" if self.calculated_tax_total is not None else "unknown"
        correct = f"R$ {self.correct_tax_total:.2f}" if self.correct_tax_total is not None else "unknown"
        diff = f"R$ {self.discrepancy_amount:.2f}" if self.discrepancy_amount is not None else "unknown"
        return (
            f"Document: {self.fiscal_document_id}\n"
            f"Calculated tax total: {calc} (reference: {correct}, discrepancy: {diff})\n"
            f"Main cause: {self.main_cause}\n"
            f"Recommended action: {self.recommended_action}"
        )


def _classify_cause(discrepancy_reason: str | None, worst_rule: dict | None) -> tuple[str, str]:
    """Classify the discrepancy's root cause via the local classifier, falling back to a
    keyword-matching heuristic if the classifier is unavailable — same discipline as
    `agents/quality/data_quality_agent.py::_recommend_action_for_cause`, this function must never
    raise just because the optimization layer is missing.

    Args:
        discrepancy_reason: the ground-truth label ("invalid_ncm" | "cst_cfop_mismatch" |
            "rate_out_of_range" | "none" | None) — preferred classifier input when available,
            since it's the exact real category, not a guess. `"none"` means the ground truth
            itself confirms this document is clean — that must short-circuit here, distinct from
            `None` (no ground truth available at all, e.g. document outside the synthetic
            dataset), which is the only case that falls back to `worst_rule` below. Conflating
            the two would misdiagnose a genuinely clean document using the dataset's unrelated
            global worst rule.
        worst_rule: `get_fiscal_quality()`'s `worst_rule` dict, used as the classifier input only
            when `discrepancy_reason` is `None` (not `"none"`).
    """
    if discrepancy_reason == "none":
        return "no discrepancy detected", "No action needed — calculated and reference tax totals match."

    classifier_input = discrepancy_reason
    if classifier_input is None and worst_rule and worst_rule.get("description"):
        classifier_input = worst_rule["description"]
    if classifier_input is None:
        return "no discrepancy detected", "No action needed — calculated and reference tax totals match."

    try:
        from agents.fiscal.tax_discrepancy_classifier import classify_discrepancy

        result = classify_discrepancy(classifier_input)
        return (
            f"[{result.human_label}, confidence {result.confidence:.0%}]",
            result.recommended_action,
        )
    except Exception:
        logger.exception(
            "tax_discrepancy_classifier failed for input %r — falling back to keyword heuristic", classifier_input
        )

    if "ncm" in classifier_input.lower():
        return "NCM issue (fallback)", "Review the item's NCM classification against the product catalog."
    if "cst" in classifier_input.lower() or "cfop" in classifier_input.lower():
        return "CST/CFOP issue (fallback)", "Review the CST/CFOP combination on this document."
    if "rate" in classifier_input.lower() or "alíquota" in classifier_input.lower():
        return "Rate issue (fallback)", "Review the IBS/CBS/Imposto Seletivo rates on this document."
    return "unknown (fallback)", "Inspect data_quality/reports/fiscal_dq_report.json manually."


def diagnose_tax_discrepancy(fiscal_document_id: str) -> TaxDiagnosis:
    """Diagnose why a fiscal document's calculated tax total diverges from the reference figure.

    Args:
        fiscal_document_id: e.g. "NFE00000042".

    Returns:
        A TaxDiagnosis with the discrepancy amount, root cause and recommended action. If the
        document isn't found, every numeric field is None and `main_cause` says so explicitly —
        never fabricated.
    """
    doc = get_fiscal_document(fiscal_document_id)
    if not doc.get("found"):
        return TaxDiagnosis(
            fiscal_document_id=fiscal_document_id,
            calculated_tax_total=None,
            correct_tax_total=None,
            discrepancy_amount=None,
            main_cause=f"unknown — {fiscal_document_id} not found in the synthetic fiscal dataset",
            recommended_action="Verify the document id, or run data/synthetic/generate_all.py --only fiscal.",
        )

    quality = get_fiscal_quality()
    label, action = _classify_cause(doc.get("discrepancy_reason"), quality.get("worst_rule"))

    return TaxDiagnosis(
        fiscal_document_id=fiscal_document_id,
        calculated_tax_total=doc.get("calculated_tax_total"),
        correct_tax_total=doc.get("correct_tax_total"),
        discrepancy_amount=doc.get("discrepancy_amount"),
        main_cause=label,
        recommended_action=action,
    )
