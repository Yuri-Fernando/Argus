"""Golden Q&A set for the local RAG stack — 15 questions genuinely grounded in the actual
content of `data/documents/*.md` (read directly from those four files; no invented facts, per
Constitution Article IV).

Each entry maps a question to the `doc_type` (== source file stem) whose content should surface
in the top-k retrieved chunks. `expected_doc_types` is a list because a couple of questions
legitimately span two documents (e.g. VIP loyalty status referencing the segmentation model).
`must_contain` is an optional substring the correct chunk's text should contain, used only for
sanity-checking the golden set itself, not scored by `precision_at_k.py`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GoldenQuestion:
    question: str
    expected_doc_types: tuple[str, ...]
    must_contain: str


GOLDEN_QUESTIONS: list[GoldenQuestion] = [
    GoldenQuestion(
        "How many days does a customer have to request a refund after delivery?",
        ("refund_policy",),
        "30 days",
    ),
    GoldenQuestion(
        "What is the right of withdrawal (arrependimento) window under Brazilian consumer law?",
        ("refund_policy",),
        "7 calendar days",
    ),
    GoldenQuestion(
        "Which refunds require supervisor approval / human-in-the-loop?",
        ("refund_policy",),
        "R$ 1,000",
    ),
    GoldenQuestion(
        "Are final sale or clearance products eligible for a refund?",
        ("refund_policy",),
        "final sale",
    ),
    GoldenQuestion(
        "How long does it take to process an approved refund back to the original payment method?",
        ("refund_policy",),
        "10 business days",
    ),
    GoldenQuestion(
        "What is the estimated delivery window for the Southeast region (SP, RJ, MG, ES)?",
        ("delivery_policy",),
        "3",
    ),
    GoldenQuestion(
        "When is an order considered late?",
        ("delivery_policy",),
        "estimated delivery date",
    ),
    GoldenQuestion(
        "What happens after 3 failed delivery attempts?",
        ("delivery_policy",),
        "returned to the seller",
    ),
    GoldenQuestion(
        "Does a late delivery qualify for any automatic refund?",
        ("delivery_policy",),
        "shipping-fee refund",
    ),
    GoldenQuestion(
        "How many orders in a rolling 12 months are required to reach Gold loyalty tier?",
        ("loyalty_policy",),
        "8+ orders",
    ),
    GoldenQuestion(
        "What benefit does the Platinum loyalty tier give?",
        ("loyalty_policy",),
        "10% cashback",
    ),
    GoldenQuestion(
        "Do VIP-segmented customers automatically get Gold-tier loyalty benefits?",
        ("loyalty_policy",),
        "VIP",
    ),
    GoldenQuestion(
        "What personal data does the platform collect about customers?",
        ("privacy_policy",),
        "Name, email, phone",
    ),
    GoldenQuestion(
        "How are government ID numbers stored, if at all?",
        ("privacy_policy",),
        "SHA-256",
    ),
    GoldenQuestion(
        "How long does the company take to fulfil a data access or deletion request under LGPD?",
        ("privacy_policy",),
        "15 business days",
    ),
]
