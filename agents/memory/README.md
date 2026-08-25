# agents/memory/

**Short-term + long-term conversational memory** — [ADR-013](../../docs/decisions/ADR-013-agent-memory.md), addressing the `add2.txt` requirement: "criar agentes conversacionais com memória de curto e longo prazo, garantindo rastreabilidade e personalização para o cliente."

```
agents/memory/
├── short_term.py   # LangGraph checkpointer-style conversation buffer, scoped per thread_id
└── long_term.py     # vector-store-backed customer interaction memory, scoped per master_customer_id
```

## Two different problems, two modules

| | `short_term.py` | `long_term.py` |
|---|---|---|
| Scope | One conversation thread (`thread_id`) | One customer, across all sessions (`master_customer_id`) |
| Lifetime | Ephemeral — cleared when the session ends | Durable — persisted in a vector store |
| Backing | In-process buffer today; the LangGraph checkpointer contract (`MemorySaver` locally, Postgres-backed in production) tomorrow | `rag/local_stack/vector_store.py`'s `VectorStore` (ChromaDB locally; a Snowflake/Cortex-backed store in production) |
| Answers | "What did the customer just say two turns ago?" | "What do we know about this customer from every past interaction?" — the personalization signal |

Long-term memory is deliberately built **on top of the existing RAG vector store abstraction**, not a second, parallel vector database — the underlying problem ("store and semantically retrieve embedded text, scoped to an owner") is the same one `rag/local_stack/vector_store.py` already solves for policy documents. `LongTermMemory` just uses a per-customer collection (`customer_memory__{master_customer_id}`) instead of the shared `policy_docs__rag` collection. See [ADR-011](../../docs/decisions/ADR-011-local-rag-stack.md) and [ADR-013](../../docs/decisions/ADR-013-agent-memory.md).

## Traceability (LGPD accountability)

Every `LongTermMemory.remember()` call requires a non-empty `source_interaction_id` — a support ticket id, a conversation `thread_id`, an MCP tool call id, anything that lets a later reviewer answer *"why does the platform believe this about the customer, and when did it learn it?"* This mirrors two patterns already established elsewhere in the platform:

- `mdm/golden_record/survivorship_log/` — every Golden Record field has a `{field, winning_source, rule_applied, timestamp}` trail ([governance/lgpd.md](../../governance/lgpd.md)).
- `agents/recommendation/approval_queue.py` — every approval/rejection requires a non-empty `approved_by`/`rejected_by`, "an anonymous approval is not an audit trail."

`long_term.py` applies the same discipline to memory writes: an anonymous or unattributed memory write is not accepted (`LongTermMemoryError`), for the same LGPD accountability reason.

## Deletion (LGPD Art. 18 IV)

`LongTermMemory.forget_customer(master_customer_id, memory_ids)` removes specific entries. Because memories are stored in a per-customer collection, a full-customer erasure request degrades cleanly to "delete that one collection" — the same one-point-of-truth deletion story [`governance/lgpd.md`](../../governance/lgpd.md) already describes for the Golden Record ("deletion is a pipeline re-run, not a manual multi-system hunt").

## Related

- [ADR-013 — Agent memory](../../docs/decisions/ADR-013-agent-memory.md)
- [`rag/local_stack/vector_store.py`](../../rag/local_stack/vector_store.py) — the shared `VectorStore` interface this module reuses
- [`governance/lgpd.md`](../../governance/lgpd.md) — the accountability standard this module's traceability requirement is consistent with
- [`agents/orchestrator/customer_intelligence_agent.py`](../orchestrator/customer_intelligence_agent.py) — the primary consumer of both memory types for multi-turn, personalized answers
