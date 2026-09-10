"""Strategy pattern — contrato de política de predição.

Cada modelo/algoritmo (GBDT, linear, LLM) é uma `PredictionStrategy`. A
camada de aplicação depende só desta abstração; as implementações concretas
vivem em `infrastructure/strategies_impl.py` e são resolvidas pela
`ModelFactory`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from inference_service.domain.model import InferenceRequest, ModelKind, Prediction


class PredictionStrategy(ABC):
    kind: ModelKind

    @abstractmethod
    def predict(self, request: InferenceRequest) -> Prediction:
        """Produz uma `Prediction` para o `request`."""
        raise NotImplementedError
