# Imposto Seletivo (IS) — Visão Geral Sintética

*Resumo educacional de alto nível, escrito para este projeto de portfólio — não é aconselhamento
fiscal ou jurídico. Ver `docs/decisions/ADR-015-fiscal-tax-reform-extension.md`.*

## O que é
O **Imposto Seletivo** é um tributo federal adicional, previsto na Reforma Tributária, incidente
sobre bens e serviços considerados prejudiciais à saúde ou ao meio ambiente — por isso também
chamado informalmente de "imposto do pecado" (sin tax), um mecanismo já usado em outros países
para desestimular o consumo de certas categorias através do preço.

## Categorias tipicamente afetadas
- Bebidas alcoólicas
- Cigarros e produtos derivados do tabaco
- Bebidas açucaradas
- Veículos, embarcações e aeronaves de alto impacto ambiental (dependendo da regulamentação)

Neste projeto, a coluna `product_category` de `data/synthetic/fiscal/fiscal_documents.csv` marca
como elegíveis ao Imposto Seletivo apenas um subconjunto ilustrativo de categorias (bebida
alcoólica, cigarros, refrigerante açucarado) — uma simplificação para fins de demonstração, não
uma lista oficial e completa de incidência.

## Como se soma ao IBS/CBS
O Imposto Seletivo incide **além** do IBS e da CBS, não em substituição a eles — um produto
elegível carrega três alíquotas simultâneas sobre o mesmo valor de base. É por isso que
`data/synthetic/generators/fiscal.py::_correct_tax()` soma as três alíquotas (`ibs_rate +
cbs_rate + imposto_seletivo_rate`) ao calcular o tributo total esperado de um item, exceto quando
a operação tem CST de imunidade ou isenção, caso em que o tributo total correto é zero
independentemente das alíquotas cadastradas.
