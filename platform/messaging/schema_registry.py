"""Validação de mensagens contra os JSON Schemas de `schemas/`.

Um substituto local e sem dependência do Confluent Schema Registry: carrega
os `*.schema.json` e valida cada `publish` contra o schema do tópico. Usa
`jsonschema` se disponível; caso contrário, faz uma validação mínima de
campos obrigatórios (mantém o registry testável em ambiente mínimo).
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent / "schemas"


def _load_schemas() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        out[schema["title"]] = schema
    return out


class SchemaRegistry:
    def __init__(self) -> None:
        self._schemas = _load_schemas()

    def topics(self) -> list[str]:
        return sorted(self._schemas)

    def validate(self, topic: str, message: dict) -> None:
        schema = self._schemas.get(topic)
        if schema is None:
            raise KeyError(f"tópico sem schema registrado: {topic}")
        try:
            import jsonschema

            jsonschema.validate(message, schema)
        except ImportError:
            missing = [f for f in schema.get("required", []) if f not in message]
            if missing:
                raise ValueError(f"{topic}: campos obrigatórios ausentes: {missing}") from None


class ValidatingBus:
    """Decorator sobre um `MessageBus` que valida toda publicação contra o
    schema do tópico antes de entregar."""

    def __init__(self, bus, registry: SchemaRegistry | None = None):
        self._bus = bus
        self._registry = registry or SchemaRegistry()

    def publish(self, topic: str, message: dict) -> None:
        self._registry.validate(topic, message)
        self._bus.publish(topic, message)

    def subscribe(self, topic: str, handler) -> None:
        self._bus.subscribe(topic, handler)
