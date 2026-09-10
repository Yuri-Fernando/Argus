"""Testes do read model CQRS — projeção incremental, KPIs, e a propriedade
central: reconstrução por replay produz o MESMO estado que o consumo
incremental."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "messaging"))

from churn_read_model import ChurnReadModel  # noqa: E402
from bus import InMemoryBus  # noqa: E402


EVENTS = [
    ("customer.updated", {"customer_id": "C1", "occurred_at": "2026-09-10T00:00:00Z"}),
    ("model.prediction.created", {"customer_id": "C1", "model_id": "churn@3", "score": 0.81,
                                  "high_risk": True, "occurred_at": "2026-09-10T00:01:00Z"}),
    ("model.prediction.created", {"customer_id": "C2", "model_id": "churn@3", "score": 0.20,
                                  "high_risk": False, "occurred_at": "2026-09-10T00:02:00Z"}),
    ("model.prediction.created", {"customer_id": "C1", "model_id": "churn@3", "score": 0.55,
                                  "high_risk": False, "occurred_at": "2026-09-10T00:03:00Z"}),
]


def test_incremental_projection_updates_customer_and_kpis():
    rm = ChurnReadModel()
    for topic, payload in EVENTS:
        (rm.on_customer_updated if topic == "customer.updated" else rm.on_prediction_created)(payload)

    c1 = rm.customer("C1")
    assert c1["last_score"] == 0.55
    assert c1["high_risk"] == 0
    assert c1["updates"] >= 2

    kpis = rm.kpis()
    assert kpis["scored_customers"] == 2
    assert kpis["high_risk_count"] == 0  # último score de C1 baixou o risco


def test_replay_equals_incremental():
    incremental = ChurnReadModel()
    for topic, payload in EVENTS:
        (incremental.on_customer_updated if topic == "customer.updated" else incremental.on_prediction_created)(payload)

    replayed = ChurnReadModel().rebuild_from_events(EVENTS)

    assert replayed.dump() == incremental.dump()


def test_subscribe_to_bus_wires_handlers():
    bus = InMemoryBus()
    rm = ChurnReadModel()
    rm.subscribe_to(bus)
    bus.publish("model.prediction.created", {"customer_id": "CX", "model_id": "churn@3",
                                             "score": 0.9, "high_risk": True,
                                             "occurred_at": "2026-09-10T00:00:00Z"})
    assert rm.customer("CX")["last_score"] == 0.9
    assert rm.kpis()["high_risk_count"] == 1
