import { Routes } from '@angular/router';
import { loadRemoteModule } from '@angular-architects/module-federation';

/** Cada rota carrega um microfrontend independente via Module Federation. */
export const APP_ROUTES: Routes = [
  {
    path: 'customer',
    loadComponent: () =>
      loadRemoteModule({ type: 'module', remoteEntry: 'http://localhost:4201/remoteEntry.js', exposedModule: './Component' })
        .then((m) => m.CustomerComponent),
  },
  {
    path: 'analytics',
    loadComponent: () =>
      loadRemoteModule({ type: 'module', remoteEntry: 'http://localhost:4202/remoteEntry.js', exposedModule: './Component' })
        .then((m) => m.AnalyticsComponent),
  },
  {
    path: 'ai-operations',
    loadComponent: () =>
      loadRemoteModule({ type: 'module', remoteEntry: 'http://localhost:4203/remoteEntry.js', exposedModule: './Component' })
        .then((m) => m.AiOperationsComponent),
  },
  {
    path: 'governance',
    loadComponent: () =>
      loadRemoteModule({ type: 'module', remoteEntry: 'http://localhost:4204/remoteEntry.js', exposedModule: './Component' })
        .then((m) => m.GovernanceComponent),
  },
  { path: '', redirectTo: 'customer', pathMatch: 'full' },
];
