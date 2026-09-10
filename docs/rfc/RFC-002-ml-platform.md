# RFC-002 — ML Platform: do notebook ao serviço governado

**Status:** Proposto · **Data:** 2026-09-10

## Resumo

Padronizar o ciclo de vida de modelo em etapas versionadas e testáveis
independentemente, com **gates obrigatórios** antes de produção.

## Fluxo proposto

```text
data-product  ->  feature engineering  ->  training  ->  evaluation
     ->  MLflow (registro + estágio "Staging")
     ->  GATE: qualidade + fairness + privacidade + robustez adversarial (ThemisAI)
     ->  se aprovado: build de imagem -> ECR -> deploy canary (EKS) -> "Production"
     ->  monitoramento (Evidently): drift -> model.drift.detected -> re-treino
```

## Componentes (`ml-platform/`)

| Pasta | Responsabilidade |
|---|---|
| `datasets/` | referência a Data Products + splits versionados |
| `feature-engineering/` | transformações reutilizáveis (offline + online parity) |
| `training/` | jobs de treino parametrizados, logam em MLflow |
| `evaluation/` | métricas + cortes por subgrupo |
| `registry/` | convenções de nome/estágio no MLflow |
| `adversarial-evaluation/` | chama ThemisAI `run_security_assessment`; decide aprovação |
| `deployment/` | template de serviço de inferência + canary |
| `monitoring/` | drift, qualidade de predição, alertas |

## Gate de promoção (decisão binária)

```
promote(model) if:
  metric_primary >= threshold
  AND fairness_gap <= max_gap
  AND privacy_risk in {LOW, MEDIUM}
  AND robustness.overall_risk in {LOW, MEDIUM}
  AND robustness.robust_accuracy >= min_robust_acc
```

## Alternativas

- **CI genérico + deploy manual** — sem gate consistente; robustez/fairness
  viram "quando alguém lembra".
- **Plataforma de MLOps SaaS** — fora do princípio local-first (ADR-010)
  para o caminho de desenvolvimento.
