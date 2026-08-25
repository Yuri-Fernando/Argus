"""Co-located unit test for tax_discrepancy_classifier.py — mirrors the co-location convention
tests/unit/README.md documents (e.g. mdm/matching/test_fuzzy.py next to fuzzy.py), not a
tests/unit/ file.
"""
from __future__ import annotations

from agents.fiscal.tax_discrepancy_classifier import CATEGORY_ACTIONS, classify_discrepancy, evaluation_report


def test_evaluation_report_reflects_real_training_run():
    """`evaluation_report()` must return a real, freshly-computed held-out score every time — a
    minimal floor assertion, not a pinned exact number (the exact score can shift slightly if
    _seed_examples()'s paraphrase list ever changes), but proves the classifier trains and
    generalizes meaningfully better than the ~33% random baseline for 3 classes."""
    report = evaluation_report()
    assert report["n_classes"] == 3
    assert 0.0 <= report["accuracy"] <= 1.0
    assert report["accuracy"] > 0.33  # meaningfully better than chance across 3 classes


def test_classify_discrepancy_returns_a_known_category():
    """Every prediction must land in the closed CATEGORY_ACTIONS set — this is a closed-set
    classification task by design (see module docstring), never free text."""
    result = classify_discrepancy("NCM code must be in the platform's catalog")
    assert result.predicted_category in CATEGORY_ACTIONS
    assert 0.0 <= result.confidence <= 1.0
    assert result.human_label and result.recommended_action


if __name__ == "__main__":
    test_evaluation_report_reflects_real_training_run()
    test_classify_discrepancy_returns_a_known_category()
    print("All tests passed.")
