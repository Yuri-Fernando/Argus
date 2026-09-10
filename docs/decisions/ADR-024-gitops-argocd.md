# ADR-024 — GitOps com Argo CD

**Status:** Aceito · **Data:** 2026-09-10

## Decisão

O estado desejado do cluster (Helm releases, manifests, config) vive no Git.
**Argo CD** reconcilia o cluster para o estado do repo continuamente. Deploy
= merge de PR que altera a tag da imagem / values do Helm. Rollback = revert
do commit.

- Ambientes (`dev`/`staging`/`prod`) como pastas/branches com values
  próprios.
- Promoção entre ambientes por PR (imagem imutável, só muda a referência).
- Drift detection: se alguém alterar o cluster à mão, Argo CD sinaliza e
  (opcionalmente) reverte.

## Alternativas

- **`kubectl apply` no CI (push-based)** — o CI precisa de credenciais de
  prod; sem reconciliação contínua nem drift detection.
- **Flux** — equivalente; Argo CD escolhido pela UI de visualização de
  sync/health, útil para portfólio e para operar.

## Consequências

- (+) Auditoria completa (todo deploy é um commit); rollback trivial;
  cluster e repo nunca divergem em silêncio.
- (−) Mais uma peça de plataforma para instalar/operar; app-of-apps precisa
  de organização desde o início.
