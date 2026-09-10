"""Testes da interface gRPC do inference-service — servidor in-process +
canal local, exercitando o mesmo use case da interface REST."""
from __future__ import annotations

import json

import grpc
import pytest

from inference_service.interfaces.grpc_gen import inference_pb2, inference_pb2_grpc
from inference_service.interfaces.grpc_server import serve

FEATURES = {"recency_days": 90.0, "frequency": 2.0, "avg_ticket": 120.0, "support_incidents": 3.0}


@pytest.fixture()
def grpc_stub():
    server = serve(port=50077)
    channel = grpc.insecure_channel("localhost:50077")
    yield inference_pb2_grpc.InferenceServiceStub(channel)
    channel.close()
    server.stop(grace=None)


def test_health(grpc_stub):
    resp = grpc_stub.Health(inference_pb2.HealthRequest())
    assert resp.status == "ok"


def test_predict_returns_scored_response(grpc_stub):
    resp = grpc_stub.Predict(inference_pb2.PredictRequest(
        model_name="churn-linear", model_version="1", request_id="g1", features=FEATURES,
    ))
    assert resp.model_id == "churn-linear@1"
    assert 0.0 <= resp.score <= 1.0
    assert resp.label in ("high_risk", "low_risk")
    assert json.loads(resp.explanation_json)["method"] == "linear"


def test_predict_unknown_model_is_invalid_argument(grpc_stub):
    with pytest.raises(grpc.RpcError) as exc:
        grpc_stub.Predict(inference_pb2.PredictRequest(
            model_name="nope", model_version="1", request_id="g2", features=FEATURES,
        ))
    assert exc.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_rest_and_grpc_agree_on_score(grpc_stub):
    from fastapi.testclient import TestClient

    from inference_service.interfaces.rest import create_app

    rest = TestClient(create_app())
    rest_score = rest.post("/v1/predict", json={
        "model_name": "churn-linear", "model_version": "1", "request_id": "x", "features": FEATURES,
    }).json()["score"]
    grpc_score = grpc_stub.Predict(inference_pb2.PredictRequest(
        model_name="churn-linear", model_version="1", request_id="x", features=FEATURES,
    )).score
    assert abs(rest_score - grpc_score) < 1e-9
