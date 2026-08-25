# modules/azure/monitoring

Provisions Log Analytics + Application Insights and a `diagnostic_targets` map that lets `environments/dev/main.tf` opt individual resources (ADLS, ADF, Event Hubs, Key Vault) into platform-log export, forming the Azure-native half of the observability stack in [ARCHITECTURE.md §17](../../../../ARCHITECTURE.md#17-layer-14--observability--finops). The portable half (OpenTelemetry → Prometheus/Grafana) lives outside Terraform in `monitoring/` and is cloud-agnostic by design.

Built in **Sprint 16** ([ROADMAP.md](../../../../ROADMAP.md)).
