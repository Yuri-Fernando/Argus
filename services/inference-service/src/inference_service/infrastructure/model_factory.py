"""Factory pattern — cria e cacheia a `PredictionStrategy` concreta para
cada `ModelId`, a partir de um registro declarativo (`models.yaml` no
projeto real; um dict embutido aqui para o skeleton).

Implementa o port `StrategyResolver` que o use case consome.
"""
from __future__ import annotations

from inference_service.application.ports import StrategyResolver
from inference_service.domain.model import ModelId, ModelKind
from inference_service.domain.strategies import PredictionStrategy
from inference_service.infrastructure.adapters import LLMProviderPort, LocalHeuristicAdapter
from inference_service.infrastructure.strategies_impl import (
    GbdtTabularStrategy,
    LinearTabularStrategy,
    LlmStrategy,
)

# Registro de modelos (no projeto real: agents/llm_gateway/models.yaml + MLflow registry).
_REGISTRY: dict[str, dict] = {
    "churn": {
        "kind": ModelKind.TABULAR_GBDT,
        "feature_order": ["recency_days", "frequency", "avg_ticket", "support_incidents"],
        "weights": [0.03, -0.05, -0.0002, 0.4],
        "bias": -0.5,
    },
    "churn-linear": {
        "kind": ModelKind.TABULAR_LINEAR,
        "feature_order": ["recency_days", "frequency", "avg_ticket", "support_incidents"],
        "weights": [0.03, -0.05, -0.0002, 0.4],
        "bias": -0.5,
    },
    "churn-llm": {"kind": ModelKind.LLM},
}


class ModelFactory(StrategyResolver):
    def __init__(self, llm_provider: LLMProviderPort | None = None):
        self._llm_provider = llm_provider or LocalHeuristicAdapter()
        self._cache: dict[str, PredictionStrategy] = {}

    def resolve(self, model_id: ModelId) -> PredictionStrategy:
        if model_id.name in self._cache:
            return self._cache[model_id.name]

        spec = _REGISTRY.get(model_id.name)
        if spec is None:
            raise KeyError(f"modelo não registrado: {model_id.name}")

        strategy = self._build(spec)
        self._cache[model_id.name] = strategy
        return strategy

    def _build(self, spec: dict) -> PredictionStrategy:
        kind = spec["kind"]
        if kind == ModelKind.TABULAR_LINEAR:
            return LinearTabularStrategy(spec["feature_order"], spec["weights"], spec.get("bias", 0.0))
        if kind == ModelKind.TABULAR_GBDT:
            fallback = LinearTabularStrategy(spec["feature_order"], spec["weights"], spec.get("bias", 0.0))
            return GbdtTabularStrategy(spec["feature_order"], fallback)
        if kind == ModelKind.LLM:
            return LlmStrategy(self._llm_provider)
        raise ValueError(f"kind desconhecido: {kind}")
