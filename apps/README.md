# apps/ — Frontend (Angular Microfrontends)

`web-shell` é o host; cada área de produto é um **microfrontend** com deploy
independente, carregado em runtime via **Module Federation**
(`@angular-architects/module-federation`).

| Remote | Porta | Domínio | Status |
|---|---|---|---|
| `web-shell` | 4200 | host / navegação | 🗺️ skeleton (configs válidas) |
| `customer-mfe` | 4201 | Customer 360, busca, merge | 🗺️ planejado |
| `analytics-mfe` | 4202 | churn, segmentação, KPIs | 🗺️ planejado |
| `ai-operations-mfe` | 4203 | RAG, agentes, aprovações (HITL) | 🗺️ planejado |
| `governance-mfe` | 4204 | políticas, fairness, model risk | 🗺️ planejado |

> **Status:** 🗺️ skeleton. `package.json`, `webpack.config.js` (Module
> Federation), `tsconfig.json` e `src/` são válidos e coerentes, mas o
> `ng build` não roda neste ambiente (pasta sincronizada + sem `ng` CLI
> instalado — ver regra de node-env). Next.js do RetentIQ **não** é
> substituído (ADR do RetentIQ); Angular fica só aqui, deliberadamente
> (ADR-017 não cobre front — decisão registrada no README do Argus).
