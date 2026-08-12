# modules/azure/openai

Provisions the Azure OpenAI (Cognitive Services) account and a single chat-model deployment (default `gpt-4o`) that backs the LangGraph agents in [ARCHITECTURE.md §15](../../../../ARCHITECTURE.md#15-layer-12--mcp--agentic-ai) for calls that don't go through Snowflake Cortex. Kept to one deployment and modest TPM capacity to control portfolio cost; region is parameterized separately since Azure OpenAI is not available in every Azure region.

Built in **Sprint 14** ([ROADMAP.md](../../../../ROADMAP.md)), when the LangGraph agents first need a real LLM endpoint.
