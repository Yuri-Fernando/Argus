"""Docling wrapper — local-dev parsing of complex documents into layout-aware chunks.

Built per ADR-011, as the local-first counterpart of `rag/parsing/`'s Snowflake
`AI_PARSE_DOCUMENT` / `AI_EXTRACT`. Solves one named problem (ARCHITECTURE.md §1): turning a
PDF/DOCX with tables, multi-column layout, or embedded images into structured, chunkable text
without a Snowflake account or a hand-rolled `pdfplumber` script that breaks on the first table.

Used by `agents/knowledge_ingestion/agent.py` for any source that is a file rather than a live
URL (Crawl4AI's job, see `crawler.py`) — chiefly `data/documents/*.pdf` and any DOCX/complex PDF a
future extension adds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ChunkKind = Literal["paragraph", "table", "heading", "list_item"]


@dataclass
class DocumentChunk:
    """One layout-aware chunk, shaped to match what `rag/parsing/` produces from
    `AI_PARSE_DOCUMENT` — this is what keeps `vector_store.py` and `retrieval/` backend-agnostic.
    """

    chunk_id: str
    text: str
    kind: ChunkKind
    source_path: str
    page_number: int | None
    metadata: dict[str, Any] = field(default_factory=dict)


class DoclingDocumentParser:
    """Thin wrapper around Docling's `DocumentConverter`.

    One responsibility only: file-in, `DocumentChunk`-list-out. No embedding, no indexing — those
    stay in `vector_store.py`, per the "one tool, one problem" rule (ARCHITECTURE.md §1).
    """

    def __init__(self, *, max_chunk_chars: int = 1500) -> None:
        """
        Args:
            max_chunk_chars: soft cap on chunk size, matching the chunking granularity
                `rag/parsing/`'s AI_PARSE_DOCUMENT-based pipeline targets, so retrieval@k behaves
                comparably whichever backend produced the index.
        """
        self.max_chunk_chars = max_chunk_chars

    def parse(self, source_path: str | Path) -> list[DocumentChunk]:
        """Parse a local document (PDF, DOCX, or Markdown) into layout-aware chunks.

        TODO(Sprint 12 extension): replace the stub below with a real call:

            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            result = converter.convert(str(source_path))
            chunks = []
            for i, item in enumerate(result.document.iterate_items()):
                chunks.append(DocumentChunk(
                    chunk_id=f"{Path(source_path).stem}-{i}",
                    text=item.text,
                    kind=_map_docling_label(item.label),
                    source_path=str(source_path),
                    page_number=getattr(item.prov[0], "page_no", None) if item.prov else None,
                ))
            return _merge_to_chunk_size(chunks, self.max_chunk_chars)

        Docling's table extraction is the specific reason this wrapper exists rather than reusing
        a plain PDF-text-extraction library: the synthetic loyalty_policy document's tier table
        (name/threshold/benefit columns) needs to survive as structured rows, not a scrambled
        text blob, for `AI_EXTRACT`-equivalent structured retrieval to work locally.

        Args:
            source_path: path to a local document under `data/documents/`.

        Returns:
            An ordered list of `DocumentChunk`, empty until the TODO above is wired.
        """
        _ = Path(source_path)
        return []

    def parse_many(self, source_paths: list[str | Path]) -> dict[str, list[DocumentChunk]]:
        """Parse several documents, keyed by their (string) source path.

        Args:
            source_paths: local document paths, typically `data/documents/*.pdf`.

        Returns:
            `{source_path: [DocumentChunk, ...]}` for every input path.
        """
        return {str(path): self.parse(path) for path in source_paths}
