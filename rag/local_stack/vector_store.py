"""Local vector store abstraction — ChromaDB (primary) with a FAISS alternative implementation.

Built per ADR-011. One interface (`VectorStore`), two backends, so `agents/knowledge_ingestion/`
and `agents/memory/long_term.py` never need to know which one is active — matching the pattern
`mcp/tools/customer.py` uses for its stable-contract-over-unfinished-implementation stubs.

See `rag/local_stack/README.md` for the ChromaDB-vs-FAISS trade-off table this module implements
both sides of.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class VectorRecord:
    """One embedded chunk plus the metadata needed to filter/attribute it at query time.

    `source_type` and `master_customer_id` are the two metadata fields
    `agents/memory/long_term.py` relies on for scoping a query to one customer's history — see
    that module for why ChromaDB's native metadata filtering (not FAISS's) is the default choice
    there specifically.
    """

    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryMatch:
    """One retrieved record plus its similarity score, ordered by relevance in `VectorStore.query`."""

    record: VectorRecord
    score: float


class EmbeddingFunction(Protocol):
    """Anything that turns text into a vector. Injected, not hard-coded, so the same VectorStore
    code works whether embeddings come from Azure OpenAI, a local sentence-transformers model, or
    (in production) Snowflake `AI_EMBED` — see `agents/llm_gateway/` for the multi-provider story
    on the generation side; embeddings follow the same "don't hard-code one vendor" instinct.
    """

    def __call__(self, texts: list[str]) -> list[list[float]]: ...


class VectorStore(ABC):
    """Common contract both ChromaDB and FAISS backends implement."""

    @abstractmethod
    def upsert(self, records: list[VectorRecord]) -> None:
        """Insert or update records by id."""

    @abstractmethod
    def query(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[QueryMatch]:
        """Return the `top_k` most similar records, optionally filtered by metadata.

        Args:
            query_embedding: the embedded query vector.
            top_k: maximum number of matches to return.
            where: metadata filter (e.g. `{"doc_type": "refund_policy"}`). Supported by
                `ChromaVectorStore` natively; `FaissVectorStore` applies it as a post-filter over
                a maintained id→metadata map, since FAISS itself has no metadata store — this is
                the concrete cost of the trade-off documented in the README.
        """

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        """Remove records by id — used by the LGPD-driven deletion path in `agents/memory/`."""


class ChromaVectorStore(VectorStore):
    """Primary backend — ChromaDB, chosen for local-dev ergonomics and native metadata filtering.

    Collection naming convention: `{purpose}__{scope}`, e.g. `policy_docs__rag` for the RAG
    knowledge base, `customer_memory__{master_customer_id}` for long-term agent memory
    (`agents/memory/long_term.py`) — one Chroma collection per customer keeps the LGPD deletion
    path (governance/lgpd.md Art. 18 IV) a single `collection.delete()` away from complete.
    """

    def __init__(self, *, persist_directory: str = "./data/chroma", embedding_fn: EmbeddingFunction | None = None) -> None:
        """
        Args:
            persist_directory: local on-disk path Chroma persists to — matches the local-first
                philosophy (ADR-010): no external service required.
            embedding_fn: optional injected embedding function; if omitted, callers are expected
                to pass already-embedded `VectorRecord.embedding` values.
        """
        self.persist_directory = persist_directory
        self.embedding_fn = embedding_fn
        # TODO(Sprint 12 extension): replace with a real client:
        #   import chromadb
        #   self._client = chromadb.PersistentClient(path=persist_directory)
        #   self._collection = self._client.get_or_create_collection("policy_docs__rag")
        self._records: dict[str, VectorRecord] = {}

    def upsert(self, records: list[VectorRecord]) -> None:
        # TODO(Sprint 12 extension): self._collection.upsert(ids=..., embeddings=..., metadatas=..., documents=...)
        for record in records:
            self._records[record.id] = record

    def query(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[QueryMatch]:
        # TODO(Sprint 12 extension): self._collection.query(query_embeddings=[query_embedding],
        #   n_results=top_k, where=where) — Chroma applies the `where` filter natively at query
        #   time, before the similarity search, which is the specific ergonomic win over FAISS.
        _ = (query_embedding, top_k, where)
        return []

    def delete(self, ids: list[str]) -> None:
        # TODO(Sprint 12 extension): self._collection.delete(ids=ids)
        for record_id in ids:
            self._records.pop(record_id, None)


class FaissVectorStore(VectorStore):
    """Documented alternative backend — FAISS, for when scale outgrows ChromaDB's comfort zone.

    Not the default: this project's local vector store only ever holds a handful of policy
    documents' worth of chunks plus per-customer memory, well inside ChromaDB's sweet spot. Kept
    here, fully implementing the same `VectorStore` contract, as the documented next step if a
    future extension needs to index millions of chunks locally (see `rag/local_stack/README.md`'s
    trade-off table) — swapping backends is then a one-line change at the call site, not a
    rewrite.
    """

    def __init__(self, *, dimension: int = 1536) -> None:
        """
        Args:
            dimension: embedding vector dimensionality FAISS's index is built for (e.g. 1536 for
                `text-embedding-3-small`) — unlike Chroma, FAISS requires this up front.
        """
        self.dimension = dimension
        # TODO(scale-out extension): replace with a real index:
        #   import faiss
        #   self._index = faiss.IndexFlatIP(dimension)  # inner product on normalized vectors
        self._id_to_metadata: dict[str, dict[str, Any]] = {}
        self._records: dict[str, VectorRecord] = {}

    def upsert(self, records: list[VectorRecord]) -> None:
        # TODO(scale-out extension): self._index.add(np.array([r.embedding for r in records]));
        # FAISS has no native id/metadata store, so both are tracked here alongside it — this
        # is the concrete extra bookkeeping the README's trade-off table refers to.
        for record in records:
            self._records[record.id] = record
            self._id_to_metadata[record.id] = record.metadata

    def query(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[QueryMatch]:
        # TODO(scale-out extension): distances, indices = self._index.search(
        #   np.array([query_embedding]), top_k * (5 if where else 1))  # over-fetch, then
        # post-filter by `where` against self._id_to_metadata, since FAISS can't filter natively.
        _ = (query_embedding, top_k, where)
        return []

    def delete(self, ids: list[str]) -> None:
        # FAISS's flat index has no cheap delete-by-id; a real implementation rebuilds the index
        # from `self._records` minus `ids`, which is the concrete operational cost this backend
        # trades against ChromaDB's built-in delete — documented, not hidden.
        for record_id in ids:
            self._records.pop(record_id, None)
            self._id_to_metadata.pop(record_id, None)


def get_default_vector_store(*, embedding_fn: EmbeddingFunction | None = None) -> VectorStore:
    """Return the platform's default local vector store — ChromaDB, per ADR-011.

    Callers that need FAISS explicitly (e.g. an evaluation script comparing both backends'
    retrieval precision@k) should instantiate `FaissVectorStore` directly instead of using this
    factory.
    """
    return ChromaVectorStore(embedding_fn=embedding_fn)
