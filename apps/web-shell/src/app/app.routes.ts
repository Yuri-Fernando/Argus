import { Routes } from '@angular/router';

/**
 * Rotas do shell. Cada área é um microfrontend independente.
 *
 * Arquitetura-alvo (ADR-017 do Argus): carregar cada área como um *remote*
 * via Module Federation (`webpack.config.js` + @angular-architects/module-
 * federation), com deploy próprio nas portas 4201-4204. Enquanto os remotes
 * não existem, as rotas apontam para componentes locais (lazy) — o shell
 * builda e navega, e a troca para `loadRemoteModule` é local a este arquivo.
 */
export const routes: Routes = [
  { path: 'customer', loadComponent: () => import('./mfe/customer.component').then(m => m.CustomerComponent) },
  { path: 'analytics', loadComponent: () => import('./mfe/analytics.component').then(m => m.AnalyticsComponent) },
  { path: 'ai-operations', loadComponent: () => import('./mfe/ai-operations.component').then(m => m.AiOperationsComponent) },
  { path: 'governance', loadComponent: () => import('./mfe/governance.component').then(m => m.GovernanceComponent) },
  { path: '', redirectTo: 'customer', pathMatch: 'full' },
];
