# Enterprise Customer Intelligence Platform

**Lakehouse · Data Warehouse · MDM · Machine Learning · IA Generativa · MCP · Governança**

> Uma plataforma de Dados & IA cloud-native, com pegada de produção, que transforma dados de clientes fragmentados, duplicados e pouco confiáveis — espalhados entre CRM, e-commerce, marketing, atendimento e pagamentos — em um **Golden Record** único e governado, expõe esse dado através de **métricas governadas** (dbt/MetricFlow, Unity Catalog Metric Views, Snowflake Semantic Views) e permite que tanto humanos (Power BI) quanto agentes de IA (Snowflake Cortex, Databricks Genie, ferramentas MCP customizadas, Claude) consultem, expliquem e ajam sobre esse dado — sempre com um humano no controle para decisões consequentes.

🇺🇸 Read in English: [README.md](README.md)

---

## 1. O problema de negócio

Uma empresa de e-commerce brasileira de médio porte tem dados de clientes espalhados por sistemas independentes — loja online, CRM, automação de marketing, atendimento, pagamentos — cada um com sua própria visão de quem é o cliente. Isso gera:

- Cadastros duplicados entre sistemas
- Métricas inconsistentes ("Receita" significa uma coisa em cada dashboard)
- Nenhuma forma confiável de detectar churn, clusters de fraude ou clientes VIP
- LLMs/agentes respondendo sem embasamento confiável
- Dashboards manuais e ad-hoc que nunca batem entre si

Esta plataforma resolve isso: uma arquitetura coerente, ponta a ponta, em que **cada tecnologia existe para resolver um problema real específico** — não para inflar currículo.

## 2. Arquitetura em um relance

Ver diagrama completo (Mermaid) e detalhamento por camada em **[ARCHITECTURE.md](ARCHITECTURE.md)** (inglês, documento técnico principal).

Resumo do fluxo:

```
Fontes (Olist + sintéticos + documentos)
   → Azure Data Factory / Event Hubs
   → Azure Data Lake Storage Gen2 (landing/raw/bronze/silver/gold)
   → Azure Databricks Lakehouse (Delta Lake, PySpark, Unity Catalog, MLflow)
   → Data Quality (GX Core) + MDM/Golden Record
   → Gold (modelo dimensional)
   → ML (churn, segmentação, matching) + Snowflake (DWH + Cortex)
   → Semantic Layer (dbt/MetricFlow · UC Metric Views · Snowflake Semantic Views)
   → Power BI (humanos) + Cortex/MCP (agentes de IA)
   → Camada de Agentes (Customer / Data Quality / Recommendation / Monitoring) com aprovação humana
```

## 3. Por que Databricks *e* Snowflake?

Não são redundantes — cada um tem uma responsabilidade clara:

| Camada | Responsabilidade |
|---|---|
| **Azure Data Lake (ADLS Gen2)** | Armazenamento bruto, barato e durável. Landing zone. |
| **Azure Databricks** | Lakehouse: ingestão, ETL/ELT, PySpark, Delta Lake, Bronze/Silver/Gold, MDM, feature engineering, treino de ML, MLflow. |
| **Snowflake** | Enterprise Data Warehouse: modelo dimensional governado, Semantic Views, Cortex (Analyst/Search/Agents/AI Functions) como **camada de serving de IA**. |
| **Power BI** | BI corporativo tradicional para humanos. |
| **MCP + Claude** | Interface agentic — o mesmo dado governado, consultado em linguagem natural por agentes de IA em vez de dashboards. |

Detalhamento completo do trade-off: [`docs/decisions/ADR-002-lakehouse-vs-warehouse.md`](docs/decisions/ADR-002-lakehouse-vs-warehouse.md).

## 4. Stack tecnológica

`Python` `PySpark` `Azure Data Factory` `Azure Databricks` `Delta Lake` `Unity Catalog` `MLflow` `dbt / MetricFlow` `Great Expectations (GX Core)` `Snowflake` `Snowflake Cortex` `Power BI` `LangGraph` `Azure OpenAI` `MCP` `FastAPI` `Terraform` `Docker` `GitHub Actions` `OpenTelemetry` `Prometheus` `Grafana` `NetworkX`.

## 5. Roadmap

Construído em 16 sprints ao longo de 8 fases (Fundação → Engenharia de Dados → MDM → Warehouse/BI → ML → GenAI/RAG → Agentic/MCP → Hardening Enterprise). Detalhamento completo: **[ROADMAP.md](ROADMAP.md)**.

## 6. Datasets

- **Olist Brazilian E-Commerce Public Dataset** (real, anonimizado, ~100 mil pedidos).
- **CRM / Marketing / Suporte / Web Events / Financeiro sintéticos** — gerados com seed reprodutível, contendo duplicidades e inconsistências propositais para o pipeline de MDM/DQ resolver de verdade.
- **Documentos corporativos sintéticos** (políticas de reembolso/entrega/fidelidade/privacidade) — alimentam RAG / Cortex Search.

Schemas completos: [DATA_MODEL.md](DATA_MODEL.md).

## 7. Índice de documentação

| Doc | Conteúdo |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura completa, diagramas, racional de cada ferramenta (EN) |
| [ROADMAP.md](ROADMAP.md) | Sprints, épicos, stories, critérios de aceite (EN) |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de versões desta especificação (EN) |
| [DATA_MODEL.md](DATA_MODEL.md) | Datasets, schemas, modelo dimensional (EN) |
| [IMPROVEMENTS_AND_RESEARCH.md](IMPROVEMENTS_AND_RESEARCH.md) | Lacunas do design original + pesquisa de ago/2026 (PT-BR) |
| [docs/decisions/](docs/decisions/) | ADRs — Architecture Decision Records (PT-BR) |

## 8. Nota do autor

Este projeto demonstra atuação ponta a ponta em Engenharia de Dados (ETL/ELT, PySpark, Delta, dbt), Governança de Dados (MDM, Golden Record, lineage, RBAC, LGPD), Data Science/MLOps (feature engineering, MLflow, SHAP) e Engenharia de IA (RAG, agentes, MCP, human-in-the-loop) — construído sobre Azure/Databricks como nuvem principal, com AWS documentado como alvo de portabilidade com base em experiência prática em ambas.

## Licença

MIT — ver [LICENSE](LICENSE). Todo dado é público/anonimizado (Olist) ou sintético; nenhum PII real é usado neste repositório.
