# governance/

Governance, security and compliance policy for the platform — [ARCHITECTURE.md §16 "Layer 13 — Governance & Security"](../ARCHITECTURE.md#16-layer-13--governance--security), built incrementally from **Sprint 1** (RBAC/catalog skeleton) through **Sprint 16** (full AI security + LGPD hardening).

This directory is **policy and documentation**, not code — it defines the rules that `terraform/modules/{databricks,snowflake}/`, `mcp/server/`, and `agents/*/` are built to enforce. Where a rule is enforced in code, the file below links to the enforcing path.

```
governance/
├── README.md              # this file
├── security.md             # AI/agent threat model (STRIDE) — operationalizes ADR-007
├── lgpd.md                  # LGPD compliance policy — legal basis, data subject rights, retention
├── pii.md                    # PII classification table + masking policy per role
├── lineage.md                  # Unity Catalog + Purview lineage, cross-platform limitations
├── access_control.md            # RBAC model — Unity Catalog + Snowflake roles, MCP inheritance
└── data_catalog.md                # how the platform catalogs itself — UC + Snowflake registries
```

## The six documents

| Doc | Answers | Primary ADR |
|---|---|---|
| [`security.md`](security.md) | What can go wrong specifically because agents and MCP tools exist, and what stops it? | [ADR-007](../docs/decisions/ADR-007-ai-guardrails.md) |
| [`lgpd.md`](lgpd.md) | What is the legal basis for holding this data, what rights does a data subject have, and how are they honored? | [ADR-009](../docs/decisions/ADR-009-dataset-strategy.md) |
| [`pii.md`](pii.md) | Which fields are PII, at what sensitivity, and who sees them unmasked? | — |
| [`lineage.md`](lineage.md) | Where did this value come from, and how far can that trail be followed automatically? | — |
| [`access_control.md`](access_control.md) | Who (human or agent) can do what, in Unity Catalog, Snowflake, and via MCP? | [ADR-004](../docs/decisions/ADR-004-mcp-strategy.md) |
| [`data_catalog.md`](data_catalog.md) | How is every table/schema/model registered and discoverable? | [ADR-002](../docs/decisions/ADR-002-lakehouse-vs-warehouse.md) |

## Relationship to security vs. AI security

`access_control.md` and `pii.md` cover **traditional infrastructure security** — RBAC, masking policies, Key Vault-backed secrets, the kind of control that predates any of this platform's AI layer. `security.md` covers a narrower and newer surface: **what changes once agents and MCP tools sit in front of that same governed data.** RBAC controls *what* an agent can reach; `security.md` is about *how* a malicious prompt could still misuse that reach. Both are necessary; neither substitutes for the other — see [ADR-007](../docs/decisions/ADR-007-ai-guardrails.md).

## Why this exists

The original design (`rascunho.md`) never addressed AI-specific security, formal LGPD rights handling, or a documented RBAC/lineage model — see [IMPROVEMENTS_AND_RESEARCH.md §2](../IMPROVEMENTS_AND_RESEARCH.md#2-lacunas-do-design-original-preenchidas-nesta-consolidação). This directory closes that gap. All of it is a **demonstration of governance-aware design** on synthetic and public data — see [ADR-009](../docs/decisions/ADR-009-dataset-strategy.md) — not a real Data Protection Officer's compliance program.
