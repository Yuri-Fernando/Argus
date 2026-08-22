"""Monitoring Agent — watches pipeline/model/LLM health signals and raises alerts.

Built in ROADMAP.md Sprint 14 (agent), wired to real signals in Sprint 16 ("Governance,
Security, Observability, IaC, FinOps"). This is agent #4 of the four described in
ARCHITECTURE.md §15. It reads the OpenTelemetry-derived metrics ARCHITECTURE.md §17 lists
(`pipeline_duration`, `rows_processed`, `dq_score`, `ml_latency`, `agent_latency`, `mcp_calls`,
`llm_tokens`) once `monitoring/prometheus/` (ROADMAP.md Sprint 16) exists, and raises structured
alerts when a signal crosses a threshold.

Like the Data Quality Agent, this agent only observes and reports — it never restarts a job,
rolls back a deployment, or otherwise mutates platform state. Any such response is, per the same
human-in-the-loop posture as the rest of the platform (ADR-006), a recommendation for a human
on-call engineer, not an automatic action.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AlertSeverity(str, Enum):
    """Alert severity, ordered low to high."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class HealthSignal:
    """A single observed metric value, mirroring one of ARCHITECTURE.md §17's tracked metrics."""

    name: str  # e.g. "pipeline_duration", "dq_score", "ml_latency", "agent_latency"
    value: float | None
    unit: str  # e.g. "seconds", "score", "ms", "tokens"
    threshold: float | None = None
    source: str | None = None  # e.g. pipeline/job/model/agent name this signal came from


@dataclass
class Alert:
    """A raised alert — what the agent emits when a signal crosses its threshold."""

    signal_name: str
    severity: AlertSeverity
    message: str
    value: float | None
    threshold: float | None
    source: str | None = None


# Default thresholds for the metrics ARCHITECTURE.md §17 lists as tracked. These are placeholder
# values to be replaced once real distributions are observed in Sprint 16 — see the TODO in
# evaluate_signals(). Kept as a plain dict (not hardcoded per-check) so a later sprint can load
# this from `monitoring/prometheus/` alerting rules instead of Python source.
DEFAULT_THRESHOLDS: dict[str, float] = {
    "dq_score": 0.90,  # alert if dq_score drops below this
    "pipeline_duration_seconds": 3600.0,  # alert if a job runs longer than this
    "ml_latency_ms": 2000.0,
    "agent_latency_ms": 8000.0,
    "mcp_call_error_rate": 0.05,
}


def fetch_health_signals() -> list[HealthSignal]:
    """Collect the current value of every tracked health signal.

    `dq_score` is wired to the real `data_quality/reports/dq_report.json` (produced by
    `lakehouse/run_pipeline.py`) — no Prometheus needed for a point-in-time snapshot read. The
    remaining four signals genuinely need a running Prometheus exporter accumulating values over
    time (job duration history, per-request ML/agent latency, MCP call error rate) — none of
    that infra runs in this environment (ADR-010, local-first), so they stay honestly `None`
    rather than a fabricated point estimate. See the TODO below for exactly what wiring those
    needs once Sprint 16's `monitoring/prometheus/` stack is actually running.

    Returns:
        A list of HealthSignal, one per metric ARCHITECTURE.md §17 lists.
    """
    signals = [
        HealthSignal(name=name, value=None, unit="unknown", threshold=threshold)
        for name, threshold in DEFAULT_THRESHOLDS.items()
    ]

    dq_signal = next(s for s in signals if s.name == "dq_score")
    try:
        import json
        from pathlib import Path

        report_path = Path(__file__).resolve().parents[2] / "data_quality" / "reports" / "dq_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        dq_signal.value = report["overall_score"]
        dq_signal.unit = "score"
        dq_signal.source = "data_quality/reports/dq_report.json"
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass  # report not generated yet (`python lakehouse/run_pipeline.py` never ran) — stays None.

    # TODO(Sprint 16 / monitoring): once monitoring/prometheus/ actually runs, replace the loop
    # above for the remaining four signals with real queries against its HTTP API (or the
    # `prometheus-client` registry directly if this agent runs in-process with the exporter).
    return signals


def evaluate_signals(signals: list[HealthSignal]) -> list[Alert]:
    """Compare each signal to its threshold and produce alerts for breaches.

    Args:
        signals: signals as returned by fetch_health_signals() (or a synthetic list in tests).

    Returns:
        A list of Alert, one per signal that breached its threshold. Signals with `value=None`
        (not yet wired to a real source) never raise an alert — an unknown value is not treated
        as a breach, to avoid false positives before Sprint 16's wiring lands.
    """
    alerts: list[Alert] = []
    for signal in signals:
        if signal.value is None or signal.threshold is None:
            continue

        # dq_score alerts when the value drops BELOW threshold; everything else alerts when the
        # value rises ABOVE threshold. TODO(Sprint 16): move this per-metric comparison
        # direction into the threshold config itself (e.g. {"metric": ..., "direction": "below"})
        # once there is more than one "lower is worse" metric to justify the generalization.
        breached = signal.value < signal.threshold if signal.name == "dq_score" else signal.value > signal.threshold
        if not breached:
            continue

        severity = AlertSeverity.CRITICAL if signal.name == "dq_score" else AlertSeverity.WARNING
        alerts.append(
            Alert(
                signal_name=signal.name,
                severity=severity,
                message=f"{signal.name} breached threshold: {signal.value} vs {signal.threshold}",
                value=signal.value,
                threshold=signal.threshold,
                source=signal.source,
            )
        )
    return alerts


def run_monitoring_cycle() -> list[Alert]:
    """One full monitoring pass: fetch signals, evaluate them, return any raised alerts.

    TODO(Sprint 16): call this on a schedule (e.g. a lightweight loop or a Databricks/Airflow-
    style job) and forward `alerts` to whatever channel the platform uses for on-call paging —
    not specified yet; documented as an open item in ROADMAP.md Sprint 16.
    """
    signals = fetch_health_signals()
    return evaluate_signals(signals)
