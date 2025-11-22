// Simple API server to expose PDK plugins as REST endpoints
// Place this file in PramaIA-PDK/server/plugin-api-server.js

import express from 'express';
import fs from 'fs';
import path from 'path';
import cors from 'cors';
import fileUpload from 'express-fileupload';  // Per gestire upload di file
import EventSourceManager from './event-source-manager.js';  // Import EventSourceManager
import logger from './logger.js';  // Import nuovo modulo di logging

// Import dei moduli estratti
import { executePythonPlugin } from './python-executor.js';
import { configurePluginRoutes } from './plugin-routes.js';
import { configureEventSourceRoutes } from './event-source-routes.js';

import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PLUGIN_DIR = path.join(__dirname, '../plugins'); // Directory with plugin folders
const EVENT_SOURCE_DIR = path.join(__dirname, '../event-sources'); // Directory with event source folders

// Configurazione porta dal environment o default
const PORT = process.env.PDK_SERVER_PORT || 3001;

// Imposta il livello di log dall'environment o default con ottimizzazioni
logger.setSensibleDefaults(process.env.PDK_LOG_LEVEL || 'INFO');
logger.info(`PDK Server: Livello di log impostato a ${logger.getConfig().level}`);

// Log configurazione LogService
const logConfig = logger.getConfig();
logger.info(`LogService configurato: ${logConfig.logServiceEnabled ? 'ABILITATO' : 'DISABILITATO'}`);
logger.info(`LogService URL: ${logConfig.logServiceUrl}`);
logger.info(`LogService API Key: ${logConfig.apiKey ? logConfig.apiKey.substring(0, 10) + '...' : 'NON CONFIGURATA'}`);

// Cache per i plugin caricati
const pluginCache = new Map();

// Event Source Manager instance
const eventSourceManager = new EventSourceManager(EVENT_SOURCE_DIR);

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));  // Per gestire form data
app.use(fileUpload({
  createParentPath: true,
  limits: { fileSize: 50 * 1024 * 1024 }, // 50MB max
  abortOnLimit: true,
  useTempFiles: true,
  tempFileDir: './tmp/'
})); // Per gestire file uploads
// Middleware per logging delle richieste
app.use((req, res, next) => {
  logger.info(`🌐 ${req.method} ${req.path} - Richiesta ricevuta`);
  next();
});

// La funzione executePythonPlugin è stata spostata nel modulo python-executor.js

// Configurazione delle route per i plugin
configurePluginRoutes(app, PLUGIN_DIR, executePythonPlugin, logger);

// Health check endpoint
app.get('/health', (req, res) => {
    logger.info(`Health check request received`);
    const availablePlugins = fs.readdirSync(PLUGIN_DIR).filter(folder => {
        const manifestPath = path.join(PLUGIN_DIR, folder, 'plugin.json');
        return fs.existsSync(manifestPath);
    });
    
    const response = { 
        status: 'OK',
        timestamp: new Date().toISOString(),
        plugins_dir: PLUGIN_DIR,
        available_plugins: availablePlugins.length,
        plugin_list: availablePlugins
    };
    
    logger.info(`Health check: ${availablePlugins.length} plugins available`);
    res.json(response);
});

// ============================================================================
// Event Sources Endpoints
// ============================================================================

// Configurazione delle route per gli event sources
configureEventSourceRoutes(app, eventSourceManager, logger);

// Event listener setup for forwarding events to webhook or other integrations
eventSourceManager.on('eventReceived', async (eventData) => {
    logger.info(`[EventManager] Event received from ${eventData.sourceId}`);
    logger.debug(`Event data: ${JSON.stringify(eventData)}`);
    
    // Forward event to PramaIAServer trigger system
    try {
        const pramaiaServerUrl = process.env.BACKEND_BASE_URL || process.env.BACKEND_URL || 'http://localhost:8000';
        const eventEndpoint = `${pramaiaServerUrl}/api/events/process`;
        
        logger.info(`Forwarding event to PramaIAServer: ${eventEndpoint}`);
        
        const payload = {
            event_type: eventData.eventType || 'pdk_event',
            data: eventData.data || {},
            metadata: {
                source: `pdk-event-source-${eventData.sourceId}`,
                timestamp: eventData.timestamp || new Date().toISOString(),
                additional_data: {
                    source_id: eventData.sourceId,
                    pdk_server: 'localhost:3001'
                }
            }
        };
        
        const response = await fetch(eventEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            const result = await response.json();
            logger.info(`✅ Event forwarded successfully. Triggers activated: ${result.results?.length || 0}`);
            
            // Log lifecycle event
            await logger.lifecycle(
                'event_forwarded',
                `Event ${eventData.eventType} forwarded to PramaIAServer`,
                {
                    event_type: eventData.eventType,
                    source_id: eventData.sourceId,
                    triggers_activated: result.results?.length || 0,
                    event_id: result.event_id
                },
                {
                    endpoint: eventEndpoint,
                    status: 'success'
                }
            );
        } else {
            const errorText = await response.text();
            logger.error(`❌ Failed to forward event: ${response.status} - ${errorText}`);
            
            await logger.lifecycle(
                'event_forward_error',
                `Failed to forward event ${eventData.eventType}`,
                {
                    event_type: eventData.eventType,
                    source_id: eventData.sourceId,
                    error: errorText,
                    status_code: response.status
                },
                {
                    endpoint: eventEndpoint,
                    status: 'error'
                }
            );
        }
    } catch (error) {
        logger.error(`❌ Exception forwarding event: ${error.message}`);
        
        await logger.lifecycle(
            'event_forward_exception',
            `Exception forwarding event ${eventData.eventType}`,
            {
                event_type: eventData.eventType,
                source_id: eventData.sourceId,
                error: error.message,
                stack: error.stack
            },
            {
                status: 'exception'
            }
        );
    }
});

// Graceful shutdown handling
process.on('SIGINT', async () => {
    logger.info('Ricevuto SIGINT, spegnimento in corso...');
    await eventSourceManager.stopAll();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    logger.info('Ricevuto SIGTERM, spegnimento in corso...');
    await eventSourceManager.stopAll();
    process.exit(0);
});

app.listen(PORT, () => {
    logger.info(`✅ Server PDK avviato su http://localhost:${PORT}`);
    logger.info(`Data e ora: ${new Date().toISOString()}`);
    logger.info(`Directory plugin: ${PLUGIN_DIR}`);
    
    // Conta e mostra i plugin disponibili (nodi e event sources)
    const availablePlugins = fs.readdirSync(PLUGIN_DIR)
        .filter(folder => {
            const manifestPath = path.join(PLUGIN_DIR, folder, 'plugin.json');
            return fs.existsSync(manifestPath);
        });
    
    logger.info(`Plugin disponibili: ${availablePlugins.length}`);
    
    if (logger.getConfig().level >= 3) { // 3 è il valore di LOG_LEVELS.DEBUG
        availablePlugins.forEach(plugin => {
            try {
                const manifestPath = path.join(PLUGIN_DIR, plugin, 'plugin.json');
                const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
                
                if (manifest.type === 'event-source') {
                    logger.debug(`  - ${plugin}: [EVENT SOURCE] ${manifest.name} (${manifest.eventTypes?.length || 0} event types)`);
                } else {
                    logger.debug(`  - ${plugin}: [PLUGIN] ${manifest.name} (${manifest.nodes?.length || 0} nodes)`);
                }
            } catch (e) {
                logger.warn(`  - ${plugin}: [Errore lettura manifest]`);
            }
        });
        
        // Show available event sources
        const eventSources = eventSourceManager.getAvailableSources();
        logger.debug(`Event sources disponibili: ${eventSources.length}`);
        eventSources.forEach(source => {
            logger.debug(`  - ${source.id}: ${source.name} (${source.eventTypes?.length || 0} event types)`);
        });
    } else {
        logger.info(`Usa il livello di log DEBUG per visualizzare i dettagli dei plugin (PDK_LOG_LEVEL=DEBUG)`);
    }
    
    logger.info(`Server pronto ad accettare connessioni`);
});
