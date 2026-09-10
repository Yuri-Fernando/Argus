"""Adaptador de `EventPublisher` em memória — usado em desenvolvimento e
testes. Em produção, o adaptador Kafka publica `PredictionMade` no tópico
`model.prediction.created` (`platform/messaging/`).
"""
from __future__ import annotations

from inference_service.application.ports import EventPublisher
from inference_service.domain.events import PredictionMade


class InMemoryEventBus(EventPublisher):
    def __init__(self) -> None:
        self.published: list[PredictionMade] = []

    def publish(self, event: PredictionMade) -> None:
        self.published.append(event)
