# architecture/

Visual source-of-truth companion to [`ARCHITECTURE.md`](../ARCHITECTURE.md) (the Mermaid diagrams there are the always-up-to-date version; files here are the polished/exported versions for the README hero image and for slide decks).

## Contents (to be added — Sprint 0/16)

- `architecture.drawio` / `architecture.png` — the reference architecture diagram (ARCHITECTURE.md §2), exported for non-Markdown contexts (LinkedIn post, PDF resume attachment).
- `data-flow.drawio` — the end-to-end data flow (source → lake → lakehouse → warehouse → semantic → consumption).
- `ai-agent-flow.drawio` — the MCP/agent orchestration flow (ARCHITECTURE.md §15).
- `security.drawio` — governance/security boundary diagram (ARCHITECTURE.md §16).
- `decisions/` — **do not use this folder**; ADRs live in [`../docs/decisions/`](../docs/decisions/), kept together with the rest of the written documentation.

## Convention

Every diagram here must have a Mermaid equivalent embedded directly in the relevant `.md` file (renders natively on GitHub, no export step needed to stay current). `.drawio`/`.png` exports exist only for contexts that can't render Mermaid.
