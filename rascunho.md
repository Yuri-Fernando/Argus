cara agora baseado em tudo o que nao tenho desse chat e cortex e tudo mais que faltou e o que voce sabe desenha um projeto utilizando isso camada estrutura e tudo criando uma aplicaçao disso tudo, assim eu enriqueço muito meu porfolio

Eu iria além. Em vez de fazer um projeto "Snowflake Cortex demo", faria um projeto que engloba Data Engineering + MDM + AI + Analytics + Governança, porque ele cobre praticamente todas as vagas do Itaú, Nubank, Mercado Livre, CI&T, BCG X, Thoughtworks, Accenture, Deloitte, AWS, Microsoft, Snowflake e Databricks.

A ideia é construir um projeto que pareça um produto corporativo.

Projeto: Data Intelligence Platform (Cortex Ready)

Problema

Empresas possuem informações de clientes espalhadas em CRM, ERP, atendimento, marketing e financeiro.

Resultado:

cadastros duplicados
métricas inconsistentes
IA respondendo errado
dashboards diferentes
baixa governança

A plataforma resolve isso.

Arquitetura
                APIs
CRM
ERP
Excel
CSV
Mongo
Postgres
SAP
Salesforce
Hubspot

        │
        ▼

-------------------------
INGESTION
-------------------------

Python
Airflow
Databricks Jobs

↓

RAW

↓

Data Quality

↓

Silver

↓

Golden Record

↓

Semantic Layer

↓

Snowflake Cortex

↓

LLM

↓

API

↓

Dashboard
Stack

Python

PySpark

Databricks

Snowflake

Snowflake Cortex

OpenAI

LangGraph

FastAPI

Terraform

Docker

GitHub Actions

dbt

Great Expectations

Airflow

Prometheus

Grafana

Redis

Postgres

Vector DB

Camadas
1 Raw

Recebe dados exatamente como chegam.

crm_customer.csv

erp_customer.csv

salesforce.json

hubspot.json

Nada é alterado.

2 Quality Layer

Aqui entram

Great Expectations

Python

PySpark

Validações

CPF válido

Email válido

Telefone

Data nascimento

Duplicidade

NULL

Tipo

Schema


gera

quality_report.json
3 Standardization

Padroniza

Nome

Email

Telefone

Endereço

CPF

Estado

Cidade

4 Entity Resolution

Agora entra IA.

Golden Record.

Cliente

João Silva

Joao Silva

João A Silva


↓

vira

Customer_ID = 1003

utilizando

Similarity

Levenshtein

Embeddings

Graph

5 Relationship Graph

Neo4j

NetworkX

Nós

Pessoa

Empresa

Telefone

Email

Conta

Cartão

arestas

usa

pertence

mora

compartilha


Agora pode descobrir

fraude

duplicidade

clusters

famílias

empresas relacionadas

6 Feature Store

Agora gera atributos

num_emails

num_cpfs

centralidade

grau

idade

renda

cidade

inadimplente

7 ML

Random Forest

XGBoost

LightGBM

Gradient Boosting

predizem

Cadastro ruim

Duplicado

Fraude

Cliente VIP

Churn


gera

score_qualidade

score_risco

score_fraude
8 Semantic Layer

dbt

Métricas

Clientes ativos

Clientes válidos

Duplicados

NPS

Receita

Lifetime Value


Todas documentadas.

9 Cortex

Agora Cortex recebe

Semantic Models

Metrics

Views


usuário pergunta

Quantos clientes duplicados existem?

↓

LLM

↓

SQL

↓

Snowflake

↓

Resposta

10 AI Agent

LangGraph

Agente

Recebe pergunta

↓

consulta catálogo

↓

consulta Cortex

↓

consulta documentação

↓

gera SQL

↓

executa

↓

explica resultado

↓

gera gráfico
11 Recommendation Agent

Se detectar

duplicidade

↓

recomenda merge

↓

confiança 97%

↓

aguarda aprovação humana

Human in the Loop.

12 Monitoring Agent

Monitora

Pipeline

Qualidade

Custo

Performance

LLM

Prompt

Latência

Token

Observabilidade

Prometheus

Grafana

OpenTelemetry

Logs

Tracing

Alertas

Segurança

RBAC

Masking Policy

Dynamic Data Masking

Column Level Security

LGPD

Lineage

Audit Logs

Secrets Manager

Infra

Terraform

Docker

GitHub Actions

CI/CD

Organização
src/

 ingestion/

 transformation/

 quality/

 golden_record/

 graph/

 features/

 ml/

 cortex/

 agents/

 api/

 dashboard/

monitoring/

tests/

terraform/

docs/

dbt/

APIs
POST

/customer

GET

/customer/{id}

GET

/customer/score

GET

/customer/duplicates

GET

/metrics
Dashboard

Power BI

Grafana

Mostra

Pipeline

Qualidade

Duplicidade

Custos

Tokens

Agentes

Performance

Diferencial

No lugar de um chatbot, a plataforma entrega um ecossistema completo de engenharia de dados e IA:

ETL/ELT em Databricks com PySpark.
Qualidade de dados com Great Expectations.
MDM e Golden Record com resolução de entidades.
Grafo de relacionamentos para análise de vínculos.
Camada semântica com dbt para métricas reutilizáveis.
IA Generativa com Snowflake Cortex e agentes LangGraph.
APIs para integração corporativa.
Observabilidade, governança, LGPD, CI/CD e infraestrutura como código.
O que isso agrega ao seu portfólio

Esse projeto permite afirmar, de forma prática, experiência em:

Engenharia de Dados (Databricks, PySpark, SQL, ETL/ELT).
Governança de Dados (RBAC, catálogo, lineage, qualidade).
MDM (Golden Record, deduplicação, entity resolution).
IA Generativa (RAG, LangGraph, agentes, Cortex-ready).
Arquitetura de Dados Moderna (camadas Raw/Silver/Gold, dbt, APIs).
MLOps e Observabilidade (monitoramento, métricas, tracing, CI/CD).

É o tipo de projeto que dialoga diretamente com os requisitos que apareceram em praticamente todas as perguntas das entrevistas que você compartilhou e demonstra capacidade de projetar uma plataforma de dados corporativa de ponta a ponta.

Pensou por 18s

Sim. Agora dá para transformar isso em um projeto de portfólio realmente forte — não um "dashboard de vendas com chatbot", mas uma plataforma corporativa de Data + AI que demonstra Lakehouse, Data Warehouse, Data Lake, ETL/ELT, qualidade, MDM/Golden Record, ML, Power BI, MCP, agentes e governança.

E eu faria uma coisa importante: não colocar 25 tecnologias só para dizer que usou 25 tecnologias. Vamos desenhar uma arquitetura coerente, em que cada tecnologia resolve um problema real.

Pesquisei as capacidades atuais do ecossistema. O Databricks hoje suporta arquitetura Medallion/Delta Lake, Unity Catalog, AI/BI e Genie; inclusive existe um servidor MCP gerenciado para Genie. O Power BI também já possui MCP remoto para agentes consultarem modelos semânticos via linguagem natural — atualmente em Preview.

Projeto: Enterprise Customer Intelligence Lakehouse
Nome para o GitHub

Enterprise Customer Intelligence Platform — Lakehouse, MDM, ML & Agentic AI

Ou mais curto:

Customer Intelligence Lakehouse

1. O problema de negócio

Vamos simular uma empresa de e-commerce brasileira.

Ela possui dados espalhados:

E-commerce
CRM
Marketing
Atendimento
Pagamentos
Produtos
Logística
Clientes
Web Analytics

O problema:

            CRM
             │
Marketing ───┼── ERP
             │
      Atendimento
             │
       E-commerce

Cada sistema possui uma visão diferente do cliente.

Isso gera:

clientes duplicados;
dados inconsistentes;
métricas diferentes;
dificuldade para descobrir churn;
dificuldade para entender comportamento;
dashboards manuais;
decisões baseadas em dados fragmentados;
IA sem contexto confiável.

A plataforma vai transformar tudo isso em:

RAW DATA
   ↓
DATA LAKE
   ↓
LAKEHOUSE
   ↓
DATA QUALITY
   ↓
GOLDEN RECORD
   ↓
DATA WAREHOUSE
   ↓
SEMANTIC LAYER
   ↓
POWER BI
   ↓
AI / MCP / AGENTS
2. Arquitetura geral

Eu desenharia assim:

                         DATA SOURCES
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
       OLIST                CRM              MARKETING
          │                   │                   │
       CSV/JSON             API              CSV/API
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ↓
                    ┌──────────────────┐
                    │  INGESTION LAYER │
                    │ Python / APIs    │
                    │ Databricks Jobs  │
                    └────────┬─────────┘
                             ↓
                  ┌─────────────────────┐
                  │       BRONZE        │
                  │ Raw / Delta Lake    │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │       SILVER        │
                  │ Clean / Standardize │
                  │ Quality / Dedup     │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │    MDM / GOLDEN     │
                  │      RECORD         │
                  └──────────┬──────────┘
                             ↓
                  ┌─────────────────────┐
                  │        GOLD         │
                  │ Business Data       │
                  │ Facts + Dimensions │
                  └──────────┬──────────┘
                             ↓
              ┌──────────────┴──────────────┐
              ↓                             ↓
       DATABRICKS SQL                 SNOWFLAKE
       WAREHOUSE                      WAREHOUSE
              │                             │
              └──────────────┬──────────────┘
                             ↓
                    SEMANTIC LAYER
                             │
                 ┌───────────┴───────────┐
                 ↓                       ↓
             POWER BI              AI / AGENTS
                 │                       │
              Dashboard             MCP
                                         │
                         ┌───────────────┼──────────────┐
                         ↓               ↓              ↓
                      Databricks       Power BI       Cortex
                        Genie            MCP
                         │               │              │
                         └───────────────┼──────────────┘
                                         ↓
                                  AI ANALYTICS

O ponto interessante é que não é um amontoado de ferramentas. Cada camada tem função.

3. Data Lake

Vamos usar armazenamento de objetos:

S3 / ADLS

No seu ambiente de desenvolvimento, podemos até usar:

MinIO

para não depender de cloud durante o desenvolvimento.

Estrutura:

data-lake/

├── raw/
│   ├── olist/
│   ├── crm/
│   ├── marketing/
│   ├── support/
│   └── web_events/
│
├── bronze/
│
├── silver/
│
└── gold/

O Bronze mantém os dados próximos da origem. Essa é justamente a lógica da arquitetura Medallion recomendada pelo Databricks: Bronze como origem bruta, Silver refinada e Gold pronta para negócio.

4. Dataset principal: Olist

Eu usaria o Brazilian E-Commerce Public Dataset by Olist como nosso núcleo.

Ele é excelente para isso porque já possui aproximadamente 100 mil pedidos, além de informações de clientes, produtos, pagamentos, avaliações, vendedores, logística e geolocalização.

Dataset oficial do Olist no Kaggle

Ele permite construir:

customers
orders
order_items
products
sellers
payments
reviews
geolocation
product_category

Perfeito.

5. Mas não vamos usar somente Olist

Aqui está a sacada.

Vamos criar fontes adicionais sintéticas, simulando sistemas corporativos.

CRM
crm_customers.csv

Campos:

crm_customer_id
name
email
phone
cpf_hash
birth_date
city
state
created_at
updated_at
Marketing
marketing_campaigns.csv
marketing_interactions.csv
customer_id
campaign_id
channel
impressions
clicks
conversion
cost
timestamp
Atendimento
support_tickets.csv
ticket_id
customer_id
category
priority
created_at
resolved_at
sentiment
resolution_status
Web Analytics
web_events.json
session_id
customer_id
event_type
product_id
timestamp
device
source
Financeiro
customer_payments.csv

Assim teremos múltiplas fontes heterogêneas, exatamente como uma empresa real.

6. Golden Record

Aqui entra uma das partes mais importantes do projeto.

Teremos:

Olist customer
CRM customer
Marketing customer
Support customer

E precisamos descobrir:

Quem é a mesma pessoa?

Exemplo:

CRM

João da Silva
joao.silva@gmail.com
11999999999


Marketing

Joao Silva
joao.silva@gmail.com
11999999999


Olist

João Silva
joao.silva@gmail.com
11999999999

↓

MASTER_CUSTOMER_ID = 000001
7. Entity Resolution

Vamos implementar três níveis.

Regra determinística
email exato
CPF hash exato
telefone exato
Similaridade
Levenshtein
Jaro-Winkler
fuzzy matching
ML

Depois podemos criar:

match_score

com:

Random Forest
Gradient Boosting

Features:

email_similarity
name_similarity
phone_match
address_similarity
city_match

Resultado:

0.97 → MATCH
0.52 → REVIEW
0.12 → DIFFERENT

Isso transforma o projeto em MDM + Machine Learning.

8. Grafo

Agora vamos colocar:

Graph Analytics

Nós:

Customer
Email
Phone
Address
Product
Order
Seller

Relacionamentos:

CUSTOMER ──HAS_EMAIL──> EMAIL

CUSTOMER ──HAS_PHONE──> PHONE

CUSTOMER ──LIVES_AT──> ADDRESS

CUSTOMER ──PLACED──> ORDER

ORDER ──CONTAINS──> PRODUCT

ORDER ──SOLD_BY──> SELLER

Isso permite detectar:

clusters

clientes relacionados

contas compartilhadas

comportamentos suspeitos

duplicidades

comunidades

Podemos implementar primeiro com NetworkX e depois opcionalmente com Neo4j.

9. Data Quality Framework

Essa parte precisa ficar muito bonita no GitHub.

Criamos:

data_quality/

com regras:

not_null
unique
valid_email
valid_phone
valid_date
referential_integrity
range_check
duplicate_rate
schema_check

Exemplo:

customer_id → NOT NULL

email → valid format

order_id → UNIQUE

order.customer_id → EXISTS customer.customer_id

Podemos usar Great Expectations, que trabalha justamente com Expectations como afirmações verificáveis sobre os dados.

Dashboard:

DATA QUALITY SCORE

██████████████████░░ 92%

Completeness      97%
Validity          95%
Uniqueness        91%
Consistency       94%
Referential       98%
10. Lakehouse — Databricks

Aqui entra o coração do projeto.

Databricks

Unity Catalog

Delta Lake

PySpark

Databricks SQL

Catalog:

customer_intelligence

Schemas:

bronze
silver
gold
ml
monitoring

Por exemplo:

customer_intelligence.silver.customers

customer_intelligence.silver.orders

customer_intelligence.gold.dim_customer

customer_intelligence.gold.fact_orders

Unity Catalog entra para governança, organização e controle de acesso. O Databricks atualmente posiciona Unity Catalog como camada de governança para dados e ativos de IA.

11. Modelo dimensional

Gold:

                 dim_customer
                      │
                      │
dim_product ─── fact_orders ─── dim_date
                      │
                      │
                 dim_seller
fact_orders
order_id
customer_key
product_key
seller_key
date_key
order_value
freight_value
delivery_days
review_score
dim_customer
customer_key
master_customer_id
city
state
customer_segment
lifetime_value
churn_score
quality_score
12. dbt

Eu colocaria dbt na camada Gold.

Estrutura:

dbt/

├── models/
│   ├── staging/
│   ├── intermediate/
│   └── marts/
│
├── tests/
├── macros/
├── snapshots/
└── dbt_project.yml

E criaria métricas oficiais:

Revenue

Orders

AOV

Customers

Repeat Rate

Churn Rate

CLV

NPS

Delivery SLA

A regra:

Uma métrica, uma definição.

Isso é importantíssimo para IA.

13. Semantic Layer

Agora criamos uma camada que entende:

Revenue

não significa:

SUM(order_value)

em qualquer lugar.

Significa:

Revenue =
completed orders
excluding canceled orders

Isso evita a famosa:

"Power BI mostrou R$ 10M e o agente mostrou R$ 13M."

14. Power BI

Agora construímos um dashboard profissional.

Página 1 — Executive Overview

Cards:

Revenue
Orders
Customers
AOV
Churn
NPS
Data Quality

Gráficos:

Revenue over time

Orders by state

Revenue by category

Customer segmentation
15. Página 2 — Customer Intelligence
Total Customers

Active Customers

Repeat Customers

Churn Risk

CLV

Gráficos:

RFM segmentation

Customer lifetime value

Churn probability

Customer geography
16. Página 3 — Operations
Delivery SLA

Average delivery time

Late orders

Cancellation rate

Review score
17. Página 4 — Data Quality

Essa vai diferenciar muito seu dashboard.

Data Quality Score

Completeness

Validity

Uniqueness

Freshness

Duplicate Rate

Tabela:

Dataset       Quality     Errors
customers     98%         102
orders        96%         423
products      91%         871
payments      99%          31
18. Página 5 — ML
Churn Distribution

ROC-AUC

Precision

Recall

F1

Feature Importance

E:

Top 100 customers at risk
19. Power BI MCP

Aqui o projeto começa a ficar muito moderno.

O Power BI atualmente possui um MCP Server remoto que permite que agentes consultem modelos semânticos, recuperem esquema, gerem DAX e executem consultas; está em Preview.

Então o usuário pode perguntar:

"Qual estado teve maior crescimento de receita nos últimos 3 meses?"

Agente:

User
 ↓
MCP
 ↓
Power BI Semantic Model
 ↓
DAX
 ↓
Data
 ↓
LLM
 ↓
Resposta
20. Databricks Genie

Também colocamos o Genie.

O Databricks Genie permite perguntas em linguagem natural sobre dados governados pelo Unity Catalog, e a camada de semântica pode definir métricas e contexto reutilizáveis.

Então teremos:

Power BI
   +
Databricks Genie

E conseguimos comparar:

BI tradicional
       vs
AI/BI

Isso é excelente para portfólio.

21. MCP Gateway

Agora vem seu diferencial.

Criamos nosso próprio MCP Server:

mcp_server/

Ferramentas:

get_customer()

get_customer_quality()

get_customer_churn()

search_orders()

get_sales_metrics()

get_data_quality()

get_model_metrics()

get_customer_graph()

recommend_action()

O agente não precisa conhecer o banco.

Ele conhece ferramentas.

Agent
 ↓
MCP
 ├── SQL
 ├── Power BI
 ├── Databricks
 ├── Customer API
 ├── ML Model
 └── Data Quality

MCP é justamente um padrão para conectar agentes a ferramentas, recursos e contexto.

22. Agente principal

Chamaria:

Customer Intelligence Agent

Fluxo:

Pergunta
   ↓
Intent Detection
   ↓
Tool Selection
   ↓
MCP
   ↓
Data Retrieval
   ↓
Validation
   ↓
Reasoning
   ↓
Response

Exemplo:

"Por que o churn aumentou em São Paulo?"

Agente:

1. Consulta churn
2. Filtra SP
3. Compara período
4. Consulta comportamento
5. Consulta tickets
6. Consulta reviews
7. Analisa segmentos
8. Gera hipótese
9. Retorna evidências
23. Agente de qualidade

Outro agente:

Data Quality Agent

Pergunta:

"Por que a qualidade dos clientes caiu?"

Ele consulta:

DQ metrics
schema
pipeline logs
freshness
duplicates
null rates

E responde:

Quality decreased from 97.8% → 92.4%.

Primary cause:
customer_email completeness.

Source:
CRM ingestion.

Recommendation:
review CRM extraction job.
24. Agente de recomendação

E aí:

Recommendation Agent

Exemplo:

Customer 92831

Churn Score: 0.87

CLV: R$ 4,821

Last purchase: 63 days

Support tickets: 4

Review sentiment: negative

Agente:

Cliente de alto valor com alto risco de churn.

Recomendação:

Priority = HIGH

Action:
Retention campaign

Suggested incentive:
10% discount

Human approval:
REQUIRED

Aí você coloca Human-in-the-loop.

25. Machine Learning

Teremos pelo menos três modelos.

Churn
Logistic Regression
Random Forest
Gradient Boosting

Comparação:

Modelo	ROC-AUC	F1	Precision
Logistic Regression	...	...	...
Random Forest	...	...	...
Gradient Boosting	...	...	...

Depois:

MLflow

para tracking.

26. Explainability

Use:

SHAP

Para explicar:

Por que esse cliente recebeu score 0.87?

Exemplo:

+0.24  baixa frequência de compra
+0.18  reclamações recentes
+0.16  aumento do tempo desde última compra
+0.12  queda de engajamento

Isso é muito melhor que simplesmente:

"O modelo disse que ele vai sair."

27. Snowflake

Agora podemos colocar Snowflake como Enterprise Warehouse / AI Serving Layer.

Não precisa duplicar tudo.

Fluxo:

Databricks Gold
      │
      ↓
Snowflake
      │
      ├── Analytics
      ├── Semantic
      └── Cortex

E podemos criar um módulo:

snowflake/

├── schemas/
├── tables/
├── views/
├── semantic/
└── cortex/

Cortex entra principalmente no módulo de AI analytics/documentos. As funções de documentos do Cortex, por exemplo, podem transformar documentos não estruturados em conteúdo pesquisável/analisável e alimentar RAG e analytics.

28. Document Intelligence

Vamos colocar PDFs fictícios:

docs/

├── customer_policy.pdf
├── refund_policy.pdf
├── delivery_policy.pdf
└── loyalty_program.pdf

Cortex/LLM:

PDF
 ↓
Parse
 ↓
Extract
 ↓
Chunk
 ↓
Embedding
 ↓
Vector Search
 ↓
RAG

Agora o agente consegue responder:

"Qual política de reembolso se aplica ao cliente?"

e combinar:

Customer Data
+
Policy Documents

Isso vira Enterprise RAG.

29. Observabilidade

Não deixaria isso de fora.

OpenTelemetry
Prometheus
Grafana

Monitorar:

Pipeline latency

Rows processed

Failures

Data freshness

DQ score

Model latency

LLM latency

Token usage

MCP calls

API latency

Dashboard técnico:

PIPELINE HEALTH

Bronze       ✓
Silver       ✓
Gold         ✓
ML           ✓
Power BI     ✓
MCP          ✓
Agents       ✓
30. Infraestrutura

Tudo versionado:

Terraform
Docker
GitHub Actions

Pipeline:

git push
   ↓
lint
   ↓
unit tests
   ↓
data tests
   ↓
dbt tests
   ↓
build Docker
   ↓
security scan
   ↓
deploy
31. Segurança

Colocaria uma seção inteira no projeto:

Security & Governance

Com:

RBAC

Unity Catalog

Secrets

Data Masking

PII classification

Audit logs

Row-level security

Column-level security

Encryption

Data lineage

E muito importante:

não usar CPF, e-mail ou telefone real.

Os dados do Olist são anonimizados, mas os datasets sintéticos também devem ser claramente marcados como sintéticos.

32. Estrutura final do GitHub

Eu faria assim:

customer-intelligence-lakehouse/

├── README.md
│
├── architecture/
│   ├── architecture.png
│   ├── architecture.drawio
│   ├── data-flow.drawio
│   └── decisions/
│       ├── ADR-001-lakehouse.md
│       ├── ADR-002-medallion.md
│       ├── ADR-003-mdm.md
│       ├── ADR-004-mcp.md
│       └── ADR-005-semantic-layer.md
│
├── data/
│   ├── raw/
│   ├── synthetic/
│   │   ├── crm/
│   │   ├── marketing/
│   │   ├── support/
│   │   └── web/
│   └── samples/
│
├── ingestion/
│   ├── olist/
│   ├── crm/
│   ├── marketing/
│   └── support/
│
├── databricks/
│   ├── notebooks/
│   ├── jobs/
│   ├── workflows/
│   └── unity_catalog/
│
├── pyspark/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── dbt/
│   ├── models/
│   ├── tests/
│   ├── macros/
│   ├── snapshots/
│   └── seeds/
│
├── data_quality/
│   ├── expectations/
│   ├── checks/
│   └── reports/
│
├── mdm/
│   ├── entity_resolution/
│   ├── golden_record/
│   └── matching/
│
├── graph/
│   ├── network/
│   ├── algorithms/
│   └── queries/
│
├── ml/
│   ├── churn/
│   ├── segmentation/
│   ├── feature_engineering/
│   ├── training/
│   ├── evaluation/
│   └── explainability/
│
├── mlflow/
│
├── snowflake/
│   ├── ddl/
│   ├── views/
│   ├── semantic/
│   └── cortex/
│
├── powerbi/
│   ├── semantic_model/
│   ├── dax/
│   └── dashboard/
│
├── mcp/
│   ├── server/
│   ├── tools/
│   ├── resources/
│   └── prompts/
│
├── agents/
│   ├── customer_agent/
│   ├── quality_agent/
│   ├── recommendation_agent/
│   └── monitoring_agent/
│
├── api/
│   ├── routes/
│   ├── schemas/
│   └── services/
│
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   └── opentelemetry/
│
├── terraform/
│   ├── aws/
│   ├── databricks/
│   └── modules/
│
├── docker/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── data/
│
├── docs/
│   ├── data_dictionary.md
│   ├── runbooks/
│   ├── governance.md
│   ├── security.md
│   └── semantic_layer.md
│
├── .github/
│   └── workflows/
│
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── README.md

Isso já parece repositório de empresa, não projeto de faculdade.

33. Dataset: estratégia

Eu faria três fontes.

Fonte 1 — real/anônima

Olist.

Olist Brazilian E-Commerce Dataset

Fonte 2 — sintética

CRM.

Gerada por nós:

100k customers

com duplicidades deliberadas:

5% duplicates

2% missing email

1% invalid phone

1% inconsistent address

Isso cria um problema real para o pipeline resolver.

Fonte 3 — sintética

Marketing/support/web.

1M web events
200k marketing interactions
50k support tickets

Assim conseguimos testar processamento distribuído.

34. E aqui está a parte genial

Nós introduzimos problemas propositalmente.

O pipeline precisa detectar:

NULL
duplicate
invalid
schema drift
late data
orphan records

Então o dashboard mostra:

              DATA QUALITY

Customers       98.2%
Orders          99.1%
Marketing       94.7%
Support         96.3%

Overall         97.1%

Isso dá uma narrativa muito forte:

"A plataforma não apenas processa dados; ela mede a confiabilidade dos próprios dados."

35. Dashboard principal

Eu faria visualmente assim:

┌─────────────────────────────────────────────────────┐
│ CUSTOMER INTELLIGENCE PLATFORM                      │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ Revenue  │ Orders   │ Customers│ Churn    │ DQ      │
│ R$ 12.4M │ 98.4K    │ 84.2K    │ 8.7%     │ 97.2%   │
├──────────────────────┬──────────────────────────────┤
│ Revenue Trend        │ Customer Segments            │
│                      │                              │
│       ╱╲             │  VIP        ███████         │
│  ╱╲  ╱  ╲            │  Loyal      ███████████     │
│ ╱  ╲╱    ╲           │  At Risk    ████            │
├──────────────────────┼──────────────────────────────┤
│ Churn Risk           │ Data Quality                 │
│                      │                              │
│ High   ███████       │ Completeness   97%           │
│ Medium █████████     │ Validity       95%           │
│ Low    ███████████   │ Uniqueness     98%           │
└──────────────────────┴──────────────────────────────┘
36. E colocaria um segundo dashboard
AI & Data Platform Observability
Pipeline Success Rate

99.3%

Average Pipeline Duration

2m 31s

Data Quality

97.2%

ML Inference Latency

84ms

Agent Latency

1.8s

MCP Calls

12,492

LLM Cost

$...

Isso mostra que você entende Data Engineering + MLOps + LLMOps + FinOps.

37. Roadmap de desenvolvimento

Não tente fazer tudo de uma vez.

Fase 1 — Foundation
Olist
↓
S3/MinIO
↓
Databricks
↓
Bronze
↓
Silver
↓
Gold
Fase 2 — Data Engineering
PySpark
dbt
Data Quality
Unity Catalog
Fase 3 — MDM
Entity Resolution
Golden Record
Graph
Fase 4 — Analytics
Power BI
Semantic Model
DAX
Dashboard
Fase 5 — ML
Churn
Segmentation
MLflow
SHAP
Fase 6 — AI
RAG
LLM
LangGraph
Agents
Fase 7 — MCP
Custom MCP
Databricks MCP
Power BI MCP
Fase 8 — Enterprise
Security
Governance
Observability
Terraform
CI/CD
38. O diferencial absurdo para entrevista

Você vai poder abrir o GitHub e explicar:

"Eu construí uma plataforma de Customer Intelligence baseada em uma arquitetura Lakehouse. Os dados entram por múltiplas fontes, passam por Bronze, Silver e Gold no Databricks, são submetidos a data quality e entity resolution para construção do Golden Record, e depois são disponibilizados em uma camada semântica para Power BI e aplicações de IA."

Depois:

"O Power BI disponibiliza os indicadores corporativos, enquanto agentes podem consultar os mesmos dados por MCP. Também tenho um agente de qualidade que monitora os pipelines e um agente de recomendação que utiliza os scores de ML."

Isso responde praticamente todas aquelas perguntas que você recebeu nas candidaturas.

E o mais importante: você vai ter código para provar.

39. A arquitetura que eu escolheria para o MVP

Para não virar um Frankenstein de cloud:

                 ┌──────────────┐
                 │ OLIST        │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ S3 / MinIO   │
                 └──────┬───────┘
                        ↓
              ┌───────────────────┐
              │    DATABRICKS     │
              │                   │
              │ Bronze             │
              │ Silver             │
              │ Gold               │
              │ Unity Catalog      │
              │ MLflow             │
              │ SQL Warehouse      │
              └─────────┬─────────┘
                        ↓
                 ┌──────────────┐
                 │    DBT       │
                 └──────┬───────┘
                        ↓
              ┌───────────────────┐
              │ SEMANTIC LAYER    │
              └─────────┬─────────┘
                        │
             ┌──────────┴──────────┐
             ↓                     ↓
        ┌──────────┐         ┌──────────┐
        │ POWER BI │         │   AGENTS │
        └────┬─────┘         └────┬─────┘
             │                    │
             │                    ↓
             │                  MCP
             │                    │
             │             ┌──────┴──────┐
             │             ↓             ↓
             │        Databricks      Power BI
             │           MCP            MCP
             │
             ↓
         DASHBOARD

Snowflake/Cortex entra como extensão Enterprise, não como dependência obrigatória do MVP.

Isso é importante porque você consegue desenvolver quase tudo sem ficar queimando dinheiro em cinco clouds.

E sim: esse projeto é um baita projeto.

Na verdade, eu diria que ele pode virar o projeto principal do seu portfólio de Data/AI Engineering.

Porque ele não demonstra só "sei Python".

Ele demonstra:

Data Lake → Lakehouse → Warehouse → ETL/ELT → PySpark → SQL → dbt → Data Quality → MDM → Golden Record → Graph → ML → MLflow → Power BI → Semantic Layer → GenAI → RAG → Agents → MCP → APIs → Observability → Governance → Terraform → CI/CD.

E isso está muito alinhado com o que você acabou de enfrentar nas entrevistas.

Um detalhe especialmente atual: o Power BI MCP remoto está em Preview e permite agentes consultarem modelos semânticos, enquanto o Databricks já oferece MCP gerenciado e um Genie MCP para conectar agentes a dados governados pelo Unity Catalog. Isso nos permite fazer a parte MCP do projeto de maneira muito mais realista do que simplesmente criar um "chatbot que chama SQL".

Eu faria esse projeto em etapas e documentaria cada decisão arquitetural. O resultado final pode ser praticamente um case study de arquitetura de dados empresarial, com GitHub + diagrama + dashboard + demo do agente + métricas de qualidade + pipeline CI/CD.

Se quiser, no próximo passo eu montaria a especificação técnica v1.0 inteira, já no nível de implementação: datasets exatos, schema de cada tabela, arquitetura Databricks/Delta, banco Gold, modelo dimensional, regras de Data Quality, features do ML, métricas do Power BI, ferramentas MCP e estrutura dos agentes, para começarmos a codar sem ficar decidindo arquitetura no meio do caminho.

Obrigado pelo retorno e pela pergunta.
Minha experiência como Cientista de Dados é construída principalmente na interseção entre Data Science, Data Engineering e IA aplicada, com atuação em projetos acadêmicos e, mais recentemente, em ambientes corporativos.
Em contexto corporativo, tive atuação em projetos envolvendo dados, modelagem, automação e soluções de IA, incluindo experiência no Itaú, trabalhando em um ambiente corporativo de grande porte e com demandas relacionadas a engenharia e tratamento de dados, automação e soluções de IA. Também venho desenvolvendo projetos próprios e profissionais envolvendo Python, SQL, PySpark, Machine Learning, GenAI, MLflow, Databricks e pipelines de dados.
Um dos projetos mais estruturados que desenvolvi foi uma arquitetura de monitoramento de modelos, com pipeline dividido em ingestão, feature engineering, WOE binning, monitoramento estatístico e governança. Nesse projeto trabalhei com métricas como PSI, IV e drift, processamento de dados com Python/Pandas e geração automatizada de artefatos para análise e auditoria.
Também tenho experiência prática com Databricks, principalmente na construção e arquitetura de pipelines utilizando PySpark, integração de dados, processamento distribuído e estruturação de ambientes de Data Lake/Lakehouse/Warehouse. Minha experiência em Azure está associada principalmente à arquitetura e utilização dos serviços de dados e ML, enquanto AWS também faz parte da minha experiência prática em cloud.
Em relação a grandes volumes de dados, minha experiência está principalmente em processamento distribuído, pipelines de dados e arquiteturas Lakehouse, utilizando Spark/PySpark e Databricks, além de bancos relacionais e soluções de armazenamento em cloud.
Quanto ao tempo formal especificamente com o título de Senior Data Scientist, prefiro ser transparente: minha trajetória não foi construída exclusivamente sob esse cargo por vários anos. Minha experiência combina engenharia de dados, ciência de dados, Machine Learning e IA, com forte atuação prática em projetos de ponta a ponta — desde ingestão e preparação dos dados até modelagem, monitoramento e arquitetura para deployment.
Acredito que esse perfil híbrido seja justamente um diferencial, porque consigo atuar não apenas na construção do modelo, mas também na infraestrutura e no pipeline necessários para colocá-lo em produção.

tem como colocar azure no projeto eu tenho experiencia em aws mas enriquece adiciona isso e o power bi eu vou usar pelo claude msm kkk e vou usar databricks por mcp tbm adiciona o azure e faz ele inteiro mesmo por favor, tendo todos os conceitos de datalake. faz o projeto abrangendo tudo, tudo detalhado resolvendo, esse vai ser meu top tier projeto de dados ne

Sim. E agora eu faria isso como seu projeto flagship de Data Engineering / Data Science / AI, mas com uma regra: não vamos montar um Frankenstein de ferramentas. Vamos construir uma arquitetura corporativa em que cada tecnologia tenha uma função clara.

A sua experiência em AWS entra como diferencial de cloud/multicloud, mas vamos fazer a implementação principal em Azure + Databricks, porque isso conversa diretamente com as vagas que estão te perguntando sobre Azure, Databricks, Power BI e engenharia de dados. E vamos deixar Snowflake/Cortex como uma extensão enterprise, não como dependência do núcleo.

Pesquisei a documentação atual para alinhar a arquitetura com o que as plataformas realmente oferecem hoje. O Azure Databricks tem Unity Catalog como camada de governança de dados e IA, com controle de acesso, lineage e auditoria; a arquitetura de referência da Microsoft usa justamente ADLS Gen2 + Azure Data Factory + Azure Databricks + Unity Catalog + Power BI + Purview.

Além disso, o Databricks atualmente possui MCPs gerenciados que conectam agentes a dados governados pelo Unity Catalog, e o Power BI possui um MCP remoto para agentes consultarem modelos semânticos — este último ainda está em Preview.

🚀 Projeto flagship
Enterprise Customer Intelligence Data Platform
Lakehouse + Data Warehouse + MDM + ML + GenAI + MCP + BI + Governance

A narrativa do projeto será:

Construir uma plataforma corporativa de inteligência de clientes capaz de ingerir dados de múltiplas fontes, transformar dados brutos em informação confiável, construir Golden Records, gerar modelos preditivos, disponibilizar métricas governadas no Power BI e permitir que agentes de IA consultem e expliquem os dados por meio de MCP.

Isso é muito mais forte que simplesmente:

"Fiz um pipeline em PySpark."

Você vai demonstrar arquitetura de dados de ponta a ponta.

1. A arquitetura definitiva

Eu faria:

                         ┌─────────────────────────┐
                         │       DATA SOURCES       │
                         │                         │
                         │ Olist                   │
                         │ CRM                     │
                         │ Marketing                │
                         │ Support                  │
                         │ Web Events               │
                         │ Payments                 │
                         │ Documents                │
                         └────────────┬────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     │                                 │
                BATCH DATA                       STREAMING
                     │                                 │
               Azure Data Factory                Event Hubs
                     │                                 │
                     └────────────────┬────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────┐
                    │       AZURE DATA LAKE       │
                    │          ADLS Gen2          │
                    │                            │
                    │ RAW / LANDING               │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                ╔════════════════════════════════════╗
                ║          AZURE DATABRICKS          ║
                ║                                    ║
                ║           UNITY CATALOG            ║
                ║                                    ║
                ║ Bronze → Silver → Gold             ║
                ║                                    ║
                ║ PySpark / Spark SQL / Delta Lake   ║
                ╚════════════════╤═══════════════════╝
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                 │
               ▼                 ▼                 ▼
          DATA QUALITY          MDM               ML
          Great Expectations    Golden Record      MLflow
          DQ Monitoring         Entity Resolution  Feature Store
               │                 │                 │
               └─────────────────┼─────────────────┘
                                 ▼
                         BUSINESS GOLD
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
          DATABRICKS SQL     POWER BI        SNOWFLAKE*
          Warehouse          Semantic        Enterprise
                             Model           Extension
                │                │                │
                └────────────────┼────────────────┘
                                 ▼
                          SEMANTIC LAYER
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
              HUMAN USERS                 AI AGENTS
                   │                           │
               Power BI                     MCP
                                               │
                                  ┌────────────┼────────────┐
                                  ▼            ▼            ▼
                             Databricks     Power BI     Custom MCP
                                MCP            MCP
                                  │            │            │
                                  └────────────┼────────────┘
                                               ▼
                                         AGENTIC AI
                                               │
                              ┌────────────────┼──────────────┐
                              ▼                ▼              ▼
                         Analytics       Data Quality    Recommendations
                         Agent             Agent            Agent

* Snowflake entra como módulo complementar, não como duplicação obrigatória do Lakehouse.

2. O conceito central

Quero que você consiga explicar assim numa entrevista:

"Minha plataforma utiliza ADLS Gen2 como Data Lake, Azure Databricks e Delta Lake como Lakehouse, Databricks SQL como camada analítica/warehouse, Power BI como camada de BI e um conjunto de agentes de IA conectados aos dados governados por MCP."

Isso sozinho já responde uma quantidade absurda de perguntas de entrevista.

A arquitetura Medallion do Delta Lake organiza os dados em Bronze, Silver e Gold, respectivamente raw, refinado e pronto para negócio.

3. O Data Lake
Azure Data Lake Storage Gen2

Estrutura:

adls/

├── landing/
│
├── raw/
│
├── bronze/
│
├── silver/
├── gold/
│
├── quarantine/
│
├── checkpoints/
│
└── archive/
Landing

Dados recém-chegados.

Raw

Cópia fiel da origem.

Quarantine

Dados que falharam nas validações.

Archive

Histórico.

Checkpoints

Estado de processamento incremental/streaming.

4. Fontes de dados

Vamos utilizar um dataset real + fontes sintéticas.

Fonte principal

Olist Brazilian E-Commerce Public Dataset

Ele fornece:

customers
orders
order_items
products
sellers
payments
reviews
geolocation

É uma ótima base porque possui cerca de 100 mil pedidos e permite construir uma arquitetura de e-commerce realista.

Olist Brazilian E-Commerce Dataset

5. Mas não vamos parar no Olist

Vamos criar dados sintéticos para simular sistemas corporativos.

CRM
crm_customers
customer_id
name
email
phone
document_hash
birth_date
address
city
state
created_at
updated_at
Marketing
campaigns

campaign_interactions

Campos:

campaign_id
customer_id
channel
impressions
clicks
conversion
cost
timestamp
6. Atendimento
support_tickets
ticket_id
customer_id
category
priority
sentiment
created_at
resolved_at
resolution_status

Isso permitirá relacionar:

Customer → Support → Churn

7. Web Analytics

Criamos:

web_events

com:

session_id
customer_id
event_type
product_id
timestamp
device
browser
source
campaign

Podemos gerar milhões de eventos.

Aí você realmente consegue demonstrar:

PySpark + processamento distribuído.

8. Documentos

Vamos adicionar documentos corporativos:

documents/

refund_policy.pdf
delivery_policy.pdf
loyalty_policy.pdf
privacy_policy.pdf
customer_service_policy.pdf

Isso alimentará o módulo:

RAG + AI Document Intelligence.

9. Data Lake → Lakehouse

O ADLS guarda os dados.

O Databricks transforma isso em Lakehouse.

ADLS
   ↓
Delta Lake
   ↓
Databricks
10. Bronze

A Bronze mantém os dados próximos da origem.

Exemplo:

bronze.olist_customers

bronze.olist_orders

bronze.crm_customers

bronze.web_events

bronze.support_tickets

Aqui fazemos mínima transformação.

Isso é importante para:

auditoria;
replay;
troubleshooting;
reconstrução do pipeline.
11. Silver

Agora começa engenharia de dados pesada.

silver.customer

silver.order

silver.product

silver.payment

silver.support

silver.web_event

Aqui:

normalização;
deduplicação;
casting;
padronização;
tratamento de NULL;
schema enforcement;
joins;
enriquecimento;
validações.
12. Data Quality

Criaremos um framework próprio:

data_quality/

├── expectations/
├── rules/
├── validators/
├── reports/
└── quarantine/

Regras:

NOT NULL

UNIQUE

VALID EMAIL

VALID PHONE

VALID DATE

REFERENTIAL INTEGRITY

RANGE CHECK

SCHEMA CHECK

DUPLICATE RATE

FRESHNESS

VOLUME ANOMALY

E teremos:

DQ SCORE = 97.8%
13. Data Quality Monitoring

Além das regras estáticas, vamos monitorar:

volume
freshness
null_rate
duplicate_rate
schema_drift
distribution_drift

O próprio Databricks atualmente oferece Data Quality Monitoring com profiling e detecção de anomalias de frescor/completude.

Nós vamos implementar uma camada própria também para demonstrar conhecimento de engenharia.

14. Silver → MDM

Agora vem uma das partes mais interessantes.

Golden Record

Temos:

Olist Customer

CRM Customer

Marketing Customer

Support Customer

e queremos:

MASTER_CUSTOMER_ID
15. Entity Resolution
Nível 1

Determinístico:

email == email
phone == phone
document_hash == document_hash
Nível 2

Fuzzy:

Jaro-Winkler
Levenshtein
Nível 3

ML:

Random Forest
Gradient Boosting

Features:

name_similarity

email_similarity

phone_match

address_similarity

city_match

state_match

Output:

match_probability
16. Golden Record

Tabela:

gold.dim_customer
master_customer_id

canonical_name

canonical_email

canonical_phone

city

state

customer_segment

customer_quality_score

churn_score

lifetime_value

created_at

updated_at

Agora temos:

Single Customer View.

17. Grafo

Agora vamos enriquecer.

Customer
   │
   ├── Email
   ├── Phone
   ├── Address
   ├── Order
   ├── Product
   └── Seller

Implementação inicial:

NetworkX

Depois podemos criar uma extensão:

Neo4j

18. Métricas do grafo
degree

betweenness

centrality

connected_components

community

similarity

Isso permite:

detectar clusters;
encontrar relacionamentos;
detectar possíveis duplicidades;
identificar estruturas suspeitas.
19. Gold

Agora construímos o modelo dimensional.

                 dim_customer
                      │
                      │
dim_product ─── fact_orders ─── dim_date
                      │
                      │
                 dim_seller
20. Fact tables
fact_orders

fact_order_items

fact_payments

fact_customer_interactions
21. Dimensions
dim_customer

dim_product

dim_seller

dim_date

dim_geography

dim_campaign
22. Data Warehouse

Aqui podemos utilizar:

Principal

Databricks SQL Warehouse

Isso mantém a arquitetura simples.

Databricks referencia oficialmente Databricks SQL + Power BI para workloads de BI, com Unity Catalog fornecendo descoberta e controle de acesso.

23. Snowflake como extensão

Criamos:

snowflake/

├── ddl/
├── models/
├── semantic/
├── cortex/
└── monitoring/

E fazemos uma demonstração:

Databricks Gold
       ↓
Snowflake
       ↓
Cortex

Assim você pode dizer:

"Também desenvolvi uma arquitetura interoperável entre Lakehouse e Warehouse."

Não precisa fazer todo o projeto depender do Snowflake.

24. dbt

Vamos colocar dbt na camada de transformação analítica.

dbt/

models/

├── staging/
├── intermediate/
└── marts/

E:

tests/

macros/

snapshots/

seeds/
25. Métricas governadas

Teremos definições únicas:

Revenue

Orders

Customers

AOV

Retention

Churn

CLV

NPS

Delivery SLA

Customer Quality

Exemplo:

Revenue =
SUM(completed_order_value)

Não:

SUM(all_orders)
26. Semantic Layer

Esse é um dos pontos que vai te diferenciar.

O agente não deve interpretar:

"receita"

sozinho.

Ele deve saber:

Revenue

definition:
completed orders only

exclude:
cancelled

currency:
BRL

grain:
order

owner:
Finance
27. Power BI

Dashboard principal:

Executive Overview
Revenue
Orders
Customers
AOV
Churn
Customer Quality

Gráficos:

receita temporal;
receita por estado;
receita por categoria;
pedidos;
clientes;
churn.
28. Dashboard 2 — Customer Intelligence
Customers

VIP

At Risk

Churn

CLV

Retention

RFM:

Recency

Frequency

Monetary
29. Dashboard 3 — Data Quality

Esse vai ficar muito bom.

DATA QUALITY

97.4%
Dataset	Completeness	Validity	Uniqueness	Freshness
Customers	98%	97%	96%	99%
Orders	99%	98%	99%	98%
Marketing	94%	96%	93%	95%
30. Dashboard 4 — ML
Churn Distribution

ROC-AUC

Precision

Recall

F1

Calibration

E:

Top customers at risk
31. Dashboard 5 — Platform Observability
Pipeline Success

Pipeline Duration

Rows Processed

DQ Score

ML Latency

Agent Latency

MCP Calls

LLM Tokens

Cloud Cost

Agora seu Power BI também monitora a própria plataforma.

32. Machine Learning

Vamos construir dois modelos.

Churn

Modelos:

Logistic Regression
Random Forest
Gradient Boosting

Comparar:

ROC-AUC
Precision
Recall
F1
PR-AUC
Calibration
33. Customer Segmentation

Clustering:

KMeans

Features:

recency

frequency

monetary

avg_order

support_tickets

engagement

Segmentos:

VIP

Loyal

Potential

At Risk

Inactive
34. MLflow

Tudo rastreado:

experiment

parameters

metrics

artifacts

model

dataset version

E:

Model Registry

Isso conecta diretamente com seu perfil de MLOps.

35. SHAP

Para explicar:

Por que esse cliente possui churn 0.86?

Resposta:

Last purchase        +0.22
Support complaints    +0.18
Engagement drop       +0.13
Purchase frequency    +0.09
36. IA Generativa

Agora começa a parte "AI".

Teremos:

Customer Intelligence Agent
37. Agent Architecture
                 USER
                   │
                   ▼
              ORCHESTRATOR
                   │
         ┌─────────┼─────────┐
         ▼         ▼         ▼
       SQL       MCP       RAG
         │         │         │
         ▼         ▼         ▼
      Databricks Power BI Documents
38. MCP

Vamos implementar nosso MCP Server.

Ferramentas:

get_customer

search_customers

get_customer_quality

get_customer_churn

get_customer_orders

get_customer_graph

get_sales_metrics

get_data_quality

get_model_metrics

get_pipeline_status

recommend_action
39. Databricks MCP

E aqui entra sua ideia.

O Databricks possui atualmente servidores MCP gerenciados que conectam agentes a dados do Unity Catalog, Genie Agents, AI Search e funções customizadas, com as permissões do Unity Catalog sendo aplicadas.

Então teremos:

Claude
   ↓
MCP
   ↓
Databricks
   ↓
Unity Catalog
   ↓
Gold
40. Power BI MCP

Também:

Claude
   ↓
Power BI MCP
   ↓
Semantic Model
   ↓
DAX
   ↓
Power BI

O MCP remoto do Power BI permite que agentes consultem modelos semânticos, obtenham schema e gerem/executem consultas DAX; porém, como está em Preview, devemos tratá-lo como componente experimental do projeto.

41. Genie

Databricks Genie:

User
 ↓
Genie
 ↓
Unity Catalog
 ↓
SQL
 ↓
Answer

O Genie atualmente fornece interação em linguagem natural sobre dados governados pelo Unity Catalog.

E existe inclusive o Genie One MCP Server, em Beta, para expor o Genie como ferramenta MCP.

42. Agora fazemos a coisa realmente interessante

O Claude poderá ter:

Databricks MCP
Power BI MCP
Custom MCP

E escolher a ferramenta.

Pergunta:

"Quanto vendemos em São Paulo?"

Pode usar:

Power BI MCP

Pergunta:

"Por que caiu?"

Pode usar:

Databricks MCP
+
ML
+
Support

Pergunta:

"Esse cliente é realmente único?"

Pode usar:

Golden Record
+
Graph
+
Entity Resolution

Isso é Agentic Data Platform.

43. Agente de Data Quality

Pergunta:

"Por que a qualidade dos clientes caiu?"

Agente consulta:

DQ

pipeline

schema

logs

source

freshness

Resposta:

Quality decreased:

97.8% → 92.4%

Main cause:
CRM email completeness.

Affected rows:
12,341

Recommended action:
Review CRM extraction job.
44. Agente de recomendação

Cliente:

Customer: 12345

CLV: R$ 5,200

Churn: 0.89

Last purchase: 72 days

Tickets: 4

Agente:

Alto risco de churn e alto valor.

Recomendação:

Priority: HIGH

Action:
Retention campaign

Suggested:
10% incentive

Human approval:
REQUIRED
45. Human-in-the-loop

Nunca deixe o agente executar ações sensíveis sozinho.

AI
 ↓
Recommendation
 ↓
Confidence
 ↓
Human
 ↓
Approve / Reject
 ↓
Execute

Isso adiciona:

AI Governance.

46. RAG

Documentos:

refund_policy

delivery_policy

loyalty_policy

privacy_policy

Pipeline:

PDF
 ↓
Extract
 ↓
Chunk
 ↓
Embedding
 ↓
Vector Search
 ↓
RAG
 ↓
Agent

Agora:

"Esse cliente tem direito a reembolso?"

O agente combina:

Customer Data
+
Transaction Data
+
Policy
47. Azure OpenAI

Aqui colocamos sua experiência de Azure no projeto.

Azure OpenAI

para:

embeddings;
classificação;
sumarização;
RAG;
agentes.

Isso deixa a arquitetura:

Azure
 ├── ADLS
 ├── Data Factory
 ├── Databricks
 ├── Key Vault
 ├── Azure OpenAI
 ├── Monitor
 └── Power BI
48. Governança
Unity Catalog

Controla:

catalogs

schemas

tables

views

models

functions

volumes

O Unity Catalog atualmente atua como camada unificada de governança de dados e IA no Azure Databricks, incluindo controle de acesso, lineage e auditoria.

49. Microsoft Purview

Vamos conectar:

Databricks
      ↓
Purview

para:

catálogo;
descoberta;
classificação;
lineage;
governança.

O conector atual do Microsoft Purview para Azure Databricks Unity Catalog consegue extrair metadados de metastore, catalogs, schemas, tabelas, views e tags; há limitações de lineage dependendo do cenário, que vamos documentar no projeto.

Isso é Enterprise Governance de verdade.

50. Security
Microsoft Entra ID

RBAC

Unity Catalog

Key Vault

Managed Identity

Secrets

Encryption

Private Endpoints

Network Security

PII:

email

phone

document

devem ser:

masked
hashed
restricted
51. AWS

Sua experiência em AWS entra numa camada de portabilidade.

Arquitetura equivalente:

Azure                    AWS

ADLS Gen2       →        S3

Data Factory    →        Glue / Step Functions

Databricks      →        Databricks AWS

Key Vault       →        Secrets Manager

Azure Monitor   →        CloudWatch

Entra ID        →        IAM

Azure OpenAI    →        Bedrock/OpenAI

Você não precisa duplicar o projeto.

Documenta:

Cloud portability strategy.

52. Terraform

Estrutura:

terraform/

├── azure/
│
│   ├── resource_group
│   ├── adls
│   ├── databricks
│   ├── key_vault
│   ├── networking
│   ├── monitoring
│   └── openai
│
├── aws/
│   ├── s3
│   ├── iam
│   ├── networking
│   └── monitoring
│
└── modules/
53. CI/CD

GitHub:

push
 ↓
lint
 ↓
unit tests
 ↓
SQL tests
 ↓
dbt tests
 ↓
DQ tests
 ↓
build
 ↓
security scan
 ↓
Terraform plan
 ↓
deploy
54. Observabilidade

OpenTelemetry:

API

Agent

MCP

Databricks

LLM

Prometheus:

pipeline_duration

rows_processed

errors

latency

DQ_score

Grafana:

Infrastructure

Pipeline

AI

ML
55. Custos

Vamos monitorar:

Databricks DBU

Storage

Power BI

LLM tokens

MCP calls

API calls

Dashboard:

COST

Databricks      $120
Storage          $12
LLM              $38
Power BI         $25
--------------------
Total           $195

Isso introduz:

FinOps.

56. Estrutura final do GitHub

Eu fecharia assim:

enterprise-customer-intelligence/
│
├── README.md
├── LICENSE
├── Makefile
├── docker-compose.yml
├── pyproject.toml
│
├── architecture/
│   ├── architecture.drawio
│   ├── architecture.png
│   ├── data-flow.drawio
│   ├── network.drawio
│   └── decisions/
│
├── data/
│   ├── raw/
│   ├── synthetic/
│   │   ├── crm/
│   │   ├── marketing/
│   │   ├── support/
│   │   ├── web/
│   │   └── finance/
│   └── documents/
│
├── ingestion/
│   ├── api/
│   ├── files/
│   ├── olist/
│   └── streaming/
│
├── databricks/
│   ├── notebooks/
│   ├── workflows/
│   ├── jobs/
│   ├── sql/
│   └── unity_catalog/
│
├── lakehouse/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── dbt/
│   ├── models/
│   ├── tests/
│   ├── macros/
│   ├── snapshots/
│   └── seeds/
│
├── data_quality/
│   ├── expectations/
│   ├── validators/
│   ├── monitoring/
│   └── reports/
│
├── mdm/
│   ├── entity_resolution/
│   ├── golden_record/
│   └── matching/
│
├── graph/
│   ├── networkx/
│   ├── algorithms/
│   └── queries/
│
├── ml/
│   ├── features/
│   ├── churn/
│   ├── segmentation/
│   ├── training/
│   ├── evaluation/
│   └── explainability/
│
├── mlflow/
│
├── agents/
│   ├── orchestrator/
│   ├── customer/
│   ├── data_quality/
│   ├── recommendation/
│   └── monitoring/
│
├── mcp/
│   ├── server/
│   ├── tools/
│   ├── resources/
│   └── prompts/
│
├── rag/
│   ├── ingestion/
│   ├── embeddings/
│   ├── retrieval/
│   └── evaluation/
│
├── snowflake/
│   ├── ddl/
│   ├── models/
│   ├── semantic/
│   └── cortex/
│
├── powerbi/
│   ├── semantic_model/
│   ├── dax/
│   └── dashboards/
│
├── api/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   └── middleware/
│
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   └── opentelemetry/
│
├── governance/
│   ├── security.md
│   ├── lgpd.md
│   ├── data_catalog.md
│   ├── lineage.md
│   └── access_control.md
│
├── terraform/
│   ├── azure/
│   ├── aws/
│   └── modules/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── data/
│   └── ml/
│
├── docs/
│   ├── data_dictionary.md
│   ├── runbooks/
│   ├── deployment.md
│   ├── troubleshooting.md
│   └── architecture.md
│
└── .github/
    └── workflows/
        ├── ci.yml
        ├── data-tests.yml
        ├── dbt.yml
        └── terraform.yml
57. Como o dado atravessa a plataforma

Esse é o fluxo que você precisa saber explicar de cabeça:

Olist / CRM / APIs
        ↓
Azure Data Factory
        ↓
ADLS Gen2
        ↓
Bronze Delta
        ↓
PySpark
        ↓
Data Quality
        ↓
Silver Delta
        ↓
Entity Resolution
        ↓
Golden Record
        ↓
Feature Engineering
        ↓
Gold Delta
        ↓
dbt / Databricks SQL
        ↓
Semantic Layer
        ↓
Power BI
        ↓
MCP
        ↓
AI Agent
        ↓
Insight / Recommendation
58. O que vai aparecer no seu README

Logo no topo:

Enterprise Customer Intelligence Platform

A production-oriented Lakehouse and AI platform designed to integrate heterogeneous customer data, establish trusted Golden Records, generate predictive insights and expose governed analytics through BI and agentic AI interfaces.

Depois:

Architecture

Data Engineering

Data Quality

MDM

Machine Learning

Generative AI

MCP

Governance

Observability

CI/CD

Infrastructure as Code
59. O que você poderá colocar no currículo

Depois de implementar de verdade, algo como:

Enterprise Customer Intelligence Lakehouse — Designed and implemented an end-to-end cloud data platform using Azure Data Lake Storage, Azure Databricks, Delta Lake, PySpark, Unity Catalog, dbt and Power BI. Built Medallion architecture, automated ETL/ELT pipelines, data quality monitoring, entity resolution and Golden Record generation, predictive ML models with MLflow, semantic data models, and MCP-enabled AI agents for governed natural-language analytics.

Isso é muito forte.

E no LinkedIn/GitHub:

Built a production-oriented Lakehouse architecture integrating Data Engineering, MDM, Machine Learning, Generative AI and Agentic Analytics.

60. O que você NÃO deve fazer

Não tente fazer isso tudo simultaneamente.

A ordem correta é:

Sprint 1

Data Lake

ADLS + dataset + ingestion.

Sprint 2

Lakehouse

Databricks + Delta + Bronze/Silver/Gold.

Sprint 3

Data Engineering

PySpark + SQL + dbt.

Sprint 4

Data Quality

Great Expectations + DQ dashboard.

Sprint 5

MDM

Entity Resolution + Golden Record.

Sprint 6

Warehouse

Databricks SQL + dimensional model.

Sprint 7

Power BI

Semantic model + dashboard.

Sprint 8

ML

Churn + segmentation + MLflow + SHAP.

Sprint 9

RAG

Documents + embeddings + retrieval.

Sprint 10

Agents

LangGraph + Azure OpenAI.

Sprint 11

MCP

Custom MCP + Databricks MCP + Power BI MCP.

Sprint 12

Governance

Unity Catalog + Purview + Security.

Sprint 13

DevOps

Docker + GitHub Actions + Terraform.

Sprint 14

Observability

OpenTelemetry + Prometheus + Grafana.

Sprint 15

Enterprise polish

Documentação + arquitetura + benchmark + testes + demo.

61. E aí vem o ponto mais importante

Não precisamos pagar por tudo.

O desenvolvimento local pode usar:

Python
Docker
PostgreSQL
MinIO
PySpark
dbt
MLflow
NetworkX
Great Expectations
LangGraph
FastAPI

Depois usamos cloud somente para demonstrar:

Azure ADLS
Azure Databricks
Power BI
Azure OpenAI

E os componentes Preview/Beta:

Power BI MCP
Databricks Genie MCP

entram como demo avançada, não como requisito do core.

62. Por que esse projeto é realmente top tier

Porque ele demonstra cinco níveis diferentes de engenharia:

Data Engineering
ETL
ELT
PySpark
SQL
Delta
dbt
Data Lake
Lakehouse
Warehouse
Data Science
EDA
Feature Engineering
Regression
Random Forest
Gradient Boosting
Clustering
MLflow
SHAP
Data Governance
MDM
Golden Record
Data Quality
Lineage
Unity Catalog
Purview
RBAC
LGPD
AI Engineering
RAG
LLM
LangGraph
Agents
Human-in-the-loop
MCP
Cloud / DevOps
Azure
AWS
Terraform
Docker
GitHub Actions
CI/CD
Observability
FinOps

Isso conversa diretamente com aquelas perguntas que você acabou de receber: Databricks, PySpark, ETL/ELT, SQL, Azure, qualidade, Golden Record, grandes volumes, modelos estatísticos, agentes, MCP, Power BI, Snowflake/Cortex e governança.

Minha recomendação de arquitetura final

Core:

Azure ADLS Gen2 → Azure Data Factory → Azure Databricks → Delta Lake → Unity Catalog → dbt/Databricks SQL → Power BI

Intelligence:

MLflow + Churn + Segmentation + SHAP + MDM + Golden Record + Graph

AI:

Azure OpenAI + LangGraph + RAG + MCP

Agentic BI:

Claude → Power BI MCP / Databricks MCP / Custom MCP

Governance:

Unity Catalog + Microsoft Purview + Entra ID + Key Vault + LGPD

Enterprise extension:

Snowflake + Cortex

DevOps:

Terraform + Docker + GitHub Actions + OpenTelemetry + Prometheus + Grafana

Essa é a versão que eu considero "top tier" para o seu portfólio. Não porque tem muita ferramenta, mas porque existe uma história arquitetural coerente: dado bruto → dado confiável → cliente unificado → modelo → métrica governada → BI → agente → decisão, com segurança e observabilidade em volta.

E tem uma vantagem brutal para você: o projeto vai servir como laboratório para as vagas que você está buscando, porque cada etapa produz uma evidência concreta de competência, em vez de você simplesmente escrever "tenho experiência com Databricks/Azure/MCP".

Sim. E agora eu faria isso como seu projeto flagship de Data Engineering / Data Science / AI, mas com uma regra: não vamos montar um Frankenstein de ferramentas. Vamos construir uma arquitetura corporativa em que cada tecnologia tenha uma função clara.
A sua experiência em AWS entra como diferencial de cloud/multicloud, mas vamos fazer a implementação principal em Azure + Databricks, porque isso conversa diretamente com as vagas que estão te perguntando sobre Azure, Databricks, Power BI e engenharia de dados. E vamos deixar Snowflake/Cortex como uma extensão enterprise, não como dependência do núcleo.
Pesquisei a documentação atual para alinhar a arquitetura com o que as plataformas realmente oferecem hoje. O Azure Databricks tem Unity Catalog como camada de governança de dados e IA, com controle de acesso, lineage e auditoria; a arquitetura de referência da Microsoft usa justamente ADLS Gen2 + Azure Data Factory + Azure Databricks + Unity Catalog + Power BI + Purview.
Além disso, o Databricks atualmente possui MCPs gerenciados que conectam agentes a dados governados pelo Unity Catalog, e o Power BI possui um MCP remoto para agentes consultarem modelos semânticos — este último ainda está em Preview. mas eu quero terraform e snowflakes cara isso tem que conter mesmo que fique extenso

Pensou por 10s

Sim. Se é para ser o seu flagship, eu não tiraria Snowflake nem Terraform. Na verdade, eu mudaria a arquitetura para que os dois sejam componentes de primeira classe, com responsabilidades muito claras.

A arquitetura final fica mais interessante porque você demonstra que sabe trabalhar com Lake + Lakehouse + Warehouse + Cloud + IaC + BI + ML + AI, e principalmente que sabe quando usar cada camada.

Pesquisei a documentação atual para não montarmos algo conceitualmente bonito, mas tecnicamente errado: o provider oficial do Databricks para Terraform permite gerenciar workspace, jobs, clusters e acesso; o provider oficial do Snowflake permite gerenciar recursos da conta; e o Snowflake atual tem Semantic Views, Cortex Analyst, Cortex Search, Cortex Agents e AI Functions.

Enterprise Customer Intelligence Platform
Azure + Databricks + Snowflake + Terraform + Power BI + MCP + Cortex + ML + GenAI

Esse passa a ser o projeto.

1. A arquitetura definitiva

Eu dividiria em 4 planos:

┌─────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE DATA PLATFORM                     │
└─────────────────────────────────────────────────────────────────┘

                        DATA SOURCES
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
        APIs               Files            Events
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ↓
                 ┌──────────────────────┐
                 │   AZURE DATA FACTORY │
                 │      EVENT HUBS      │
                 └──────────┬───────────┘
                            ↓
                 ╔══════════════════════╗
                 ║   AZURE DATA LAKE   ║
                 ║       ADLS Gen2     ║
                 ╚══════════╤═══════════╝
                            ↓
             ╔══════════════════════════════╗
             ║       AZURE DATABRICKS      ║
             ║                              ║
             ║ Delta Lake                   ║
             ║ PySpark                      ║
             ║ Spark SQL                    ║
             ║ Unity Catalog                ║
             ║ MLflow                       ║
             ╚══════════════╤═══════════════╝
                            │
              ┌─────────────┼──────────────┐
              ↓             ↓              ↓
          DATA QUALITY     MDM             ML
              │          Golden Record    MLflow
              │          Entity Res.      Features
              └─────────────┼──────────────┘
                            ↓
                       GOLD DATA
                            │
                            ↓
                  ╔══════════════════╗
                  ║    SNOWFLAKE     ║
                  ║                  ║
                  ║ Enterprise DWH   ║
                  ║ Semantic Views    ║
                  ║ Cortex Analyst   ║
                  ║ Cortex Search    ║
                  ║ Cortex Agents    ║
                  ╚════════╤═════════╝
                           │
                ┌──────────┼───────────┐
                ↓          ↓           ↓
            POWER BI    CORTEX       APIs
                │       / AGENTS
                │          │
                └────┬─────┘
                     ↓
              MCP / AGENT LAYER
                     │
              ┌──────┼──────┐
              ↓      ↓      ↓
           Claude  Databricks  Power BI
                    MCP         MCP

─────────────────────────────────────────────────────────────────

                 GOVERNANCE / DEVOPS
                        
       Terraform + GitHub Actions + Unity Catalog
       Snowflake RBAC + Entra ID + Key Vault
       Purview + OpenTelemetry + Prometheus
       Grafana + Audit + Data Quality + FinOps

Essa é a arquitetura que eu usaria.

2. Por que Databricks + Snowflake?

Aqui está a parte que você precisa conseguir explicar numa entrevista.

Não vamos usar os dois para fazer a mesma coisa.

Azure Data Lake / ADLS

É o Data Lake.

Responsável por:

armazenamento bruto;
histórico;
arquivos;
dados estruturados;
dados semiestruturados;
documentos;
landing zone.
Databricks

É o Lakehouse / processamento / ML.

Responsável por:

ingestão;
ETL/ELT;
PySpark;
Delta Lake;
Bronze/Silver/Gold;
qualidade;
engenharia de features;
MDM;
Golden Record;
Machine Learning;
MLflow;
processamento distribuído.
Snowflake

É o Enterprise Data Warehouse / Semantic + AI Serving Layer.

Responsável por:

modelo dimensional;
dados analíticos governados;
métricas;
Semantic Views;
Cortex Analyst;
Cortex Search;
Cortex Agents;
AI Functions;
consumo corporativo.

O Snowflake Semantic View é particularmente interessante aqui porque permite colocar métricas, entidades, relacionamentos e definições de negócio dentro da própria camada semântica, servindo tanto BI quanto aplicações de IA.

Ou seja:

Databricks transforma o dado. Snowflake organiza e serve o dado para Analytics e AI.

Isso é uma arquitetura muito mais defensável.

3. E Terraform?

Terraform vira o control plane de infraestrutura.

Não será um arquivo main.tf de enfeite.

Vamos realmente provisionar:

Azure
Resource Groups
ADLS Gen2
Data Factory
Event Hubs
Key Vault
Networking
Managed Identity
Databricks Workspace
Azure OpenAI
Monitoring
Databricks
Workspace configuration
Clusters
Jobs
Workflows
Secret scopes
Unity Catalog
Catalogs
Schemas
External locations
Permissions

O provider do Databricks é justamente destinado a automatizar workspace e recursos associados, incluindo clusters, jobs e acesso a dados.

Snowflake
Account configuration
Warehouses
Databases
Schemas
Roles
Users/service accounts
Grants
Tables
Views
Stages
Tasks
Streams
Semantic objects

O provider Snowflake-Labs/snowflake existe justamente para gerenciar recursos da conta Snowflake via Terraform.

4. Estrutura Terraform

Eu faria:

terraform/

├── environments/
│
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars.example
│   │
│   ├── staging/
│   └── prod/
│
├── modules/
│
│   ├── azure/
│   │   ├── resource_group/
│   │   ├── adls/
│   │   ├── data_factory/
│   │   ├── event_hubs/
│   │   ├── key_vault/
│   │   ├── networking/
│   │   ├── monitoring/
│   │   └── openai/
│   │
│   ├── databricks/
│   │   ├── workspace/
│   │   ├── clusters/
│   │   ├── jobs/
│   │   ├── unity_catalog/
│   │   └── permissions/
│   │
│   └── snowflake/
│       ├── warehouse/
│       ├── databases/
│       ├── schemas/
│       ├── roles/
│       ├── grants/
│       ├── stages/
│       └── semantic/
│
└── policies/
    ├── security/
    ├── tagging/
    └── naming/

Isso já demonstra Infrastructure as Code de verdade.

5. Data Lake

O ADLS terá:

adls://customer-platform/

├── landing/
│
├── raw/
│   ├── olist/
│   ├── crm/
│   ├── marketing/
│   ├── support/
│   ├── payments/
│   └── web/
│
├── bronze/
├── silver/
├── gold/
│
├── quarantine/
├── archive/
└── checkpoints/
6. Data Lake → Lakehouse

A arquitetura será:

                 ADLS
                  │
                  ↓
              RAW FILES
                  │
                  ↓
             BRONZE DELTA
                  │
                  ↓
             SILVER DELTA
                  │
                  ↓
              GOLD DELTA
                  │
                  ↓
              SNOWFLAKE

O Delta Lake é o mecanismo que nos dá transações, schema enforcement, histórico/versionamento e processamento Lakehouse.

7. Bronze
bronze.olist_orders
bronze.olist_customers
bronze.crm_customers
bronze.marketing_events
bronze.support_tickets
bronze.web_events

Regra:

Bronze preserva a origem.

Não destruir informação.

8. Silver
silver.customers
silver.orders
silver.order_items
silver.products
silver.payments
silver.support
silver.web_events

Aqui entram:

schema validation
casting
deduplication
normalization
standardization
data quality
joins
enrichment
9. Gold

Gold já representa negócio:

gold.customer
gold.orders
gold.customer_behavior
gold.customer_interactions
gold.customer_risk
10. MDM / Golden Record

Aqui está um dos diferenciais.

Olist
CRM
Marketing
Support
        │
        ↓
Entity Resolution
        │
        ↓
Golden Record

Exemplo:

CRM:

João da Silva
joao@gmail.com
1199999999

Olist:

Joao Silva
joao@gmail.com
1199999999

Marketing:

João Silva
joao@gmail.com
1199999999

↓

MASTER_CUSTOMER_ID = C000123
11. Entity Resolution

Teremos três estratégias.

Determinística
CPF
email
phone
Probabilística
Jaro-Winkler
Levenshtein
similaridade
ML
Random Forest
Gradient Boosting

Output:

match_score = 0.97
decision = MATCH

ou:

match_score = 0.61
decision = HUMAN_REVIEW
12. Customer Graph

Criamos:

CUSTOMER
   │
   ├── EMAIL
   ├── PHONE
   ├── ADDRESS
   ├── ORDER
   ├── PRODUCT
   └── SELLER

Com:

NetworkX

e opcionalmente:

Neo4j

Depois calculamos:

degree
centrality
communities
connected components
similarity
13. Machine Learning
Modelo 1

Customer Churn

Logistic Regression
Random Forest
Gradient Boosting
Modelo 2

Customer Segmentation

KMeans
Modelo 3

Duplicate / Match Model

Random Forest
Gradient Boosting
14. MLflow

Tudo registrado:

experiment
run
parameters
metrics
artifacts
model
dataset version

E fazemos:

Model Registry
15. Snowflake entra agora

Depois do Gold:

Databricks Gold
       ↓
Data Product
       ↓
Snowflake

Vamos criar:

CUSTOMER_INTELLIGENCE
│
├── RAW
├── STAGING
├── CORE
├── ANALYTICS
├── SEMANTIC
└── AI
16. Snowflake Data Warehouse
CORE
DIM_CUSTOMER

DIM_PRODUCT

DIM_SELLER

DIM_DATE

DIM_GEOGRAPHY
FACT
FACT_ORDER

FACT_ORDER_ITEM

FACT_PAYMENT

FACT_CUSTOMER_INTERACTION

FACT_SUPPORT
17. Snowflake Tasks / Streams

Agora demonstramos processamento incremental também no Warehouse.

Databricks
    ↓
Snowflake
    ↓
STREAM
    ↓
TASK
    ↓
CURATED

Assim você demonstra que conhece:

batch + incremental + CDC-like patterns.

18. Semantic Views

Essa é uma das partes que eu faria questão de colocar.

No Snowflake:

SEMANTIC_CUSTOMER_ANALYTICS

Define:

CUSTOMER
ORDER
PRODUCT
REGION
REVENUE
AOV
CHURN
CLV
RETENTION

Por exemplo:

Revenue
=
SUM(completed_order_amount)

E não deixa cada dashboard inventar sua própria receita.

Semantic Views são justamente a abstração recomendada pelo Snowflake para representar conceitos, métricas e relações de negócio e servir o Cortex Analyst.

19. Cortex Analyst

Agora temos:

                         SNOWFLAKE
                             │
                    SEMANTIC VIEW
                             │
                             ↓
                      CORTEX ANALYST
                             │
                             ↓
                          SQL
                             │
                             ↓
                           DATA

Usuário:

Qual foi a receita de São Paulo nos últimos seis meses?

Cortex:

Natural Language
       ↓
Semantic View
       ↓
SQL
       ↓
Snowflake
       ↓
Answer

O Cortex Analyst possui inclusive API REST para consultas em linguagem natural sobre Semantic Views.

20. E vamos avaliar o Cortex Analyst

Isso é muito importante.

Não vamos dizer:

"Meu agente funciona."

Vamos medir.

Criamos:

evaluation/

├── questions.csv
├── ground_truth.sql
├── generated_sql/
├── results/
└── metrics/

Perguntas:

Qual foi a receita em SP?

Qual categoria vendeu mais?

Qual foi o AOV?

Qual segmento possui maior churn?

E medimos:

SQL correctness
answer correctness
latency
regression

O Snowflake possui atualmente avaliações do Cortex Analyst baseadas em verified queries, comparando SQL gerado com ground truth e acompanhando accuracy, regressões e latência.

Isso é excelente para o seu portfólio.

21. Cortex Search

Agora entram os documentos.

refund_policy.pdf
delivery_policy.pdf
loyalty_policy.pdf
privacy_policy.pdf

Snowflake:

AI_PARSE_DOCUMENT
        ↓
structured text
        ↓
Cortex Search
        ↓
retrieval

O Snowflake disponibiliza funções de documentos como AI_PARSE_DOCUMENT, AI_EXTRACT e AI_CLASSIFY, e documenta explicitamente seu uso em RAG e pesquisa inteligente.

22. Cortex AI Functions

Vamos demonstrar:

AI_PARSE_DOCUMENT
AI_EXTRACT
AI_CLASSIFY
AI_COMPLETE
AI_SENTIMENT
AI_EMBED
AI_SIMILARITY
AI_REDACT

Não precisa usar todas.

Eu escolheria:

AI_PARSE_DOCUMENT

document intelligence.

AI_EXTRACT

extração estruturada.

AI_SENTIMENT

tickets/reviews.

AI_EMBED

RAG/similarity.

AI_REDACT

PII.

A documentação atual do Snowflake lista essas funções como parte do conjunto de AI Functions.

23. Cortex Agents

Aqui o projeto sobe de nível.

O Snowflake possui atualmente Cortex Agents, que podem combinar ferramentas como Cortex Analyst para dados estruturados e Cortex Search para dados não estruturados em um fluxo governado.

Então podemos ter:

             CUSTOMER INTELLIGENCE AGENT
                         │
             ┌───────────┼────────────┐
             ↓           ↓            ↓
          Analyst      Search      Python
             │           │            │
          Metrics      Docs       Calculations
24. Claude + MCP

E aqui entra o que você falou.

Claude será nosso cliente/agente externo de desenvolvimento e exploração.

Ele terá acesso por MCP a:

Databricks MCP
Power BI MCP
Custom MCP

E podemos construir um MCP próprio para Snowflake/Cortex:

Claude
   ↓
MCP
   ↓
Snowflake Cortex Analyst
   ↓
Semantic View
   ↓
SQL

Ou:

Claude
   ↓
MCP
   ↓
Snowflake Cortex Agent
25. MCP customizado

Estrutura:

mcp/

├── server.py
│
├── tools/
│   ├── customer.py
│   ├── analytics.py
│   ├── quality.py
│   ├── ml.py
│   ├── snowflake.py
│   └── databricks.py
│
├── resources/
│   ├── catalog.py
│   └── documentation.py
│
└── prompts/
    └── enterprise_analytics.py

Tools:

get_customer

get_customer_churn

get_customer_quality

get_customer_graph

get_sales_metrics

get_data_quality

get_pipeline_status

query_snowflake

query_databricks

get_model_prediction
26. Power BI

Agora temos uma arquitetura muito interessante:

                  SNOWFLAKE
                     │
              Semantic Views
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
      Power BI              Cortex
          │                     │
       Dashboard             AI

Power BI vira o BI tradicional.

Cortex vira o AI Analytics.

E Claude/MCP vira a interface agentic.

27. Power BI MCP

No projeto vamos documentar:

Claude
   ↓
Power BI MCP
   ↓
Power BI Semantic Model
   ↓
DAX
   ↓
Answer

O MCP remoto do Power BI atualmente permite recuperar esquema do modelo semântico e executar consultas DAX, mas a funcionalidade está em Preview, então eu colocaria isso no projeto como experimental/advanced integration, não como dependência do core.

28. Três formas de perguntar

Isso é muito legal para a demo.

Power BI

"Mostre o faturamento por estado."

Cortex

"Por que o faturamento caiu?"

Claude + MCP

"Investigue por que o faturamento caiu em São Paulo e me diga quais fatores contribuíram."

E o agente pode consultar:

Power BI
+
Snowflake
+
Databricks
+
ML
+
Support
29. AI Data Quality Agent

Também criamos:

Data Quality Agent

Pergunta:

Por que a qualidade do cadastro caiu?

Ele consulta:

DQ metrics
pipeline
schema
freshness
duplicates
nulls

E responde:

Data Quality: 97.8% → 92.4%

Main issue:
CRM email completeness

Affected records:
12,341

Source:
CRM ingestion

Recommendation:
Inspect extraction job.
30. Recommendation Agent

Input:

customer
+
churn
+
CLV
+
support
+
behavior

Output:

risk = HIGH

recommendation =
retention campaign

confidence =
0.91

Mas:

AI
 ↓
Recommendation
 ↓
Human approval
 ↓
Action
31. Governance

Agora vamos fazer a plataforma realmente enterprise.

Azure
Entra ID
Managed Identity
Key Vault
RBAC
Private Networking
Databricks
Unity Catalog
Catalog permissions
Schema permissions
Table permissions
Column masking
Lineage
Audit
Snowflake
RBAC
Roles
Grants
Warehouses
Masking policies
Row access policies
Tags
Audit
32. PII

Nunca guardaríamos CPF real.

document_hash

E:

email
phone
address

teriam políticas de acesso.

Exemplo:

DATA_ANALYST

→ masked email
→ masked phone

enquanto:

DATA_STEWARD

→ authorized access
33. Microsoft Purview

Também entra.

Azure
   ↓
Purview
   ↓
Catalog
   ↓
Lineage
   ↓
Classification

Isso fecha a parte de Data Governance.

34. Observabilidade

Teremos:

Azure Monitor
Databricks monitoring
Snowflake monitoring
OpenTelemetry
Prometheus
Grafana

Monitoramos:

pipeline latency

rows processed

failed jobs

DQ score

warehouse utilization

query latency

ML latency

LLM latency

MCP latency

token usage

cloud cost
35. FinOps

Dashboard:

                    CLOUD COST

Azure                     $120
Databricks                $180
Snowflake                 $140
Storage                    $15
LLM                        $35
Power BI                   $25
--------------------------------
TOTAL                     $515

E:

Cost / 1M records

Cost / pipeline

Cost / AI request

Cost / dashboard query

Isso é muito bom para demonstrar maturidade.

36. AWS entra como arquitetura secundária

Você tem experiência em AWS, então vamos explorar isso.

Não precisamos duplicar o projeto inteiro.

Vamos criar:

cloud-portability/

azure.md
aws.md
architecture-comparison.md

Tabela:

Azure	AWS
ADLS Gen2	S3
Data Factory	Glue / Step Functions
Event Hubs	Kinesis
Azure Databricks	Databricks AWS
Key Vault	Secrets Manager
Entra ID	IAM
Azure Monitor	CloudWatch
Azure OpenAI	Bedrock/OpenAI
Purview	Glue Catalog/Lake Formation ecosystem

Você demonstra:

cloud-agnostic architecture + Azure implementation + AWS knowledge.

37. Estrutura definitiva do GitHub

Agora sim eu fecharia o repositório assim:

enterprise-customer-intelligence-platform/

├── README.md
│
├── architecture/
│   ├── architecture.drawio
│   ├── architecture.png
│   ├── data-flow.drawio
│   ├── security.drawio
│   ├── ai-agent-flow.drawio
│   └── decisions/
│       ├── ADR-001-cloud.md
│       ├── ADR-002-lakehouse.md
│       ├── ADR-003-warehouse.md
│       ├── ADR-004-mdm.md
│       ├── ADR-005-semantic-layer.md
│       ├── ADR-006-mcp.md
│       └── ADR-007-ai-governance.md
│
├── data/
│   ├── raw/
│   ├── synthetic/
│   │   ├── crm/
│   │   ├── marketing/
│   │   ├── support/
│   │   ├── web/
│   │   └── finance/
│   └── documents/
│
├── ingestion/
│   ├── api/
│   ├── olist/
│   ├── files/
│   └── streaming/
│
├── databricks/
│   ├── notebooks/
│   ├── jobs/
│   ├── workflows/
│   ├── sql/
│   └── unity_catalog/
│
├── lakehouse/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── data_quality/
│   ├── rules/
│   ├── expectations/
│   ├── validators/
│   ├── monitoring/
│   └── reports/
│
├── mdm/
│   ├── entity_resolution/
│   ├── golden_record/
│   ├── matching/
│   └── survivorship/
│
├── graph/
│   ├── networkx/
│   ├── algorithms/
│   └── queries/
│
├── ml/
│   ├── features/
│   ├── churn/
│   ├── segmentation/
│   ├── matching/
│   ├── training/
│   ├── evaluation/
│   └── explainability/
│
├── mlflow/
│
├── snowflake/
│   ├── databases/
│   ├── schemas/
│   ├── warehouses/
│   ├── roles/
│   ├── grants/
│   ├── tables/
│   ├── views/
│   ├── semantic_views/
│   ├── cortex/
│   │   ├── analyst/
│   │   ├── search/
│   │   ├── agents/
│   │   └── functions/
│   └── evaluations/
│
├── dbt/
│   ├── models/
│   ├── tests/
│   ├── macros/
│   ├── snapshots/
│   └── seeds/
│
├── rag/
│   ├── ingestion/
│   ├── parsing/
│   ├── embeddings/
│   ├── retrieval/
│   └── evaluation/
│
├── agents/
│   ├── orchestrator/
│   ├── customer/
│   ├── quality/
│   ├── recommendation/
│   └── monitoring/
│
├── mcp/
│   ├── server/
│   ├── tools/
│   ├── resources/
│   └── prompts/
│
├── powerbi/
│   ├── semantic_model/
│   ├── dax/
│   ├── dashboards/
│   └── documentation/
│
├── api/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   └── middleware/
│
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   ├── opentelemetry/
│   └── dashboards/
│
├── governance/
│   ├── security.md
│   ├── lgpd.md
│   ├── pii.md
│   ├── lineage.md
│   ├── access_control.md
│   └── data_catalog.md
│
├── terraform/
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   │
│   ├── modules/
│   │   ├── azure/
│   │   ├── databricks/
│   │   └── snowflake/
│   │
│   └── policies/
│
├── cloud/
│   ├── azure/
│   ├── aws/
│   └── architecture-comparison.md
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── data/
│   ├── ml/
│   └── ai/
│
├── docs/
│   ├── data-dictionary.md
│   ├── semantic-dictionary.md
│   ├── deployment.md
│   ├── runbooks/
│   └── troubleshooting/
│
├── docker/
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── data-quality.yml
│       ├── dbt.yml
│       ├── ml.yml
│       ├── terraform.yml
│       └── security.yml
│
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── .gitignore
38. O fluxo completo

A história do projeto fica:

                        SOURCE
                          │
                          ↓
                 AZURE DATA FACTORY
                          │
                          ↓
                       ADLS
                          │
                          ↓
                    BRONZE DELTA
                          │
                          ↓
                      PYSPARK
                          │
                 ┌────────┴────────┐
                 ↓                 ↓
             QUALITY              MDM
                 │                 │
                 ↓                 ↓
               SILVER        GOLDEN RECORD
                 │                 │
                 └────────┬────────┘
                          ↓
                         GOLD
                          │
                          ↓
                      SNOWFLAKE
                          │
                 ┌────────┼────────┐
                 ↓        ↓        ↓
              DWH     SEMANTIC   CORTEX
                       VIEWS       │
                 │        │        │
                 ↓        ↓        ↓
              POWER BI  ANALYST  AGENTS
                 │        │        │
                 └────────┼────────┘
                          ↓
                         MCP
                          │
                          ↓
                        CLAUDE
                          │
                 ┌────────┼────────┐
                 ↓        ↓        ↓
              DATA       ML      RECOMMEND
             QUALITY   MODELS      ACTION
39. Terraform controla a fundação

E paralelamente:

                         TERRAFORM
                             │
       ┌─────────────────────┼─────────────────────┐
       ↓                     ↓                     ↓
     AZURE                DATABRICKS            SNOWFLAKE
       │                     │                     │
   ADLS                  Workspace             Warehouse
   ADF                   Clusters              Database
   Event Hub             Jobs                  Schemas
   Key Vault             UC                    Roles
   OpenAI                Permissions            Grants
   Monitor

Então você pode falar:

"A infraestrutura é declarativa e reproduzível. O ambiente pode ser destruído e recriado a partir do código."

Isso é exatamente a mentalidade DevOps/IaC que você quer demonstrar.

40. O projeto terá três níveis de execução
Local
Docker
MinIO
PostgreSQL
PySpark
dbt
MLflow
FastAPI
NetworkX
Cloud
Azure
ADLS
Data Factory
Databricks
Azure OpenAI
Power BI
Enterprise AI
Snowflake
Cortex Analyst
Cortex Search
Cortex Agents
MCP
Claude

Assim você não precisa deixar tudo ligado e pagando o tempo inteiro.

41. A cereja do bolo: Benchmark

Eu criaria uma pasta:

benchmarks/

E mediria:

Pipeline
processing_time
records_per_second
failure_rate
Data Quality
completeness
validity
duplicate_rate
freshness
ML
ROC-AUC
F1
precision
recall
calibration
Cortex
SQL accuracy
answer accuracy
latency
regression rate
Agent
tool selection accuracy
task completion
latency
hallucination rate
cost/request
Infrastructure
Azure cost
Databricks DBU
Snowflake credits
storage
LLM tokens

Agora você não está apenas dizendo:

"Construí uma plataforma."

Você consegue dizer:

"Eu medi a plataforma."

42. E a parte mais importante: não esconder as limitações

No README teremos:

Production readiness
Componente	Status
Data Lake	Production-like
Databricks	Production-like
Delta Lake	Production-like
Data Quality	Production-like
MDM	Research/Prototype
ML	Production-like
Snowflake	Production-like
Cortex	Experimental
Power BI	Production-like
Power BI MCP	Preview
Databricks MCP	Platform-dependent
Terraform	Production-like
Agents	Prototype/Production-like
Governance	Production-like

Isso passa muito mais maturidade do que fingir que um projeto pessoal é um sistema de produção de banco.

43. E o seu currículo fica muito mais forte

Depois de realmente implementar, você poderá colocar:

Enterprise Customer Intelligence Platform

Designed and implemented a cloud-native Data & AI platform using Azure ADLS Gen2, Azure Data Factory, Azure Databricks, PySpark, Delta Lake, Unity Catalog, Snowflake, dbt, Power BI and Terraform. Built Medallion Lakehouse architecture, enterprise data warehouse, data quality framework, MDM/Golden Record, entity resolution, ML pipelines with MLflow, semantic views and AI applications using Snowflake Cortex, RAG, MCP and agentic workflows.

Isso é uma bala.

E a narrativa em entrevista:

"Eu consigo trabalhar desde o dado bruto no Data Lake até a camada de decisão e IA."

Essa é exatamente a mensagem que seu portfólio precisa passar.

Minha decisão arquitetural final

Eu fecharia o projeto assim:

Azure = Cloud Foundation

ADLS Gen2 = Data Lake

Data Factory + Event Hubs = Ingestion

Databricks + Delta Lake = Lakehouse

PySpark = Processing

Unity Catalog = Governance

MDM + Golden Record = Trusted Customer Data

MLflow + ML = Data Science

Snowflake = Enterprise Data Warehouse

Snowflake Semantic Views = Business Semantics

Cortex Analyst = Natural Language Analytics

Cortex Search = Unstructured Data / RAG

Cortex Agents = Managed Agentic AI

Power BI = Enterprise BI

Claude = External AI Interface

MCP = Agent/Data Integration Layer

Terraform = Infrastructure as Code

GitHub Actions = CI/CD

Purview = Data Governance/Catalog

OpenTelemetry + Prometheus + Grafana = Observability

AWS = Multicloud Architecture / Portability

E o mais importante: Databricks e Snowflake não competem dentro do projeto; eles representam duas camadas diferentes da plataforma. Databricks é onde você transforma, processa, treina e governa o Lakehouse. Snowflake é onde você publica produtos analíticos governados, semântica e AI serving. Isso torna a arquitetura defensável tecnicamente, em vez de parecer "joguei tudo que conheço no GitHub".

Esse sim eu considero seu projeto top-tier de portfólio. E, honestamente, ele é grande o suficiente para virar quase uma pequena "empresa de dados" simulada dentro do GitHub — com arquitetura, IaC, pipelines, qualidade, ML, BI, AI, segurança, observabilidade e governança.
vc ja preparou os dataset e as coisas aqui ne

Sim — já definimos exatamente quais datasets e dados sintéticos o projeto vai usar, mas tem uma distinção importante:

Dataset principal: Olist Brazilian E-Commerce Dataset.
Dados sintéticos que vamos gerar: CRM, marketing, suporte, web events, financeiro/pagamentos e alguns eventos de comportamento.
Documentos: políticas de reembolso, entrega, fidelidade, privacidade etc. para RAG/Cortex Search.
Dados de ML: serão derivados dos dados Silver/Gold, não precisamos baixar outro dataset separado.
Dados de observabilidade: serão gerados pelos próprios pipelines, jobs, APIs, MCP e agentes.

A estrutura que já planejamos é:

data/
├── raw/
│   └── olist/
│
├── synthetic/
│   ├── crm/
│   ├── marketing/
│   ├── support/
│   ├── web/
│   └── finance/
│
└── documents/
    ├── refund_policy.pdf
    ├── delivery_policy.pdf
    ├── loyalty_policy.pdf
    └── privacy_policy.pdf

E o fluxo:

Olist + Dados Sintéticos + Documentos
                 ↓
              ADLS
                 ↓
        Bronze / Silver / Gold
                 ↓
            Databricks
                 ↓
      MDM / ML / Data Quality
                 ↓
             Snowflake
                 ↓
      Semantic Layer / Cortex
                 ↓
          Power BI + MCP
                 ↓
       Claude / AI Agents

Mas ainda não gerei os arquivos físicos aqui na conversa. Até agora montamos a especificação e arquitetura dos datasets. Se você quiser, o próximo passo ideal é eu gerar o pacote inicial de dados do projeto de verdade: schemas, CSV/Parquet sintéticos, scripts de geração, dicionário de dados e estrutura data/ pronta para jogar no GitHub/Databricks.


