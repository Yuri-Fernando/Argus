# agents/knowledge_ingestion/

**The Agno-based agent** — [ADR-011](../../docs/decisions/ADR-011-local-rag-stack.md), addressing `add2.txt`'s "desenvolver agentes autônomos inteligentes utilizando frameworks modernos como LangChain e Agno, criando fluxos que combinem múltiplas ferramentas" and "usar web scraping (Crawl4AI) e parsing de documentos complexos (Docling) para alimentar pipelines de conhecimento."

```
agents/knowledge_ingestion/
└── agent.py   # KnowledgeIngestionAgent — autonomously picks Crawl4AI / Docling / static-read per source
```

## Why this agent, and why Agno

The four agents in [ARCHITECTURE.md §15](../../ARCHITECTURE.md#15-layer-12--mcp--agentic-ai) are all LangGraph, because they all share one requirement: an explicit state machine with a human-in-the-loop gate (ADR-006) before any consequential action. The Knowledge Ingestion Agent has a **different** job — deciding, per knowledge source, which extraction tool solves it (a live URL needs Crawl4AI; a complex local PDF/DOCX needs Docling; the existing synthetic Markdown policy files need neither) and orchestrating the pipeline end-to-end. That is a multi-tool composition problem, not a state-machine-with-approval problem, so it is built with **Agno** instead — genuine framework breadth, not a redundant reimplementation of an agent that already exists. See [ADR-011](../../docs/decisions/ADR-011-local-rag-stack.md)'s "LangChain vs. Agno vs. LangGraph" section for the full comparison table.

This agent never calls `agents/recommendation/approval_queue.py` — ingesting a document chunk into the knowledge base is not a customer-facing consequential action under [ADR-006](../../docs/decisions/ADR-006-human-in-the-loop.md), unlike a merge, refund, or retention offer.

## What it does

`KnowledgeIngestionAgent.ingest(sources)` takes a list of `KnowledgeSource` (a URL or file path) and, for each one:

1. `classify_source()` decides the `SourceKind` — `LIVE_URL`, `COMPLEX_DOCUMENT`, or `STATIC_FILE`.
2. Routes to the matching tool: [`rag/local_stack/crawler.py`](../../rag/local_stack/crawler.py) (Crawl4AI), [`rag/local_stack/document_parser.py`](../../rag/local_stack/document_parser.py) (Docling), or a direct file read.
3. Writes the result into the shared [`rag/local_stack/vector_store.py`](../../rag/local_stack/vector_store.py) `VectorStore` — the same index `agents/orchestrator/` queries at answer time and `agents/memory/long_term.py` reuses for customer memory.

## Why the dispatch is explicit today

`agent.py`'s `ingest()` calls `classify_source()` and dispatches directly, rather than letting Agno's own LLM-driven tool-selection loop decide — this keeps the module's behavior deterministic and unit-testable (`classify_source` is a pure function, same pattern as `agents/recommendation/recommendation_agent.py`'s `score_recommendation`) while the underlying Agno `Agent(tools=[...])` wiring is completed. The TODO in `KnowledgeIngestionAgent.__init__` marks exactly where the explicit dispatch is replaced by Agno's own reasoning loop over the same three tool functions — the tool implementations don't change, only who decides to call them.

## Related

- [ADR-011 — Local-first RAG stack](../../docs/decisions/ADR-011-local-rag-stack.md)
- [`rag/local_stack/README.md`](../../rag/local_stack/README.md) — the three tools this agent orchestrates
- [`agents/orchestrator/customer_intelligence_agent.py`](../orchestrator/customer_intelligence_agent.py) — the LangGraph agent that queries the index this agent populates
- [ROADMAP.md Sprint 12](../../ROADMAP.md) — where this agent's checklist items live
