"""Adapter pattern — normaliza provedores de LLM heterogêneos numa única
interface `LLMProviderPort`.

- `OpenAIAdapter` / `BedrockAdapter`: adaptam SDKs externos (importados só
  quando usados; não são dependência do serviço).
- `LocalHeuristicAdapter`: implementação local determinística, usada em
  desenvolvimento/teste e como fallback quando nenhum provedor está
  configurado (mesma filosofia local-first do resto do Argus — ADR-010).
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProviderPort(ABC):
    name: str

    @abstractmethod
    def complete(self, prompt: str) -> str: ...


class LocalHeuristicAdapter(LLMProviderPort):
    """Sem chamada externa: deriva um score do próprio conteúdo do prompt
    (soma normalizada dos números presentes em `Features: {...}`)."""

    name = "local-heuristic"

    def complete(self, prompt: str) -> str:
        import re

        nums = [float(n) for n in re.findall(r"-?\d+\.?\d*", prompt.split("Features:")[-1])]
        if not nums:
            return "risk=0.5"
        raw = sum(abs(n) for n in nums) / (len(nums) * 100.0)
        return f"risk={min(max(raw, 0.0), 1.0):.3f}"


class OpenAIAdapter(LLMProviderPort):
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.model = model
        self._api_key = api_key

    def complete(self, prompt: str) -> str:
        from openai import OpenAI  # dependência externa, importada só aqui

        client = OpenAI(api_key=self._api_key) if self._api_key else OpenAI()
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return resp.choices[0].message.content or ""


class BedrockAdapter(LLMProviderPort):
    name = "bedrock"

    def __init__(self, model_id: str = "anthropic.claude-3-haiku-20240307-v1:0", region: str = "us-east-1"):
        self.model_id = model_id
        self.region = region

    def complete(self, prompt: str) -> str:
        import json

        import boto3  # dependência externa, importada só aqui

        client = boto3.client("bedrock-runtime", region_name=self.region)
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 64,
                "messages": [{"role": "user", "content": prompt}],
            }
        )
        resp = client.invoke_model(modelId=self.model_id, body=body)
        payload = json.loads(resp["body"].read())
        return payload["content"][0]["text"]
