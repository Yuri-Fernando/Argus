# ADR-012 — LLM Gateway: roteamento multi-modelo em vez de acoplamento a um único provedor

**Status:** Aceito
**Data:** 2026-08-11

## Contexto

ARCHITECTURE.md §3 escolheu **LangGraph + Azure OpenAI** como stack de orquestração e raciocínio dos agentes — decisão que continua válida (integração nativa com Key Vault/Entra ID, alinhamento ao mercado-alvo). Porém, toda chamada de LLM na plataforma hoje pressupõe implicitamente um único provedor: não há mecanismo para avaliar se um modelo mais barato/rápido resolveria uma tarefa de classificação simples (ex: `detect_intent` do orquestrador) tão bem quanto GPT-4o, nem para comparar tecnicamente OpenAI/Gemini/DeepSeek em cenários reais de uso — competência explicitamente pedida em `add2.txt` ("experimentar e integrar diferentes LLMs... avaliando tecnicamente os cenários de uso e trade-offs de performance/custo").

Adicionar SDKs de múltiplos provedores sem um propósito estruturado violaria ARCHITECTURE.md §1 ("every tool solves one named problem") — o objetivo não é "ter todos os SDKs instalados", é ter uma forma real e testável de decidir qual modelo atende melhor cada tipo de tarefa.

## Decisão

Introduzir `agents/llm_gateway/` com uma interface única, `complete(prompt, task_type)`, que roteia para Azure OpenAI, OpenAI, Gemini ou DeepSeek conforme um registro declarativo (`models.yaml`) — provider, modelo, custo por 1M tokens, tier de latência e `task_type`s de melhor encaixe. Nenhum agente chama um SDK de provedor diretamente; todos passam por este gateway.

**Insight que evita duplicação de código:** Azure OpenAI, OpenAI e DeepSeek expõem uma API de chat completions **compatível com o formato OpenAI** — um único cliente HTTP (`openai` SDK, apontado para `base_url`s diferentes) atende aos três, sem exigir um SDK específico da DeepSeek. Gemini, com formato de API genuinamente diferente, recebe seu próprio adaptador.

O roteamento por `task_type` é o mecanismo concreto da avaliação de trade-off pedida: tarefas de classificação de alto volume e baixa dificuldade (ex: `intent_classification`) são roteadas para modelos baratos/rápidos (`azure-gpt-4o-mini`, `gemini-2.5-flash`); tarefas de raciocínio final (`final_reasoning`, `policy_qa`) permanecem no modelo mais forte disponível (`azure-gpt-4o`). Qualquer mudança no mapeamento `defaults` em `models.yaml` deve ser respaldada por uma execução do harness de avaliação (`agents/*/evaluation/`), não uma preferência não testada.

Otimização de LLM (quantização, fine-tuning) é tratada como **alavanca de custo documentada, não implementada** — ver `agents/llm_gateway/README.md` e o backlog em `IMPROVEMENTS_AND_RESEARCH.md`: substituir a chamada de classificação de categoria do Data Quality Agent por um classificador local pequeno, quantizado, é o exemplo concreto escolhido, mas implementá-lo agora inflaria o escopo do MVP sem um problema nomeado urgente — ver ARCHITECTURE.md §1.

## Alternativas consideradas

1. **Manter Azure OpenAI como único provedor, sem gateway** — rejeitado: não atenderia ao requisito explícito de `add2.txt` de experimentar e avaliar tecnicamente múltiplos LLMs; também deixaria a plataforma sem um caminho de fallback caso o deployment Azure fique indisponível ou rate-limited.
2. **Integrar cada provedor com seu próprio SDK dedicado, chamado diretamente de cada agente** — rejeitado: gera acoplamento espalhado (cada agente precisaria saber sobre credenciais/formatos de 4 provedores) e nenhum ponto único onde a decisão de trade-off custo/latência/qualidade é auditável — o objetivo explícito de `add2.txt` é demonstrar essa avaliação, não escondê-la.
3. **Implementar fine-tuning/quantização agora, junto com o gateway** — rejeitado nesta consolidação: seria escopo desproporcional a um portfólio (treinar, avaliar e servir um modelo quantizado é um projeto à parte); documentado como item de backlog priorizado com alvo concreto em vez de implementado às pressas.

## Consequências

- Positivas: um único ponto de auditoria para a decisão "qual modelo responde esta tarefa" (`models.yaml` + `router.py`); troca de provedor por tarefa é uma edição de registro, não uma reescrita de agente; demonstra avaliação técnica real de trade-off custo/latência/qualidade, não apenas integração de SDKs.
- Negativas: mais uma camada de indireção entre o agente e o provedor de LLM (mitigado por manter `complete()` como a única API pública, sem vazamento de detalhes de provedor para os chamadores); DeepSeek e Gemini têm histórico de garantias de disponibilidade/enterprise-support menos maduro que Azure OpenAI para um empregador-alvo regulado — mantidos como alternativas avaliadas, não como padrão, decisão registrada explicitamente em `models.yaml`'s notes.
