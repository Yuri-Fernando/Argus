# inference-service (Python / FastAPI)

Bounded context: **Model Inference**. Serve predições de modelos registrados
(churn, segmentação, next-best-action) atrás de uma API REST, desacoplado do
algoritmo concreto.

## Arquitetura (hexagonal — ADR-014)

```
interfaces/  →  application/  →  domain/
   rest.py       predict.py       model.py · events.py · strategies.py
      ↑              ↑
      └── infrastructure/ (adapta o mundo externo aos ports do domínio)
            strategies_impl.py · model_factory.py · adapters.py · in_memory_event_bus.py
```

## Design patterns

| Padrão | Onde | Para quê |
|---|---|---|
| **Strategy** | `domain/strategies.py` + `infrastructure/strategies_impl.py` | trocar o algoritmo de predição (GBDT / linear / LLM) sem tocar no use case |
| **Factory** | `infrastructure/model_factory.py` | criar/cachear a `PredictionStrategy` de cada `ModelId` a partir de um registro declarativo |
| **Adapter** | `infrastructure/adapters.py` | normalizar provedores de LLM heterogêneos (OpenAI, Bedrock, local) numa única `LLMProviderPort` |
| **Ports & Adapters** | `application/ports.py` | o use case depende de `EventPublisher` / `StrategyResolver`, nunca de infra concreta |

## Domain event

Toda predição emite `PredictionMade`, publicado no tópico Kafka
`model.prediction.created` (`platform/messaging/schemas/`). Em dev/teste o
adaptador é `InMemoryEventBus`.

## Rodar

```bash
# a partir da raiz do Argus (deps já no pyproject)
uvicorn inference_service.interfaces.rest:app --app-dir services/inference-service/src --reload
# POST http://localhost:8000/v1/predict
```

```bash
pytest services/inference-service/tests -q
```

## Status

✅ Implementado e testado localmente (13 testes). `xgboost` é opcional — sem
ele, `GbdtTabularStrategy` degrada para a estratégia linear (o serviço
continua testável em ambiente mínimo). Providers OpenAI/Bedrock são
importados só quando usados (não são dependência do serviço).
