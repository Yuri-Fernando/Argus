# platform/read_models/ (CQRS — ADR-022)

Projeções de leitura materializadas a partir de domain events. O lado de
escrita publica `model.prediction.created` / `customer.updated`; este
consumidor materializa em SQLite:

- `customer_360(customer_id, last_score, high_risk, updates, last_seen)`
- `churn_kpis(key, value)` — `scored_customers`, `avg_score`, `high_risk_count`

**Propriedade central:** o read model é reconstruível por replay do log —
`rebuild_from_events()` produz exatamente o mesmo estado que o consumo
incremental (testado em `tests/test_churn_read_model.py`).

```python
from churn_read_model import ChurnReadModel
rm = ChurnReadModel("cqrs.db")
rm.subscribe_to(bus)          # consumo incremental
rm2 = ChurnReadModel().rebuild_from_events(event_log)  # replay
```
