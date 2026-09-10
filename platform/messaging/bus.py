"""Abstração de messaging do Argus.

`MessageBus` é o contrato; três implementações:

- `InMemoryBus`: síncrona, para dev/teste e para o notebook de demo. Roda
  sem broker.
- `KafkaBus`: event streaming durável (domain events, replay, integração
  com o data platform). Usa `kafka-python` — importado só quando instanciado.
- `RabbitBus`: work-queue (comandos/jobs assíncronos: geração de relatório,
  suíte de robustez adversarial). Usa `pika` — importado só quando instanciado.

Ver ADR-016 (event-driven architecture) e ADR-019 (Kafka vs RabbitMQ).
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable

Handler = Callable[[dict], None]


class MessageBus(ABC):
    @abstractmethod
    def publish(self, topic: str, message: dict) -> None: ...

    @abstractmethod
    def subscribe(self, topic: str, handler: Handler) -> None: ...


class InMemoryBus(MessageBus):
    """Entrega síncrona in-process. Cada `publish` invoca os handlers
    inscritos no tópico imediatamente."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self.log: list[tuple[str, dict]] = []

    def publish(self, topic: str, message: dict) -> None:
        # round-trip por JSON garante que a mensagem é serializável (mesma
        # restrição de um broker real)
        payload = json.loads(json.dumps(message))
        self.log.append((topic, payload))
        for handler in self._handlers[topic]:
            handler(payload)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._handlers[topic].append(handler)


class KafkaBus(MessageBus):
    def __init__(self, bootstrap_servers: str = "localhost:9092", group_id: str = "argus"):
        from kafka import KafkaConsumer, KafkaProducer  # dependência externa

        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        self._KafkaConsumer = KafkaConsumer
        self._bootstrap = bootstrap_servers
        self._group_id = group_id

    def publish(self, topic: str, message: dict) -> None:
        self._producer.send(topic, message)
        self._producer.flush()

    def subscribe(self, topic: str, handler: Handler) -> None:
        consumer = self._KafkaConsumer(
            topic,
            bootstrap_servers=self._bootstrap,
            group_id=self._group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        for record in consumer:  # loop bloqueante — rodado num worker dedicado
            handler(record.value)


class RabbitBus(MessageBus):
    def __init__(self, url: str = "amqp://guest:guest@localhost:5672/"):
        import pika  # dependência externa

        self._pika = pika
        self._params = pika.URLParameters(url)

    def publish(self, topic: str, message: dict) -> None:
        conn = self._pika.BlockingConnection(self._params)
        ch = conn.channel()
        ch.queue_declare(queue=topic, durable=True)
        ch.basic_publish(
            exchange="",
            routing_key=topic,
            body=json.dumps(message),
            properties=self._pika.BasicProperties(delivery_mode=2),
        )
        conn.close()

    def subscribe(self, topic: str, handler: Handler) -> None:
        conn = self._pika.BlockingConnection(self._params)
        ch = conn.channel()
        ch.queue_declare(queue=topic, durable=True)
        ch.basic_qos(prefetch_count=1)

        def _on_message(chx, method, _props, body):
            handler(json.loads(body))
            chx.basic_ack(delivery_tag=method.delivery_tag)

        ch.basic_consume(queue=topic, on_message_callback=_on_message)
        ch.start_consuming()  # loop bloqueante — rodado num worker dedicado
