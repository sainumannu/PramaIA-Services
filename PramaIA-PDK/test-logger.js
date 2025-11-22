// Test script per verificare l'invio dei log dal PDK al LogService
import logger from './server/logger.js';

console.log('=== Test Logger PDK ===\n');

// Mostra configurazione
const config = logger.getConfig();
console.log('Configurazione Logger:');
console.log(`- LogService abilitato: ${config.logServiceEnabled}`);
console.log(`- LogService URL: ${config.logServiceUrl}`);
console.log(`- API Key: ${config.apiKey}`);
console.log(`- Progetto: ${config.project}`);
console.log(`- Modulo: ${config.module}`);
console.log(`- Livello di log: ${config.level}\n`);

// Test dei vari livelli di log
console.log('--- Test log standard ---');
logger.info('Test messaggio INFO');
logger.warn('Test messaggio WARNING');
logger.error('Test messaggio ERROR');
logger.debug('Test messaggio DEBUG');

console.log('\n--- Test log LIFECYCLE ---');

// Test lifecycle log
await logger.lifecycle(
    'test_event',
    'Test evento lifecycle dal PDK',
    {
        document_id: 'test-doc-123',
        file_name: 'test-document.pdf',
        file_hash: 'abc123def456',
        test_field: 'test_value'
    },
    {
        test_context: 'test_context_value',
        user: 'test_user'
    }
);

console.log('\n--- Test workflow logging ---');

// Test workflow logging
await logger.workflowStarted(
    'test-workflow-001',
    'test-doc-456',
    { 
        workflow_name: 'Test Workflow',
        trigger: 'manual'
    },
    {
        user_id: 'admin',
        source: 'test-script'
    }
);

await logger.documentDetected(
    'test-doc-789',
    '/test/path/document.pdf',
    {
        file_size: 1024000,
        file_type: 'application/pdf'
    },
    {
        source: 'document-monitor',
        trigger: 'file-created'
    }
);

console.log('\n✅ Test completati. Verifica sul LogService dashboard se i log sono arrivati.');
console.log(`   Dashboard: http://localhost:8081/dashboard`);

// Aspetta un po' per permettere l'invio asincrono
setTimeout(() => {
    console.log('\n⏱️  Attesa completata. Chiusura script.');
    process.exit(0);
}, 2000);
