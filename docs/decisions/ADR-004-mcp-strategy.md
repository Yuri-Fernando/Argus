# ADR-004 — MCP como camada de integração agente↔dado, em vez de SQL direto via LLM

**Status:** Aceito
**Data:** 2026-08-10

## Contexto

A forma mais simples de dar a um LLM acesso aos dados é deixá-lo gerar SQL livremente e executá-lo contra o banco. Isso é frágil (SQL incorreto, sem controle de permissão granular, sem contrato de ferramenta) e não demonstra nada de diferenciado — é "chatbot que chama SQL", exatamente o que o design original queria evitar.

## Decisão

Toda interação agente↔dado passa por **MCP (Model Context Protocol)**: um servidor MCP customizado (`mcp/server/`) expõe ferramentas nomeadas e tipadas (`get_customer`, `get_customer_churn`, `query_snowflake`, etc.), complementado pelos servidores MCP gerenciados que as plataformas já oferecem — Databricks Managed MCP (GA, herda permissões do Unity Catalog automaticamente) e, de forma experimental, Power BI MCP (Public Preview).

## Alternativas consideradas

1. **LLM gera SQL livre e executa direto** — rejeitado: sem controle de escopo, sem RBAC herdado, superfície de ataque grande (ver [ADR-007](ADR-007-ai-guardrails.md)).
2. **Function calling customizado sem MCP** — rejeitado: reinventa um protocolo que já virou padrão de mercado (o próprio uso do MCP é o diferencial que o projeto quer demonstrar); também não interopera com Claude Desktop/Claude Code fora da caixa.
3. **Só usar os MCPs gerenciados (Databricks/Power BI), sem MCP customizado** — rejeitado: um MCP customizado é necessário para expor lógica de negócio própria (ex: `get_customer_graph`, `recommend_action`) que nenhum MCP gerenciado conhece.

## Consequências

- Positivas: cada ferramenta MCP tem contrato explícito (schema de entrada/saída), permissão escopada, e é testável isoladamente; alinhado com o padrão de mercado emergente.
- Negativas: manter três integrações MCP diferentes (custom, Databricks, Power BI) é mais código do que uma só — mitigado tratando Power BI MCP como estritamente experimental (não bloqueia nenhum sprint core).
