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
