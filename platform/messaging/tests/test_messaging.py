"""Testes da camada de messaging — bus in-memory, schema registry, e o
fluxo event-driven da demo."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from bus import InMemoryBus  # noqa: E402
from schema_registry import SchemaRegistry, ValidatingBus  # noqa: E402
from demo import build_demo_bus  # noqa: E402


def test_in_memory_bus_delivers_to_subscribers():
    bus = InMemoryBus()
    received = []
    bus.subscribe("t", received.append)
    bus.publish("t", {"a": 1})
    assert received == [{"a": 1}]
    assert bus.log == [("t", {"a": 1})]


def test_registry_lists_known_topics():
    topics = SchemaRegistry().topics()
    assert "customer.updated" in topics
    assert "model.prediction.created" in topics
    assert "model.drift.detected" in topics


def test_validating_bus_rejects_message_missing_required_field():
    bus = ValidatingBus(InMemoryBus())
    with pytest.raises((ValueError, Exception)):
        bus.publish("model.prediction.created", {"model_id": "x@1"})  # falta score/label/...


def test_validating_bus_accepts_valid_message():
    bus = ValidatingBus(InMemoryBus())
    bus.publish(
        "model.prediction.created",
        {
            "request_id": "r1", "model_id": "churn@3", "score": 0.5,
            "label": "low_risk", "high_risk": False, "occurred_at": "2026-09-10T00:00:00Z",
        },
    )


def test_demo_flow_fans_out_customer_update_to_prediction_and_dashboard():
    bus, seen = build_demo_bus()
    bus.publish(
        "customer.updated",
        {
            "event_id": "00000000-0000-0000-0000-000000000000",
            "occurred_at": "2026-09-10T00:00:00Z",
            "customer_id": "CUST-1",
            "source_system": "crm",
            "changed_fields": ["email"],
            "payload": {},
        },
    )
    assert seen["mdm"] == ["CUST-1"]
    assert seen["predictions"] == ["churn@3"]
    assert seen["dashboard"] == [("churn@3", True)]
