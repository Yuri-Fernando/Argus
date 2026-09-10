# platform/service-mesh/istio/

Manifests de referência do service mesh (ADR-023). Aplicados a um
subconjunto de serviços primeiro (prova de conceito), não à malha inteira.

| Arquivo | O que demonstra |
|---|---|
| `peer-authentication.yaml` | mTLS `STRICT` no namespace (zero-trust interno) |
| `inference-destinationrule.yaml` | connection pool + circuit breaker (outlier detection) + subsets v1/v2 |
| `inference-virtualservice.yaml` | timeout, retry e **canary** (90/10) por peso; roteamento por header para testes |

> **Status:** 🗺️ referência. Requer um cluster com Istio instalado
> (`istioctl install`) — não executado no ambiente local.
