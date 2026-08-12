# agents/llm_gateway/

**Multi-model LLM routing** — [ADR-012](../../docs/decisions/ADR-012-llm-gateway-multimodel.md), addressing the `add2.txt` requirement to "experimentar e integrar diferentes LLMs (OpenAI, Gemini, DeepSeek, etc.), avaliando tecnicamente os cenários de uso e trade-offs de performance/custo."

```
agents/llm_gateway/
├── router.py     # complete(prompt, task_type) — the single entrypoint every agent should call
└── models.yaml   # model registry: provider, model, cost/1M tokens, latency tier, best-fit task types
```

## The problem this solves

ARCHITECTURE.md §3 picked **LangGraph + Azure OpenAI** as the platform's agent orchestration and reasoning stack — that choice stands, and Azure OpenAI remains the default for the platform's core reasoning calls (data residency, Azure-native integration with Key Vault/Entra ID, matches the target job market). What was missing is an honest answer to "what if a task is cheap enough that GPT-4o is overkill, or a competitor model is measurably better/cheaper for a specific task?" — every call site hard-coding one provider makes that question impossible to answer without a rewrite. `router.py`'s `complete(prompt, task_type)` interface is the fix: one call, routed by a registry (`models.yaml`) that can change without touching agent code.

This is deliberately **not** "add every SDK to look busy" — per [ARCHITECTURE.md §1](../../ARCHITECTURE.md#1-design-principles), the one named problem is *"the platform needs to make a defensible, evaluated cost/latency/quality trade-off per task type, instead of one model for everything."*

## Why one HTTP client can serve several providers

Azure OpenAI, OpenAI, and DeepSeek all expose an **OpenAI-compatible chat completions API** — `router.py`'s `_complete_openai_compatible()` is the one adapter that serves all three, differing only by `base_url` and credential source. Gemini has a genuinely different SDK shape and gets its own adapter (`_complete_gemini()`). This is why `models.yaml` lists DeepSeek as a routable provider without a `deepseek` line ever appearing in `pyproject.toml` — see the comment there.

## Model registry (`models.yaml`)

Each entry records: provider, model, approximate cost per 1M tokens (blended input+output), a relative latency tier, and the `task_type`s it's the best fit for. The `defaults` section is the actual routing table `resolve_model_id()` reads. Two illustrative rows:

| task_type | Default model | Rationale |
|---|---|---|
| `intent_classification` | `azure-gpt-4o-mini` | High-volume, low-reasoning-difficulty call (the orchestrator's `detect_intent` node) — a cheap/fast model is the right trade-off; correctness cost of a misclassified intent is low because `validate_data`/retry logic downstream catches most failures |
| `final_reasoning` | `azure-gpt-4o` | Composing the actual customer-facing answer — the platform's strongest available model, because being wrong here is the expensive failure mode, not latency or token cost |

## Evaluating a new provider or model

Before a model_id becomes a `defaults` entry, it should be run through `agents/*/evaluation/golden_questions.yaml` (the same harness described in ARCHITECTURE.md §15's "AI security" paragraph) with `model_id` explicitly overridden in `complete()`, scored on: accuracy against the golden answer set, p50/p95 latency, and cost per 1000 requests at the observed token count. Changing `defaults` in `models.yaml` without a benchmark run backing it is the one thing this module explicitly asks reviewers not to accept — the registry is meant to be evaluated, not vibes-based.

## LLM optimization: quantization and fine-tuning as a cost lever

`add2.txt` also names "conhecimento sobre otimização de LLMs (quantização, fine-tuning, etc.)" as a target-role skill. This platform doesn't implement it — implementing a fine-tuning pipeline would be disproportionate to what a portfolio project needs to prove, and would risk the exact anti-pattern ARCHITECTURE.md §1 warns against (a tool bolted on without a named problem it solves *today*). Instead it is documented honestly as a **backlog item with a concrete target**, in [IMPROVEMENTS_AND_RESEARCH.md §4](../../IMPROVEMENTS_AND_RESEARCH.md):

> Replace the Data Quality Agent's `dq_category_classification` LLM call (currently routed to `azure-gpt-4o-mini` in `models.yaml`) with a small, fine-tuned local classifier — e.g. a `distilbert`-class model fine-tuned on labeled DQ root-cause categories, quantized (INT8 via `onnxruntime` or `bitsandbytes`) for CPU inference — eliminating a per-call LLM cost and network round-trip for a closed-set classification task that doesn't need a general-purpose LLM at all. This is the textbook LLMOps cost-optimization move: only the tasks that genuinely need open-ended reasoning (`final_reasoning`, `policy_qa`) should ever call a hosted LLM.

## Related

- [ADR-012 — LLM Gateway / multi-model strategy](../../docs/decisions/ADR-012-llm-gateway-multimodel.md)
- [ARCHITECTURE.md §3 — Tech stack rationale](../../ARCHITECTURE.md#3-tech-stack-rationale) — original LangGraph + Azure OpenAI entry, unchanged as the default
- [`agents/orchestrator/customer_intelligence_agent.py`](../orchestrator/customer_intelligence_agent.py) — the `detect_intent`/`reason` nodes this gateway is meant to back
- [`versioning/experimentation_pipeline.md`](../../versioning/experimentation_pipeline.md) — the experiment→version→publish discipline this registry's evaluation flow follows
