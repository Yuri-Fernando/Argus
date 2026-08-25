# cloud/

Cloud portability documentation — [ADR-001](../docs/decisions/ADR-001-cloud-strategy.md) and [ARCHITECTURE.md §19 "Cloud portability (AWS)"](../ARCHITECTURE.md#19-cloud-portability-aws).

```
cloud/
├── README.md                       # this file
├── architecture-comparison.md        # full Azure ↔ AWS service mapping, expanded from ARCHITECTURE.md §19
├── azure/
│   └── README.md                      # implemented primary cloud — points to terraform/modules/azure/
└── aws/
    └── README.md                       # documented portability target only, not implemented
```

## Why this directory exists

Per [ADR-001](../docs/decisions/ADR-001-cloud-strategy.md), the platform is built **Azure-primary** — matching the target job market (Itaú, Nubank, Mercado Livre, CI&T, BCG X, Thoughtworks, Accenture, Deloitte, Microsoft, Databricks) — while the author also has hands-on production AWS experience. Rather than building the whole platform twice, `cloud/` documents the AWS equivalent honestly: a service-by-service mapping backed by real experience, not a second implementation. See [`azure/README.md`](azure/README.md) for what's actually deployed and [`aws/README.md`](aws/README.md) for what's deliberately not.

## Related

- [ADR-001 — Cloud strategy](../docs/decisions/ADR-001-cloud-strategy.md) — the decision this directory documents.
- [ARCHITECTURE.md §19](../ARCHITECTURE.md#19-cloud-portability-aws) — the summary table this directory expands on.
- [`terraform/README.md`](../terraform/README.md) — the IaC that actually provisions the Azure side.
