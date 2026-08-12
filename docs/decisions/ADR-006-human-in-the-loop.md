# ADR-006 — Nenhum agente executa ação consequente sem aprovação humana

**Status:** Aceito
**Data:** 2026-08-10

## Contexto

O Recommendation Agent pode sugerir merges de cadastro, reembolsos ou campanhas de retenção. Executar isso automaticamente é o tipo de decisão que, errada, gera dano real (mesmo em um projeto de portfólio, o padrão de design importa mais que o dado ser sintético).

## Decisão

Toda ação que altera estado (merge de Golden Record, reembolso, oferta de retenção) passa por um **gate de aprovação humana** explícito antes de ser marcada como "executada". O agente produz: recomendação + confiança + evidências; um humano aprova ou rejeita; só então a ação é aplicada e logada como tal.

## Alternativas consideradas

1. **Auto-executar acima de um limiar de confiança (ex: >95%)** — rejeitado: mesmo com confiança alta, decisões de reembolso/merge exigem accountability humana (também alinhado a LGPD Art. 20 — direito a revisão de decisão automatizada).
2. **Sem nenhum mecanismo de aprovação (agente só sugere, sem rastrear decisão)** — rejeitado: perde a trilha de auditoria que demonstra governança de IA madura.

## Consequências

- Positivas: alinhado com o padrão que o próprio mercado (bancos, Itaú incluso) exige de qualquer sistema de decisão automatizada; gera um artefato de auditoria natural para demo.
- Negativas: adiciona uma etapa de UI/fluxo (fila de aprovação) que precisa ser implementada (`agents/recommendation/approval_queue.py`, Sprint 14).
