# ADR-001 — Azure como nuvem principal, AWS como alvo de portabilidade documentado

**Status:** Aceito
**Data:** 2026-08-10

## Contexto

O autor tem experiência prática em AWS (produção, Itaú e projetos próprios), mas as vagas-alvo deste portfólio (Itaú, Nubank, Mercado Livre, CI&T, BCG X, Thoughtworks, Accenture, Deloitte, Microsoft, Databricks) majoritariamente perguntam por Azure + Databricks + Power BI. Construir o projeto inteiro duas vezes (Azure e AWS) dobraria o esforço sem dobrar o valor de portfólio.

## Decisão

A implementação principal usa **Azure** (ADLS Gen2, Data Factory, Event Hubs, Key Vault, Entra ID, Azure OpenAI, Azure Monitor) como nuvem primária, integrada ao Azure Databricks. AWS **não é implementado em paralelo**; em vez disso, é documentado como alvo de portabilidade em [`cloud/architecture-comparison.md`](../../cloud/architecture-comparison.md), com uma tabela de equivalência de serviços, apoiada na experiência prática já existente do autor com AWS.

## Alternativas consideradas

1. **Implementar tudo em AWS** — rejeitado: não conversa tão diretamente com o mercado-alvo atual (mais vagas pedindo Azure/Databricks/Power BI no momento).
2. **Implementar ambos em paralelo (multicloud real)** — rejeitado para o MVP: dobra o custo de infraestrutura e o tempo de implementação sem agregar um conceito arquitetural novo (o padrão de camadas é o mesmo).
3. **Cloud-agnostic desde o dia 1 (Terraform com abstração dupla)** — rejeitado: abstrações genéricas demais tendem a esconder justamente o conhecimento específico de cada provedor que as entrevistas cobram.

## Consequências

- Positivas: foco de esforço, alinhamento direto com o mercado-alvo, e ainda assim demonstra visão multicloud através da documentação comparativa.
- Negativas: a tabela de portabilidade não é "testada" (não há um `terraform apply` real em AWS) — isso é declarado explicitamente no README, não escondido.
- Se uma vaga específica pedir AWS, o `cloud/aws/` pode ser promovido a implementação real reaproveitando os módulos Databricks/Snowflake (que são cloud-agnostic por natureza).
