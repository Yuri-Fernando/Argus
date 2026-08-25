"""rag/embeddings/ — local-dev embedding + indexing stage.

Snowflake-native `rag/README.md` describes this stage as `AI_EMBED` -> Cortex Search (cloud).
This package is the local-dev equivalent: thin orchestration glue that embeds `DocumentChunk`s
with a local sentence-transformers model and upserts them into
`rag/local_stack/vector_store.py`'s `ChromaVectorStore` — it does not reimplement the vector
store or embedding model, per ADR-011.
"""

from rag.embeddings.embedder import LocalEmbedder
from rag.embeddings.ingest import ingest_documents

__all__ = ["LocalEmbedder", "ingest_documents"]
