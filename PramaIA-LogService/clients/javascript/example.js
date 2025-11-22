/**
 * Esempio di utilizzo del client JavaScript per PramaIA-LogService.
 */

const { PramaIALogger, LogLevel, LogProject } = require('./pramaialog');

/**
 * Simula l'esecuzione di un workflow con vari livelli di log.
 */
async function simulateWorkflowExecution() {
  // Crea un'istanza del logger
  // Risolvi host dal .env / variabili d'ambiente se presenti
  let backend = process.env.BACKEND_URL || process.env.PRAMAIALOG_HOST || 'http://localhost:8081';
  const port = process.env.PRAMAIALOG_PORT;
  if (port && !/:\d+$/.test(backend)) {
    backend = `${backend.replace(/\/$/, '')}:${port}`;
  }

  const logger = new PramaIALogger({
    apiKey: 'pramaiapdk_api_key_123456', // Questa è una delle chiavi predefinite
    project: LogProject.PDK,
    module: 'workflow_editor',
    host: backend
  });
  
  // Simula l'avvio di un workflow
  const workflowId = `wf-${Math.floor(1000 + Math.random() * 9000)}`;
  logger.info(
    `Avvio editor per workflow ${workflowId}`,
    null,
    { workflowId, userId: 'admin' }
  );
  
  // Simula alcuni log di debug durante l'esecuzione
  logger.debug(
    'Caricamento configurazione workflow',
    { configFile: `/workflows/${workflowId}/config.json` },
    { workflowId }
  );
  
  await new Promise(resolve => setTimeout(resolve, 1000)); // Simula un po' di elaborazione
  
  // Simula un warning
  if (Math.random() < 0.7) {
    logger.warning(
      'Potenziale problema di performance rilevato nel workflow',
      { 
        issue: 'too_many_nodes',
        nodeCount: Math.floor(20 + Math.random() * 30),
        recommended: 'Dividere il workflow in sotto-workflow'
      },
      { workflowId }
    );
  }
  
  await new Promise(resolve => setTimeout(resolve, 1000)); // Altra elaborazione
  
  // Simula occasionalmente un errore
  if (Math.random() < 0.3) {
    try {
      // Simula un'eccezione
      throw new Error('Errore durante la validazione dei nodi del workflow');
    } catch (error) {
      logger.error(
        `Errore durante la modifica del workflow ${workflowId}`,
        {
          errorType: error.name,
          errorMessage: error.message,
          stackTrace: error.stack
        },
        { workflowId }
      );
      
      // Log critico per errori gravi
      if (Math.random() < 0.5) {
        logger.critical(
          'Errore critico durante il salvataggio del workflow',
          { errorType: 'SaveFailure', nodeId: 'processor-node-1' },
          { workflowId }
        );
        
        // Assicurati che tutti i log vengano inviati
        await logger.flush();
        return false;
      }
    }
  }
  
  // Log di completamento
  logger.info(
    `Workflow ${workflowId} salvato con successo`,
    { nodeCount: Math.floor(5 + Math.random() * 15) },
    { workflowId }
  );
  
  // Assicurati che tutti i log vengano inviati
  await logger.flush();
  return true;
}

/**
 * Funzione principale
 */
async function main() {
  console.log('Simulazione di interazione con l\'editor workflow con logging...');
  
  // Esegui diverse simulazioni
  for (let i = 0; i < 5; i++) {
    console.log(`\nEsecuzione simulazione ${i+1}/5...`);
    const result = await simulateWorkflowExecution();
    console.log(`Simulazione completata ${result ? 'con successo' : 'con errori'}`);
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  console.log('\nSimulazione completata. Controlla il servizio di logging per vedere i log generati.');
}

// Esegui la simulazione
main().catch(error => {
  console.error('Errore durante la simulazione:', error);
});
