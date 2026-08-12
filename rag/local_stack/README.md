# rag/local_stack/

**Local-dev equivalent of Snowflake `AI_PARSE_DOCUMENT` + `AI_EMBED` + Cortex Search** ([ARCHITECTURE.md §14](../../ARCHITECTURE.md#14-layer-11--rag--document-intelligence)), added per [ADR-011](../../docs/decisions/ADR-011-local-rag-stack.md) and built to the same local-first principle as the rest of the platform ([ADR-010](../../docs/decisions/ADR-010-local-first-development.md)): you should be able to develop and demo the entire RAG pipeline with `docker-compose up` and zero Snowflake credentials, then point the same pipeline shape at Cortex when a paid account is available.

```
rag/local_stack/
├── crawler.py           # Crawl4AI wrapper — pulls live policy pages instead of only static synthetic PDFs
├── document_parser.py   # Docling wrapper — layout-aware parsing of complex documents (tables, PDFs, DOCX)
└── vector_store.py       # ChromaDB (primary) / FAISS (documented alternative) local vector store
```

This module does **not** replace [`rag/README.md`](../README.md)'s Snowflake-native pipeline (`parsing/`, `embeddings/`, `retrieval/`) — it is the **local-dev path** that mirrors it stage-for-stage, so the same evaluation harness (`rag/evaluation/`) can run against either backend:

| Stage | Cloud/production path (`rag/`) | Local-dev path (`rag/local_stack/`) |
|---|---|---|
| Ingestion | Static synthetic PDFs/Markdown from `data/documents/` | `crawler.py` (Crawl4AI) can additionally pull live web pages (e.g. a real refund-policy-style page) — or fall back to the static files, same as the cloud path |
| Parsing | `AI_PARSE_DOCUMENT` / `AI_EXTRACT` (Snowflake Cortex) | `document_parser.py` (Docling) — layout-aware chunking done locally, no Snowflake account needed |
| Embedding + index | `AI_EMBED` → Cortex Search | `vector_store.py` — ChromaDB (default) or FAISS |
| Retrieval | Cortex Search query + customer/order join | Same retrieval contract, backed by ChromaDB/FAISS instead |

One tool, one problem, per [ARCHITECTURE.md §1](../../ARCHITECTURE.md#1-design-principles): Crawl4AI solves "get live web content into the pipeline without a headless-browser script per site," Docling solves "parse a complex document — tables, multi-column PDFs, DOCX — without paying for `AI_PARSE_DOCUMENT` while iterating locally," and the vector store solves "make chunks searchable by similarity without a Snowflake account." None of the three change what the pipeline does — only where it runs.

## ChromaDB vs. FAISS — trade-off table

| | **ChromaDB** (primary) | **FAISS** (documented alternative) |
|---|---|---|
| Setup | `pip install chromadb`, in-process, persists to disk with zero config | `pip install faiss-cpu`, lower-level index API, no built-in persistence/metadata layer |
| Metadata filtering | Native — filter by `{"doc_type": "refund_policy", "source": "crawl"}` alongside the similarity query | None built in — you maintain a parallel id→metadata mapping yourself |
| Local dev ergonomics | Best — this is exactly what it's built for; matches the "90 seconds from `pip install` to a working store" experience this project wants for `make up && make seed` | More setup work for the same outcome; worth it only once scale justifies it |
| Scale / raw query speed | Weakest of the two past roughly 1-5M vectors — treated here as a **prototyping/dev store, not a production target** (consistent with community consensus as of 2026) | Faster at scale, no metadata store, used in production RAG systems that outgrow ChromaDB |
| Chosen here because | This project's local vector store only ever needs to hold four-to-a-few-dozen policy documents' worth of chunks — ChromaDB's ceiling is irrelevant at this scale, and its metadata filtering is used directly by `retrieval/` to scope a query to one document type | Kept as the **documented scale-out path** — if a future extension needed to index millions of chunks locally (e.g. ingesting the full Olist review corpus for semantic search), FAISS is the noted next step, not a redesign |

`vector_store.py` exposes one interface (`VectorStore.upsert(...)` / `VectorStore.query(...)`) implemented by both `ChromaVectorStore` (default) and `FaissVectorStore` (alternative, same contract) — callers in `retrieval/`-equivalent code don't need to know which backend is active.

## Relationship to the Knowledge Ingestion Agent

[`agents/knowledge_ingestion/agent.py`](../../agents/knowledge_ingestion/agent.py) is the Agno-based agent that decides, per source, whether to call `crawler.py`, `document_parser.py`, or read a static file directly, then writes the result into `vector_store.py` — see [ADR-011](../../docs/decisions/ADR-011-local-rag-stack.md) for why that orchestration logic lives in a separate LangChain/Agno-vs-LangGraph decision, not folded into this module.

## Related

- [ADR-011 — Local-first RAG stack](../../docs/decisions/ADR-011-local-rag-stack.md)
- [ADR-010 — Local-first development](../../docs/decisions/ADR-010-local-first-development.md)
- [ARCHITECTURE.md §14 — RAG / Document Intelligence](../../ARCHITECTURE.md#14-layer-11--rag--document-intelligence)
- [`rag/README.md`](../README.md) — the Snowflake-native production pipeline this mirrors
- [`agents/memory/long_term.py`](../../agents/memory/long_term.py) — reuses `vector_store.py` for long-term conversational memory instead of standing up a second vector store
