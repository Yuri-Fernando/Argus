"""Data Quality Agent — diagnoses DQ drops with root cause, affected rows, recommended action.

Built in ROADMAP.md Sprint 14. This is agent #2 of the four described in ARCHITECTURE.md §15.
It calls `get_data_quality` / `get_pipeline_status` / `get_customer_quality`
(`mcp/tools/quality.py`) and turns the raw scores into the structured diagnosis format the
original design sketch (rascunho.md §43) demonstrated:

    Quality decreased: 97.8% -> 92.4%
    Main cause: CRM email completeness.
    Affected rows: 12,341
    Recommended action: Review CRM extraction job.

That example is the acceptance bar this agent is built against — see
`agents/quality/evaluation/golden_questions.yaml` for the encoded version of it.

This agent is read/diagnose-only: it never triggers a pipeline re-run or any other write itself.
"Recommended action" is exactly that — a recommendation surfaced to a human (typically a data
engineer, not the Recommendation Agent's customer-facing approval flow), consistent with the
platform-wide human-in-the-loop stance in ADR-006 even though this particular agent's actions
are lower-stakes than customer-facing ones.
"""

from __future__ import annotations

from dataclasses import dataclass

from mcp.tools.quality import get_data_quality, get_pipeline_status


@dataclass
class QualityDiagnosis:
    """The four-part diagnosis this agent always produces, matching ARCHITECTURE.md §15's example."""

    dataset: str
    previous_score: float | None
    current_score: float | None
    main_cause: str
    affected_rows: int | None
    recommended_action: str

    def as_text(self) -> str:
        """Render the diagnosis in the exact prose shape from ARCHITECTURE.md §15's example."""
        prev = f"{self.previous_score:.1%}" if self.previous_score is not None else "unknown"
        curr = f"{self.current_score:.1%}" if self.current_score is not None else "unknown"
        rows = f"{self.affected_rows:,}" if self.affected_rows is not None else "unknown"
        return (
            f"Quality decreased: {prev} -> {curr}\n"
            f"Main cause: {self.main_cause}\n"
            f"Affected rows: {rows}\n"
            f"Recommended action: {self.recommended_action}"
        )


def _infer_main_cause(dataset: str, dimension_scores: dict[str, float | None]) -> str:
    """Pick the lowest-scoring DQ dimension as the headline root cause.

    Args:
        dataset: the dataset name being diagnosed, used only for the fallback message.
        dimension_scores: the `dimension_scores` dict from get_data_quality()'s output
            (completeness/validity/uniqueness/referential_integrity/freshness/schema/
            volume_anomaly).

    Returns:
        A short human-readable cause string, e.g. "CRM email completeness.".
    """
    scored = {k: v for k, v in dimension_scores.items() if v is not None}
    if not scored:
        return f"unknown — no dimension scores available for {dataset} yet"
    worst_dimension = min(scored, key=lambda k: scored[k])
    return f"{dataset} {worst_dimension}."


def _recommend_action_for_cause(main_cause: str) -> str:
    """Map a diagnosed cause to a short, human-actionable recommendation.

    Backed by `agents/quality/root_cause_classifier.py` — a local, CPU-only, no-LLM-round-trip
    classifier trained on the platform's real DQ rule catalog (see that module's docstring for
    the honest scope note on how this relates to the add2.txt "LLM optimization/quantization"
    backlog item it implements). Falls back to the original keyword-matching heuristic if the
    classifier is unavailable for any reason (e.g. scikit-learn not installed in a minimal
    deployment) — this function must never raise just because the optimization layer is missing.
    """
    try:
        from agents.quality.root_cause_classifier import classify_root_cause

        result = classify_root_cause(main_cause)
        return f"[{result.human_label}, confidence {result.confidence:.0%}] {result.recommended_action}"
    except Exception:
        pass

    if "completeness" in main_cause:
        return "Review the upstream extraction job for missing-field regressions."
    if "freshness" in main_cause:
        return "Check the ingestion schedule/trigger for the affected source."
    if "schema" in main_cause:
        return "Compare current vs. expected schema; likely an upstream schema drift."
    return "Inspect the GX Data Docs report for this dataset for the specific failing expectations."


def diagnose_quality_drop(dataset: str, previous_score: float | None = None) -> QualityDiagnosis:
    """Diagnose a data quality score drop for a given dataset.

    Args:
        dataset: dataset name, e.g. "silver.crm_customers" (see ARCHITECTURE.md §6/§7).
        previous_score: the last-known-good score to compare against. If omitted, the diagnosis
            reports only the current score with `previous_score=None` (i.e. "unknown" in the
            rendered text) rather than guessing a baseline.

    Returns:
        A QualityDiagnosis with root cause, affected row count and a recommended action —
        matching the ARCHITECTURE.md §15 example format.
    """
    dq = get_data_quality(dataset)
    pipeline = get_pipeline_status(dataset)

    main_cause = _infer_main_cause(dataset, dq["dimension_scores"])
    recommended_action = _recommend_action_for_cause(main_cause)

    # TODO(Sprint 3 / data_quality): affected_rows should come from the specific failing GX
    # Expectation's `unexpected_count` in `data_quality/reports/`, not from `pipeline`'s
    # generic `rows_processed` — using the latter as a stand-in until that report shape is
    # available to read from here.
    affected_rows = pipeline.get("rows_processed")

    return QualityDiagnosis(
        dataset=dataset,
        previous_score=previous_score,
        current_score=dq["dq_score"],
        main_cause=main_cause,
        affected_rows=affected_rows,
        recommended_action=recommended_action,
    )
