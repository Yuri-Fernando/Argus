# Experimentation → Versioning → Publication Pipeline

Addresses `add2.txt`'s "Cultura de Engenharia: Montar pipelines de experimentação, versionamento e publicação (MLOps) sempre com foco em escalabilidade e código limpo" and "Experiência em MLOps para automação do ciclo de vida de modelos." This document names the discipline explicitly, end-to-end, rather than leaving it implicit across [`mlflow/`](../mlflow/), [`model_versioning.md`](model_versioning.md), and CI — it is the single place that states the full experiment→version→publish lifecycle as one pipeline, cross-linking the pieces that already implement each stage.

## The three stages

```
1. EXPERIMENT              2. VERSION                    3. PUBLISH
   (mlflow/)                  (model_versioning.md)          (this platform's specific
                                                               publication targets)
   Every training run    →    Best run promoted to      →    Pinned version consumed by:
   logged: params,             Staging in MLflow Model         - batch scoring jobs
   metrics, artifacts           Registry (best PR-AUC/           (ml/training/config.yaml)
   (ARCHITECTURE.md §10)        silhouette/F1 on held-out)     - agents/llm_gateway/models.yaml
                                                                  (for the LLM-routing "experiment"
                              Promoted to Production only        equivalent — see below)
                              after ml/evaluation/ confirms     - agents/reinforcement/ policy
                              no regression vs. current           updates (once promoted out of
                              Production model                    extension status)
```

### 1. Experiment

Every training run in [`ml/training/`](../ml/training/) is logged to MLflow (params, metrics, artifacts) — nothing is a "throwaway" run; every run is queryable later, which is what makes the champion-model criterion in [`ml/README.md`](../ml/README.md) ("best PR-AUC on the held-out set") an auditable comparison across runs, not a claim taken on faith.

This same discipline is deliberately extended to the **non-model** experiments this platform now runs, per `add2.txt`'s broader MLOps culture ask:

- **LLM provider/model comparisons** (`agents/llm_gateway/`) — before a `task_type` default changes in `models.yaml`, it is run through `agents/*/evaluation/golden_questions.yaml` with the candidate `model_id` and scored on accuracy/latency/cost, exactly the "compared before promoted" pattern this document describes for ML models. See [`agents/llm_gateway/README.md`](../agents/llm_gateway/README.md#evaluating-a-new-provider-or-model).
- **RAG retrieval backend comparisons** (`rag/local_stack/`) — ChromaDB vs. FAISS retrieval precision@k, scored against the same golden Q&A set `rag/evaluation/` already uses for the Snowflake Cortex Search path.

### 2. Version

Model versioning follows [`model_versioning.md`](model_versioning.md)'s `None → Staging → Production → Archived` stages and `{model_name}-v{MAJOR}.{MINOR}` tagging scheme unchanged — that document remains the source of truth for **model** versioning specifically. This pipeline document is the wider frame: the same "pin an evaluated version, don't always-latest it" discipline applies to `agents/llm_gateway/models.yaml`'s `defaults` mapping (a routing-table version, changed only behind a benchmark run) and, once promoted out of extension status, to `ml/reinforcement/`'s bandit policy (an offline-evaluated policy version, not an always-online-learning one — see [`ml/reinforcement/README.md`](../ml/README.md)).

### 3. Publish

"Publication" in this platform means a specific, named consumer starts reading the pinned version — never an implicit always-latest read:

- A registered MLflow model version is read by the batch scoring job via `ml/training/config.yaml`'s pinned version (see `model_versioning.md`'s Rollback section).
- An `agents/llm_gateway/models.yaml` `defaults` entry is read by every `complete(prompt, task_type)` call across all agents — one file, one source of truth, same "one metric, one definition" instinct [ARCHITECTURE.md §1](../ARCHITECTURE.md#1-design-principles) already applies to the semantic layer.

## Code cleanliness and scalability, concretely

"Sempre com foco em escalabilidade e código limpo" is not a slogan restated here — it is the same two things this repository already enforces structurally, named explicitly for this pipeline:

- **Clean code**: every new module added under this integration (`rag/local_stack/`, `agents/llm_gateway/`, `agents/memory/`, `agents/knowledge_ingestion/`, `ml/reinforcement/`) follows the existing codebase's own established pattern — typed dataclasses for state, docstrings citing the ADR/ROADMAP sprint that motivated the module, TODOs marking exactly where a stub becomes a real integration, matching `mcp/tools/customer.py` and `agents/recommendation/approval_queue.py`'s style, not introduced as a one-off convention.
- **Scalability**: every abstraction added is interface-first — `VectorStore` (ChromaDB today, FAISS or a Snowflake-backed store tomorrow, same call sites), `complete(prompt, task_type)` (any provider behind it, same call sites) — so scaling a component up is a backend swap behind a stable interface, not a rewrite of its callers.

## Related

- [`model_versioning.md`](model_versioning.md) — model-specific versioning detail this document doesn't duplicate
- [`mlflow/`](../mlflow/) — the experiment-tracking implementation
- [`agents/llm_gateway/README.md`](../agents/llm_gateway/README.md) — the LLM-comparison instance of stage 1
- [`ml/reinforcement/README.md`](../ml/reinforcement/README.md) — the RL policy-versioning instance of stage 2, once promoted out of extension status
