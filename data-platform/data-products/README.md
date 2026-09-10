# data-platform/data-products/ (Data Mesh — RFC-001)

A camada Gold é organizada como **Data Products** de propriedade dos
domínios de negócio, não como tabelas técnicas sem dono.

| Data Product | Domínio | Owner | Porta de saída |
|---|---|---|---|
| `customer-360` | customer | customer-domain-team | Delta `gold.customer_360` + `/v1/customers/{id}` |
| `churn-scores` | analytics | analytics-domain-team | tópico `model.prediction.created` + Delta |
| `revenue` | sales | sales-domain-team | Delta `gold.revenue` |
| `risk` | risk | risk-domain-team | Delta `gold.risk` (extensão fiscal) |

Cada `contract.yaml` declara: **schema versionado**, **SLA** (freshness,
disponibilidade, latência), **quality rules** (validadas por Great
Expectations), **lineage** (upstream) e **política de acesso**
(classificação + masking).

Validação (roda no CI):

```bash
python data-platform/data-products/validate.py
```

Consumidores dependem do **contrato do produto**, não da tabela física —
mudança incompatível de schema é um bump de `version` com deprecação da
anterior.
