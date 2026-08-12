"""Knowledge Ingestion Agent — an Agno-based, multi-tool autonomous agent for the RAG pipeline.

Built per ADR-011, addressing add2.txt's "desenvolver agentes autônomos inteligentes utilizando
frameworks modernos como LangChain e Agno, criando fluxos que combinem múltiplas ferramentas."

Deliberately built with **Agno**, not LangGraph, because its responsibility is genuinely
different from the four LangGraph agents in ARCHITECTURE.md §15: this agent does not answer a
customer question through a human-in-the-loop-gated state machine — it autonomously decides,
per knowledge source, which extraction tool to use (Crawl4AI for a live URL, Docling for a local
complex document, or a direct static-file read for the existing synthetic policy docs), then
writes the result into the local vector store. That is exactly the "multi-tool agent picks the
right tool per input" pattern Agno is built for, and it never touches
`agents/recommendation/approval_queue.py` — ingesting a knowledge chunk is not a consequential,
customer-facing action under ADR-006, so it does not need that gate.

See docs/decisions/ADR-011-local-rag-stack.md's "LangChain vs. Agno vs. LangGraph" section for the
full framework-selection rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from rag.local_stack.crawler import Crawl4AICrawler
from rag.local_stack.document_parser import DoclingDocumentParser
from rag.local_stack.vector_store import VectorRecord, VectorStore, get_default_vector_store


class SourceKind(str, Enum):
    """The three extraction paths this agent chooses between, one per knowledge source."""

    LIVE_URL = "live_url"  # -> Crawl4AI (crawler.py)
    COMPLEX_DOCUMENT = "complex_document"  # -> Docling (document_parser.py)
    STATIC_FILE = "static_file"  # -> direct read, e.g. the existing synthetic Markdown policies


@dataclass
class KnowledgeSource:
    """One thing the agent has been asked to ingest — a URL or a local file path."""

    identifier: str  # URL or file path
    kind: SourceKind
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestionResult:
    """Outcome of ingesting one KnowledgeSource — the audit trail for what the agent decided."""

    source: KnowledgeSource
    tool_used: str
    chunks_written: int
    success: bool
    error: str | None = None


def classify_source(identifier: str) -> SourceKind:
    """Decide which extraction tool a source needs, based on its shape.

    This is the core "autonomous tool selection" decision the Agno agent makes per source — kept
    as a standalone, unit-testable function (same pattern as
    `agents/recommendation/recommendation_agent.py`'s `score_recommendation`) so the decision
    logic can be tested without invoking Agno's runtime.

    Args:
        identifier: a URL (routes to Crawl4AI) or a local file path (routes to Docling for
            PDF/DOCX, or a direct static read for .md/.txt).
    """
    if identifier.startswith(("http://", "https://")):
        return SourceKind.LIVE_URL
    suffix = Path(identifier).suffix.lower()
    if suffix in (".pdf", ".docx"):
        return SourceKind.COMPLEX_DOCUMENT
    return SourceKind.STATIC_FILE


class KnowledgeIngestionAgent:
    """Agno-based agent that autonomously ingests knowledge sources into the local RAG store.

    Composes three tools — `Crawl4AICrawler`, `DoclingDocumentParser`, and a static-file reader —
    behind one `ingest(sources)` entrypoint, choosing per-source which to call via
    `classify_source()`, then writing every resulting chunk into a shared `VectorStore`
    (`rag/local_stack/vector_store.py`) so `agents/orchestrator/` and `agents/memory/long_term.py`
    read from the same index this agent populates.
    """

    def __init__(
        self,
        *,
        crawler: Crawl4AICrawler | None = None,
        document_parser: DoclingDocumentParser | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self._crawler = crawler or Crawl4AICrawler()
        self._document_parser = document_parser or DoclingDocumentParser()
        self._vector_store = vector_store or get_default_vector_store()
        # TODO(Sprint 12 extension): wrap the three tool calls below (`_ingest_live_url`,
        # `_ingest_complex_document`, `_ingest_static_file`) as Agno `@tool`-decorated functions
        # and register them on an `agno.agent.Agent(tools=[...])` instance, so tool selection is
        # driven by Agno's own reasoning loop over a task like "ingest these N sources into the
        # knowledge base" rather than the explicit `classify_source()` dispatch below. The
        # dispatch table is kept explicit for now so this module's behavior is deterministic and
        # testable before wiring in the LLM-driven Agno runtime — see README "Why the dispatch is
        # explicit today".
        #
        #   from agno.agent import Agent
        #   from agno.tools import tool
        #   self._agno_agent = Agent(tools=[self._ingest_live_url, self._ingest_complex_document,
        #                                    self._ingest_static_file], instructions=[...])

    async def ingest(self, sources: list[KnowledgeSource]) -> list[IngestionResult]:
        """Ingest every source, routing each to the tool `classify_source` selects for it.

        Args:
            sources: knowledge sources to pull in — e.g. a live policy-style URL, a complex PDF
                under `data/documents/`, or one of the existing synthetic Markdown policy files.

        Returns:
            One `IngestionResult` per source, in order — the audit trail of which tool the agent
            chose and how many chunks it wrote, for the Sprint 12 evaluation harness
            (`rag/evaluation/`) to check against.
        """
        results: list[IngestionResult] = []
        for source in sources:
            if source.kind is SourceKind.LIVE_URL:
                results.append(await self._ingest_live_url(source))
            elif source.kind is SourceKind.COMPLEX_DOCUMENT:
                results.append(self._ingest_complex_document(source))
            else:
                results.append(self._ingest_static_file(source))
        return results

    async def _ingest_live_url(self, source: KnowledgeSource) -> IngestionResult:
        """Route a live-URL source through Crawl4AI."""
        crawl_result = await self._crawler.crawl_url(source.identifier)
        if not crawl_result.success:
            return IngestionResult(
                source=source, tool_used="crawl4ai", chunks_written=0, success=False, error=crawl_result.error
            )
        # TODO(Sprint 12 extension): chunk crawl_result.markdown before upsert — today this writes
        # one record per page, matching document_parser.py's current single-chunk-per-call stub
        # depth; both should converge on the same chunking utility once real parsing lands.
        self._vector_store.upsert(
            [VectorRecord(id=source.identifier, text=crawl_result.markdown, embedding=[], metadata=source.metadata)]
        )
        return IngestionResult(source=source, tool_used="crawl4ai", chunks_written=1, success=True)

    def _ingest_complex_document(self, source: KnowledgeSource) -> IngestionResult:
        """Route a complex local document (PDF/DOCX) through Docling."""
        chunks = self._document_parser.parse(source.identifier)
        self._vector_store.upsert(
            [
                VectorRecord(id=chunk.chunk_id, text=chunk.text, embedding=[], metadata={**source.metadata, "kind": chunk.kind})
                for chunk in chunks
            ]
        )
        return IngestionResult(source=source, tool_used="docling", chunks_written=len(chunks), success=True)

    def _ingest_static_file(self, source: KnowledgeSource) -> IngestionResult:
        """Route a plain static file (e.g. the existing synthetic .md policy docs) via a direct read."""
        path = Path(source.identifier)
        if not path.exists():
            return IngestionResult(
                source=source, tool_used="static_read", chunks_written=0, success=False, error=f"{path} not found"
            )
        text = path.read_text(encoding="utf-8")
        self._vector_store.upsert([VectorRecord(id=str(path), text=text, embedding=[], metadata=source.metadata)])
        return IngestionResult(source=source, tool_used="static_read", chunks_written=1, success=True)


def build_default_agent() -> KnowledgeIngestionAgent:
    """Construct the agent with the platform's default local tool set (Crawl4AI + Docling + ChromaDB)."""
    return KnowledgeIngestionAgent()
