"""Testes do Inference Service — domínio, use case, Factory/Strategy/Adapter
e a interface REST."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from inference_service.application.predict import PredictUseCase
from inference_service.domain.model import HIGH_RISK_THRESHOLD, InferenceRequest, ModelId, Prediction
from inference_service.infrastructure.adapters import LocalHeuristicAdapter
from inference_service.infrastructure.in_memory_event_bus import InMemoryEventBus
from inference_service.infrastructure.model_factory import ModelFactory
from inference_service.interfaces.rest import create_app

FEATURES = {"recency_days": 90, "frequency": 2, "avg_ticket": 120.0, "support_incidents": 3}


# --- domínio -----------------------------------------------------------------

def test_model_id_str_is_ubiquitous_language():
    assert str(ModelId("churn", "3")) == "churn@3"


def test_model_id_rejects_empty():
    with pytest.raises(ValueError):
        ModelId("", "1")


def test_prediction_rejects_out_of_range_score():
    with pytest.raises(ValueError):
        Prediction(ModelId("m", "1"), "r1", score=1.5, label="x")


def test_high_risk_property():
    p = Prediction(ModelId("m", "1"), "r1", score=HIGH_RISK_THRESHOLD, label="high_risk")
    assert p.is_high_risk is True


def test_inference_request_requires_features():
    with pytest.raises(ValueError):
        InferenceRequest(ModelId("m", "1"), {}, "r1")


# --- Factory + Strategy ----------------------------------------------------

def test_factory_resolves_and_caches_strategy():
    factory = ModelFactory()
    s1 = factory.resolve(ModelId("churn-linear", "1"))
    s2 = factory.resolve(ModelId("churn-linear", "1"))
    assert s1 is s2  # cache


def test_factory_unknown_model_raises():
    with pytest.raises(KeyError):
        ModelFactory().resolve(ModelId("does-not-exist", "1"))


def test_linear_strategy_returns_calibrated_score_and_contributions():
    factory = ModelFactory()
    strategy = factory.resolve(ModelId("churn-linear", "1"))
    pred = strategy.predict(InferenceRequest(ModelId("churn-linear", "1"), FEATURES, "r1"))
    assert 0.0 <= pred.score <= 1.0
    assert set(pred.explanation["contributions"]) == set(FEATURES)


def test_gbdt_strategy_falls_back_when_untrained():
    factory = ModelFactory()
    strategy = factory.resolve(ModelId("churn", "1"))
    pred = strategy.predict(InferenceRequest(ModelId("churn", "1"), FEATURES, "r1"))
    assert pred.explanation["method"].startswith("gbdt")


def test_llm_strategy_via_local_adapter():
    factory = ModelFactory(llm_provider=LocalHeuristicAdapter())
    strategy = factory.resolve(ModelId("churn-llm", "1"))
    pred = strategy.predict(InferenceRequest(ModelId("churn-llm", "1"), FEATURES, "r1"))
    assert pred.explanation["provider"] == "local-heuristic"
    assert 0.0 <= pred.score <= 1.0


# --- use case + evento ---------------------------------------------------

def test_use_case_publishes_domain_event():
    factory = ModelFactory()
    bus = InMemoryEventBus()
    uc = PredictUseCase(factory, bus)
    uc.execute(InferenceRequest(ModelId("churn-linear", "1"), FEATURES, "r1"))
    assert len(bus.published) == 1
    assert bus.published[0].model_id == "churn-linear@1"
    assert "occurred_at" in bus.published[0].to_message()


# --- REST -------------------------------------------------------------------

def test_rest_predict_endpoint():
    client = TestClient(create_app())
    resp = client.post(
        "/v1/predict",
        json={"model_name": "churn-linear", "model_version": "1", "request_id": "req-1", "features": FEATURES},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_id"] == "churn-linear@1"
    assert 0.0 <= body["score"] <= 1.0
    assert isinstance(body["high_risk"], bool)


def test_rest_predict_unknown_model_is_400():
    client = TestClient(create_app())
    resp = client.post(
        "/v1/predict",
        json={"model_name": "nope", "model_version": "1", "request_id": "r", "features": FEATURES},
    )
    assert resp.status_code == 400
