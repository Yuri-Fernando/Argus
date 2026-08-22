"""Local embedding function — `sentence-transformers`, injected into `VectorStore` per the
`EmbeddingFunction` Protocol defined in `rag/local_stack/vector_store.py`.

Local-dev counterpart of Snowflake `AI_EMBED` (ARCHITECTURE.md §14 / ADR-011). Model choice:
`paraphrase-multilingual-MiniLM-L12-v2` — the policy documents mix English section headings with
Portuguese legal terms (LGPD, CDC Art. 49, "arrependimento"), so a multilingual model gives more
faithful similarity scores than an English-only one, at a small (384-dim) embedding size that
keeps local retrieval fast with no GPU required.
"""

from __future__ import annotations

DEFAULT_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


class LocalEmbedder:
    """Wraps a `sentence-transformers` model behind the `EmbeddingFunction` Protocol
    (`__call__(texts: list[str]) -> list[list[float]]`) so it plugs directly into
    `ChromaVectorStore(embedding_fn=LocalEmbedder())`.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def __call__(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()
