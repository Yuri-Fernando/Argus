# modules/azure/resource_group

Provisions the single Azure Resource Group every other `modules/azure/*` module deploys into for a given environment. Deliberately trivial — it exists so the naming/tagging logic lives in exactly one place instead of being copy-pasted into every other module.

Built in **Sprint 1** ([ROADMAP.md](../../../../ROADMAP.md)) alongside the ADLS module, since both are needed before anything else can be provisioned. See [ARCHITECTURE.md §18](../../../../ARCHITECTURE.md#18-layer-15--infrastructure-as-code).
