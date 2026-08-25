"""Retrieval precision@k for the local RAG stack, scored against `golden_questions.py`.

Per `rag/README.md`'s Sprint 12 acceptance criteria: retrieval precision@3 >= 0.8 on the golden
set. This script re-ingests the four policy documents into a fresh in-memory-only Chroma
collection (so scoring is repeatable and independent of whatever the persisted
`data/rag/chroma` store currently holds), embeds each golden question, retrieves top-k chunks,
and checks whether at least one retrieved chunk's `doc_type` metadata matches the question's
`expected_doc_types`.

A question counts as a "hit" at k if ANY of the top-k retrieved chunks came from an expected
document. precision@k here is the fraction of questions that hit, not a per-chunk precision —
this matches how `rag/README.md` frames the acceptance criterion (retrieval finds the right
document(s) among the top-k results).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from rag.embeddings.embedder import LocalEmbedder
from rag.embeddings.ingest import ingest_documents
from rag.evaluation.golden_questions import GOLDEN_QUESTIONS
from rag.local_stack.vector_store import ChromaVectorStore


@dataclass
class QuestionResult:
    question: str
    expected_doc_types: tuple[str, ...]
    retrieved: list[dict] = field(default_factory=list)
    hit: bool = False


def evaluate_precision_at_k(k: int = 3) -> dict:
    """Run the golden Q&A set against a freshly-ingested vector store and compute precision@k.

    Returns a dict with the aggregate `precision_at_k` plus per-question detail, suitable for
    both a human-readable report and a machine-checkable assertion in CI.
    """
    embedder = LocalEmbedder()
    tmp_dir = tempfile.mkdtemp(prefix="rag_eval_chroma_")
    try:
        store = ChromaVectorStore(persist_directory=tmp_dir, embedding_fn=embedder)
        _, chunk_count = ingest_documents(embedder=embedder, vector_store=store)

        results: list[QuestionResult] = []
        for gq in GOLDEN_QUESTIONS:
            query_embedding = embedder([gq.question])[0]
            matches = store.query(query_embedding, top_k=k)
            retrieved = [
                {
                    "chunk_id": m.record.id,
                    "doc_type": m.record.metadata.get("doc_type", ""),
                    "score": round(m.score, 4),
                    "text": m.record.text[:120],
                }
                for m in matches
            ]
            hit = any(r["doc_type"] in gq.expected_doc_types for r in retrieved)
            results.append(
                QuestionResult(
                    question=gq.question,
                    expected_doc_types=gq.expected_doc_types,
                    retrieved=retrieved,
                    hit=hit,
                )
            )
    finally:
        # Chroma's sqlite backend keeps file handles open on Windows until the process/client is
        # garbage-collected, so a hard rmtree can transiently fail here — best-effort cleanup,
        # never let a leftover temp dir fail the evaluation run itself.
        shutil.rmtree(tmp_dir, ignore_errors=True)

    hits = sum(1 for r in results if r.hit)
    precision = hits / len(results) if results else 0.0

    return {
        "k": k,
        "chunk_count": chunk_count,
        "num_questions": len(results),
        "hits": hits,
        "precision_at_k": round(precision, 4),
        "target": 0.8,
        "meets_target": precision >= 0.8,
        "results": [
            {
                "question": r.question,
                "expected_doc_types": list(r.expected_doc_types),
                "hit": r.hit,
                "retrieved": r.retrieved,
            }
            for r in results
        ],
    }


def _print_report(report: dict) -> None:
    print(f"Indexed {report['chunk_count']} chunks")
    print(
        f"precision@{report['k']} = {report['precision_at_k']} "
        f"({report['hits']}/{report['num_questions']}) "
        f"target={report['target']} meets_target={report['meets_target']}"
    )
    print()
    for r in report["results"]:
        mark = "HIT " if r["hit"] else "MISS"
        top = r["retrieved"][0] if r["retrieved"] else None
        top_desc = f"{top['doc_type']} ({top['score']})" if top else "no results"
        print(f"[{mark}] {r['question']}")
        print(f"       expected={r['expected_doc_types']} top1={top_desc}")


if __name__ == "__main__":
    report = evaluate_precision_at_k(k=3)
    _print_report(report)

    out_path = Path(__file__).resolve().parent / "precision_at_k_results.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nFull report written to {out_path}")
