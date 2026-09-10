import { Component } from '@angular/core';

/**
 * Placeholder do microfrontend "ai-operations". Na arquitetura-alvo (webpack.config.js
 * + @angular-architects/module-federation) esta rota carrega um remote
 * independente em runtime — ver apps/README.md. Por ora é um componente local
 * para o shell buildar e navegar.
 */
@Component({
  selector: 'argus-ai-operations',
  standalone: true,
  template: `<section><h2>AiOperations MFE</h2><p>Microfrontend independente — carregado via Module Federation na arquitetura-alvo.</p></section>`,
})
export class AiOperationsComponent {}
