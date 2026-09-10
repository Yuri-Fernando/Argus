"""Testes do transactional outbox — durabilidade do domain event e relay
idempotente para o bus."""
from __future__ import annotations

from inference_service.application.predict import PredictUseCase
from inference_service.domain.model import InferenceRequest, ModelId
from inference_service.infrastructure.model_factory import ModelFactory
from inference_service.infrastructure.outbox import OutboxEventPublisher, SqliteOutbox, relay

FEATURES = {"recency_days": 90, "frequency": 2, "avg_ticket": 120.0, "support_incidents": 3}


class _CapturingBus:
    def __init__(self):
        self.messages = []

    def publish(self, topic, msg):
        self.messages.append((topic, msg))


def test_outbox_persists_event_on_predict(tmp_path):
    outbox = SqliteOutbox(tmp_path / "ob.db")
    uc = PredictUseCase(ModelFactory(), OutboxEventPublisher(outbox))
    uc.execute(InferenceRequest(ModelId("churn-linear", "1"), FEATURES, "r1"))

    assert outbox.stats() == {"total": 1, "pending": 1, "published": 0}
    row = outbox.pending()[0]
    assert row["topic"] == "model.prediction.created"


def test_relay_drains_to_bus_and_marks_published(tmp_path):
    outbox = SqliteOutbox(tmp_path / "ob.db")
    uc = PredictUseCase(ModelFactory(), OutboxEventPublisher(outbox))
    for i in range(3):
        uc.execute(InferenceRequest(ModelId("churn-linear", "1"), FEATURES, f"r{i}"))

    bus = _CapturingBus()
    n = relay(outbox, bus)
    assert n == 3
    assert len(bus.messages) == 3
    assert all(t == "model.prediction.created" for t, _ in bus.messages)
    assert outbox.stats()["pending"] == 0


def test_relay_is_idempotent_after_crash(tmp_path):
    """Simula: relay publica 2, processo cai antes de marcar a 3ª — ao
    reiniciar, o relay só reenvia o que ficou pendente (não re-publica)."""
    outbox = SqliteOutbox(tmp_path / "ob.db")
    uc = PredictUseCase(ModelFactory(), OutboxEventPublisher(outbox))
    for i in range(3):
        uc.execute(InferenceRequest(ModelId("churn-linear", "1"), FEATURES, f"r{i}"))

    seen = []

    class _Bus:
        def publish(self, topic, msg):
            seen.append(msg["request_id"])

    relay(outbox, _Bus(), limit=2)          # "crash" após 2
    assert outbox.stats()["pending"] == 1
    relay(outbox, _Bus())                    # reinício
    assert outbox.stats()["pending"] == 0
    assert seen == ["r0", "r1", "r2"]        # cada evento exatamente uma vez
