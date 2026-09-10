"""Implementações concretas de `PredictionStrategy` (infra).

- `LinearTabularStrategy`: regressão logística em numpy (sem dependência
  de framework). Coeficientes fixos/treináveis; explicação = contribuição
  por feature.
- `GbdtTabularStrategy`: usa `xgboost` se disponível; degrada para a
  estratégia linear se a lib não estiver instalada (mantém o serviço
  testável em ambiente mínimo).
- `LlmStrategy`: delega a um `LLMProviderPort` (Adapter pattern) e converte
  a resposta textual em score/label.
"""
from __future__ import annotations

import math
import re

from inference_service.domain.model import InferenceRequest, ModelKind, ModelId, Prediction
from inference_service.domain.strategies import PredictionStrategy
from inference_service.infrastructure.adapters import LLMProviderPort


def _to_vector(features: dict, order: list[str]) -> list[float]:
    return [float(features.get(name, 0.0) or 0.0) for name in order]


class LinearTabularStrategy(PredictionStrategy):
    kind = ModelKind.TABULAR_LINEAR

    def __init__(self, feature_order: list[str], weights: list[float], bias: float = 0.0):
        if len(feature_order) != len(weights):
            raise ValueError("feature_order e weights com tamanhos diferentes")
        self.feature_order = feature_order
        self.weights = weights
        self.bias = bias

    def predict(self, request: InferenceRequest) -> Prediction:
        x = _to_vector(request.features, self.feature_order)
        contributions = {f: round(w * xi, 4) for f, w, xi in zip(self.feature_order, self.weights, x)}
        z = sum(contributions.values()) + self.bias
        score = 1.0 / (1.0 + math.exp(-z))
        label = "high_risk" if score >= 0.7 else "low_risk"
        return Prediction(
            model_id=request.model_id,
            request_id=request.request_id,
            score=round(score, 6),
            label=label,
            explanation={"method": "linear", "contributions": contributions, "bias": self.bias},
        )


class GbdtTabularStrategy(PredictionStrategy):
    kind = ModelKind.TABULAR_GBDT

    def __init__(self, feature_order: list[str], fallback: LinearTabularStrategy):
        self.feature_order = feature_order
        self._fallback = fallback
        self._booster = None
        try:  # xgboost é opcional no ambiente de teste mínimo
            import xgboost  # noqa: F401
            self._xgb_available = True
        except Exception:
            self._xgb_available = False

    def fit(self, X, y) -> "GbdtTabularStrategy":
        if not self._xgb_available:
            return self
        import numpy as np
        import xgboost as xgb

        dtrain = xgb.DMatrix(np.asarray(X, dtype=float), label=np.asarray(y, dtype=float))
        self._booster = xgb.train(
            {"objective": "binary:logistic", "max_depth": 3, "eta": 0.3, "verbosity": 0},
            dtrain, num_boost_round=30,
        )
        return self

    def predict(self, request: InferenceRequest) -> Prediction:
        if self._booster is None:
            pred = self._fallback.predict(request)
            pred.explanation["method"] = "gbdt->linear_fallback"
            return pred
        import numpy as np
        import xgboost as xgb

        x = np.asarray([_to_vector(request.features, self.feature_order)], dtype=float)
        score = float(self._booster.predict(xgb.DMatrix(x))[0])
        return Prediction(
            model_id=request.model_id,
            request_id=request.request_id,
            score=round(score, 6),
            label="high_risk" if score >= 0.7 else "low_risk",
            explanation={"method": "gbdt", "n_trees": 30},
        )


class LlmStrategy(PredictionStrategy):
    kind = ModelKind.LLM

    def __init__(self, provider: LLMProviderPort):
        self._provider = provider

    def predict(self, request: InferenceRequest) -> Prediction:
        prompt = (
            "Classifique o risco de churn deste cliente numa escala 0.0 a 1.0. "
            f"Features: {request.features}. Responda apenas 'risk=<valor>'."
        )
        text = self._provider.complete(prompt)
        match = re.search(r"risk\s*=\s*([01](?:\.\d+)?)", text)
        score = float(match.group(1)) if match else 0.5
        score = min(max(score, 0.0), 1.0)
        return Prediction(
            model_id=request.model_id,
            request_id=request.request_id,
            score=round(score, 6),
            label="high_risk" if score >= 0.7 else "low_risk",
            explanation={"method": "llm", "provider": self._provider.name, "raw": text},
        )
