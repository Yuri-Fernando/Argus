"""Production robustness gate — decide se um modelo pode ser promovido a
produção com base no relatório de segurança do ThemisAI.

Integração: no pipeline real (`RFC-002`), o `ml-platform` chama
`themis_ai.core.adversarial_ml.run_security_assessment(model, X_test,
y_test, ...)` (repo `themis-ai`) e passa o `ModelSecurityReport` retornado
para `evaluate_gate()` aqui.

Este módulo depende só de um **protocolo estrutural** (`SecurityReportLike`),
não do pacote do Themis — assim o gate é testável isoladamente e o Argus
não acopla sua build ao repo de governança.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

_RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@runtime_checkable
class RobustnessLike(Protocol):
    clean_accuracy: float
    robust_accuracy: float
    risk_level: object  # enum ou str; normalizado por _risk_name


@runtime_checkable
class SecurityReportLike(Protocol):
    model_name: str
    overall_risk: object
    robustness: RobustnessLike


@dataclass(frozen=True)
class GateThresholds:
    max_overall_risk: str = "medium"        # aceita low|medium
    min_robust_accuracy: float = 0.60
    max_clean_to_robust_drop: float = 0.35


@dataclass(frozen=True)
class GateDecision:
    approved: bool
    model_name: str
    reasons: list[str]

    def as_dict(self) -> dict:
        return {"approved": self.approved, "model_name": self.model_name, "reasons": self.reasons}


def _risk_name(value: object) -> str:
    # aceita RiskLevel enum (tem .value) ou string
    return str(getattr(value, "value", value)).lower()


def evaluate_gate(report: SecurityReportLike, thresholds: GateThresholds | None = None) -> GateDecision:
    th = thresholds or GateThresholds()
    reasons: list[str] = []

    overall = _risk_name(report.overall_risk)
    if _RISK_RANK.get(overall, 3) > _RISK_RANK[th.max_overall_risk]:
        reasons.append(f"overall_risk={overall} acima do máximo permitido ({th.max_overall_risk})")

    rob = report.robustness
    if rob.robust_accuracy < th.min_robust_accuracy:
        reasons.append(
            f"robust_accuracy={rob.robust_accuracy:.2%} < mínimo {th.min_robust_accuracy:.0%}"
        )

    drop = rob.clean_accuracy - rob.robust_accuracy
    if drop > th.max_clean_to_robust_drop:
        reasons.append(
            f"queda clean→robust de {drop:.2%} > máximo {th.max_clean_to_robust_drop:.0%}"
        )

    return GateDecision(approved=not reasons, model_name=report.model_name, reasons=reasons)
