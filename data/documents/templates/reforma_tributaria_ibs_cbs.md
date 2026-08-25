# Reforma Tributária — IBS e CBS (Resumo Educacional Sintético)

*Este documento é um resumo educacional de alto nível, escrito para o Enterprise Customer
Intelligence Platform (projeto de portfólio) — não é um texto legal oficial, não substitui a
Emenda Constitucional 132/2023, sua lei complementar, ou qualquer regulamentação vigente, e não
deve ser usado como fonte de conformidade fiscal real. Ver `docs/decisions/
ADR-015-fiscal-tax-reform-extension.md` para o escopo desta extensão.*

## O que muda
A Reforma Tributária substitui um conjunto de tributos sobre consumo (PIS, Cofins, IPI, ICMS,
ISS) por um modelo de **IVA dual**: o **IBS** (Imposto sobre Bens e Serviços — competência
estadual e municipal) e a **CBS** (Contribuição sobre Bens e Serviços — competência federal).

## Princípios centrais
- **Não cumulatividade plena**: o imposto pago em uma etapa da cadeia gera crédito integral na
  etapa seguinte, reduzindo o efeito "imposto sobre imposto" do modelo anterior.
- **Cobrança no destino**: o tributo passa a ser recolhido no local de consumo, não no local de
  produção — mudança relevante para operações interestaduais.
- **Transição gradual**: um período de convivência entre o sistema antigo e o novo (previsto para
  se estender por vários anos) evita uma troca abrupta, com alíquotas de teste e ajustes
  progressivos.

## Situações tributárias (CST)
Cada operação carrega um **Código de Situação Tributária (CST)** que indica como o IBS/CBS incide
sobre ela — por exemplo, tributação integral, isenção, imunidade ou diferimento. O CST de uma
operação precisa ser compatível com o CFOP (código que descreve a natureza da operação) — uma
operação marcada como isenta não deveria, ao mesmo tempo, ser tratada como uma venda tributada
integral no sistema, uma inconsistência que `data_quality/expectations/fiscal_document.py` valida
neste projeto (coluna derivada `cst_cfop_valid`).

## Por que isso importa para uma plataforma de dados
Uma mudança tributária dessa magnitude é, na prática, um problema de dados: milhões de
documentos fiscais precisam ser classificados corretamente (NCM, CFOP, CST), alíquotas corretas
aplicadas por categoria de produto, e discrepâncias identificadas e corrigidas — exatamente a
disciplina de Data Quality, rastreabilidade e agentes de diagnóstico que o resto desta plataforma
já demonstra em outro domínio (customer intelligence). Ver `agents/fiscal/root_cause_agent.py`.
