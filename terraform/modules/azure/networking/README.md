# modules/azure/networking

Provisions a VNet with the two delegated subnets (`public`/`private`) Azure Databricks requires for **VNet injection** (secure cluster connectivity, no public IPs on cluster nodes), plus a baseline NSG. This is the networking prerequisite consumed by `modules/databricks/workspace` and demonstrates the enterprise-grade deployment pattern even though this portfolio runs a single-region, low-traffic footprint.

Built in **Sprint 16** ([ROADMAP.md](../../../../ROADMAP.md)) as part of the governance/security hardening pass — see [ARCHITECTURE.md §16](../../../../ARCHITECTURE.md#16-layer-13--governance--security).
