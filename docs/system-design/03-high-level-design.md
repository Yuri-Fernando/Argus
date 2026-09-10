# 03 — High-Level Design

```text
                         Angular Microfrontends (web-shell + MFEs)
                                        │
                              API Gateway / BFF
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
  customer-service (Java)        inference-service (Python)      rag-service (Python)
  identity-service (Java)        churn-service (Python)          agent-orchestrator
        │                               │                               │
        └───────────────  Kafka (event backbone)  ──────────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
       Operational DB           Data Platform               ML Platform
       (Postgres, 1/serviço)    S3 → Lakehouse → Gold        MLflow registry
                                        │                    ThemisAI gate
                                 Data Products (Data Mesh)          │
                                        │                    Canary deploy (EKS)
                                   BI (Power BI) / RAG
```

- Serviços **stateless**; estado em Postgres (um schema/DB por serviço —
  ADR-020) e em Kafka.
- **RabbitMQ** paralelo ao Kafka só para jobs de trabalho (relatórios,
  suíte de robustez) — ADR-019.
- Service mesh (Istio) provê mTLS, retry, timeout, circuit breaking e canary.
