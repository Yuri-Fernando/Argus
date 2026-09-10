# ADR-023 — Kubernetes gerenciado (EKS) + service mesh (Istio)

**Status:** Aceito · **Data:** 2026-09-10

## Contexto

Serviços poliglotas, stateless, com necessidade de mTLS, canary,
retry/timeout e telemetria uniforme.

## Decisão

- **EKS** (Kubernetes gerenciado na AWS) como orquestrador. Control plane
  gerenciado; nós em multi-AZ; IRSA para credenciais por serviço.
- **Istio** como service mesh, aplicado a **2–3 serviços** primeiro (prova
  de conceito), não a tudo de uma vez:
  - `PeerAuthentication STRICT` (mTLS obrigatório);
  - `DestinationRule` + `VirtualService` para retry, timeout, circuit
    breaking (outlier detection) e **canary** (split de tráfego por peso);
  - telemetria automática (sem instrumentar código).
- Helm para empacotar; Argo CD para GitOps (ADR-024).

## Alternativas

- **ECS/Fargate** — mais simples de operar, mas menos portável e sem o
  ecossistema de mesh/GitOps que se quer demonstrar.
- **K8s sem mesh** (mTLS via app, retry via lib) — espalha responsabilidade
  transversal pelo código de cada serviço poliglota; o mesh centraliza.
- **Linkerd** — mais leve; Istio escolhido pela amplitude de recursos
  (canary por header, telemetria, extensibilidade) e por ser o nome mais
  cobrado no mercado.

## Consequências

- (+) mTLS, canary e observabilidade sem tocar no código dos serviços.
- (−) Overhead de sidecar (CPU/mem, latência de µs) e curva de aprendizado;
  por isso o rollout é incremental e documentado.
