"""Steps do BDD de churn scoring. Exercita o bus real (`platform/messaging`)
e um scorer determinístico simples — o mesmo contrato score->evento que o
churn-service usa em produção."""
from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "platform" / "messaging"))

from bus import InMemoryBus  # noqa: E402

CHURN_THRESHOLD = 0.70


def _score(customer: dict) -> float:
    z = (
        0.03 * customer["recency_days"]
        - 0.05 * customer["frequency"]
        + 0.35 * customer["support_incidents"]
        - 0.5
    )
    return 1.0 / (1.0 + 2.718281828 ** (-z))


@given('um cliente com uso em queda e múltiplos incidentes de suporte recentes')
def step_high_risk_customer(context):
    context.customer = {"recency_days": 95, "frequency": 1, "support_incidents": 4}
    context.bus = InMemoryBus()
    context.events = []
    context.bus.subscribe("customer.churn.risk_detected", context.events.append)


@given('um cliente engajado sem incidentes de suporte')
def step_healthy_customer(context):
    context.customer = {"recency_days": 5, "frequency": 20, "support_incidents": 0}
    context.bus = InMemoryBus()
    context.events = []
    context.bus.subscribe("customer.churn.risk_detected", context.events.append)


@when('o modelo de churn avalia o cliente')
def step_score(context):
    context.churn_probability = _score(context.customer)
    if context.churn_probability > CHURN_THRESHOLD:
        context.bus.publish(
            "customer.churn.risk_detected",
            {"score": round(context.churn_probability, 4), "customer": context.customer},
        )


@then('a probabilidade de churn deve exceder o limiar configurado')
def step_above(context):
    assert context.churn_probability > CHURN_THRESHOLD, context.churn_probability


@then('a probabilidade de churn deve ficar abaixo do limiar configurado')
def step_below(context):
    assert context.churn_probability < CHURN_THRESHOLD, context.churn_probability


@then('um evento "{topic}" deve ser publicado no bus')
def step_event_published(context, topic):
    assert any(t == topic for t, _ in context.bus.log), context.bus.log


@then('nenhum evento de retenção deve ser publicado')
def step_no_event(context):
    assert context.events == []
