"""Ports (hexagonal architecture) — o que a aplicação precisa do mundo
externo, expresso como interfaces. Os adaptadores concretos vivem em
`infrastructure/`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from inference_service.domain.events import PredictionMade
from inference_service.domain.model import ModelId
from inference_service.domain.strategies import PredictionStrategy


class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event: PredictionMade) -> None: ...


class StrategyResolver(ABC):
    """Resolve um `ModelId` para a `PredictionStrategy` concreta a usar."""

    @abstractmethod
    def resolve(self, model_id: ModelId) -> PredictionStrategy: ...
