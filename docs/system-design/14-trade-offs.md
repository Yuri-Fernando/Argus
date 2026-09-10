# 14 — Trade-offs (registro explícito)

| Decisão | Ganho | Custo aceito |
|---|---|---|
| Microsserviços por domínio | deploy/scale independentes, limites claros | complexidade operacional, consistência eventual |
| Java + Python poliglota | linguagem certa por workload | dois toolchains, dois runtimes de imagem |
| Kafka **e** RabbitMQ | streaming durável + work-queue com semântica própria | dois brokers para operar |
| DB por serviço | isolamento de falha e de schema | sem JOIN cross-serviço; dados por evento |
| Istio | mTLS/retry/canary sem código | overhead de sidecar, curva de aprendizado |
| Data Mesh | ownership por domínio, escala organizacional | governança federada precisa de disciplina |
| Local-first (ADR-010) | roda sem nuvem/custo, reprodutível | paridade nuvem↔local exige atenção |
| Gate de robustez adversarial no deploy | modelo frágil não vai a produção | pipeline de deploy mais lento |

Cada linha tem ADR correspondente em `docs/decisions/`.
