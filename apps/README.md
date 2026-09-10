# apps/ — Frontend (Angular)

`web-shell` é o host de navegação. Cada área de produto é servida por uma
rota; na arquitetura-alvo cada uma é um **microfrontend** com deploy
independente, carregado em runtime via **Module Federation**
(`web-shell/webpack.config.js` + `@angular-architects/module-federation`).

| Área | Porta (alvo) | Domínio | Status |
|---|---|---|---|
| `web-shell` | 4200 | host / navegação | ✅ **builda** (`ng build` production, Angular 18) |
| Customer MFE | 4201 | Customer 360, busca, merge | 🗺️ hoje é componente local no shell |
| Analytics MFE | 4202 | churn, segmentação, KPIs | 🗺️ hoje é componente local no shell |
| AI Operations MFE | 4203 | RAG, agentes, aprovações (HITL) | 🗺️ hoje é componente local no shell |
| Governance MFE | 4204 | políticas, fairness, model risk | 🗺️ hoje é componente local no shell |

## Estado atual

`web-shell` é um **workspace Angular 18 real e buildável**:

```bash
cd apps/web-shell
npm ci
npm run build          # ng build production -> dist/web-shell
npm start              # ng serve em :4200
```

`ng build` gera o bundle do shell + **um lazy chunk por área**
(`customer` / `analytics` / `ai-operations` / `governance`). Job `web-shell`
no workflow `.github/workflows/enterprise-v2.yml`.

Enquanto os *remotes* não existem, as rotas (`src/app/app.routes.ts`)
carregam componentes locais lazy. A troca para `loadRemoteModule` (Module
Federation) é local a esse arquivo — `webpack.config.js` já traz a config
dos 4 remotes.

> Next.js do RetentIQ **não** é substituído (ADR próprio). Angular fica só
> aqui, deliberadamente (ADR-017 do Argus não cobre front — decisão
> registrada no README raiz).
