# ADR-013 — Memória de agente: curto prazo por thread, longo prazo por cliente, ambas rastreáveis

**Status:** Aceito
**Data:** 2026-08-11

## Contexto

`add2.txt` pede explicitamente agentes conversacionais "com memória de curto e longo prazo, garantindo rastreabilidade e personalização para o cliente." Hoje, `agents/orchestrator/customer_intelligence_agent.py` (LangGraph, Sprint 14) processa cada pergunta via seu `AgentState`, mas não há nenhum mecanismo que preserve contexto entre turnos de uma mesma conversa, nem entre sessões diferentes do mesmo cliente. Isso limita a personalização a "o que está nesta única pergunta" — sem lembrança de preferências, histórico de tickets ou padrões de interação anteriores.

Ao mesmo tempo, a plataforma já tem um padrão estabelecido para dados sensíveis de cliente: toda escrita precisa ser atribuível (survivorship log do Golden Record, `mdm/golden_record/survivorship_log/`) e toda ação consequente passa por aprovação humana rastreável (`agents/recommendation/approval_queue.py`, [ADR-006](ADR-006-human-in-the-loop.md)). Memória de agente sobre um cliente é dado pessoal na forma mais direta — precisa herdar essa mesma disciplina, não reinventar uma mais fraca.

## Decisão

Separar memória em dois módulos com escopo e ciclo de vida diferentes, ambos em `agents/memory/`:

1. **Curto prazo** (`short_term.py`) — buffer de conversa por `thread_id`, no mesmo papel que um LangGraph checkpointer (`MemorySaver` local, backend Postgres em produção) cumpriria. Efêmero por natureza; não é o alvo de um pedido de rastreabilidade LGPD porque não persiste além da sessão.
2. **Longo prazo** (`long_term.py`) — memória de interação por `master_customer_id`, construída **sobre `rag/local_stack/vector_store.py`** (a mesma abstração `VectorStore` já usada para RAG de documentos de política) em vez de um segundo banco vetorial paralelo — o problema ("armazenar e recuperar semanticamente texto embutido, escopado por dono") é o mesmo problema, resolvido uma vez ([ADR-011](ADR-011-local-rag-stack.md)). Em produção, o mesmo contrato é implementado sobre Snowflake/Cortex em vez de ChromaDB local.

**Rastreabilidade:** toda escrita em `long_term.py` exige um `source_interaction_id` não vazio — um ticket de suporte, um `thread_id` de conversa, um id de chamada de ferramenta MCP. Isso segue exatamente o padrão já usado por `approval_queue.py` (`approved_by`/`rejected_by` obrigatórios: "an anonymous approval is not an audit trail") e pelo survivorship log do Golden Record. Uma memória sem origem atribuível não é gravada — `LongTermMemoryError` é levantado.

**Deleção:** cada cliente tem sua própria coleção vetorial (`customer_memory__{master_customer_id}`), então um pedido de apagamento (LGPD Art. 18 IV) é uma operação localizada, não uma varredura cross-customer — o mesmo desenho que `governance/lgpd.md` já descreve para o Golden Record.

## Alternativas consideradas

1. **Um único módulo de memória, sem separar curto/longo prazo** — rejeitado: os dois têm ciclo de vida, escopo (thread vs. cliente) e requisito de rastreabilidade completamente diferentes; misturá-los tornaria a política de retenção (curto prazo efêmero vs. longo prazo com trilha de auditoria) ambígua.
2. **Um segundo banco vetorial dedicado a memória, separado do usado por RAG** — rejeitado: duplicaria a lógica de upsert/query/delete já resolvida em `rag/local_stack/vector_store.py`, violando ARCHITECTURE.md §1; a única diferença real é o nome da coleção (por cliente, não compartilhada).
3. **Gravar memória sem exigir atribuição de origem, adicionando rastreabilidade depois "se for preciso"** — rejeitado: o padrão já estabelecido pelo survivorship log e pelo `approval_queue.py` é atribuição obrigatória desde o primeiro write, não uma camada adicionada depois; enfraquecer esse padrão especificamente para memória de agente seria inconsistente com o restante da governança do projeto.

## Consequências

- Positivas: personalização real (o agente pode responder com base em interações passadas do cliente) sem introduzir um segundo sistema de armazenamento vetorial; toda memória de longo prazo é auditável e apagável por cliente, alinhado a LGPD Art. 18; reaproveita a interface `VectorStore` já testada por RAG, reduzindo superfície de bugs.
- Negativas: acoplamento entre `agents/memory/long_term.py` e `rag/local_stack/vector_store.py` significa que uma mudança de contrato na interface `VectorStore` afeta os dois consumidores — mitigado por manter essa interface deliberadamente pequena (`upsert`/`query`/`delete`) e estável; memória de curto prazo em processo (não persistida) hoje é perdida em um restart do processo — aceitável para o skeleton do Sprint 14, com o mesmo caminho de evolução (checkpointer real) já documentado no TODO do módulo.
