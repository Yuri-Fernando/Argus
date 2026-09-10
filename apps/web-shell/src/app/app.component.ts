import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'argus-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="shell-header">
      <h1>Argus</h1>
      <nav>
        <a routerLink="/customer" routerLinkActive="active">Customer</a>
        <a routerLink="/analytics" routerLinkActive="active">Analytics</a>
        <a routerLink="/ai-operations" routerLinkActive="active">AI Operations</a>
        <a routerLink="/governance" routerLinkActive="active">Governance</a>
      </nav>
    </header>
    <main class="shell-main"><router-outlet /></main>
  `,
  styles: [`
    .shell-header { display:flex; align-items:center; gap:2rem; padding:1rem 1.5rem;
      border-bottom:1px solid #ddd; }
    .shell-header h1 { margin:0; font-size:1.25rem; }
    nav a { margin-right:1rem; text-decoration:none; color:#555; }
    nav a.active { color:#111; font-weight:600; }
    .shell-main { padding:1.5rem; }
  `],
})
export class AppComponent {}
