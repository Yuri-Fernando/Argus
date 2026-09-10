# 01 — Requisitos

## Funcionais (resumo)

- FR-1 Ingerir/atualizar cadastros de cliente de 5 sistemas de origem.
- FR-2 Produzir e manter um Golden Record por cliente (Entity Resolution).
- FR-3 Expor métricas governadas (semantic layer) para BI e para agentes.
- FR-4 Servir predições de churn/segmentação/NBA com explicação.
- FR-5 Responder perguntas em linguagem natural sobre o cliente (RAG + agentes),
  com aprovação humana para ações consequentes.
- FR-6 Bloquear promoção de modelo que não passe nos gates de qualidade,
  fairness, privacidade e **robustez adversarial**.

## Não-funcionais

| NFR | Alvo |
|---|---|
| Disponibilidade (APIs de leitura) | 99.9% |
| Latência `POST /predict` | P95 < 300 ms |
| Latência consulta de métrica governada | P95 < 800 ms |
| Escalabilidade | horizontal (stateless services + Kafka partitions) |
| Consistência | forte dentro do agregado; eventual entre bounded contexts |
| Durabilidade | eventos de domínio persistidos (retenção Kafka >= 7 dias) |
| Segurança | zero-trust (mTLS entre serviços), least-privilege IAM |
| Observabilidade | traces + logs estruturados + métricas RED/USE |
| RPO / RTO | RPO <= 15 min, RTO <= 1 h |

## Restrições (CON-*)

- CON-1 Projeto de portfólio: sem dados reais de pessoas; datasets públicos
  (Olist) + sintéticos.
- CON-2 Local-first: todo caminho crítico roda localmente sem serviço pago
  (ADR-010).
- CON-3 Stack poliglota deliberada (Java + Python), não monolíngue.
