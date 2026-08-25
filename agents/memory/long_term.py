"""Long-term (cross-session) customer interaction memory — vector-store-backed, traceable.

Built per ADR-013, addressing add2.txt's "memória de ... longo prazo, garantindo rastreabilidade e
personalização para o cliente." Deliberately built on `rag/local_stack/vector_store.py`'s
`VectorStore` interface in local dev — NOT a second, duplicate vector store implementation — with
a Snowflake/Cortex-backed store as the production equivalent (same contract, per
ARCHITECTURE.md §12's AI Functions), matching the "one tool, one problem" principle: the problem
of "store and semantically retrieve embedded text scoped by owner" is one problem, whether the
text is a policy-document chunk or a past customer interaction.

Every write here is attributable to a source interaction — the traceability requirement
governance/lgpd.md already commits to for the Golden Record's survivorship log applies equally
here: a memory entry that cannot be traced back to *which* interaction produced it is not
LGPD-accountable, and is not written by this module.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from rag.local_stack.vector_store import EmbeddingFunction, QueryMatch, VectorRecord, VectorStore, get_default_vector_store


def _memory_collection_name(master_customer_id: str) -> str:
    """One collection per customer — see rag/local_stack/vector_store.py's ChromaVectorStore
    docstring: this is what makes an LGPD Art. 18 IV erasure request a single `delete()` call
    against exactly that customer's collection, never a cross-customer scan.
    """
    return f"customer_memory__{master_customer_id}"


@dataclass
class MemoryEntry:
    """One long-term memory record — always attributable to a source interaction (traceability).

    `source_interaction_id` is the required link back to whatever produced this memory (a support
    ticket id, a conversation `thread_id` from `short_term.py`, an MCP tool call id) — this field
    has no default and callers must supply it, mirroring `approval_queue.py`'s
    `approved_by`/`rejected_by` requirement pattern: an unattributed write is not accepted.
    """

    memory_id: str
    master_customer_id: str
    text: str
    source_interaction_id: str
    created_at: datetime
    metadata: dict[str, Any]


class LongTermMemoryError(RuntimeError):
    """Raised when a caller attempts a write without the traceability fields this module requires."""


class LongTermMemory:
    """Per-customer, vector-store-backed memory of past interactions, with mandatory attribution.

    Local dev: backed by `rag/local_stack/vector_store.py`'s `ChromaVectorStore` (via
    `get_default_vector_store()`). Production: the same `VectorStore` interface, backed by a
    Snowflake/Cortex-backed implementation (`AI_EMBED` + a Cortex Search index scoped per
    customer) — swapping backends does not change this class's public API, by design.
    """

    def __init__(self, *, store: VectorStore | None = None, embedding_fn: EmbeddingFunction | None = None) -> None:
        """
        Args:
            store: injected `VectorStore` implementation; defaults to the platform's local
                ChromaDB store (`rag.local_stack.vector_store.get_default_vector_store`).
            embedding_fn: used to embed `MemoryEntry.text` before writing — same injected-function
                pattern as `vector_store.py`, so the embedding provider is not hard-coded here
                either (could route through `agents/llm_gateway/router.py`'s provider set).
        """
        self._store = store or get_default_vector_store(embedding_fn=embedding_fn)
        self._embedding_fn = embedding_fn

    def remember(
        self,
        *,
        master_customer_id: str,
        text: str,
        source_interaction_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Write one attributable memory entry for a customer.

        Args:
            master_customer_id: the MDM-assigned survivor ID (ARCHITECTURE.md §8) — never a raw
                source-system id, so memory stays keyed the same way the Golden Record is.
            text: the interaction content to remember (e.g. a support resolution summary, a
                stated preference — "prefers email over phone contact").
            source_interaction_id: REQUIRED traceability link — see `MemoryEntry` docstring.
            metadata: optional extra fields (e.g. `{"channel": "support_ticket", "sentiment": 0.4}`).

        Raises:
            LongTermMemoryError: if `source_interaction_id` is empty — an anonymous memory write
                is not an audit trail, mirroring `approval_queue.approve()`'s guard on
                `approved_by`.
        """
        if not source_interaction_id:
            raise LongTermMemoryError(
                "source_interaction_id is required — every long-term memory write must be "
                "attributable to a source interaction (LGPD accountability, see governance/lgpd.md)."
            )

        memory_id = str(uuid.uuid4())
        entry = MemoryEntry(
            memory_id=memory_id,
            master_customer_id=master_customer_id,
            text=text,
            source_interaction_id=source_interaction_id,
            created_at=datetime.now(timezone.utc),
            metadata=dict(metadata or {}),
        )

        # TODO(Sprint 14 extension): embed via self._embedding_fn (or agents/llm_gateway/router.py
        # once an embedding-capable task_type is added there) before upsert — placeholder vector
        # keeps the contract stable until that wiring lands, same pattern as vector_store.py's
        # other TODOs.
        embedding = self._embedding_fn([text])[0] if self._embedding_fn else []
        self._store.upsert(
            [
                VectorRecord(
                    id=memory_id,
                    text=text,
                    embedding=embedding,
                    metadata={
                        "master_customer_id": master_customer_id,
                        "source_interaction_id": source_interaction_id,
                        "created_at": entry.created_at.isoformat(),
                        **entry.metadata,
                    },
                )
            ]
        )
        return entry

    def recall(
        self,
        master_customer_id: str,
        query_embedding: list[float],
        *,
        top_k: int = 5,
    ) -> list[QueryMatch]:
        """Retrieve the most relevant past memories for one customer, scoped to that customer only.

        Uses ChromaDB's native metadata filtering (`where={"master_customer_id": ...}`) — the
        specific reason ChromaDB, not FAISS, is the default backend here (see
        `rag/local_stack/README.md`'s trade-off table): personalization requires per-customer
        scoping on every query, and Chroma does that natively at query time.

        Args:
            master_customer_id: whose memory to search — never cross-customer.
            query_embedding: the embedded current context (e.g. the customer's latest message).
            top_k: maximum number of memories to return.
        """
        return self._store.query(
            query_embedding,
            top_k=top_k,
            where={"master_customer_id": master_customer_id},
        )

    def forget_customer(self, master_customer_id: str, memory_ids: list[str]) -> None:
        """Erase specific memory entries for a customer — the LGPD Art. 18 IV deletion path.

        Args:
            master_customer_id: unused for lookup here (kept for call-site clarity and future
                collection-per-customer routing, see `_memory_collection_name`), but required so
                this method's signature makes the scope of the deletion explicit at every call
                site rather than relying on `memory_ids` alone.
            memory_ids: the specific entries to delete.
        """
        _ = master_customer_id
        self._store.delete(memory_ids)


def content_fingerprint(text: str) -> str:
    """SHA-256 fingerprint of memory text, for de-duplication before writing near-identical
    memories twice — matches the hashing discipline `governance/lgpd.md` already applies to
    document identifiers (`document_hash`) elsewhere in this platform.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
