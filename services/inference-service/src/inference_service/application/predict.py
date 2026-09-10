"""Use case: executar uma predição.

Orquestra: resolve a estratégia (Strategy) via o resolver injetado
(Factory), executa a predição e publica o domain event `PredictionMade`.
Não conhece framework web nem provider concreto — só ports do domínio.
"""
from __future__ import annotations

from inference_service.application.ports import EventPublisher, StrategyResolver
from inference_service.domain.events import PredictionMade
from inference_service.domain.model import InferenceRequest, Prediction


class PredictUseCase:
    def __init__(self, resolver: StrategyResolver, event_publisher: EventPublisher):
        self._resolver = resolver
        self._events = event_publisher

    def execute(self, request: InferenceRequest) -> Prediction:
        strategy = self._resolver.resolve(request.model_id)
        prediction = strategy.predict(request)
        self._events.publish(PredictionMade.from_prediction(prediction))
        return prediction
