# modules/azure/key_vault

Provisions the Key Vault that backs the "no credentials in code/config ever" rule in [ARCHITECTURE.md §16](../../../../ARCHITECTURE.md#16-layer-13--governance--security). RBAC authorization is enabled (rather than legacy access policies) and the applying identity is granted Key Vault Administrator so downstream modules (`data_factory`, `openai`, CI/CD) can be wired to read/write secrets through role assignments instead of hardcoded policy lists.

Built in **Sprint 1** ([ROADMAP.md](../../../../ROADMAP.md)), hardened further in **Sprint 16** (governance pass).
