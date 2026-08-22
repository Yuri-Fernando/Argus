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

        Uses Docling's `DocumentConverter` to walk the document's layout tree
        (`result.document.iterate_items()`, which yields `(item, level)` pairs) and groups
        consecutive body items under their nearest `section_header`/`title` into one chunk per
        section — this is what "layout-aware" means here: chunk boundaries follow the document's
        actual structure (headings, tables) rather than a blind fixed-size character split.
        Sections longer than `max_chunk_chars` are further split by `_merge_to_chunk_size`.

        Docling's table extraction is the specific reason this wrapper exists rather than reusing
        a plain PDF-text-extraction library: the synthetic loyalty_policy document's tier table
        (name/threshold/benefit columns) survives as a structured Markdown table (`TableItem`,
        exported via `item.export_to_markdown(doc)`) in its own `kind="table"` chunk, instead of a
        scrambled text blob — this is what makes `AI_EXTRACT`-equivalent structured retrieval work
        locally (e.g. "what's the threshold for Gold tier?").

        Args:
            source_path: path to a local document under `data/documents/` (Markdown, PDF, DOCX —
                anything Docling's `DocumentConverter` supports).

        Returns:
            An ordered list of `DocumentChunk`.
        """
        from docling.document_converter import DocumentConverter

        source_path = Path(source_path)
        converter = DocumentConverter()
        result = converter.convert(str(source_path))
        doc = result.document
        stem = source_path.stem

        # section_buffer holds (heading_text_or_None, [body_texts]) for the section currently
        # being accumulated; table items are flushed as their own standalone chunk immediately,
        # since a table should never be merged with surrounding prose.
        raw_chunks: list[DocumentChunk] = []
        heading = "Introduction"
        body_parts: list[str] = []
        chunk_index = 0

        def _flush(kind: ChunkKind = "paragraph") -> None:
            nonlocal chunk_index, body_parts
            text = " ".join(part for part in body_parts if part).strip()
            if text:
                raw_chunks.append(
                    DocumentChunk(
                        chunk_id=f"{stem}-{chunk_index}",
                        text=f"{heading}: {text}" if heading else text,
                        kind=kind,
                        source_path=str(source_path),
                        page_number=None,
                        metadata={"section": heading, "doc_type": stem},
                    )
                )
                chunk_index += 1
            body_parts = []

        for item, _level in doc.iterate_items():
            label = getattr(item, "label", None)
            label_value = getattr(label, "value", label)

            if label_value in ("title", "section_header"):
                _flush()
                heading = (item.text or heading).strip()
                continue

            if label_value == "table" or type(item).__name__ == "TableItem":
                _flush()
                try:
                    table_text = item.export_to_markdown(doc)
                except Exception:
                    table_text = item.text or ""
                raw_chunks.append(
                    DocumentChunk(
                        chunk_id=f"{stem}-{chunk_index}",
                        text=f"{heading}: {table_text}",
                        kind="table",
                        source_path=str(source_path),
                        page_number=None,
                        metadata={"section": heading, "doc_type": stem},
                    )
                )
                chunk_index += 1
                continue

            text = getattr(item, "text", None)
            if text:
                body_parts.append(text.strip())

        _flush()
        return _merge_to_chunk_size(raw_chunks, self.max_chunk_chars)

    def parse_many(self, source_paths: list[str | Path]) -> dict[str, list[DocumentChunk]]:
        """Parse several documents, keyed by their (string) source path.

        Args:
            source_paths: local document paths, typically `data/documents/*.pdf`.

        Returns:
            `{source_path: [DocumentChunk, ...]}` for every input path.
        """
        return {str(path): self.parse(path) for path in source_paths}


def _merge_to_chunk_size(chunks: list[DocumentChunk], max_chunk_chars: int) -> list[DocumentChunk]:
    """Split any chunk longer than `max_chunk_chars` into multiple sequential chunks.

    Section-scoped chunks from `DoclingDocumentParser.parse` are usually well under the cap (the
    synthetic policy documents' sections are short), but this keeps the contract honest for any
    future, longer document instead of silently emitting an oversized chunk. Splits on whitespace
    boundaries so a word is never cut mid-token.
    """
    merged: list[DocumentChunk] = []
    for chunk in chunks:
        if len(chunk.text) <= max_chunk_chars:
            merged.append(chunk)
            continue

        words = chunk.text.split(" ")
        part_index = 0
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip() if current else word
            if len(candidate) > max_chunk_chars and current:
                merged.append(
                    DocumentChunk(
                        chunk_id=f"{chunk.chunk_id}-p{part_index}",
                        text=current,
                        kind=chunk.kind,
                        source_path=chunk.source_path,
                        page_number=chunk.page_number,
                        metadata=chunk.metadata,
                    )
                )
                part_index += 1
                current = word
            else:
                current = candidate
        if current:
            merged.append(
                DocumentChunk(
                    chunk_id=f"{chunk.chunk_id}-p{part_index}",
                    text=current,
                    kind=chunk.kind,
                    source_path=chunk.source_path,
                    page_number=chunk.page_number,
                    metadata=chunk.metadata,
                )
            )
    return merged
