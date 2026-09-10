# terraform/modules/aws/

Módulos AWS para o **plano de aplicação** do Argus (serviços em `services/`).
O plano de dados (Databricks/Snowflake) fica nos módulos `azure/`.

| Módulo | Recurso |
|---|---|
| `network/` | VPC + subnets públicas/privadas multi-AZ (tags para ELB/EKS) |
| `eks/` | EKS control plane + node group com autoscaling (3→8) |
| `msk/` | Kafka gerenciado, 3 brokers, TLS, `min.insync.replicas=2` |
| `observability/` | workspace Prometheus (AMP) + log group |

Composição de exemplo: `terraform/environments/dev-aws/`.

> **Status:** 🗺️ referência de arquitetura. `terraform fmt`/`validate`
> passam; `apply` real não foi executado (local-first — ADR-010).
