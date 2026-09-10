# 04 — Modelo de Dados

## Operacional (por serviço)

- `customer-service`: `customer(id, external_ids jsonb, name, email, phone,
  status, updated_at)` — fonte da verdade do cadastro; publica `customer.*`.
- `identity-service`: `identity_link(golden_id, customer_id, method, score,
  valid_from)` — resultado do Entity Resolution.

## Analítico (Lakehouse, medalhão)

`bronze` (raw por origem) → `silver` (limpo, tipado, deduplicado) →
`gold` (dimensional: `dim_customer`, `fact_order`, `fact_support_ticket`,
`customer_360`).

## Data Products (Data Mesh — RFC-001)

| Produto | Domínio | Porta de saída |
|---|---|---|
| Customer 360 | Customer | tabela gold + API |
| Churn Scores | Analytics | tópico + tabela |
| Revenue | Sales | tabela gold |
| Risk / Fiscal | Risk | tabela gold |

Cada um com owner, schema versionado, SLA, regras de qualidade e lineage.
