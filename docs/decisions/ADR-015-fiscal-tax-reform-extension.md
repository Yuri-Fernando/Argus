# ADR-015 — Extensão fiscal/tributária (Reforma Tributária) e pipeline VLM

**Status:** Aceito
**Data:** 2026-08-24

## Contexto

`IMPROVEMENTS_AND_RESEARCH.md` §5.1/§5.3 documentou dois gaps reais e deliberadamente deixados em
aberto na consolidação anterior: (1) nenhum caso de uso de VLM na plataforma — `rag/local_stack/
document_parser.py` só processava texto/PDF nativo, nunca imagem/scan; e (2) nenhum dado de
domínio fiscal/tributário, apesar de `tributario.txt` (requisitos de vaga do "time de Dados da
Controladoria", pauta explícita da Reforma Tributária) pedir exatamente isso. A decisão anterior
foi **não forçar** um dataset fiscal falso dentro da plataforma de e-commerce — "um dataset fiscal
de brinquedo dentro de uma plataforma de customer intelligence seria pior portfólio do que mostrar
a disciplina de governança/rastreabilidade transferível" (§5.1 original).

O usuário pediu explicitamente essa extensão nesta sessão, e observou (corretamente) que um
documento fiscal **escaneado** é exatamente o caso de uso que faltava para o VLM — o que muda o
cálculo: deixa de ser "tecnologia solta pra engordar a lista" (o anti-padrão que
`ARCHITECTURE.md §1` proíbe) e passa a ser uma peça de trabalho só resolvendo dois gaps
documentados ao mesmo tempo, com um pedido explícito e escopado pelo usuário (ver
`AskUserQuestion` desta sessão: dataset pequeno e focado, 100% sintético, integrado em RAG +
VLM + Data Quality + um novo agente).

## Decisão

### Dataset 100% sintético, auto-contido

`data/synthetic/generators/fiscal.py` gera `fiscal_documents.csv` (itens de nota fiscal
sintéticos com campos IBS/CBS/Imposto Seletivo da Reforma Tributária) seguindo exatamente o
padrão de `crm.py`/`finance.py` — função pura, seed determinística, `FiscalDirtyRates` injetando
três problemas nomeados (`invalid_ncm`, `cst_cfop_mismatch`, `rate_out_of_range`), companion
`fiscal_documents_ground_truth.csv` com o valor de referência correto. Os códigos NCM/CFOP/CST e
alíquotas usados são **aproximações ilustrativas**, documentadas como tal no módulo — este não é
um motor de cálculo fiscal certificado, é um dataset internamente consistente para as camadas de
DQ/RAG/VLM/agente validarem contra.

`fiscal_document` **não** entra em `lakehouse/run_pipeline.py::TABLE_ORDER` — é conceitualmente
uma família de tabela diferente da CRM/support/web/campaign/finance do e-commerce, então ganha seu
próprio runner pequeno (`data_quality/validators/fiscal_report.py`), reusando o mesmo `DQEngine` e
os mesmos 10 tipos de regra fechados (`data_quality/validators/engine.py`) — nunca um 11º tipo.

### VLM real, com degradação documentada

`rag/local_stack/document_parser.py::DoclingVlmDocumentParser` usa o `VlmPipeline` do Docling
(modelo padrão: IBM Granite-Docling-258M, pesos abertos, roda localmente — **sem exigir chave de
API paga**, ao contrário dos adapters de `agents/llm_gateway/router.py`). Diferente do padrão
"stub documentado" do LLM Gateway (que sempre retorna `""` até haver credencial real), este código
**tenta rodar de verdade** contra as imagens sintéticas escaneadas
(`data/synthetic/generators/fiscal.py::render_scanned_documents`), com falha isolada e explícita
(`VlmUnavailableError`) se o modelo não puder ser baixado/carregado — nunca finge um resultado.

> **Resultado real desta sessão** (testado ao vivo contra `data/documents/fiscal/NFE00000015_scan.png`,
> não estimado): o pipeline roda de ponta a ponta sem erro — baixa e carrega de verdade o modelo
> `ibm-granite/granite-docling-258M` (~258M parâmetros) via HuggingFace/`transformers`, sem exigir
> nenhuma credencial — mas a **qualidade da extração foi ruim**: o modelo entrou em um loop de
> repetição (`"Total de tributos:\n\nTotal de tributos:\n\n..."`), sem extrair o conteúdo real da
> página. Achado honesto adicional: o pipeline **padrão** do Docling para imagens (sem forçar
> `VlmPipeline`) usa **RapidOCR** — um motor de OCR tradicional, não um VLM — e leu o mesmo
> documento quase perfeitamente (todos os campos corretos, só artefatos leves de encoding em
> acentos). Ou seja: para este caso de uso específico (documento estruturado, texto plano, sem
> imagens/diagramas), OCR tradicional supera o VLM pequeno de propósito geral — uma conclusão de
> engenharia real, não um resultado inventado para "provar" que VLM funciona. `DoclingVlmDocumentParser`
> foi mantido usando o `VlmPipeline` de propósito (é a peça que demonstra literalmente a categoria
> "VLM" da taxonomia do `add2.txt`, não OCR), com esse resultado documentado sem retoque — a mesma
> disciplina de honestidade que rege o resto do projeto (ex.: a nota sobre ChromaDB não escalar
> além de ~1-5M vetores). `VlmUnavailableError` continua existindo para o caso de falha real
> (sem internet/modelo não baixado); saída de baixa qualidade não é esse caso — o pipeline não
> falhou, só produziu um resultado ruim, e a diferença importa para quem for debugar isso depois.

### Integração nos 4 pontos pedidos

| Ponto | Onde |
|---|---|
| RAG | 2 documentos de política novos (`reforma_tributaria_ibs_cbs.md`, `imposto_seletivo_visao_geral.md`) em `data/synthetic/generators/documents.py`, indexados na coleção `policy_docs__rag` já existente — reusa o `task_type="policy_qa"` já mapeado em `agents/llm_gateway/models.yaml`, nenhum `task_type` novo |
| VLM | `DoclingVlmDocumentParser` (acima), roteado por `agents/knowledge_ingestion/agent.py::classify_source()` para `.png`/`.jpg`/`.jpeg` |
| Data Quality | `data_quality/expectations/fiscal_document.py` + `data_quality/validators/fiscal_report.py` |
| Agente | `agents/fiscal/root_cause_agent.py` (função pura + dataclass, padrão do Data Quality Agent) + `agents/fiscal/tax_discrepancy_classifier.py` (classificador local TF-IDF+LogReg, mesma técnica e mesmo honest-scope de `agents/quality/root_cause_classifier.py`) |

## Alternativas consideradas

1. **Usar um dataset fiscal público real (anonimizado)** — rejeitado: não existe uma fonte pública
   de notas fiscais brasileiras anonimizada apropriada para uso em portfólio sem risco de
   vazamento de dado real ou violação de termos de uso; o valor demonstrado (disciplina de DQ/
   rastreabilidade/agente) não depende de o dado ser real, só de ser internamente consistente e
   verificável.
2. **Construir um motor de cálculo fiscal certificado (regras completas da Reforma Tributária)** —
   rejeitado: desproporcional ao escopo de portfólio, e a legislação/regulamentação da reforma
   ainda está em curso em 2026 — qualquer implementação "completa" ficaria desatualizada rápido.
   O dataset documenta explicitamente que suas fórmulas são ilustrativas, não uma fonte de
   verdade legal.
3. **Forçar `fiscal_document` para dentro de `lakehouse/run_pipeline.py::TABLE_ORDER`** —
   rejeitado: a família de tabelas do e-commerce (CRM/support/web/campaign/finance) tem uma
   dependência real e específica (`crm_customer` roda primeiro, alimenta referential_integrity das
   demais); forçar o domínio fiscal para dentro dessa mesma ordem só para reusar o runner
   principal acoplaria dois domínios sem necessidade real — um runner pequeno e dedicado é mais
   simples e não menos real.
4. **Fine-tuning/quantização de um VLM próprio em vez do modelo pré-treinado do Docling** —
   rejeitado pela mesma razão documentada em `agents/quality/root_cause_classifier.py`'s "HONEST
   SCOPE NOTE": desproporcional a um projeto de portfólio: o modelo pré-treinado do Docling já
   demonstra o uso real de VLM sem exigir um pipeline de treino que ninguém validaria como
   correto sem dados rotulados de verdade.

## Consequências

- Positivas: fecha dois gaps documentados (VLM, domínio fiscal) com uma única peça de trabalho
  coerente; reusa 100% dos padrões e da infraestrutura já existentes (DQEngine, VectorStore,
  MCP tools, agente no padrão Data Quality Agent) — zero tipo de regra novo, zero framework novo;
  todo o dataset é sintético e determinístico, sem risco de PII ou dado fiscal real.
- Negativas: mais uma dependência opcional (`pillow`, em `genai-extra`) para a geração das imagens
  escaneadas; o pipeline VLM do Docling baixa um modelo real (~258M parâmetros) na primeira
  execução, o que exige internet e alguns minutos na primeira chamada — documentado, não
  escondido, com degradação explícita (`VlmUnavailableError`) se isso falhar; o domínio fiscal
  fica fora de `TABLE_ORDER`, então não se beneficia automaticamente de qualquer evolução futura
  do pipeline principal (ex. um dashboard Power BI dedicado precisaria de trabalho extra para
  incluir esta tabela); e, achado honesto do teste real, o modelo VLM pequeno padrão produziu
  saída de baixa qualidade (loop de repetição) no documento sintético de teste — o OCR tradicional
  do próprio Docling (não-VLM) leu o mesmo documento melhor, uma limitação real de modelos VLM
  pequenos em documentos de texto plano/estruturado, documentada acima em vez de escondida ou
  contornada com um exemplo escolhido a dedo.
