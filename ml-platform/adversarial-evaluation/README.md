# ml-platform/adversarial-evaluation/

**Production robustness gate** do pipeline de MLOps (RFC-002). Um modelo só
é promovido de "Staging" para "Production" no MLflow se passar aqui.

## Integração com o ThemisAI

```python
# no job de avaliação (pseudo — themis-ai é repo separado):
from themis_ai.core.adversarial_ml import run_security_assessment
from robustness_gate import evaluate_gate, GateThresholds

report = run_security_assessment(model, X_test, y_test, n_classes=2,
                                 X_train=X_train, y_train=y_train,
                                 model_name="churn@4")
decision = evaluate_gate(report, GateThresholds(min_robust_accuracy=0.6))
if not decision.approved:
    raise SystemExit(f"BLOQUEADO: {decision.reasons}")
```

`robustness_gate.py` depende só de um **protocolo estrutural**
(`SecurityReportLike`), não do pacote do Themis — o gate é testável isolado
e o Argus não acopla sua build ao repo de governança.

## Regra de decisão

Aprovado se **todas**:
- `overall_risk` ∈ {low, medium}
- `robust_accuracy` ≥ `min_robust_accuracy` (default 0.60)
- queda `clean_accuracy − robust_accuracy` ≤ `max_clean_to_robust_drop` (default 0.35)

## Testes

```bash
pytest ml-platform/adversarial-evaluation/tests -q
```
