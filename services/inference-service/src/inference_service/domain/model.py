"""Domain model do Inference Service — value objects e regras de domínio.

Bounded context: Model Inference. Não conhece FastAPI, XGBoost nem
provider de LLM — só o conceito de "pedir uma predição a um modelo
registrado e receber um score com explicação".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

HIGH_RISK_THRESHOLD = 0.7


class ModelKind(str, Enum):
    TABULAR_GBDT = "tabular_gbdt"
    TABULAR_LINEAR = "tabular_linear"
    LLM = "llm"


@dataclass(frozen=True)
class ModelId:
    name: str
    version: str

    def __post_init__(self) -> None:
        if not self.name or not self.version:
            raise ValueError("ModelId exige name e version não vazios")

    def __str__(self) -> str:  # ubiquitous language: "churn@3"
        return f"{self.name}@{self.version}"


@dataclass(frozen=True)
class InferenceRequest:
    model_id: ModelId
    features: dict[str, float | int | str]
    request_id: str

    def __post_init__(self) -> None:
        if not self.features:
            raise ValueError("InferenceRequest exige ao menos uma feature")


@dataclass(frozen=True)
class Prediction:
    model_id: ModelId
    request_id: str
    score: float
    label: str
    explanation: dict[str, Any] = field(default_factory=dict)
    produced_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score fora de [0,1]: {self.score}")

    @property
    def is_high_risk(self) -> bool:
        return self.score >= HIGH_RISK_THRESHOLD
