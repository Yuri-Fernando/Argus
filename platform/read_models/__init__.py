"""Read models CQRS — projeções de leitura materializadas a partir de domain
events (ADR-022). Reconstruíveis por replay do log.

Importado por path (`sys.path` -> `platform/read_models`), não como
`platform.read_models`, para evitar colisão com o módulo `platform` da
stdlib:

    import sys; sys.path.insert(0, "platform/read_models")
    from churn_read_model import ChurnReadModel
"""
