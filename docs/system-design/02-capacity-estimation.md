# 02 — Estimativa de Capacidade (ordem de grandeza)

Premissas de um cenário-alvo (não é a carga do portfólio; é o dimensionamento
que a arquitetura suporta):

| Item | Valor assumido |
|---|---|
| Clientes ativos | 5.000.000 |
| Eventos `customer.updated` / dia | 2.000.000 (0,4 update/cliente/dia) |
| Predições / dia | 8.000.000 (re-score em update + batch diário) |
| Pico de predição | ~200 req/s (4x a média) |
| Tamanho médio de evento | ~1 KB |

## Derivações

- **Kafka `model.prediction.created`**: 8M msg/dia * 1 KB ≈ 8 GB/dia; com
  retenção de 7 dias ≈ 56 GB por partição-set. 12 partições → paralelismo de
  consumo de 12.
- **inference-service**: 200 req/s / (throughput ~80 req/s por pod a P95<300ms)
  → 3 pods + HPA até 8.
- **DWH gold**: ~5M linhas customer_360 * ~2 KB ≈ 10 GB; refresh incremental.
- **Vector store (RAG local)**: ~50k chunks * 768 dims * 4 B ≈ 150 MB.
