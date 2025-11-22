/**
 * Event Input Processor - PDK Implementation
 * Gestisce input eventi per workflow
 */

class EventInputProcessor {
    constructor() {
        this.name = 'Event Input Processor';
        this.description = 'Processore per gestione input eventi workflow';
    }

    async execute(input, config, context) {
        const logger = context.logger || console;
        
        logger.info(`📨 Event Input Processor: processing input`);
        
        // Restituisci tutti i dati di input del workflow
        const result = {
            ...input,
            processed_at: new Date().toISOString(),
            processor: 'EventInputProcessor'
        };
        
        logger.info(`✅ Event input processed: ${Object.keys(input).length} keys`);
        return result;
    }

    validate(config) {
        // Event input non richiede configurazione speciale
        return { valid: true };
    }
}

module.exports = EventInputProcessor;