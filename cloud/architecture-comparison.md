# Architecture Comparison: Azure ↔ AWS

Full expansion of the [ARCHITECTURE.md §19](../ARCHITECTURE.md#19-cloud-portability-aws) summary table: every Azure service used in this project, its AWS equivalent, and a note on the behavioral/API differences that would actually matter during a real migration — not just "these are the same category of product."

> **This is a documented mapping, not a tested or deployed AWS implementation.** Per [ADR-001](../docs/decisions/ADR-001-cloud-strategy.md), the author has hands-on production AWS experience (Itaú and personal projects) that informs the notes below, but no `terraform apply` has been run against AWS for this platform, and no AWS resource backs any claim in this repository. If a specific target role requires AWS, [`aws/README.md`](aws/README.md) is where a real Terraform AWS module set would be built — reusing the Databricks and Snowflake modules unchanged, since those two are cloud-agnostic by nature.

## Storage & ingestion

| Azure service | AWS equivalent | Migration-relevant difference |
|---|---|---|
| **ADLS Gen2** | **S3** | ADLS Gen2's hierarchical namespace gives real directory rename/move as an atomic metadata operation; S3 is flat-keyspace-with-prefixes, so a "move" is actually a copy + delete, which matters for any code that assumes cheap atomic renames (e.g. Bronze partition promotion patterns) |
| **Azure Data Factory** | **AWS Glue + Step Functions** | ADF is a single managed orchestration+ETL product; on AWS the equivalent is two separate services stitched together (Glue for the ETL jobs, Step Functions for orchestration/branching) — a straight migration means splitting ADF pipeline logic across two AWS control planes, not a 1:1 swap |
| **Azure Event Hubs** | **Amazon Kinesis Data Streams** | Event Hubs' partition model and consumer group semantics map reasonably well to Kinesis shards/consumers, but throughput-based Event Hubs pricing (Throughput Units) vs. Kinesis's shard-based pricing means capacity planning math has to be redone, not just relabeled |

## Compute & lakehouse

| Azure service | AWS equivalent | Migration-relevant difference |
|---|---|---|
| **Azure Databricks** | **Databricks on AWS** | Same product, different cloud host — this is the *least* risky migration in the whole table, since Databricks' own APIs (Unity Catalog, Delta Lake, MLflow, DABs) are identical across clouds by design. The differences are entirely in the surrounding cloud plumbing (IAM roles instead of Managed Identity for cluster instance profiles, S3 instead of ADLS as the underlying storage) |

## Identity & secrets

| Azure service | AWS equivalent | Migration-relevant difference |
|---|---|---|
| **Microsoft Entra ID** | **AWS IAM** (+ IAM Identity Center for workforce identity) | Entra ID is a full identity provider (users/groups/conditional access/SSO); IAM is primarily a permissions/policy engine for resources — a real migration needs IAM Identity Center or an external IdP (Okta, Entra ID itself federated in) to cover what Entra ID does natively, not IAM alone |
| **Azure Key Vault** | **AWS Secrets Manager** (+ optionally KMS directly) | Key Vault bundles secrets, keys, and certificates in one service; AWS splits this across Secrets Manager (secrets), KMS (keys), and ACM (certificates) — code that assumes "one vault client for everything" needs three AWS SDK clients instead of one |

## Monitoring & AI

| Azure service | AWS equivalent | Migration-relevant difference |
|---|---|---|
| **Azure Monitor** | **Amazon CloudWatch** | Broadly equivalent (metrics, logs, alerts), but Azure Monitor's Log Analytics query language (KQL) has no direct CloudWatch Logs Insights equivalent — every KQL query in `monitoring/` would need to be rewritten, not just repointed |
| **Azure OpenAI** | **Amazon Bedrock** | Both are managed LLM-access layers, but the model catalogs differ (Azure OpenAI is OpenAI-model-only; Bedrock offers Anthropic/Meta/Amazon/others) and the request/response API shapes are not compatible — every LangGraph agent node calling the LLM would need its client swapped, not just its endpoint |
| **Microsoft Purview** | **AWS Glue Data Catalog + Lake Formation** | Purview is a single cross-estate governance/catalog/classification product; on AWS the equivalent is two services (Glue Catalog for metadata, Lake Formation for fine-grained access control layered on top) — Purview's automatic Unity Catalog connector ([`governance/lineage.md`](../governance/lineage.md)) has no direct AWS-side analogue, so cross-platform lineage would need to be re-architected around Lake Formation's own permission/lineage model, not simply reconfigured |

## What does *not* need to change

Two of the platform's most consequential technology choices are already cloud-agnostic by design, and would carry over to an AWS deployment with no architectural change — only a different Terraform provider target for the surrounding infra:

- **Azure Databricks → Databricks on AWS** — same platform, same Unity Catalog objects, same Delta Lake, same MLflow.
- **Snowflake** — Snowflake is not an Azure or AWS service; it already runs identically regardless of which cloud hosts it, and `terraform/modules/snowflake/` would not change at all in an AWS migration.

This is also exactly what [ADR-001](../docs/decisions/ADR-001-cloud-strategy.md)'s "Consequences" section means by *"the `cloud/aws/` directory can be promoted to a real implementation reusing the Databricks/Snowflake modules unchanged."*

## Related

- [ADR-001 — Cloud strategy](../docs/decisions/ADR-001-cloud-strategy.md) — why AWS is documented, not implemented.
- [`azure/README.md`](azure/README.md) — the implemented primary cloud.
- [`aws/README.md`](aws/README.md) — what a real AWS implementation would look like if promoted.
- [ARCHITECTURE.md §19](../ARCHITECTURE.md#19-cloud-portability-aws) — the original summary table this document expands.
