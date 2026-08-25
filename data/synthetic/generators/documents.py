"""
Generates the four synthetic corporate policy documents used by the RAG /
Cortex Search layer (see ARCHITECTURE.md §14). Writes Markdown source into
data/documents/templates/ and always keeps a .md copy in data/documents/ —
PDF rendering is attempted via `data/documents/render.py` if `reportlab` is
installed, but is optional: the RAG pipeline can ingest the Markdown
directly, so nothing is blocked by not having a PDF renderer available.
"""
from __future__ import annotations

from pathlib import Path

DOCUMENTS: dict[str, str] = {
    "refund_policy": """# Refund Policy (Synthetic)

*This document is entirely synthetic, generated for the Enterprise Customer
Intelligence Platform portfolio project. It does not represent a real
company's policy.*

## Eligibility
Customers may request a refund within **30 days** of the delivery date if:
- The product arrived damaged or materially different from its description.
- The order was not delivered within 15 business days of the estimated
  delivery date shown at checkout.
- The customer exercises the right of withdrawal (arrependimento) within
  **7 calendar days** of receipt, per Brazilian consumer law (CDC Art. 49).

## Non-eligible cases
- Products marked as final sale / clearance.
- Requests made more than 30 days after delivery.
- Items showing signs of use beyond simple inspection.

## Process
1. Customer opens a support ticket with category `refund_request`.
2. Support validates order status and delivery date via the order system.
3. Approved refunds are processed to the original payment method within
   10 business days.
4. Refunds above R$ 1,000 require supervisor approval (human-in-the-loop).
""",
    "delivery_policy": """# Delivery Policy (Synthetic)

*Synthetic document — portfolio project only.*

## Estimated delivery windows
- Southeast region (SP, RJ, MG, ES): 3–7 business days.
- South region (RS, SC, PR): 5–9 business days.
- Other regions: 7–15 business days.

## Late delivery
An order is considered **late** if it has not been delivered by the
estimated delivery date shown at checkout. Late orders automatically
qualify for a shipping-fee refund and are flagged for the customer
support team.

## Failed delivery attempts
After 3 failed delivery attempts, the order is returned to the seller and
the customer is notified to arrange re-shipment or a refund.
""",
    "loyalty_policy": """# Loyalty Program Policy (Synthetic)

*Synthetic document — portfolio project only.*

## Tiers
| Tier | Requirement (rolling 12 months) | Benefit |
|---|---|---|
| Silver | 3+ orders | Free shipping on orders over R$150 |
| Gold | 8+ orders or R$3,000+ spent | 5% cashback + priority support |
| Platinum | 15+ orders or R$8,000+ spent | 10% cashback + dedicated agent |

## VIP flag
Customers classified as `VIP` by the ML segmentation model (see
`ml/segmentation/`) automatically receive Gold-tier benefits regardless of
order count, subject to quarterly review.
""",
    "reforma_tributaria_ibs_cbs": """# Reforma Tributária — IBS e CBS (Resumo Educacional Sintético)

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
""",
    "imposto_seletivo_visao_geral": """# Imposto Seletivo (IS) — Visão Geral Sintética

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
""",
    "privacy_policy": """# Privacy Policy (Synthetic)

*Synthetic document — portfolio project only. Written to be consistent
with LGPD (Lei Geral de Proteção de Dados) principles for demonstration
purposes; see governance/lgpd.md for the platform's actual data-handling
rules.*

## Data we collect
Name, email, phone, address, order history, support interactions and
website browsing events — always with an explicit legal basis (contract
performance or legitimate interest).

## Data we never store
Full unmasked government ID numbers. All document identifiers are
one-way hashed (SHA-256) before storage; see governance/pii.md.

## Customer rights
Access, correction, deletion, portability and revocation of consent, per
LGPD Art. 18. Requests are handled via the support ticket category
`account` and fulfilled within 15 business days.
""",
}


def generate(output_dir: Path) -> list[Path]:
    templates_dir = output_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for name, content in DOCUMENTS.items():
        md_path = templates_dir / f"{name}.md"
        md_path.write_text(content, encoding="utf-8")
        # A convenience copy at the top level, ready for RAG ingestion even
        # without a PDF renderer.
        copy_path = output_dir / f"{name}.md"
        copy_path.write_text(content, encoding="utf-8")
        written.append(md_path)
    return written
