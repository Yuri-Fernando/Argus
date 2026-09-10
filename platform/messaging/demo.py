"""Demo executável do event-driven flow do Argus, sem broker.

`customer.updated` -> (MDM re-match) + (churn re-score -> `model.prediction.created`)
-> (dashboard consome). Toda publicação é validada contra o JSON Schema do tópico.

    python platform/messaging/demo.py
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bus import InMemoryBus  # noqa: E402
from schema_registry import SchemaRegistry, ValidatingBus  # noqa: E402


def build_demo_bus() -> tuple[ValidatingBus, dict]:
    seen: dict[str, list] = {"mdm": [], "predictions": [], "dashboard": []}
    bus = ValidatingBus(InMemoryBus(), SchemaRegistry())

    def on_customer_updated(msg: dict) -> None:
        seen["mdm"].append(msg["customer_id"])  # MDM re-match
        bus.publish(  # churn re-score
            "model.prediction.created",
            {
                "request_id": f"auto-{msg['customer_id']}",
                "model_id": "churn@3",
                "score": 0.81,
                "label": "high_risk",
                "high_risk": True,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def on_prediction(msg: dict) -> None:
        seen["predictions"].append(msg["model_id"])
        seen["dashboard"].append((msg["model_id"], msg["high_risk"]))

    bus.subscribe("customer.updated", on_customer_updated)
    bus.subscribe("model.prediction.created", on_prediction)
    return bus, seen


def main() -> None:
    bus, seen = build_demo_bus()
    bus.publish(
        "customer.updated",
        {
            "event_id": str(uuid.uuid4()),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "customer_id": "CUST-42",
            "source_system": "crm",
            "changed_fields": ["email", "phone"],
            "payload": {"email": "novo@exemplo.com"},
        },
    )
    print("MDM re-match:", seen["mdm"])
    print("Predições geradas:", seen["predictions"])
    print("Dashboard recebeu:", seen["dashboard"])


if __name__ == "__main__":
    main()
