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

## Portas

| Porta | Onde | Uso |
|---|---|---|
| **REST** (`/v1/predict`) | `interfaces/rest.py` (FastAPI) | integração externa / BFF |
| **gRPC** (`InferenceService.Predict`) | `interfaces/grpc_server.py` + `proto/inference.proto` | chamadas internas quentes (ADR-021). Um teste garante que REST e gRPC devolvem o **mesmo score**. |

Regenerar stubs: `make proto` (a partir da raiz do Argus).

## Domain event + Transactional Outbox

Toda predição emite `PredictionMade`. Dois publishers implementam o port
`EventPublisher`:

- `InMemoryEventBus` — dev/teste.
- `OutboxEventPublisher` (`infrastructure/outbox.py`) — grava o evento numa
  tabela SQLite `outbox` (durabilidade garantida antes de qualquer broker);
  `relay(outbox, bus)` drena o outbox para o broker real, **idempotente**
  (sobrevive a crash entre publish e ack — testado).

Em produção o evento vai para o tópico Kafka `model.prediction.created`
(`platform/messaging/schemas/`).

## Rodar

```bash
# REST
uvicorn inference_service.interfaces.rest:app --app-dir services/inference-service/src --reload
# gRPC
python -m inference_service.interfaces.grpc_server   # :50051

pytest services/inference-service/tests -q           # 20 testes (+3 integração skipados sem broker)
```

## Status

✅ Implementado e testado (20 testes: domínio, use case, patterns, REST, gRPC,
outbox). Testes `@pytest.mark.integration` (Kafka/RabbitMQ reais) rodam com
`RUN_INTEGRATION=1` após `make up-enterprise`. `xgboost` é opcional — sem
ele, `GbdtTabularStrategy` degrada para a estratégia linear. Providers
OpenAI/Bedrock são importados só quando usados.
