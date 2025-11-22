import './style.css'
import typescriptLogo from './typescript.svg'
import viteLogo from '/vite.svg'
import { setupCounter } from './counter'
import { LogService, LogLevel } from './services/log-service'

// Inizializza il servizio di logging
const logger = LogService.getInstance({
  module: 'main-app'
});

// Esempi di utilizzo del logging
logger.info('Applicazione inizializzata', { appVersion: '1.0.0' });
logger.debug('Dettagli di inizializzazione', { 
  environment: import.meta.env.MODE,
  features: ['logging', 'workflow-editor'] 
});

// Ottieni un logger specifico per un componente
const counterLogger = logger.getModuleLogger('counter-component');
counterLogger.info('Componente contatore inizializzato');

document.querySelector<HTMLDivElement>('#app')!.innerHTML = `
  <div>
    <a href="https://vite.dev" target="_blank">
      <img src="${viteLogo}" class="logo" alt="Vite logo" />
    </a>
    <a href="https://www.typescriptlang.org/" target="_blank">
      <img src="${typescriptLogo}" class="logo vanilla" alt="TypeScript logo" />
    </a>
    <h1>PramaIA PDK</h1>
    <h2>Plugin Development Kit</h2>
    <div class="card">
      <button id="counter" type="button"></button>
    </div>
    <p>
      <button id="generate-error">Genera Errore di Test</button>
    </p>
    <p class="read-the-docs">
      Sistema di logging integrato con PramaIA LogService
    </p>
  </div>
`

setupCounter(document.querySelector<HTMLButtonElement>('#counter')!)

// Aggiungi un gestore per il pulsante di errore
const errorButton = document.querySelector<HTMLButtonElement>('#generate-error');
if (errorButton) {
  errorButton.addEventListener('click', () => {
    try {
      // Genera un errore di test
      throw new Error('Errore di test generato dall\'utente');
    } catch (error) {
      if (error instanceof Error) {
        logger.error('Si è verificato un errore', { 
          errorMessage: error.message,
          stack: error.stack
        });
      }
    }
  });
}
