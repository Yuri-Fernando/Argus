"""LLM Gateway — a `complete(prompt, task_type)` router across multiple model providers.

Built per ADR-012. Solves one named problem (ARCHITECTURE.md §1): every agent in this platform
(`agents/orchestrator/`, `agents/quality/`, `agents/recommendation/`, `agents/monitoring/`,
`agents/knowledge_ingestion/`) currently calls "the LLM" as if there were exactly one — Azure
OpenAI, per ARCHITECTURE.md §3's original tech stack rationale. That is still the platform's
default, but it is no longer the *only* wired-in path: this module lets a caller ask for a
`task_type` (e.g. "intent_classification" or "final_reasoning") and get routed to whichever
provider/model `agents/llm_gateway/models.yaml` currently designates as the best fit for that
task, instead of every call site hard-coding a provider SDK.

Key insight this module encodes: DeepSeek, and most other newer providers, expose an
**OpenAI-compatible** chat completions API. That means one HTTP client (`openai`'s SDK, pointed at
a different `base_url`) serves Azure OpenAI, OpenAI, and DeepSeek — no separate DeepSeek SDK
needed. Gemini is the one provider here with a genuinely different API shape, so it gets its own
thin adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

MODELS_REGISTRY_PATH = Path(__file__).parent / "models.yaml"

# Providers that speak the OpenAI-compatible chat completions API — one HTTP client class serves
# all of them, differing only by base_url + api_key. This is the concrete mechanism behind
# ADR-012's "no separate SDK per provider" claim.
OPENAI_COMPATIBLE_PROVIDERS = frozenset({"azure_openai", "openai", "deepseek"})


@dataclass
class CompletionResult:
    """The router's normalized response shape, regardless of which provider answered."""

    text: str
    provider: str
    model: str
    model_id: str
    input_tokens: int | None
    output_tokens: int | None


class LLMGatewayError(RuntimeError):
    """Raised when a task_type has no default mapping and no explicit model_id was provided."""


def _load_registry() -> dict[str, Any]:
    """Load and parse `models.yaml`. Re-read on every call (not cached) so a registry edit is
    picked up without restarting whatever process holds the router — the registry changes far
    less often than requests are served, so this cost is negligible.
    """
    with open(MODELS_REGISTRY_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_model_id(task_type: str, *, registry: dict[str, Any] | None = None) -> str:
    """Look up which model_id `models.yaml` currently designates as the default for `task_type`.

    Args:
        task_type: one of the task_type values documented in `models.yaml` (e.g.
            "intent_classification", "final_reasoning", "policy_qa").
        registry: optional pre-loaded registry dict, to avoid re-reading the file in a loop
            (e.g. from an evaluation script scoring many task_types in one run).

    Raises:
        LLMGatewayError: if `task_type` has no entry in `models.yaml`'s `defaults` section — a
            missing mapping is treated as a configuration error, never silently defaulted to an
            arbitrary model.
    """
    registry = registry or _load_registry()
    defaults = registry.get("defaults", {})
    if task_type not in defaults:
        raise LLMGatewayError(
            f"No default model configured for task_type={task_type!r} in models.yaml — "
            "add an entry to `defaults` (backed by an evaluation run, see README) before using it."
        )
    return defaults[task_type]


def get_model_spec(model_id: str, *, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fetch the full `models.yaml` entry for a given `model_id`."""
    registry = registry or _load_registry()
    for spec in registry.get("models", []):
        if spec["id"] == model_id:
            return spec
    raise LLMGatewayError(f"Unknown model_id={model_id!r} — not present in models.yaml.")


def complete(
    prompt: str,
    task_type: str,
    *,
    model_id: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> CompletionResult:
    """Route a completion request to the provider/model best suited for `task_type`.

    This is the single entrypoint every agent in this platform should call instead of importing a
    provider SDK directly — e.g. `agents/orchestrator/customer_intelligence_agent.py`'s
    `detect_intent()` node TODO ("replace the keyword heuristic ... with an LLM classification
    call") should call `complete(question, "intent_classification")`, not construct an Azure
    OpenAI client inline.

    Args:
        prompt: the fully-rendered prompt text (templating happens upstream, e.g. in
            `mcp/prompts/`).
        task_type: selects the default model via `models.yaml`, unless `model_id` overrides it.
        model_id: explicit override — used by the evaluation harness (README "Evaluating a new
            provider") to force a specific candidate model regardless of the current default.
        max_tokens: passed through to the provider call.
        temperature: passed through to the provider call; 0.0 by default since most of this
            platform's LLM calls are classification/extraction/synthesis, not creative writing.

    Returns:
        A `CompletionResult` normalized across providers.

    Raises:
        LLMGatewayError: if neither `model_id` nor a `task_type` default resolves to a known model.
    """
    registry = _load_registry()
    resolved_model_id = model_id or resolve_model_id(task_type, registry=registry)
    spec = get_model_spec(resolved_model_id, registry=registry)
    provider = spec["provider"]

    if provider in OPENAI_COMPATIBLE_PROVIDERS:
        text = _complete_openai_compatible(prompt, spec, max_tokens=max_tokens, temperature=temperature)
    elif provider == "gemini":
        text = _complete_gemini(prompt, spec, max_tokens=max_tokens, temperature=temperature)
    elif provider == "bedrock":
        text = _complete_bedrock(prompt, spec, max_tokens=max_tokens, temperature=temperature)
    else:
        raise LLMGatewayError(f"No adapter implemented for provider={provider!r} yet.")

    return CompletionResult(
        text=text,
        provider=provider,
        model=spec["model"],
        model_id=resolved_model_id,
        input_tokens=None,
        output_tokens=None,
    )


def _complete_openai_compatible(
    prompt: str, spec: dict[str, Any], *, max_tokens: int, temperature: float
) -> str:
    """Shared adapter for Azure OpenAI / OpenAI / DeepSeek — all speak the same chat completions
    shape, differing only in `base_url` + credential source.

    TODO(Sprint 14 extension): wire the real client, one `openai.OpenAI(...)` instance per
    provider, base_url resolved from environment variables (per ADR-010's local-vs-cloud endpoint
    discipline — never hard-coded here):
        - azure_openai -> AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY (azure-specific auth flow)
        - openai       -> default OpenAI base_url, OPENAI_API_KEY
        - deepseek     -> base_url="https://api.deepseek.com", DEEPSEEK_API_KEY
    All three then call `.chat.completions.create(model=spec["model"], messages=[...], ...)`
    identically — this is the concrete "one HTTP client serves several providers" claim from the
    module docstring and ADR-012.
    """
    _ = (prompt, spec, max_tokens, temperature)
    return ""


def _complete_gemini(prompt: str, spec: dict[str, Any], *, max_tokens: int, temperature: float) -> str:
    """Adapter for Google Gemini — genuinely different SDK shape from the OpenAI-compatible group.

    TODO(Sprint 14 extension): wire `google-genai`'s client:
        from google import genai
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(model=spec["model"], contents=prompt, ...)
    """
    _ = (prompt, spec, max_tokens, temperature)
    return ""


def _complete_bedrock(prompt: str, spec: dict[str, Any], *, max_tokens: int, temperature: float) -> str:
    """Adapter for AWS Bedrock — added in Sprint 17 (ROADMAP.md) per the gap identified in
    IMPROVEMENTS_AND_RESEARCH.md §5: the project's cloud strategy is Azure-primary (ADR-001), so
    AWS Bedrock is not a default anywhere — it exists here purely as an evaluated/documented
    alternative provider, same status as deepseek-chat's honesty note in models.yaml, following
    the exact same documented-stub pattern as `_complete_openai_compatible()` / `_complete_gemini()`
    above: a real-wiring docstring plus a stub body returning "" until real AWS credentials exist.

    Genuinely different SDK/call shape from both groups above — Bedrock's `invoke_model()` takes a
    model-family-specific JSON request/response body (e.g. Anthropic Claude on Bedrock uses the
    "anthropic_version" + "messages" shape; other Bedrock model families use their own shapes), so
    this adapter cannot reuse `_complete_openai_compatible()`'s single request/response mapping.

    TODO(when real AWS credentials are configured): wire `boto3`'s Bedrock Runtime client:
        import json
        import os
        import boto3

        client = boto3.client(
            "bedrock-runtime",
            region_name=os.environ["AWS_REGION"],  # per .env.example, e.g. "sa-east-1"
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
        response = client.invoke_model(
            modelId=spec["model"],  # e.g. "anthropic.claude-3-5-sonnet-20240620-v1:0"
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                }
            ),
        )
        payload = json.loads(response["body"].read())
        return payload["content"][0]["text"]

    boto3 is intentionally NOT imported at module level (and not added to pyproject.toml's core
    `dependencies`) so importing agents/llm_gateway/router.py never requires installing an AWS SDK
    that most local-dev/demo runs of this platform (Azure-primary, per ADR-001) will never use —
    mirrors why `google-genai` lives in the optional `genai-extra` extra, not core dependencies.
    """
    _ = (prompt, spec, max_tokens, temperature)
    return ""
