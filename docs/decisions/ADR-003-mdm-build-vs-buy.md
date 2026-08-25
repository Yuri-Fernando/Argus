# ADR-003 — MDM construído internamente (build), não uma ferramenta comercial (buy)

**Status:** Aceito
**Data:** 2026-08-10

## Contexto

Existem ferramentas comerciais de MDM (Reltio, Informatica MDM, Ataccama) que resolveriam entity resolution "de fábrica". Este é um projeto de portfólio cujo objetivo explícito é demonstrar competência técnica, não entregar o MDM mais barato/rápido possível.

## Decisão

Implementar MDM (resolução de entidade determinística → fuzzy → ML e Golden Record com survivorship) como código próprio em `mdm/`, usando bibliotecas abertas (`jellyfish` para Jaro-Winkler/Levenshtein, `scikit-learn`/`xgboost` para o classificador de match).

## Alternativas consideradas

1. **Ferramenta MDM comercial (SaaS)** — rejeitada: licenciada, opaca (esconde exatamente a técnica que o projeto precisa demonstrar), e inviável de custo para um projeto pessoal.
2. **Apenas matching determinístico (sem ML)** — rejeitada: não demonstra a competência de ML aplicado a um problema de dados real, e tem recall muito mais baixo em dados sujos (nomes com variação, sem e-mail).

## Consequências

- Positivas: cada etapa (determinística, fuzzy, ML) é auditável e explicável — ótimo para demo/entrevista.
- Negativas: precisão/recall não terão o refinamento de anos de um produto comercial; mitigado documentando isso na tabela de production-readiness (MDM = "Prototype → Production-like", nunca alegado como enterprise-grade "pronto para produção real").
