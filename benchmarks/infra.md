# Infrastructure / FinOps benchmarks

What this measures and why: actual cloud spend, tracked as a first-class metric rather than an
afterthought — [ARCHITECTURE.md §17](../ARCHITECTURE.md#17-layer-14--observability--finops).
Cost-per-1M-records and cost-per-agent-request are the two numbers the FinOps dashboard is built
around, and the input a future cost-guardrail automation (alert/shutdown on daily overrun) would
alert against — see [IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) backlog item 5.

| Metric | Value | Date measured | Sprint | Notes |
|---|---|---|---|---|
| Azure cost | | | | |
| Databricks DBU | | | | |
| Snowflake credits | | | | |
| storage cost | | | | |
| LLM tokens (cost) | | | | |
| cost per 1M records | | | | |
| cost per agent request | | | | |

## Related

[ARCHITECTURE.md §17](../ARCHITECTURE.md#17-layer-14--observability--finops) ·
[IMPROVEMENTS_AND_RESEARCH.md](../IMPROVEMENTS_AND_RESEARCH.md) backlog item 5 (FinOps cost guardrails)
