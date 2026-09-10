import { Component } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';

@Component({
  selector: 'argus-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink],
  template: `
    <header>
      <h1>Argus</h1>
      <nav>
        <a routerLink="/customer">Customer</a>
        <a routerLink="/analytics">Analytics</a>
        <a routerLink="/ai-operations">AI Operations</a>
        <a routerLink="/governance">Governance</a>
      </nav>
    </header>
    <main><router-outlet></router-outlet></main>
  `,
})
export class AppComponent {}
