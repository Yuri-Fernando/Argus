# ADR-009 — Dataset real (Olist) + dados sintéticos com sujeira proposital, nenhum PII real

**Status:** Aceito
**Data:** 2026-08-10

## Contexto

Um projeto de MDM/Data Quality precisa de dados com problemas reais (duplicidade, campos ausentes, inconsistência) para ter algo a resolver. Um dataset 100% real e limpo (só Olist) não teria problema de qualidade suficiente para demonstrar MDM; um dataset 100% sintético não teria a credibilidade de "dado real de e-commerce". Usar dados reais de clientes (CPF/e-mail/telefone reais) está descartado por razões éticas e legais (LGPD), mesmo sendo um projeto pessoal.

## Decisão

Combinar: **Olist Brazilian E-Commerce Public Dataset** (real, anonimizado, licença CC BY-NC-SA 4.0, ~100 mil pedidos — https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) como espinha dorsal transacional, com **dados sintéticos gerados localmente** (CRM, Marketing, Support, Web, Finance, Documentos) via `Faker` com seed determinística, contendo sujeira proposital e documentada (ver [DATA_MODEL.md §5](../../DATA_MODEL.md#5-synthetic-data-generation-strategy)). Nenhum CPF/e-mail/telefone real é usado em lugar nenhum do repositório — mesmo os sintéticos usam hash SHA-256 em qualquer campo de documento.

## Alternativas consideradas

1. **Só Olist, sem fontes sintéticas** — rejeitado: não haveria múltiplos sistemas de origem para o MDM resolver, o que é o cerne do projeto.
2. **Dados sintéticos gerados sem seed fixa** — rejeitado: sem reprodutibilidade, o score de DQ e o benchmark de MDM mudam a cada execução, tornando impossível comparar resultados entre sprints ou demonstrar regressão.
3. **Baixar/usar um dataset de CRM real (mesmo anonimizado por terceiros)** — rejeitado: risco de reidentificação e de licenciamento incerto; a geração sintética documentada é mais segura e mais controlável.

## Consequências

- Positivas: reprodutibilidade total (`--seed 42` sempre gera os mesmos dados), zero risco de PII real vazado, controle fino sobre a taxa de "sujeira" para demonstrar a resposta do pipeline de DQ/MDM a diferentes cenários.
- Negativas: dados sintéticos não capturam toda a complexidade real de um CRM corporativo — declarado explicitamente como limitação no README, não escondido.
