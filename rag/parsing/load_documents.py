"""Ingestion + parsing glue: `data/documents/*.md` -> `DocumentChunk` list.

This is orchestration only — the actual parsing work (Docling, layout-aware chunking, table
extraction) lives in `rag/local_stack/document_parser.py::DoclingDocumentParser`. This module's
one job is to find the source documents and call that parser, per ADR-011 and ARCHITECTURE.md
§1 ("one tool, one problem").
"""

from __future__ import annotations

from pathlib import Path

from rag.local_stack.document_parser import DocumentChunk, DoclingDocumentParser

DEFAULT_DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "data" / "documents"


def find_source_documents(documents_dir: str | Path = DEFAULT_DOCUMENTS_DIR) -> list[Path]:
    """Return the policy Markdown documents to ingest, sorted for deterministic ordering."""
    documents_dir = Path(documents_dir)
    return sorted(documents_dir.glob("*.md"))


def load_and_parse_documents(
    documents_dir: str | Path = DEFAULT_DOCUMENTS_DIR,
    *,
    max_chunk_chars: int = 1500,
) -> dict[str, list[DocumentChunk]]:
    """Find and parse every policy document into layout-aware chunks.

    Args:
        documents_dir: directory holding the source Markdown documents (defaults to
            `data/documents/`).
        max_chunk_chars: forwarded to `DoclingDocumentParser`.

    Returns:
        `{source_path: [DocumentChunk, ...]}`, one entry per document found.
    """
    sources = find_source_documents(documents_dir)
    parser = DoclingDocumentParser(max_chunk_chars=max_chunk_chars)
    return parser.parse_many(sources)


if __name__ == "__main__":
    parsed = load_and_parse_documents()
    for source_path, chunks in parsed.items():
        print(f"{source_path}: {len(chunks)} chunks")
        for chunk in chunks[:2]:
            print(f"  [{chunk.kind}] {chunk.text[:100]!r}")
