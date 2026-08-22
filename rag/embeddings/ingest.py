"""End-to-end local ingestion: `data/documents/*.md` -> Docling chunks -> embeddings -> ChromaDB.

Orchestration only: calls `rag.parsing.load_and_parse_documents` (which itself calls
`DoclingDocumentParser`), embeds the resulting chunks with `LocalEmbedder`, and upserts them into
`rag/local_stack/vector_store.py`'s `ChromaVectorStore`. No parsing or embedding logic lives here
— this module wires the three existing pieces together, per ADR-011 / ARCHITECTURE.md §1.
"""

from __future__ import annotations

from pathlib import Path

from rag.embeddings.embedder import LocalEmbedder
from rag.local_stack.document_parser import DocumentChunk
from rag.local_stack.vector_store import ChromaVectorStore, VectorRecord, VectorStore
from rag.parsing.load_documents import DEFAULT_DOCUMENTS_DIR, load_and_parse_documents

DEFAULT_PERSIST_DIR = str(Path(__file__).resolve().parents[2] / "data" / "rag" / "chroma")


def ingest_documents(
    documents_dir: str | Path = DEFAULT_DOCUMENTS_DIR,
    *,
    persist_directory: str = DEFAULT_PERSIST_DIR,
    embedder: LocalEmbedder | None = None,
    vector_store: VectorStore | None = None,
) -> tuple[VectorStore, int]:
    """Parse every policy document, embed its chunks, and upsert them into the vector store.

    Args:
        documents_dir: directory holding the source Markdown documents.
        persist_directory: on-disk path the Chroma client persists to (ignored if
            `vector_store` is passed in directly, e.g. by the evaluation harness).
        embedder: injected embedding function; defaults to a fresh `LocalEmbedder`.
        vector_store: injected vector store; defaults to a fresh `ChromaVectorStore` at
            `persist_directory`.

    Returns:
        `(vector_store, chunk_count)` — the populated store and how many chunks were indexed, so
        callers (e.g. the evaluation script) can assert against a non-zero count.
    """
    embedder = embedder or LocalEmbedder()
    store = vector_store or ChromaVectorStore(persist_directory=persist_directory, embedding_fn=embedder)

    parsed = load_and_parse_documents(documents_dir)
    all_chunks: list[DocumentChunk] = [chunk for chunks in parsed.values() for chunk in chunks]
    if not all_chunks:
        return store, 0

    embeddings = embedder([chunk.text for chunk in all_chunks])
    records = [
        VectorRecord(
            id=chunk.chunk_id,
            text=chunk.text,
            embedding=embedding,
            metadata={
                "doc_type": chunk.metadata.get("doc_type", ""),
                "section": chunk.metadata.get("section", ""),
                "kind": chunk.kind,
                "source_path": chunk.source_path,
            },
        )
        for chunk, embedding in zip(all_chunks, embeddings)
    ]
    store.upsert(records)
    return store, len(records)


if __name__ == "__main__":
    vector_store, count = ingest_documents()
    print(f"Ingested {count} chunks into {DEFAULT_PERSIST_DIR}")
