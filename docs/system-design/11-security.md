# 11 — Segurança

- **Zero-trust interno**: mTLS obrigatório entre serviços (Istio
  `PeerAuthentication STRICT`). Nenhuma chamada serviço-a-serviço em texto
  claro.
- **AuthN/AuthZ**: OIDC no gateway; tokens propagados; autorização por
  serviço (RBAC + ABAC para dados de cliente).
- **Segredos**: AWS Secrets Manager / SSM; nunca em imagem ou repo. IRSA
  (IAM Roles for Service Accounts) no EKS.
- **Least privilege**: uma role IAM por serviço, escopo mínimo (S3 prefix,
  tópico Kafka, tabela).
- **Supply chain**: SBOM por imagem, scan de dependências e de imagem no
  CI (`.github/workflows/security.yml`), imagens assinadas.
- **Dados**: PII pseudonimizada na ingestão (ver `governance/`), acesso a
  dado sensível auditado (hash-chain).
- **IA generativa**: guardrails de prompt (ADR-007), aprovação humana para
  ações (ADR-006), avaliação adversarial antes do deploy (ver 12 e ThemisAI).
