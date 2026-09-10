"""Domain events do Inference Service.

Emitidos pela camada de aplicação após uma predição. Um adaptador de
infraestrutura os publica no event backbone (Kafka, tópico
`model.prediction.created` — ver `platform/messaging/schemas/`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from inference_service.domain.model import Prediction


@dataclass(frozen=True)
class PredictionMade:
    request_id: str
    model_id: str
    score: float
    label: str
    high_risk: bool
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_prediction(cls, prediction: Prediction) -> "PredictionMade":
        return cls(
            request_id=prediction.request_id,
            model_id=str(prediction.model_id),
            score=prediction.score,
            label=prediction.label,
            high_risk=prediction.is_high_risk,
        )

    def to_message(self) -> dict:
        """Payload alinhado ao JSON Schema de `model.prediction.created`."""
        return {
            "request_id": self.request_id,
            "model_id": self.model_id,
            "score": self.score,
            "label": self.label,
            "high_risk": self.high_risk,
            "occurred_at": self.occurred_at.isoformat(),
        }
