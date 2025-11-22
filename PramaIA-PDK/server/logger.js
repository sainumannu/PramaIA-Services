// logger.js - Modulo per gestire i log del PDK Server
// Permette di controllare la verbosità dei log con semplici flag

import chalk from 'chalk';
import path from 'path';
import fs from 'fs';
import os from 'os';

// Livelli di log disponibili
const LOG_LEVELS = {
    ERROR: 0,   // Solo errori
    WARN: 1,    // Errori e warning
    INFO: 2,    // Informazioni normali (default)
    DEBUG: 3,   // Informazioni dettagliate di debug
    TRACE: 4,   // Informazioni molto dettagliate
    LIFECYCLE: 5 // Eventi di ciclo di vita dei documenti (processing pipeline)
};

// Configurazione del logger
let config = {
    level: process.env.PDK_LOG_LEVEL ? 
        (LOG_LEVELS[process.env.PDK_LOG_LEVEL.toUpperCase()] || LOG_LEVELS.INFO) : 
        LOG_LEVELS.INFO,
    colorEnabled: true,
    timestamp: true,
    requestLogging: true,
    iconDebug: false,       // Log specifico per debug icone
    nodeTrace: false,       // Log dettagliato per tracciamento nodi
    responsePreview: false,  // Mostra preview delle risposte
    
    // Configurazione per il LogService (lifecycle logging)
    logServiceEnabled: true,
    logServiceUrl: (process.env.PRAMAIALOG_HOST || 'http://localhost:8081') + '/api/logs',
    apiKey: process.env.PRAMAIALOG_API_KEY || 'pramaialog_o6hlpft585hkykgb',
    project: 'PramaIA-PDK',
    module: 'workflow_engine',
    localFallback: true,  // Se true, usa logger locale come fallback
    logFilePath: path.join(process.cwd(), 'logs', 'lifecycle_events.log')
};

// Assicurati che la directory dei logs esista per il fallback lifecycle
if (!fs.existsSync(path.join(process.cwd(), 'logs'))) {
    try {
        fs.mkdirSync(path.join(process.cwd(), 'logs'));
    } catch (err) {
        console.error(`Impossibile creare directory logs: ${err.message}`);
    }
}

// Funzione per impostare il livello di log
function setLogLevel(level) {
    if (typeof level === 'string') {
        const upperLevel = level.toUpperCase();
        if (LOG_LEVELS[upperLevel] !== undefined) {
            config.level = LOG_LEVELS[upperLevel];
        } else {
            console.warn(`Livello di log non valido: ${level}. Uso default: INFO`);
            config.level = LOG_LEVELS.INFO;
        }
    } else if (typeof level === 'number' && level >= 0 && level <= 5) {
        config.level = level;
    }
    
    // Imposta variabili specifiche in base al livello
    config.iconDebug = config.level >= LOG_LEVELS.TRACE;
    config.nodeTrace = config.level >= LOG_LEVELS.DEBUG;
    config.responsePreview = config.level >= LOG_LEVELS.DEBUG;
}

// Inizializza con il livello dall'env o default
setLogLevel(process.env.PDK_LOG_LEVEL || 'INFO');

// Formatta un timestamp per i log
function getTimestamp() {
    if (!config.timestamp) return '';
    return `[${new Date().toISOString()}] `;
}

// Funzione per generare un identificatore stabile per un file
// Questa funzione aiuta a tracciare lo stesso file anche quando viene rinominato
function createFileIdentifier(fileName, filePath, fileSize) {
    // Base: nome del file (può cambiare con la rinomina)
    let idParts = [fileName || ''];
    
    // Se abbiamo un path, usa l'ultima parte della directory come altro identificativo
    if (filePath) {
        const pathParts = filePath.split(/[\\/]/);
        if (pathParts.length > 1) {
            // Aggiungi la directory contenente il file (più stabile del nome file)
            idParts.push(pathParts[pathParts.length - 2]);
        }
    }
    
    // Se abbiamo una dimensione del file, aggiungila come terzo componente
    if (fileSize) {
        idParts.push(fileSize.toString());
    }
    
    // Genera un hash semplice dalla stringa combinata
    const combinedStr = idParts.join('|');
    let hash = 0;
    for (let i = 0; i < combinedStr.length; i++) {
        const char = combinedStr.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Converti a int a 32 bit
    }
    
    // Restituisci un identificatore più leggibile
    return `file_${Math.abs(hash).toString(16)}`;
}

// Funzione helper per inviare log al LogService (lifecycle)
async function sendToLogService(level, message, details = {}, context = {}) {
    if (!config.logServiceEnabled) {
        return null;
    }
    
    try {
        const timestamp = new Date().toISOString();
        
        const payload = {
            timestamp,
            level,
            project: config.project,
            module: config.module,
            message,
            details,
            context: {
                ...context,
                hostname: os.hostname(),
                process_id: process.pid
            }
        };
        
        const response = await fetch(config.logServiceUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': config.apiKey
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`LogService risponde con errore ${response.status}: ${errorText}`);
        }
        
        return await response.json();
    } catch (err) {
        // Fallback locale se configurato
        if (config.localFallback) {
            try {
                const logEntry = JSON.stringify({
                    timestamp: new Date().toISOString(),
                    level,
                    message,
                    details,
                    context,
                    error: err.message
                }) + '\n';
                
                fs.appendFileSync(config.logFilePath, logEntry);
                console.debug(`Lifecycle log salvato localmente (fallback): ${message}`);
            } catch (fileErr) {
                console.error(`Errore durante il fallback locale del lifecycle log: ${fileErr.message}`);
            }
        }
        
        console.error(`Errore invio log al LogService: ${err.message}`);
        return null;
    }
}

// Funzioni di log per ogni livello
const logger = {
    error: (message, ...args) => {
        if (config.level >= LOG_LEVELS.ERROR) {
            console.error(
                config.colorEnabled ? 
                chalk.red(`${getTimestamp()}❌ ERROR: ${message}`) : 
                `${getTimestamp()}ERROR: ${message}`, 
                ...args
            );
        }
    },
    
    warn: (message, ...args) => {
        if (config.level >= LOG_LEVELS.WARN) {
            console.warn(
                config.colorEnabled ? 
                chalk.yellow(`${getTimestamp()}⚠️ WARN: ${message}`) : 
                `${getTimestamp()}WARN: ${message}`, 
                ...args
            );
        }
    },
    
    info: (message, ...args) => {
        if (config.level >= LOG_LEVELS.INFO) {
            console.log(
                config.colorEnabled ? 
                chalk.blue(`${getTimestamp()}ℹ️ ${message}`) : 
                `${getTimestamp()}${message}`, 
                ...args
            );
        }
    },
    
    debug: (message, ...args) => {
        if (config.level >= LOG_LEVELS.DEBUG) {
            console.log(
                config.colorEnabled ? 
                chalk.cyan(`${getTimestamp()}🔍 DEBUG: ${message}`) : 
                `${getTimestamp()}DEBUG: ${message}`, 
                ...args
            );
        }
    },
    
    trace: (message, ...args) => {
        if (config.level >= LOG_LEVELS.TRACE) {
            console.log(
                config.colorEnabled ? 
                chalk.magenta(`${getTimestamp()}📊 TRACE: ${message}`) : 
                `${getTimestamp()}TRACE: ${message}`, 
                ...args
            );
        }
    },
    
    // Funzione principale per lifecycle logging
    lifecycle: async (event, message, details = {}, context = {}) => {
        // LIFECYCLE è sempre attivo se logServiceEnabled è true
        // Non dipende dal livello di log configurato
        
        // Log locale sempre (indipendentemente da invio LogService)
        const timestamp = getTimestamp();
        console.log(
            config.colorEnabled ? 
            chalk.green(`${timestamp}🔄 [LIFECYCLE] [${event}] ${message}`) : 
            `${timestamp}[LIFECYCLE] [${event}] ${message}`
        );
        
        // Prepara dettagli arricchiti per il LogService
        const enrichedDetails = { 
            ...details, 
            event_type: event,
            log_level: 'lifecycle',  // Minuscolo per compatibilità API
            // Aggiungi sempre un ID di correlazione per tracciare eventi relativi allo stesso documento
            correlation_id: details.file_hash || details.document_id || 
                         createFileIdentifier(details.file_name, details.file_path)
        };
        
        // Invia al LogService (con livello minuscolo)
        try {
            await sendToLogService('lifecycle', message, enrichedDetails, context);
        } catch (err) {
            console.error(`Errore invio lifecycle log: ${err.message}`);
        }
    },
    
    // Funzioni specifiche per eventi lifecycle comuni
    workflowStarted: async (workflowId, documentId, details = {}, context = {}) => {
        return logger.lifecycle(
            'workflow_started',
            `Workflow iniziato: ${workflowId} per documento: ${documentId}`,
            {
                workflow_id: workflowId,
                document_id: documentId,
                ...details
            },
            context
        );
    },
    
    workflowCompleted: async (workflowId, documentId, details = {}, context = {}) => {
        return logger.lifecycle(
            'workflow_completed',
            `Workflow completato: ${workflowId} per documento: ${documentId}`,
            {
                workflow_id: workflowId,
                document_id: documentId,
                ...details
            },
            context
        );
    },
    
    workflowError: async (workflowId, documentId, errorMessage, nodeId = null, details = {}, context = {}) => {
        return logger.lifecycle(
            'workflow_error',
            `Errore workflow: ${workflowId}, documento: ${documentId}, nodo: ${nodeId || 'N/A'}, errore: ${errorMessage}`,
            {
                workflow_id: workflowId,
                document_id: documentId,
                node_id: nodeId,
                error_message: errorMessage,
                ...details
            },
            context
        );
    },
    
    nodeExecution: async (workflowId, documentId, nodeId, status, details = {}, context = {}) => {
        const statusText = status === 'started' ? 'iniziata' : 
                          status === 'completed' ? 'completata' : 
                          status === 'error' ? 'fallita' : status;
        
        return logger.lifecycle(
            `node_${status}`,
            `Esecuzione nodo ${statusText}: workflow ${workflowId}, nodo ${nodeId}, documento ${documentId}`,
            {
                workflow_id: workflowId,
                document_id: documentId,
                node_id: nodeId,
                status,
                ...details
            },
            context
        );
    },
    
    // Per API Express e richieste HTTP
    api: (method, endpoint, message = '') => {
        if (config.level >= LOG_LEVELS.INFO) {
            const methodColor = {
                'GET': chalk.green,
                'POST': chalk.blue,
                'PUT': chalk.yellow,
                'DELETE': chalk.red,
                'PATCH': chalk.magenta
            }[method] || chalk.white;
            
            console.log(
                config.colorEnabled ? 
                `${getTimestamp()}🌐 ${methodColor(method)} ${chalk.cyan(endpoint)} ${message}` : 
                `${getTimestamp()}${method} ${endpoint} ${message}`
            );
        }
    },
    
    // Log specifici per sottosistemi
    icon: (message, ...args) => {
        if (config.level >= LOG_LEVELS.TRACE && config.iconDebug) {
            console.log(
                config.colorEnabled ? 
                chalk.magenta(`${getTimestamp()}🎨 ICON: ${message}`) : 
                `${getTimestamp()}ICON: ${message}`, 
                ...args
            );
        }
    },
    
    node: (nodeId, message, ...args) => {
        if (config.level >= LOG_LEVELS.DEBUG && config.nodeTrace) {
            console.log(
                config.colorEnabled ? 
                chalk.blueBright(`${getTimestamp()}📦 NODE [${nodeId}]: ${message}`) : 
                `${getTimestamp()}NODE [${nodeId}]: ${message}`, 
                ...args
            );
        }
    },
    
    // Funzione per impostare configurazioni predefinite sensate in base al livello
    setSensibleDefaults: (level = 'INFO') => {
        setLogLevel(level);
        
        // In produzione o con log level basso, disattiva colori e riduce timestamp
        if (config.level <= LOG_LEVELS.INFO) {
            if (process.env.NODE_ENV === 'production') {
                config.colorEnabled = false;
            }
        }
        
        return config;
    },
    
    // Funzioni per tracciare il ciclo di vita dei documenti
    documentDetected: async (documentId, path, details = {}, context = {}) => {
        // Estrai il nome del file dal path
        const fileName = path ? path.split(/[\\/]/).pop() : documentId;
        
        // Crea un hash del file per garantire che si possa tracciare lo stesso file anche dopo rinomina
        const fileHash = details.fileHash || createFileIdentifier(fileName, path);
        
        return logger.lifecycle(
            'document_detected',
            `Documento rilevato: ${documentId}, percorso: ${path}`,
            {
                document_id: documentId,
                file_path: path,
                file_name: fileName,
                file_hash: fileHash,
                lifecycle_category: 'document_lifecycle',  // Categoria per filtraggio UI
                ...details
            },
            context
        );
    },
    
    documentModified: async (documentId, path, modificationType, details = {}, context = {}) => {
        // Estrai il nome del file dal path
        const fileName = path ? path.split(/[\\/]/).pop() : documentId;
        
        // Crea un hash del file per garantire che si possa tracciare lo stesso file anche dopo rinomina
        const fileHash = details.fileHash || createFileIdentifier(fileName, path);
        
        return logger.lifecycle(
            'document_modified',
            `Documento modificato (${modificationType}): ${documentId}, percorso: ${path}`,
            {
                document_id: documentId,
                file_path: path,
                file_name: fileName,
                file_hash: fileHash,
                modification_type: modificationType, // created, updated, deleted, renamed
                lifecycle_category: 'document_lifecycle',  // Categoria per filtraggio UI
                ...details
            },
            context
        );
    },
    
    documentTransmitted: async (documentId, targetSystem, status, details = {}, context = {}) => {
        // Estrai il nome del file dai dettagli se disponibile
        const fileName = details.file_name || details.fileName || 
                       (details.file_path ? details.file_path.split(/[\\/]/).pop() : documentId);
        
        // Crea un hash del file per garantire che si possa tracciare lo stesso file anche dopo rinomina
        const fileHash = details.fileHash || createFileIdentifier(fileName, details.file_path);
        
        return logger.lifecycle(
            'document_transmitted',
            `Documento trasmesso a ${targetSystem}: ${documentId}, stato: ${status}`,
            {
                document_id: documentId,
                target_system: targetSystem,
                status: status,
                file_name: fileName,
                file_hash: fileHash,
                lifecycle_category: 'document_lifecycle',  // Categoria per filtraggio UI
                ...details
            },
            context
        );
    },
    
    documentProcessed: async (documentId, processorId, status, details = {}, context = {}) => {
        // Estrai il nome del file dai dettagli se disponibile
        const fileName = details.file_name || details.fileName || 
                       (details.file_path ? details.file_path.split(/[\\/]/).pop() : documentId);
        
        // Crea un hash del file per garantire che si possa tracciare lo stesso file anche dopo rinomina
        const fileHash = details.fileHash || createFileIdentifier(fileName, details.file_path);
        
        return logger.lifecycle(
            'document_processed',
            `Documento elaborato da ${processorId}: ${documentId}, stato: ${status}`,
            {
                document_id: documentId,
                processor_id: processorId,
                status: status,
                file_name: fileName,
                file_hash: fileHash,
                lifecycle_category: 'document_lifecycle',  // Categoria per filtraggio UI
                ...details
            },
            context
        );
    },
    
    documentStored: async (documentId, storageSystem, status, details = {}, context = {}) => {
        // Estrai il nome del file dai dettagli se disponibile
        const fileName = details.file_name || details.fileName || 
                       (details.original_file_path ? details.original_file_path.split(/[\\/]/).pop() : documentId);
        
        // Crea un hash del file per garantire che si possa tracciare lo stesso file anche dopo rinomina
        const fileHash = details.fileHash || createFileIdentifier(fileName, details.original_file_path);
        
        return logger.lifecycle(
            'document_stored',
            `Documento archiviato in ${storageSystem}: ${documentId}, stato: ${status}`,
            {
                document_id: documentId,
                storage_system: storageSystem,
                status: status,
                file_name: fileName,
                file_hash: fileHash,
                lifecycle_category: 'document_lifecycle',  // Categoria per filtraggio UI
                ...details
            },
            context
        );
    },
    
    // Helper per generare un identificatore stabile di un file
    // Questa funzione aiuta a tracciare lo stesso file anche quando viene rinominato
    createFileIdentifier: (fileName, filePath, fileSize) => {
        return createFileIdentifier(fileName, filePath, fileSize);
    },
    
    // Funzioni di configurazione
    setLogLevel,
    getConfig: () => ({ ...config }),
    
    // Utilità per filtrare i log di un documento specifico
    /**
     * Genera una query di filtro per i log relativi ad un documento specifico.
     * Questa funzione può essere utilizzata nella UI per filtrare i log di un documento.
     * 
     * @param {string} documentId - ID del documento da filtrare
     * @param {string} fileName - Nome del file (opzionale)
     * @param {string} filePath - Percorso del file (opzionale)
     * @returns {object} Query object per filtrare i log
     */
    createDocumentFilterQuery: (documentId, fileName = null, filePath = null) => {
        // Costruisci i criteri di filtro
        const filters = [
            { field: "log_level", value: "LIFECYCLE" },
            { field: "lifecycle_category", value: "document_lifecycle" }
        ];
        
        // Aggiungi filtri per document_id se disponibile
        if (documentId) {
            filters.push({ field: "document_id", value: documentId });
        }
        
        // Se abbiamo nome file e percorso, aggiungi un filtro per file_hash
        if (fileName) {
            const fileHash = createFileIdentifier(fileName, filePath);
            filters.push({ field: "file_hash", value: fileHash });
            // Aggiungi anche un filtro per il nome file come fallback
            filters.push({ field: "file_name", value: fileName });
        }
        
        return {
            filters,
            orderBy: "timestamp",
            orderDirection: "asc"
        };
    }
};

// Esporta tutte le funzioni utili
export default logger;