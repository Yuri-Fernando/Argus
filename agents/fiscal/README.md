# agents/fiscal/

**Fiscal Root-Cause Agent** — [ADR-015](../../docs/decisions/ADR-015-fiscal-tax-reform-extension.md), addressing `tributario.txt`'s fiscal/regulatory domain gap and the "otimização de LLMs" backlog item from `add2.txt`, in one bolt-on extension.

```
agents/fiscal/
├── root_cause_agent.py               # diagnose_tax_discrepancy(fiscal_document_id) -> TaxDiagnosis
├── tax_discrepancy_classifier.py     # local TF-IDF+LogReg classifier, no LLM round-trip
├── test_tax_discrepancy_classifier.py
└── evaluation/golden_questions.yaml
```

## The problem this solves

`IMPROVEMENTS_AND_RESEARCH.md` §5.1 documented two real, deliberately-left-open gaps: no fiscal/tributário domain data despite `tributario.txt` asking for it, and no VLM use case in the platform. Rather than bolt on an unrelated tax dataset, this extension's synthetic fiscal documents (`data/synthetic/generators/fiscal.py`) close **both** at once: a scanned fiscal document is exactly the input `rag/local_stack/document_parser.py::DoclingVlmDocumentParser` needs, and the tabular version of the same data gives this agent something real to diagnose.

This agent is structurally the fiscal-domain sibling of `agents/quality/data_quality_agent.py` — same shape (pure function → dataclass with `.as_text()`), same human-in-the-loop discipline (read/diagnose-only, never auto-corrects a document), same local-classifier-with-fallback pattern. See that agent's README-equivalent (its own module docstring) and [ADR-011](../../docs/decisions/ADR-011-local-rag-stack.md)'s "LangChain vs. Agno vs. LangGraph" table for why a fixed four-part diagnosis over structured data uses this pattern, not the Agno multi-tool-selection pattern of `agents/knowledge_ingestion/agent.py`.

## What it diagnoses

Three deliberately-injected fiscal data problems (`data/synthetic/generators/fiscal.py::FiscalDirtyRates`):

| Category | What it means |
|---|---|
| `invalid_ncm` | The item's NCM (product classification) code isn't in the platform's synthetic catalog |
| `cst_cfop_mismatch` | An exempt/immune CST is paired with a normal taxed-sale CFOP — a logically inconsistent combination |
| `rate_out_of_range` | One of the three reform taxes (IBS/CBS/Imposto Seletivo) has a rate outside `[0, 1]` — a data-entry sign-flip bug |

Every synthetic document's true tax figure and (if dirty) discrepancy reason is recorded in `data/synthetic/fiscal/fiscal_documents_ground_truth.csv` — `diagnose_tax_discrepancy()` reads it via `mcp/tools/fiscal.py`, never fabricates a discrepancy for a genuinely clean document (see `agents/fiscal/evaluation/golden_questions.yaml`'s `clean-document-no-discrepancy` case — the exact bug a code-review pass caught while building this, see `BUILD_LOG.md`).

## `tax_discrepancy_classifier.py` — the actual "otimização de LLMs" implementation

Same technique and honesty discipline as `agents/quality/root_cause_classifier.py`: TF-IDF + Logistic Regression, CPU-only, no `torch`/`transformers`, trained on the platform's real fiscal DQ rule catalog (`data_quality/expectations/fiscal_document.py::get_rules()`). Real held-out numbers (not claimed): see `evaluation_report()` — run `python -m agents.fiscal.tax_discrepancy_classifier` for the current numbers.

## Related

- [ADR-015 — Fiscal/tax-reform extension](../../docs/decisions/ADR-015-fiscal-tax-reform-extension.md)
- [`data_quality/expectations/fiscal_document.py`](../../data_quality/expectations/fiscal_document.py) — the DQ rule catalog this agent's classifier trains on
- [`mcp/tools/fiscal.py`](../../mcp/tools/fiscal.py) — the two MCP tools this agent calls
- [`agents/quality/data_quality_agent.py`](../quality/data_quality_agent.py) — the reference pattern this agent mirrors
