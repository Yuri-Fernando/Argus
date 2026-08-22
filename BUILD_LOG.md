# Build Log — implementação flagship completa

Log vivo da sessão que está completando o projeto inteiro (todas as camadas, notebooks executáveis,
dashboard, versionamento). Atualizado a cada etapa concluída — serve de proteção contra perda de
contexto/progresso (já aconteceu uma queda de 6 agentes paralelos por limite de sessão da conta;
este arquivo garante que o que já foi validado não precisa ser refeito). Não confundir com:
- `CHANGELOG.md` — notas de release, formato Keep a Changelog
- `ROADMAP.md` — os 16 sprints originais do projeto, com checkboxes 🟢/✅

Convenção: cada entrada tem status, arquivos tocados, métricas reais obtidas (nunca inventadas —
se algo não bateu a meta, está registrado honestamente) e como reproduzir.

---

## 2026-08-13/14 — Sessão de implementação flagship

### Ambiente
- Drive de trabalho (`G:\...`) é sincronizado na nuvem (Google Drive virtual) — `git`/`find` recursivos
  são lentos ou travam. `git init` + commit baseline levou várias tentativas (lock files travados).
- Python canônico: `C:\Users\Yuri_\AppData\Local\Programs\Python\Python310\python.exe`.
- Deps faltantes instaladas: `kagglehub`, `great-expectations`, `jellyfish`, `opentelemetry-*`,
  `prometheus-client`, `uvicorn`, `python-multipart`. Já vinham instalados: pandas, numpy, sklearn,
  networkx, xgboost, shap, mlflow, fastapi, langgraph, streamlit, duckdb, faker.
- Dataset Olist (Kaggle) **não disponível** — precisa login interativo, não dá neste ambiente.
  Todo o código foi construído para degradar graciosamente sem ele (ADR-009). `make download-olist`
  pode ser rodado localmente pelo usuário depois, com conta Kaggle, para somar o dataset real.
- Dados sintéticos gerados (`make seed` / `generate_all.py --profile local`): 10.500 clientes CRM
  (500 duplicatas propositais), 20.000 interações de marketing, 2.000 tickets de suporte, 50.000
  eventos web, 10.000 pagamentos, 4 documentos de política.
- `git init` + branch `main` + commit baseline `aca0f8d` — snapshot do estado antes desta sessão.

### Incidente: 6 agentes paralelos derrubados por limite de sessão
Disparei os 6 work-packages (WP1-WP6) simultaneamente; todos morreram em segundos por
"session limit · resets 2pm (America/Sao_Paulo)" — nenhum arquivo foi salvo. Diagnóstico: o limite
parece ser de **concorrência** de sessões paralelas, não bloqueio total da conta (o turno principal
continuou funcionando normalmente). Solução adotada: disparar os WPs **um de cada vez**
(sequencial), não mais em lote. Nenhum retrabalho foi necessário além de reiniciar os WPs do zero
(estavam todos em fase de leitura/exploração, nada tinha sido escrito ainda).

---

### WP1 — Lakehouse (Bronze/Silver) + Data Quality — ✅ CONCLUÍDO

**Arquivos criados:**
- `lakehouse/bronze/{common,crm,marketing,support,web,finance,olist}.py` + `__init__.py`
- `lakehouse/silver/{common,crm_customer,support_ticket,web_event,campaign_interaction,payment_finance}.py` + `__init__.py`
- `data_quality/expectations/{crm_customer,support_ticket,web_event,campaign_interaction,payment_finance}.py` + `__init__.py`
- `data_quality/validators/{engine,quarantine,report}.py`
- `lakehouse/run_pipeline.py` (entrypoint único Bronze→Silver→DQ)
- READMEs de `lakehouse/` e `data_quality/` corrigidos (descreviam PySpark/GX-only; arquitetura real é pandas-primário, GX opcional)

**Como rodar:** `python lakehouse/run_pipeline.py`

**Métricas reais (última execução):**

| Tabela | Linhas | Score DQ | Quarentena | Taxa quarentena |
|---|---|---|---|---|
| crm_customer | 10.500 | 99.67% | 116 | 1.10% |
| support_ticket | 2.000 | 99.86% | 28 | 1.40% |
| web_event | 50.000 | 99.87% | 571 | 1.14% |
| campaign_interaction | 20.000 | 99.87% | 228 | 1.14% |
| payment_finance | 10.000 | 99.90% | 102 | 1.02% |
| **PLATAFORMA GERAL** | | **99.83%** | | |

Quarentena verificada como funcional de ponta a ponta: os 116 registros CRM quarentenados são
exatamente os que falham `valid_phone` (taxa suja de 1% proposital); as quarentenas downstream
(28/571/228/102) são cascatas de `referential_integrity` — linhas cujo `customer_id` apontava para
um cliente CRM já quarentenado. `email` ausente (~2%) é regra soft (pontuada, não quarentenada);
`phone` inválido (~1%) é hard (quarentenado), para provar o mecanismo contra um defeito conhecido.

---

### Notebooks 01-06 (existentes) — ✅ EXECUTADOS DE PONTA A PONTA

Todos os 6 notebooks já tinham lógica real (não eram stubs) mas nunca tinham rodado (0 outputs).
Corrigi a dependência rígida do Olist nos notebooks 01 e 06 (que faziam `raise FileNotFoundError`
se o Olist não existisse) para degradar graciosamente com fallback nos dados sintéticos, e executei
todos com `jupyter nbconvert --execute --inplace`.

- **01_data_quality_overview.ipynb** — corrigido (`HAS_OLIST` flag, fallback para CRM-only) e executado. 72KB de output real (gráficos incluídos).
- **02_entity_resolution_golden_record.ipynb** — executado sem alteração (autocontido). Resultado real: Recall 100% (500/500), Precisão 8,8% (5.711 pares previstos, 500 corretos), F1 16,1% — matching ingênuo determinístico+fuzzy por groupby de cidade/estado gera muitos falsos positivos; é exatamente o motivo da camada ML em `mdm/` (ver WP2 abaixo, que atinge 96,9% de precisão).
- **03_churn_model_explainability.ipynb** — executado sem alteração.
- **04_customer_segmentation.ipynb** — executado sem alteração.
- **05_customer_graph_analysis.ipynb** — executado sem alteração.
- **06_platform_kpis_dashboard.ipynb** — reescrito com fallback sintético completo (Revenue/Orders/AOV via `finance/customer_payments.csv` no lugar de pedidos Olist) e executado. Resultado real: Revenue R$ 15.666.556, Orders 9.324 (pagamentos liquidados como proxy), DQ score compacto 97,2%.

**Como reproduzir:** `jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb`

*(Nota: 02, 04 e 05 serão re-executados na fase de integração final para também mostrar os módulos
de produção reais de `mdm/`, `ml/`, `graph/` construídos pelos WPs, não só a versão local ingênua.)*

---

### WP2 — MDM (Entity Resolution + Golden Record) + Grafo de Clientes — ✅ CONCLUÍDO

**Arquivos criados:**
- `mdm/matching/{deterministic,fuzzy,ml_model}.py`
- `mdm/survivorship/rules.py`
- `mdm/golden_record/build.py` + `mdm/golden_record/survivorship_log/survivorship_log.csv`
- `mdm/entity_resolution/run.py` + `mdm/entity_resolution/evaluation/evaluate.py`
- `graph/networkx/build_graph.py`
- `graph/algorithms/{centrality,components,community}.py`
- `graph/queries/duplicate_clusters.md`
- READMEs de `mdm/` e `graph/` atualizados com seções de resultados reais

**Como rodar:** `make mdm` (já apontava para o entrypoint certo) · `python graph/networkx/build_graph.py` · `python graph/algorithms/{centrality,components,community}.py` · `mlflow ui --backend-store-uri ./mlflow/mlruns --port 5000`

**Métricas reais (10.384 linhas Silver, 495/500 pares do ground truth presentes):**
- Pipeline completo vs. ground truth: **Recall 1.0000** (meta ≥0.85 ATINGIDA), **Precisão 0.9687**, **F1 0.9841** (16 falsos positivos, coincidências raras de `document_hash`).
- ML vs. baseline fuzzy (conjunto completo de 6 features): ambos batem 1.000/1.000/1.000 — dataset não perturba telefone/endereço nas duplicatas, então essas features ficam quase determinísticas. Comparação mais honesta (ablação só nome+email, caso mais difícil): baseline 0.974/1.000/0.987 vs. RandomForest **0.980/1.000/0.990**.
- **Achado real que mudou o design:** matching só por email exato é não-confiável neste volume — o pool de emails do Faker `pt_BR` colide tanto que **0 de 505** matches só-por-email eram duplicatas reais de fato, contra 495/511 (97%) via telefone/document_hash. `deterministic.py` foi ajustado para não fundir automaticamente matches só-por-email, deixando isso para as camadas fuzzy+ML.
- **Achado do grafo:** pipeline já tem recall 1.0, então o grafo não achou nenhum cluster que o ML perdeu. O achado real vai na direção contrária: connected-components ingênuo **super-agrupa** (865 componentes multi-cliente; 368 são puramente coincidência de email do Faker, 0% taxa real de duplicata). Exemplo concreto com IDs reais em `graph/queries/duplicate_clusters.md`.

---

### WP3 — ML (Features, Churn, Segmentação, SHAP) — ✅ CONCLUÍDO

**Arquivos criados:**
- `ml/features/{entity_map,rfm,engagement,support,build_features}.py` → `data/ml/features/customer_features.parquet` (9.875 linhas, 9 features, construído a partir do `data/mdm/golden_record.parquet` do WP2, então duplicatas já colapsam num único cliente)
- `ml/churn/{label,train}.py`
- `ml/explainability/shap_analysis.py`
- `ml/segmentation/kmeans_segments.py` → `data/ml/segmentation/customer_segments.parquet`
- `ml/README.md` atualizado com seções Status/Results

**Como rodar:**
```bash
python -m ml.features.build_features
python -m ml.churn.train
python -m ml.explainability.shap_analysis
python -m ml.segmentation.kmeans_segments
```

**Rótulo de churn (`ml/churn/label.py`):** não existe evento de churn real nos dados sintéticos, então
foi construído um proxy documentado — score de risco ponderado (z-score de desengajamento 0.45,
flag de ticket não resolvido 0.25, flag de sentimento negativo 0.15, flag de não-compra 0.15) +
ruído gaussiano injetado (std=0.5), limiar no top 15%. O ruído importa: sem ele, um ensemble de
árvores reconstrói o rótulo trivialmente a partir das próprias features que o definem (ROC-AUC≈1.0,
sem sentido). Com ruído, os resultados são realistas e diferenciados.

**Métricas reais (experimento MLflow `churn_model`, `file:./mlflow/mlruns`):**

| Modelo | ROC-AUC | F1 | PR-AUC | Brier |
|---|---|---|---|---|
| Logistic Regression (campeão) | 0.882 | 0.531 | 0.657 | 0.0817 |
| Gradient Boosting | 0.880 | 0.509 | 0.648 | 0.0827 |
| Random Forest | 0.876 | 0.506 | 0.644 | 0.0827 |

Campeão registrado como `churn_model` v1, promovido a `Staging`.

**SHAP real (3 clientes de maior risco, IDs e números reais):**

| Cliente | P(churn) | Maior contribuição | 2ª | 3ª |
|---|---|---|---|---|
| MC00003652 | 0.9984 | +0.7050 dias desde última atividade=180 | +0.1423 tickets não resolvidos=2 | +0.0175 tickets=3 |
| MC00003135 | 0.9930 | +0.8236 dias desde última atividade=184 | +0.0497 tickets não resolvidos=1 | -0.0052 eventos=0 |
| MC00006078 | 0.9858 | +0.7868 dias desde última atividade=160 | +0.0600 tickets não resolvidos=1 | +0.0073 recência=367d |

**Distribuição real de segmentos (KMeans k=5, sem colapso >90%):**

| Segmento | Clientes | % |
|---|---|---|
| Loyal | 2.802 | 28.4% |
| VIP | 2.622 | 26.6% |
| Potential | 2.177 | 22.0% |
| Inactive | 1.677 | 17.0% |
| At Risk | 597 | 6.0% |

---

### Achado ambiental importante — LLM Gateway sem credenciais reais

`agents/llm_gateway/router.py` (já existente antes desta sessão) tem os adaptadores
`_complete_openai_compatible()` e `_complete_gemini()` como **stubs intencionais** — retornam
`""`, com TODO explícito "wire the real client (Sprint 14 extension)". Não há `.env` configurado
neste ambiente (só `.env.example`) e nenhuma API key de OpenAI/Azure OpenAI/Gemini/DeepSeek/
Anthropic está disponível aqui. Consequência prática: qualquer demo de agente que dependesse de
raciocínio LLM ao vivo não vai gerar texto real neste ambiente. Decisão: os notebooks/dashboard de
Agentes/MCP vão demonstrar as partes que **não** exigem LLM (chamadas de ferramenta MCP retornando
dados reais, fila de aprovação human-in-the-loop, heurísticas de intent detection) e documentar
claramente que o passo de raciocínio LLM é um TODO que o usuário pode ligar depois com uma API key
real — nunca fingir uma resposta de LLM que não aconteceu de verdade.

### ⚠️ Incidente — WP4 morreu silenciosamente sem notificar

Disparado em background, ficou "rodando" por várias horas sem produzir nenhum arquivo em
`snowflake/`, `dbt/models/` ou `powerbi/` e sem nunca enviar notificação de conclusão/falha.
`TaskOutput` não encontra mais o task-id (`a40d4bff33201fff9`) — o agente foi perdido pelo sistema
de tracking, não só travado. Só percebi porque o usuário pediu pra verificar. Ação: relançado do
zero, solo, com o mesmo prompt. Lição: depois de disparar um agente em background, não confiar só
na notificação — usar um watchdog (checagem programada) pra detectar silêncio prolongado.

### ⚠️ Incidente 2 — retry do WP4 também sumiu, mais o processo Claude Code inteiro foi interrompido

O relançamento solo do WP4 também não produziu nenhum arquivo. Além disso, o processo inteiro do
Claude Code foi interrompido/reiniciado entre uma mensagem e outra (o relógio pulou de
2026-08-14 10:06 para 2026-08-21 13:55 — quase uma semana de diferença real). Verificado: os
outputs de WP1/WP2/WP3 continuam intactos em disco (`data/lakehouse/silver/*.parquet`,
`data/mdm/*.parquet`, `data/ml/**/*.parquet`) — nada foi perdido além do próprio WP4, que nunca
chegou a escrever nada nas duas tentativas. Suspeita: o prompt pedia pra tentar `pip install
dbt-core`/`dbt-duckdb` como "nice-to-have", e isso pode ter travado numa instalação pesada no
drive lento. Ação: dividir o WP4 em duas partes menores (4a: DDL Snowflake + runner DuckDB local —
a parte crítica/provável; 4b: dbt + Power BI, sem nenhuma tentativa de pip install) e proibir
explicitamente qualquer instalação de pacote nas duas.

### Versionamento — ✅ v2.0.0 criada

Rodada de versionamento formal, seguindo Keep a Changelog (já era a convenção do `CHANGELOG.md`):
- `pyproject.toml`: `0.1.0` → **`2.0.0`** (marco: primeira implementação real de código, saindo de
  "só especificação" — LGP/Lakehouse/DQ/MDM/Grafo/ML funcionando de ponta a ponta com métricas reais)
- `CHANGELOG.md`: nova entrada **[2.0.0]** (implementação real WP1-3 + notebooks executados) e
  **[1.2.0]** (gap analysis dos novos requisitos de mercado — ver abaixo)
- `ROADMAP.md`: novo **Sprint 17** (não-core, fecha gaps de mercado) com checklist de k8s/A2A/Bedrock/ADR-014
- `IMPROVEMENTS_AND_RESEARCH.md`: novo **§5** com gap analysis completo de `tributario.txt` + complemento do `add2.txt`

### Novos requisitos de mercado (usuário adicionou `tributario.txt` + complementou `add2.txt` em 2026-08-20/21)

Usuário colou dois postings de vaga reais em `tributario.txt` (Dados da Controladoria/Reforma
Tributária + "Dev Python + AI Agents + AWS" embutido) e complementou `add2.txt` com um post sobre
taxonomia de tipos de modelo de IA. Gap analysis completo em `IMPROVEMENTS_AND_RESEARCH.md §5`.

**Gaps reais identificados (nunca existiram no projeto antes):**
1. **Kubernetes** — zero manifests em qualquer lugar do projeto
2. **A2A (Agent2Agent protocol)** — agentes só conversam entre si por chamada Python direta/LangGraph, nunca por protocolo padronizado
3. **AWS Bedrock** — projeto escolheu Azure como nuvem principal; Bedrock nunca foi um provider no LLM Gateway
4. **Arquitetura Hexagonal (Ports & Adapters)** — já existe implicitamente na estrutura (`mcp/tools/`/`api/` como adapters ao redor de `mdm/`/`ml/`/`agents/`) mas nunca foi formalizada

**Decisão consciente de NÃO fazer:** não criar um dataset sintético fiscal/tributário — o dataset
de e-commerce/customer intelligence é mantido coerente; a disciplina de governança/LGPD/
rastreabilidade já demonstrada é o que uma vaga desse tipo realmente avalia, não um dataset de
imposto de brinquedo.

**Ação:** os 4 gaps reais viram **WP7** (fila, depois do WP4/5/6), buildável sem nenhuma credencial
nova (Bedrock fica no mesmo padrão stub-documentado dos providers já existentes) — usuário pediu
explicitamente "deixa tudo pronto, se precisar login/API faz tudo [o código], só anota o que sobra
pra mim".

### WP4 — Semantic Layer (dbt + Snowflake local/DuckDB + Power BI) — 🔄 RELANÇADO (3ª tentativa, dividido em 4a/4b)

### WP4a — Snowflake DDL + runner local DuckDB — ✅ CONCLUÍDO (3ª tentativa do WP4, dividido)

**Arquivos:** `snowflake/ddl/01..08_*.sql` (dim_customer, dim_date, dim_geography, dim_campaign,
fact_payments, fact_support_interactions, fact_campaign_interactions, fact_web_events),
`snowflake/local_runner.py` (constrói `data/warehouse/local.duckdb` a partir dos parquets reais,
ponte crm_customer_id→master_customer_id via `golden_record.source_customer_ids`),
`snowflake/views/{vw_customer_360,vw_revenue_by_month}.sql`,
`snowflake/semantic_views/customer_intelligence_semantic_view.sql` (DDL real de Semantic View,
rotulado "não executado, sem conta Snowflake real"), `snowflake/README.md` atualizado.

**Como rodar:** `python snowflake/local_runner.py`

**Métricas reais obtidas:**
```json
{
  "revenue": 15515805.42,
  "aov": 1751.79,
  "churn_rate": 0.5308,
  "repeat_rate": 0.4033,
  "clv": {"avg": 990.26, "min": 0.0, "max": 12740.27, "median": 245.8},
  "orders": "SKIPPED — precisa data/raw/olist (ausente)",
  "delivery_sla": "SKIPPED — precisa data/raw/olist (ausente)",
  "nps": "SKIPPED — não implementado em nenhuma camada ainda",
  "data_quality_score": "SKIPPED — pertence ao módulo data_quality/"
}
```
Desvios documentados honestamente: Revenue/AOV via `payment_finance` liquidado (não `fact_orders`,
que não existe sem Olist); Churn Rate usa proxy `recency_days > 90` (não o rótulo temporal real de
`ml/churn/`, que não persiste artefato em disco); CLV usa a fórmula canônica (AOV × frequência ×
(1−churn_score)). Nenhum `pip install`, `git` ou pasta fora do escopo foi tocado.

### WP4b — dbt models + Power BI semantic model/DAX/dashboard spec — ✅ CONCLUÍDO

**dbt:** `dbt/models/staging/{stg_crm_customer,stg_payment_finance,stg_support_ticket,stg_campaign_interaction,stg_web_event}.sql` + `_sources.yml`/`schema.yml`; `intermediate/{int_customer_bridge,int_customer_golden_record,int_payments_resolved,int_support_tickets_resolved,int_campaign_interactions_resolved,int_web_events_resolved}.sql` (fórmulas copiadas literalmente de `local_runner.py`); `marts/{dim_customer,dim_date,dim_geography,dim_campaign,fact_payments,fact_support_interactions,fact_campaign_interactions,fact_web_events}.sql` (espelho coluna-a-coluna do `snowflake/ddl/`) + `_metrics.yml` (MetricFlow, 5 métricas); `tests/assert_{churn_score_bounded,no_negative_settled_payments}.sql`.

**Power BI:** `powerbi/semantic_model/{model,dimensions,facts,relationships}.tmdl`; `powerbi/dax/measures.md` (DAX de Revenue/AOV/Churn Rate/Repeat Rate/CLV + 9 medidas de apoio, cada uma comparada lado a lado com a SQL do `local_runner.py`); `powerbi/dashboard/page_specs.md` (blueprint página-a-página: Executive Overview, Customer Intelligence, Operations — documentada como rasa, sem Olist —, Data Quality, ML, Platform Observability — a mais rasa, sem telemetria em disco).

**Checagem de consistência (as 3 implementações do semantic layer batendo, ADR-005):**

| Métrica | Fórmula | Valor |
|---|---|---|
| Revenue | `SUM(net_amount) WHERE status='settled'` | R$ 15.515.805,42 |
| AOV | `SUM(gross_amount)/COUNT(DISTINCT payment_id) WHERE status='settled'` | R$ 1.751,79 |
| Churn Rate | `COUNT(recency_days>90)/COUNT(frequency>=2)` | 0,5308 |
| Repeat Rate | `COUNT(frequency>=2)/COUNT(frequency>=1)` | 0,4033 |
| CLV | `AVG(dim_customer.lifetime_value)` | R$ 990,26 |

Sem execução real de dbt/pip (só correção estrutural, conforme restrição desta rodada); nenhum arquivo fora do escopo tocado. **WP4 (dbt+Snowflake+PowerBI) está oficialmente concluído**, na terceira tentativa, dividido em 4a+4b.

### WP5 — RAG (parsing/embeddings/evaluation) + API FastAPI — ✅ CONCLUÍDO

Caiu de novo pelo limite de sessão da conta (reset 16h40 SP) bem perto do fim, mas já tinha escrito
quase tudo em disco (comprovado pelos `.pyc` compilados e pelo `precision_at_k_results.json` real).
Eu mesmo completei a verificação final que faltou (boot real da API, curl nos endpoints).

**Arquivos:** `rag/parsing/load_documents.py`, `rag/embeddings/{embedder,ingest}.py`,
`rag/evaluation/{golden_questions,precision_at_k}.py` + `precision_at_k_results.json`;
`api/{main.py, routes/{customer,metrics,health}.py, schemas/{customer,metrics}.py, services/{customer_service,metrics_service}.py}`.

**Métrica real de RAG:** precisão@3 = **1.0** (15/15 perguntas do golden set batem no documento certo — meta era ≥0.8). Exemplo real: "How many days does a customer have to request a refund after delivery?" → recupera `refund_policy-3`/`refund_policy-1` corretamente (scores 0.71/0.69).

**API testada por mim, ao vivo (`uvicorn api.main:app`):**
- `GET /health` → `{"status":"ok",...}`
- `GET /metrics` → mesmos valores reais do WP4 (Revenue R$15.515.805,42, AOV R$1.751,79, Churn Rate 0,5308...), com Orders/Delivery SLA/NPS/DQ score explicitamente `SKIPPED` com motivo
- `GET /customer/MC00000000` → `{"canonical_name":"Brenda Alves","city":"Curitiba","state":"PR",...,"found":true}`
- `GET /customer/duplicates` → 1.016 pares candidatos, paginados

`rag/README.md` e `api/README.md` já tinham a seção "Status: implemented" escrita antes da queda.

### WP6 — Terraform validate/fix + Governança/Versioning gaps — ⏳ NA FILA

### WP7 — Kubernetes + A2A protocol + AWS Bedrock provider + ADR-014 (Sprint 17, gaps de mercado) — ✅ CONCLUÍDO

Rodado em paralelo com o WP6 (dois agentes solo simultâneos, escopos disjuntos — funcionou sem problema).

- **`k8s/`**: Dockerfiles + Deployment/Service pra api/mcp/dashboard, `k8s/README.md`. `kubectl` existe
  (Docker Desktop) mas sem cluster/context configurado — `kubectl apply --dry-run=client` falhou na
  discovery do API server (documentado honestamente, erro real colado no README). Fallback real
  rodado: checagem estrutural via Python/PyYAML de todos os 6 manifests → `ALL MANIFESTS
  STRUCTURALLY VALID`. Limitação real documentada: `mcp/server/server.py` usa stdio transport do
  FastMCP, que não cabe num Pod sem terminal anexado — sinalizado como follow-up, não escondido.
- **`agents/a2a/`**: AgentCard + servidor A2A (`/.well-known/agent.json`, `POST tasks/send`)
  envolvendo (não reimplementando) os 4 agentes existentes. **Provado ao vivo**: subiu o servidor,
  chamou `/agents`, discovery de cada agente, e `tasks/send` nos 4 (orchestrator/quality/
  recommendation/monitoring) — todos retornaram `"state":"completed"` com output real de cada
  agente (o de recommendation chegou a enfileirar um item `PENDING` de verdade na approval_queue).
- **`agents/llm_gateway/`**: `_complete_bedrock()` adicionado ao `router.py`, mesmo padrão de stub
  documentado dos outros providers; `bedrock-claude-3-5-sonnet` em `models.yaml` (sem virar default,
  consistente com Azure como nuvem principal). Nenhum `boto3` instalado (stub não precisa).
- **`docs/decisions/ADR-014-hexagonal-architecture.md`**: formaliza Ports & Adapters, confirmado
  lendo `api/services/customer_service.py` e `mcp/tools/customer.py` — direção de dependência
  correta (adapters leem artefatos do core, nunca o contrário).
- `ROADMAP.md`: Sprint 17 com as 4 caixinhas marcadas (k8s com ressalva honesta sobre falta de cluster).

**Sprint 17 (gaps de mercado do WP7) está oficialmente concluído.**

### WP6 — Terraform validate/fix + Governança/Versioning gaps — ✅ CONCLUÍDO

O agente morreu de novo (processo Claude Code interrompido no meio) mas tinha deixado bastante
progresso real em disco (evidenciado pelos diretórios `.terraform/` com providers baixados de
verdade). Eu mesmo terminei o que faltava diretamente.

**`terraform validate` — resultado real, um módulo por vez:**

| Módulo | Resultado |
|---|---|
| azure/resource_group, adls, data_factory, event_hubs, key_vault, networking, monitoring, openai (8) | ✅ Success (pelo agente) |
| databricks/workspace, clusters (2) | ✅ Success (pelo agente) |
| databricks/jobs, permissions, unity_catalog (3) | ✅ Success (eu, direto) |
| snowflake/roles, warehouse (2) | ✅ Success (eu, direto) |
| snowflake/databases (1) | ✅ Success (eu, direto) |
| snowflake/schemas, grants, stages, semantic (4) | ⚠️ Rede caiu no meio (DNS parou de resolver até google.com/github.com — falha de conectividade do ambiente, não do Terraform) — validado por revisão manual: todas as variáveis passadas em `terraform/environments/dev/main.tf` batem exatamente com o que cada `variables.tf` declara, e todos os `module.X.output_name` referenciados existem no `outputs.tf` correspondente. Wiring confirmado correto. |

**Total: 20/20 módulos verificados** (16 via `terraform validate` real, 4 via revisão manual por
queda de rede). Nenhum erro de configuração encontrado em nenhum dos dois métodos.

**Wiring do `main.tf`:** confirmado que todos os módulos snowflake (`warehouse → databases →
schemas → roles → grants → stages → semantic`, com `depends_on` corretos) estão referenciados —
nenhum módulo órfão.

**Outros entregáveis:** `terraform/README.md` já tinha a seção "How to actually apply this for
real"; `docs/runbooks/slo.md` criado (55 linhas, metas de SLO por camada); `docs/deployment.md`
verificado. `ROADMAP.md` Sprint 16 — não confirmei se as caixinhas foram marcadas (verificar na
integração final).

### WP8 — Notebooks novos (07 RAG, 08 Agentes/MCP/A2A, 09 Terraform/Snowflake/Databricks) — ✅ CONCLUÍDO

Os 3 notebooks novos, todos executados de ponta a ponta com **0 erros**, usando os módulos de
produção reais (não reimplementações locais como os notebooks 01-06 antigos):

- **`07_rag_document_intelligence.ipynb`** (10 células) — pipeline RAG real completo (Docling →
  embeddings multilingues → ChromaDB), 4 consultas reais com scores, precisão@3 = 1.0 confirmada
  batendo com o resultado já salvo.
- **`08_agents_mcp_a2a_demo.ipynb`** (13 células) — MCP tools + Golden Record + DQ report lado a
  lado; fila de aprovação human-in-the-loop completa (enqueue→PENDING→APPROVED→EXECUTED, e o guard
  bloqueando `mark_executed()` sem aprovação); servidor A2A real subido via subprocess, testado nos
  4 agentes, encerrado limpo (confirmado via `netstat` que não sobrou nada na porta 8020).
- **`09_terraform_snowflake_databricks_walkthrough.ipynb`** (15 células) — `local_runner.py` rodado
  ao vivo (2,6s), HCL real do Terraform mostrado, e a prova mais forte do projeto: extrai a
  definição de Revenue das 3 implementações do semantic layer (dbt/Snowflake Semantic View/DAX) e
  confirma programaticamente que o valor calculado bate nas três → **Match: True**.

Todos os notebooks têm células markdown honestas distinguindo real/ao-vivo vs.
documentação-como-código (sem conta de nuvem) vs. stub assumido (sem chave de LLM) — nenhuma
resposta de LLM ou conexão de nuvem fingida em lugar nenhum.

**RESUMO: WP1 até WP9 estão TODOS concluídos.** Faltam só as etapas finais de integração (abaixo).

### WP9 — Dashboard Streamlit (6 páginas, dados reais em runtime) — ✅ CONCLUÍDO

**Arquivo:** `dashboard/app.py` (863 linhas) + `dashboard/README.md`.

**Como rodar:** `python -m streamlit run dashboard/app.py`

**Verificação real:** boot do servidor + curl HTTP 200 + `/_stcore/health` ok; validado também via
`streamlit.testing.AppTest` (executa o script de verdade contra cada página) — **as 6 páginas
rodaram sem exceção nenhuma**. Processo encerrado com `taskkill` e porta 8501 confirmada livre
(sem repetir o vazamento de processo órfão que já aconteceu antes nesta sessão).

**As 6 páginas, tudo lido ao vivo (nada hardcoded):**
1. Executive Overview — KPIs + receita mensal + segmentos, via `snowflake/local_runner.py`
2. Customer Intelligence — RFM, churn/CLV, top-20 CLV, estatísticas reais de MDM
3. Operations — tickets, campanhas (documentado honestamente como raso sem Olist)
4. Data Quality — score geral/por tabela/por regra + quarentena, direto do `dq_report.json`
5. ML — comparação de modelos de churn (lida do MLflow real), SHAP ao vivo contra o modelo campeão registrado, distribuição de segmentos
6. Platform Observability — precision/recall/F1 do MDM (recalculado ao vivo), precision@k do RAG, contagens Silver, caixa honesta "real vs. simulado"

Um bug real pego e corrigido durante o teste: contagem de linhas Silver via `pd.read_parquet(columns=[])` retornava 0 silenciosamente — trocado por `pyarrow.parquet.ParquetFile(path).metadata.num_rows`.

Ambos disparados em paralelo (escopos disjuntos: notebooks/ vs dashboard/). Rede caiu durante o
WP6 — instruí os dois a nunca depender de rede, tudo offline contra arquivos locais.

### Documentação e versionamento (eu, direto) — ✅ PARCIAL

O WP7 já tinha escrito sozinho a análise de gap do `tributario.txt`+`add2.txt` em
`IMPROVEMENTS_AND_RESEARCH.md §5` (seguindo o padrão do §4 já existente) — não precisei duplicar.
Encontrei e corrigi uma inconsistência de versionamento semântico no `CHANGELOG.md` (uma entrada
tinha sido numerada "1.2.0" depois da "2.0.0" já publicada, retrocedendo o número — renumerada pra
2.2.0). Adicionei a entrada `[2.1.0]` que faltava (WP4+WP5+WP6 nunca tinham sido documentados no
changelog). `pyproject.toml` version bump: 2.0.0 → 2.2.0. Falta ainda: `git commit` de tudo isso
(pendente até WP8/WP9 terminarem, pra commitar tudo junto no final).

### Suíte de testes ativada de verdade (eu, direto) — ✅ CONCLUÍDO

3 dos 4 testes em `tests/data/` estavam marcados como stub (`pytest.skip("Sprint N — not yet
implemented")`) desde a especificação original — mas o que eles pediam já existia agora. Ativados:

- **`test_dq_quarantine.py`** — roda `lakehouse.run_pipeline.run()` de verdade e verifica o
  critério de aceite do Sprint 3 completo: regra `valid_phone` falha, linhas vão pra quarentena,
  nenhuma linha desaparece (quarentena+silver = total), `dq_report.json` reflete a queda de score.
- **`test_metric_parity.py`** — versão honesta e escopada do critério do Sprint 8: roda
  `snowflake/local_runner.py` ao vivo e confere que bate com os valores documentados em
  `dbt/models/marts/_metrics.yml` E `powerbi/dax/measures.md`, pros 5 metrics (revenue/aov/
  churn_rate/repeat_rate/clv). Documentado no docstring que isso é um proxy local do teste completo
  (fan-out de 3 sistemas de nuvem ao vivo), não a coisa inteira — sem fingir ter mais do que tem.
- **`test_gold_snowflake_parity.py`** — não dava pra implementar de verdade (exige Databricks E
  Snowflake reais simultâneos, que não existem aqui) — mas troquei o skip incondicional por um
  `skipif` condicionado a `DATABRICKS_HOST`/`DATABRICKS_TOKEN`/`SNOWFLAKE_ACCOUNT`, pra ativar
  sozinho no dia que o usuário configurar credenciais reais, em vez de precisar editar código.

**Resultado: `pytest -v` → 7 passed, 1 skipped** (antes: 1 passed, 3 skipped).

### Integração final (eu, sem subagente) — ✅ CONCLUÍDO (o que dava pra fazer sem subagente)
- ~~Popular notebooks novos~~ → feito pelo WP8
- ~~Dashboard Streamlit~~ → feito pelo WP9
- Suíte de testes ativada (acima)
- CHANGELOG + versionamento + BUILD_LOG (feito)
- Falta: commit git final + guia de uso pro usuário (próximos passos)

---

## Pendências que só você pode resolver (nada disso me bloqueia — sigo trabalhando)

- **Dataset Olist real**: rodar `make download-olist` com sua conta Kaggle (login interativo) se
  quiser somar os dados reais de e-commerce por cima do que já é sintético. Tudo já degrada bem sem isso.
- **API keys de LLM** (`.env`, copiar de `.env.example`): sem `AZURE_OPENAI_API_KEY` / `OPENAI_API_KEY` /
  `GEMINI_API_KEY` / `DEEPSEEK_API_KEY`, os agentes não geram raciocínio LLM de verdade (os adaptadores
  em `agents/llm_gateway/router.py` são stubs — ver seção acima). Isso é esperado nesta sessão; não é
  um bug meu, é um TODO documentado do projeto desde antes de eu começar.
- **Power BI / Databricks reais**: você disse que vai conectar isso você mesmo depois via Claude/MCP.
  Deixei os artefatos (semantic model, DAX, DDL) prontos pra quando você fizer isso — não tentei
  provisionar nada de nuvem real aqui.
- **Terraform apply real**: nada foi aplicado em nuvem (sem credenciais Azure/Snowflake aqui, e não
  seria seguro fazer isso sem sua autorização explícita de qualquer forma). `terraform validate` sim,
  `apply` não.
- **Kaggle/GitHub/etc.**: nenhuma outra credencial externa é necessária pro resto do trabalho.

Qualquer outra coisa que eu não conseguir resolver sozinho, registro aqui em uma nova entrada
"⚠️ PRECISA DE VOCÊ" antes de seguir em frente, para você ver quando acordar.

## 2026-08-21 (continuação) — rede voltou, fechando pendências

Rede voltou (confirmado: `curl google.com` → 200). Usuário pediu pra reconferir add2.txt/
tributario.txt e ver o que mais dava pra inserir. Aproveitando a rede de volta:

- **Terraform**: os 4 módulos Snowflake que precisaram de revisão manual (schemas, grants, stages,
  semantic) foram revalidados de verdade agora — **20/20 módulos confirmados via `terraform
  validate` real**, zero precisando mais do fallback manual.
- **Olist**: tentativa de download automático falhou de novo (timeout esperando login interativo do
  Kaggle) — confirma que isso continua exigindo ação manual do usuário, não é algo que eu resolvo sozinho headless.
- **Classificador SLM local** (`agents/llm_gateway/README.md` §"LLM optimization" — backlog do
  add2.txt "otimização de LLMs/quantização"): próximo item sendo implementado agora — ver seção
  abaixo assim que terminar.

### Classificador SLM local de causa-raiz de DQ (eu, direto) — ✅ CONCLUÍDO

`agents/quality/root_cause_classifier.py` — implementação real e honestamente escopada do item de
backlog "otimização de LLM (quantização/fine-tuning)" do `add2.txt`, documentado em
`agents/llm_gateway/README.md`. Não é o distilbert fine-tuned+quantizado que o texto original do
backlog sugeria (desproporcional pro escopo) — é um classificador TF-IDF + Logistic Regression
genuinamente local, CPU-only, sem round-trip de rede, treinado nas 47 descrições **reais** do
catálogo de regras de `data_quality/expectations/` (10 classes, uma por tipo de regra) + poucas
paráfrases por classe pra dar sinal de treino suficiente. Resultado real (held-out): **75% de
acurácia, F1 macro 0,739** (baseline aleatório seria ~10%). Conectado em
`agents/quality/data_quality_agent.py::_recommend_action_for_cause()`, substituindo o
keyword-matching antigo, com fallback pro comportamento antigo se o classificador falhar.

### WP10 — Conectar `mcp/tools/*.py` (5 arquivos) aos dados reais — ✅ CONCLUÍDO

Todas as 5 ferramentas MCP religadas e testadas com dados reais, reaproveitando `api/services/` e
`snowflake/local_runner.py` (sem duplicar lógica):

- **`quality.py`**: `get_data_quality('crm_customer')` → score real 0,9967, dimensões reais
  (completeness 0,9925, validity 0,9972...). `get_customer_quality` liga golden_record↔quarentena
  (achado honesto: nenhum golden record tem hit de quarentena neste build, porque uma linha
  quarentenada nunca sobrevive até ser fundida — lógica correta, resultado esperado).
- **`customer.py`**: `get_customer`/`search_customers` reaproveitam `api/services/` direto (zero
  duplicação). `get_customer_graph`: o grafo persistido (`data/graph/customer_graph.gpickle`) não
  abre nesse ambiente (incompatibilidade de versão do networkx) — reconstruído em memória ao vivo
  como fallback, funcionando (4 nós, 3 arestas pra `MC00000000`).
- **`analytics.py`**: `get_sales_metrics('revenue')` → R$ 15.515.805,42 direto do `local_runner.py`.
  Métricas sem Olist (`order_count`/`nps`/`delivery_sla`) retornam `None` com motivo real, nunca inventado.
- **`ml.py`**: `get_customer_churn('MC00003652')` → carrega o modelo campeão REGISTRADO no MLflow
  (sem retreinar), SHAP ao vivo — bate exatamente com os números já registrados no BUILD_LOG pra
  esse cliente. `recommend_action` monta uma recomendação real (churn+CLV+segmento+suporte) —
  achado: `agents/recommendation/recommendation_agent.py::score_recommendation` continua sendo
  TODO stub, então a lógica composta vive direto em `ml.py` por enquanto (reaproveitando só o
  conjunto fechado `CANDIDATE_ACTIONS`).
- **`snowflake.py`**: `query_snowflake` executa SELECT validado contra o mesmo DuckDB local.

**Bug real achado e corrigido durante a integração**: `analytics.py` e `snowflake.py` cada um
chamava `build_warehouse(rebuild=True)` independentemente — DuckDB trava o arquivo pra conexão, e
o segundo rebuild quebrava no `unlink()`. Corrigido compartilhando uma única conexão cacheada.

**Pendência real que ficou registrada, não meu escopo de agora**: `recommendation_agent.py`'s
`score_recommendation` ainda é TODO stub — é o próximo item natural se quiser continuar fechando gaps.

## ✅ SESSÃO CONCLUÍDA — 2026-08-21

Commit final: `c0db5ec` (`git log --oneline -3` a partir do baseline `aca0f8d`). Versão: `2.2.0`
(`pyproject.toml` + `CHANGELOG.md`). Todos os 9 work-packages + integração final + suíte de testes
+ versionamento estão completos. Ver o resumo enviado ao usuário para o guia "como rodar tudo".

## Como continuar esta sessão se o contexto cair

1. Leia este arquivo do topo — cada seção "✅ CONCLUÍDO" já está validada e não precisa refazer.
2. Cheque `git log --oneline` para o commit baseline e quaisquer commits incrementais feitos depois.
3. Retome exatamente do primeiro item "⏳ NA FILA" ou "🔄 EM ANDAMENTO" acima.
4. Sempre disparar work-packages **um de cada vez** (não em paralelo) — ver "Incidente" acima.
