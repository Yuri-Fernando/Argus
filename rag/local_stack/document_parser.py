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

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

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
        current_page: int | None = None

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
                        page_number=current_page,
                        metadata={"section": heading, "doc_type": stem},
                    )
                )
                chunk_index += 1
            body_parts = []

        for item, _level in doc.iterate_items():
            label = getattr(item, "label", None)
            label_value = getattr(label, "value", label)
            # Docling exposes the source page via `item.prov[0].page_no` — a code-review pass
            # caught this being hardcoded to `page_number=None` everywhere below even though the
            # DocumentChunk field and this module's docstring both intend it to carry real
            # provenance (e.g. for a future "see page 4 of loyalty_policy.pdf" RAG citation).
            # `prov` can legitimately be empty for structural items (e.g. a synthesized heading),
            # so this stays a narrow, specific except rather than swallowing all errors.
            try:
                current_page = item.prov[0].page_no
            except (AttributeError, IndexError):
                pass

            if label_value in ("title", "section_header"):
                _flush()
                heading = (item.text or heading).strip()
                continue

            if label_value == "table" or type(item).__name__ == "TableItem":
                _flush()
                try:
                    table_text = item.export_to_markdown(doc)
                except Exception:
                    logger.warning(
                        "Docling export_to_markdown failed for a table in %s — falling back to "
                        "plain item.text (loses row/column structure for this chunk).",
                        source_path, exc_info=True,
                    )
                    table_text = item.text or ""
                raw_chunks.append(
                    DocumentChunk(
                        chunk_id=f"{stem}-{chunk_index}",
                        text=f"{heading}: {table_text}",
                        kind="table",
                        source_path=str(source_path),
                        page_number=current_page,
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


class VlmUnavailableError(RuntimeError):
    """Raised when `DoclingVlmDocumentParser` can't run — the `genai-extra` VLM extras aren't
    installed, or the VLM model itself couldn't be loaded (e.g. no internet on first run to
    download it from Hugging Face, insufficient disk/RAM). Callers
    (`agents/knowledge_ingestion/agent.py`) are expected to catch this and degrade that one
    source's ingestion result, never the whole batch — same resilience contract as
    `Crawl4AICrawler`'s `CrawlResult.success` flag."""


class DoclingVlmDocumentParser:
    """VLM sibling of `DoclingDocumentParser` (ADR-015) — parses a *scanned/photographed*
    document image (e.g. `data/documents/fiscal/*.png`, see `data/synthetic/generators/
    fiscal.py::render_scanned_documents`) via Docling's `VlmPipeline`. Default model:
    IBM Granite-Docling-258M — open weights, runs fully locally once downloaded, **no paid API
    key required**, unlike `agents/llm_gateway/router.py`'s provider adapters. This is the
    concrete VLM use case `IMPROVEMENTS_AND_RESEARCH.md` §5.3 previously marked "not implemented,
    no real use case with current text-only docs" — a scanned fiscal document is exactly that
    use case.

    Kept as a separate class from `DoclingDocumentParser`, not a `use_vlm` flag on it — single
    responsibility (ARCHITECTURE.md §1): the two pipelines have genuinely different input shapes
    (a native PDF/DOCX with a real text layer vs. a flat image with none) and different resource
    profiles (this path downloads and runs a real, if small, transformer model on first use).
    """

    def __init__(self, *, max_chunk_chars: int = 1500) -> None:
        self.max_chunk_chars = max_chunk_chars

    def parse(self, source_path: str | Path) -> list[DocumentChunk]:
        """Parse a scanned document image into chunks via Docling's VLM pipeline.

        Unlike `DoclingDocumentParser.parse`, this returns a single chunk per image — the VLM
        model reads the whole page as one pass and emits Markdown (`doc.export_to_markdown()`);
        splitting that back into per-section chunks the way the text pipeline does would need the
        VLM's DocTags output parsed for structure, a real extension if a future scanned document
        is long enough to need it (today's fiscal documents are a single page each).

        Args:
            source_path: path to a local image (PNG/JPEG) — e.g. `data/documents/fiscal/*.png`.

        Returns:
            A single-item list of `DocumentChunk` — same contract shape as
            `DoclingDocumentParser.parse` otherwise.

        Raises:
            VlmUnavailableError: see the class docstring — always this exception type, never a
                raw `ImportError`/library exception, so callers have one thing to catch.
        """
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import VlmPipelineOptions
            from docling.document_converter import DocumentConverter, ImageFormatOption
            from docling.pipeline.vlm_pipeline import VlmPipeline
        except ImportError as exc:
            raise VlmUnavailableError(
                "Docling's VLM pipeline extras are not installed — run `pip install -e .[genai-extra]`."
            ) from exc

        source_path = Path(source_path)
        try:
            converter = DocumentConverter(
                format_options={
                    InputFormat.IMAGE: ImageFormatOption(
                        pipeline_cls=VlmPipeline, pipeline_options=VlmPipelineOptions()
                    )
                }
            )
            result = converter.convert(str(source_path))
            text = result.document.export_to_markdown().strip()
        except Exception as exc:
            # Broad on purpose: the failure modes here are diverse and all equally "the VLM model
            # isn't usable right now" from a caller's perspective — no internet on first run to
            # download ibm-granite/granite-docling-258M from Hugging Face, insufficient disk/RAM,
            # a corrupted model cache, etc. A narrower except would need to enumerate every
            # transformers/huggingface_hub exception type, which is not a contract worth coupling
            # to here.
            raise VlmUnavailableError(f"Docling VLM pipeline failed for {source_path}: {exc}") from exc

        if not text:
            raise VlmUnavailableError(f"Docling VLM pipeline produced no text for {source_path}")

        stem = source_path.stem
        return [
            DocumentChunk(
                chunk_id=f"{stem}-vlm-0",
                text=text,
                kind="paragraph",
                source_path=str(source_path),
                page_number=1,
                metadata={"doc_type": stem, "parser": "docling_vlm"},
            )
        ]


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
