"""rag/parsing/ — local-dev document parsing stage.

Snowflake-native `rag/README.md` describes this stage as `AI_PARSE_DOCUMENT` / `AI_EXTRACT`
(cloud). This package is the local-dev equivalent: thin orchestration glue around
`rag/local_stack/document_parser.py` (Docling) — it does not reimplement parsing, it just picks
up `data/documents/*.md` and calls the existing `DoclingDocumentParser`, per ADR-011.
"""

from rag.parsing.load_documents import load_and_parse_documents

__all__ = ["load_and_parse_documents"]
