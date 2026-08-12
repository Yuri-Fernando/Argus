# Access Control (RBAC)

Role-based access control model for both Unity Catalog (Databricks) and Snowflake, and how MCP tool calls inherit these roles rather than running under their own elevated identity. Enforced in `terraform/modules/databricks/` and `terraform/modules/snowflake/` (owned by the infrastructure workstream); this document is the human-readable contract those modules implement.

## Unity Catalog roles

| Role | Can see | Can do | Cannot do |
|---|---|---|---|
| `data_engineer` | All Bronze/Silver/Gold tables (masked PII per [`pii.md`](pii.md) in interactive SQL; unmasked only inside a scheduled pipeline execution context) | Create/modify tables in `bronze`/`silver`/`gold`, run Workflows, deploy DABs | Grant catalog-level permissions to others; unmask PII in ad-hoc interactive queries |
| `data_analyst` | Gold tables and Metric Views only, PII masked by default | Query Gold + Metric Views, build Power BI reports against them | Query Bronze/Silver directly; see unmasked PII |
| `data_steward` | All layers, PII unmasked when access is logged against a justification | Approve Golden Record merges flagged `HUMAN_REVIEW` ([ARCHITECTURE.md §8](../ARCHITECTURE.md#8-layer-5--mdm--golden-record)), correct survivorship decisions, unmask PII for investigation | Modify pipeline code or infrastructure |
| `ml_engineer` | Feature tables (`customer_intelligence.ml`), Gold tables, model registry | Train/register models in MLflow, read features (pseudonymous keys only, PII masked — [`pii.md`](pii.md)) | Modify Golden Record survivorship rules; unmask PII |
| `agent_service_account` | Nothing on its own — every grant is inherited from the calling human user at request time | Execute MCP tool calls scoped to the inheriting user's own role | Hold a standing elevated grant of its own; act after a session ends |

Catalog/schema scope: `customer_intelligence.{bronze,silver,gold,ml,monitoring}` — see [`data_catalog.md`](data_catalog.md).

## Snowflake roles

Snowflake roles mirror the Unity Catalog roles above, applied to `CUSTOMER_INTELLIGENCE.{RAW,STAGING,CORE,ANALYTICS,SEMANTIC,AI}` ([`data_catalog.md`](data_catalog.md)):

| Role | Can see | Can do | Cannot do |
|---|---|---|---|
| `DATA_ENGINEER` | `RAW`/`STAGING`/`CORE`, masked PII in interactive worksheets | Build/refresh Streams + Tasks from Databricks, manage `STAGING`/`CORE` objects | Unmask PII interactively; grant roles |
| `DATA_ANALYST` | `CORE`/`ANALYTICS`/`SEMANTIC`, PII masked by masking policy | Query Semantic Views, build Cortex Analyst questions | Query `RAW`; see unmasked PII; use `AI` schema functions directly (routed through governed tools only) |
| `DATA_STEWARD` | All schemas, PII unmasked with logged justification | Approve/correct MDM decisions surfaced via `query_snowflake`; investigate masking-policy exceptions | Modify warehouse/compute configuration |
| `ML_ENGINEER` | `CORE`/`ANALYTICS`, feature-relevant `ML`-adjacent views | Read training data (pseudonymous keys, PII masked) | Unmask PII |
| `AGENT_SERVICE_ACCOUNT` | Nothing standing — same inheritance model as Unity Catalog | Execute Cortex Agents / `query_snowflake` MCP tool calls scoped to the inheriting user's role | Hold a standing elevated grant |

Snowflake enforces this with **masking policies** (column-level) and **row-access policies** (row-level, e.g. restricting a support agent's row visibility to their own assigned tickets) on the PII columns identified in [`pii.md`](pii.md) — `email`, `phone`, `document_hash`, and the quasi-identifiers. Warehouses double as cost boundaries per role/workload ([ARCHITECTURE.md §16](../ARCHITECTURE.md#16-layer-13--governance--security)).

## MCP tool call inheritance

Per [ADR-004](../docs/decisions/ADR-004-mcp-strategy.md), every interaction between an agent and data goes through MCP rather than free-form SQL generation specifically because MCP tool calls can carry and enforce a caller's role — this is the mechanism, not just the policy:

1. **Custom MCP server** (`mcp/server/`) — every tool (`get_customer`, `query_snowflake`, `recommend_action`, etc.) receives the calling user's authenticated session alongside the tool arguments. The server resolves that session to a Unity Catalog / Snowflake role **at call time** and executes the underlying query under that role's grants — never under a broad service-account role. A `data_analyst`-scoped user calling `get_customer` gets a masked response; a `data_steward`-scoped user calling the identical tool with the identical arguments gets an unmasked one, and the distinction is enforced by the warehouse/catalog grant, not by application-layer conditional logic that could be bypassed by prompt injection (see [`security.md`](security.md), Elevation of privilege row).
2. **Databricks Managed MCP (Genie)** — GA since early 2026, and this is exactly why it is treated as the primary MCP path over the custom server for Databricks-native questions: every tool call **natively inherits the caller's Unity Catalog permissions** without any custom inheritance code to get wrong ([IMPROVEMENTS_AND_RESEARCH.md §1](../IMPROVEMENTS_AND_RESEARCH.md#1-achados-de-pesquisa-agostoo2026--correções-ao-design-original)).
3. **Cortex Agents / Cortex Analyst** — queries run against Semantic Views under the calling user's Snowflake role; masking policies apply identically whether the query originates from a human's SQL worksheet or from Cortex Analyst's generated SQL.
4. **`agent_service_account` / `AGENT_SERVICE_ACCOUNT`** exists as an identity for background/scheduled agent runs (e.g. the Monitoring Agent's periodic health checks) that have no human caller to inherit from — this account is deliberately scoped to the **narrowest** possible read-only grant set (pipeline/model health metrics, never customer PII), so that even a fully compromised agent process cannot reach PII on its own authority. Any agent action that touches customer data always requires a human-attributable session to inherit from.

This inheritance model is what makes the **Elevation of privilege** row in [`security.md`](security.md) tractable: an agent cannot "become" more privileged than the human it is currently acting for, because it never holds standing privilege of its own to escalate from.

## Related

- [`pii.md`](pii.md) — the field classification and masking table these roles enforce.
- [`security.md`](security.md) — the threat model this inheritance model defends against.
- [`data_catalog.md`](data_catalog.md) — the catalog/schema scope these grants apply to.
- [ADR-004 — MCP strategy](../docs/decisions/ADR-004-mcp-strategy.md) — why MCP, specifically, is the mechanism.
