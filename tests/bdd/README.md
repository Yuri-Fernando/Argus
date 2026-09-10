# tests/bdd/

Testes BDD (Gherkin em PT-BR) com **behave**. Cada `.feature` descreve um
comportamento de negócio; os steps em `steps/` executam contra código real
(aqui: o bus de `platform/messaging` + o contrato score→evento do
churn-service).

```bash
behave tests/bdd
```

Equivalente Java (serviços Spring): Cucumber, mesmas features.
