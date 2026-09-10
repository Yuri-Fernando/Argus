# RFC-001 — Data Mesh: dados como produto por domínio

**Status:** Proposto · **Autor:** plataforma · **Data:** 2026-09-10

## Resumo

Organizar a camada Gold do Lakehouse como **Data Products** de propriedade
dos domínios de negócio, em vez de um conjunto de tabelas técnicas sem dono.

## Motivação

Hoje o Gold é um modelo dimensional único mantido pela "plataforma". Isso
escala mal com o nº de domínios: fila única de mudanças, ninguém responsável
por qualidade/semântica de um dado específico, consumidores acoplados a
detalhes de pipeline.

## Proposta

Quatro princípios do Data Mesh, aplicados no escopo do Argus:

1. **Ownership por domínio.** Cada Data Product tem um domínio dono:
   Customer 360 → Customer; Churn Scores → Analytics; Revenue → Sales;
   Risk/Fiscal → Risk.
2. **Dado como produto.** Cada um expõe: schema versionado, porta de saída
   (tabela Delta + API/tópico), SLA, regras de qualidade (Great
   Expectations), lineage e política de acesso. Documentado em
   `data-platform/data-products/<nome>/`.
3. **Plataforma self-service.** Templates de pipeline, motor de DQ, catálogo
   e lineage são fornecidos pela plataforma; os domínios não reimplementam
   infra.
4. **Governança federada.** Um comitê define padrões globais (nomenclatura,
   PII, retenção); a aplicação é automatizada (policy-as-code) — ver
   `governance/`.

## Alternativas

- **Data Warehouse centralizado** (status quo) — mais simples, mas o gargalo
  de time único reaparece com escala organizacional.
- **Data Lake sem modelagem** — flexível, mas empurra toda a semântica para
  o consumidor (o problema que o Argus existe para resolver).

## Impacto

- `data-platform/data-products/` passa a ser a unidade de organização do
  Gold.
- Cada produto ganha um `contract.yaml` (schema + SLA + owner) validado no
  CI.
- Consumidores passam a depender do contrato do produto, não da tabela
  física.
