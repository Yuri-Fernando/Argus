"""Testes de integração com brokers reais (Kafka/RabbitMQ).

Rodam apenas quando `RUN_INTEGRATION=1` e o broker está acessível — em
qualquer outro caso, `pytest.skip`. Suba os brokers com:

    make up-enterprise
    make test-integration
"""
from __future__ import annotations

import os
import socket
import sys
import uuid
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "platform" / "messaging"))


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except OSError:
        return False


def _require(host: str, port: int, name: str) -> None:
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("RUN_INTEGRATION != 1 (rode `make test-integration`)")
    if not _port_open(host, port):
        pytest.skip(f"{name} indisponível em {host}:{port} — rode `make up-enterprise`")


def test_kafka_publish_then_consume_roundtrip():
    _require("localhost", 9092, "Kafka")
    from bus import KafkaBus  # noqa: PLC0415

    topic = f"argus.itest.{uuid.uuid4().hex[:8]}"
    kb = KafkaBus(bootstrap_servers="localhost:9092")
    payload = {"request_id": "it-1", "model_id": "churn@3", "score": 0.9,
               "label": "high_risk", "high_risk": True, "occurred_at": "2026-09-10T00:00:00Z"}
    kb.publish(topic, payload)

    got = kb.consume_batch(topic, max_messages=1, timeout_s=10)
    assert got and got[0]["request_id"] == "it-1"


def test_rabbitmq_publish_then_consume_roundtrip():
    _require("localhost", 5672, "RabbitMQ")
    from bus import RabbitBus  # noqa: PLC0415

    queue = f"argus.itest.{uuid.uuid4().hex[:8]}"
    rb = RabbitBus("amqp://guest:guest@localhost:5672/")
    rb.publish(queue, {"job": "report.generate", "id": 7})

    got = rb.consume_batch(queue, max_messages=1, timeout_s=5)
    assert got and got[0]["id"] == 7


def test_outbox_relay_into_kafka():
    """Fluxo completo: predição -> outbox (SQLite) -> relay -> Kafka real."""
    _require("localhost", 9092, "Kafka")
    from bus import KafkaBus  # noqa: PLC0415

    from inference_service.application.predict import PredictUseCase
    from inference_service.domain.model import InferenceRequest, ModelId
    from inference_service.infrastructure.model_factory import ModelFactory
    from inference_service.infrastructure.outbox import OutboxEventPublisher, SqliteOutbox, relay

    topic = f"argus.itest.{uuid.uuid4().hex[:8]}"

    class _TopicBus:
        def __init__(self, kb, t):
            self._kb, self._t = kb, t

        def publish(self, _topic, msg):
            self._kb.publish(self._t, msg)

    outbox = SqliteOutbox(":memory:")
    uc = PredictUseCase(ModelFactory(), OutboxEventPublisher(outbox))
    uc.execute(InferenceRequest(ModelId("churn-linear", "1"),
                                {"recency_days": 90, "frequency": 2, "avg_ticket": 120.0,
                                 "support_incidents": 3}, "it-flow"))

    kb = KafkaBus(bootstrap_servers="localhost:9092")
    assert relay(outbox, _TopicBus(kb, topic)) == 1
    got = kb.consume_batch(topic, max_messages=1, timeout_s=10)
    assert got and got[0]["request_id"] == "it-flow"
