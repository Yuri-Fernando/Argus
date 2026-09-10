"""Platform messaging — event backbone (Kafka) + work queue (RabbitMQ) +
abstração `InMemoryBus` para dev/teste.

Importado por path (`sys.path` -> `platform/messaging`), não como
`platform.messaging`, para evitar colisão com o módulo `platform` da stdlib:

    import sys; sys.path.insert(0, "platform/messaging")
    from bus import InMemoryBus
    from schema_registry import SchemaRegistry, ValidatingBus
"""
