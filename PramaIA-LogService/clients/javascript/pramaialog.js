/**
 * Client JavaScript per il servizio di logging PramaIA.
 * 
 * Questo modulo fornisce un client per inviare log al servizio
 * PramaIA-LogService. Può essere utilizzato dai componenti JavaScript/TypeScript
 * dell'ecosistema PramaIA, come il PDK.
 * 
 * @example
 * ```javascript
 * const { PramaIALogger, LogLevel, LogProject } = require('pramaialog');
 * 
 * // Crea un'istanza del logger
 * const logger = new PramaIALogger({
 *   apiKey: 'your_api_key',
 *   project: LogProject.PDK,
 *   module: 'workflow_editor'
 * });
 * 
 * // Invia log di diversi livelli
 * logger.info('Editor avviato');
 * logger.warning('Attenzione: configurazione nodo non valida', 
 *               { nodeId: 'node-123', issues: ['Missing input'] });
 * logger.error('Errore durante il salvataggio del workflow', 
 *             { workflowId: '123', error: err.message },
 *             { userId: 'admin' });
 * ```
 */

/**
 * Livelli di log supportati
 * @enum {string}
 */
const LogLevel = {
  DEBUG: 'debug',
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical'
};

/**
 * Progetti PramaIA supportati
 * @enum {string}
 */
const LogProject = {
  SERVER: 'PramaIAServer',
  PDK: 'PramaIA-PDK',
  AGENTS: 'PramaIA-Agents',
  PLUGINS: 'PramaIA-Plugins',
  OTHER: 'other'
};

/**
 * Client per il servizio di logging PramaIA.
 */
class PramaIALogger {
  /**
   * Crea un'istanza del logger PramaIA.
   * 
   * @param {Object} options - Opzioni di configurazione
   * @param {string} options.apiKey - API key per l'autenticazione
   * @param {string} options.project - Progetto a cui appartiene il modulo
   * @param {string} options.module - Nome del modulo che genera i log
   * @param {string} [options.host='http://localhost:8081'] - Host del servizio
   * @param {number} [options.bufferSize=100] - Dimensione del buffer
   * @param {boolean} [options.autoFlush=true] - Se fare flush automaticamente
   * @param {number} [options.flushInterval=5000] - Intervallo di flush in ms
   * @param {number} [options.retryMaxAttempts=3] - Tentativi max in caso di errore
   * @param {number} [options.retryDelay=1000] - Ritardo tra tentativi in ms
   */
  constructor(options) {
    this.apiKey = options.apiKey;
    this.project = options.project;
    this.module = options.module;
    // Risolvi host da options, poi da BACKEND_URL o PRAMAIALOG_HOST (+ PRAMAIALOG_PORT), altrimenti fallback
    let resolvedHost = options.host || process.env.BACKEND_URL || process.env.PRAMAIALOG_HOST || 'http://localhost:8081';
    if (process.env.PRAMAIALOG_PORT && !/:\d+$/.test(resolvedHost)) {
      resolvedHost = `${resolvedHost.replace(/\/$/, '')}:${process.env.PRAMAIALOG_PORT}`;
    }
    this.host = resolvedHost.replace(/\/$/, '');
    this.bufferSize = options.bufferSize || 100;
    this.autoFlush = options.autoFlush !== false;
    this.flushInterval = options.flushInterval || 5000;
    this.retryMaxAttempts = options.retryMaxAttempts || 3;
    this.retryDelay = options.retryDelay || 1000;
    
    this.logBuffer = [];
    this.flushTimer = null;
    
    // Avvia il flush automatico se abilitato
    if (this.autoFlush) {
      this.startAutoFlush();
    }
  }
  
  /**
   * Avvia il flush automatico a intervalli regolari.
   * @private
   */
  startAutoFlush() {
    this.flushTimer = setInterval(() => {
      this.flush().catch(err => {
        console.error('Errore durante il flush automatico:', err);
      });
    }, this.flushInterval);
  }
  
  /**
   * Genera un UUID v4
   * @private
   * @returns {string} UUID v4
   */
  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  
  /**
   * Invia un log di livello DEBUG.
   * 
   * @param {string} message - Messaggio del log
   * @param {Object} [details=null] - Dettagli aggiuntivi
   * @param {Object} [context=null] - Contesto del log
   * @returns {string} ID del log
   */
  debug(message, details = null, context = null) {
    return this.log(LogLevel.DEBUG, message, details, context);
  }
  
  /**
   * Invia un log di livello INFO.
   * 
   * @param {string} message - Messaggio del log
   * @param {Object} [details=null] - Dettagli aggiuntivi
   * @param {Object} [context=null] - Contesto del log
   * @returns {string} ID del log
   */
  info(message, details = null, context = null) {
    return this.log(LogLevel.INFO, message, details, context);
  }
  
  /**
   * Invia un log di livello WARNING.
   * 
   * @param {string} message - Messaggio del log
   * @param {Object} [details=null] - Dettagli aggiuntivi
   * @param {Object} [context=null] - Contesto del log
   * @returns {string} ID del log
   */
  warning(message, details = null, context = null) {
    return this.log(LogLevel.WARNING, message, details, context);
  }
  
  /**
   * Invia un log di livello ERROR.
   * 
   * @param {string} message - Messaggio del log
   * @param {Object} [details=null] - Dettagli aggiuntivi
   * @param {Object} [context=null] - Contesto del log
   * @returns {string} ID del log
   */
  error(message, details = null, context = null) {
    return this.log(LogLevel.ERROR, message, details, context);
  }
  
  /**
   * Invia un log di livello CRITICAL.
   * 
   * @param {string} message - Messaggio del log
   * @param {Object} [details=null] - Dettagli aggiuntivi
   * @param {Object} [context=null] - Contesto del log
   * @returns {string} ID del log
   */
  critical(message, details = null, context = null) {
    return this.log(LogLevel.CRITICAL, message, details, context);
  }
  
  /**
   * Aggiunge un log al buffer.
   * 
   * @param {string} level - Livello del log
   * @param {string} message - Messaggio del log
   * @param {Object} [details=null] - Dettagli aggiuntivi
   * @param {Object} [context=null] - Contesto del log
   * @returns {string} ID del log
   */
  log(level, message, details = null, context = null) {
    const logId = this.generateUUID();
    const logEntry = {
      id: logId,
      timestamp: new Date().toISOString(),
      project: this.project,
      level: level,
      module: this.module,
      message: message,
      details: details,
      context: context
    };
    
    this.logBuffer.push(logEntry);
    
    // Se il buffer è pieno, fai un flush
    if (this.logBuffer.length >= this.bufferSize) {
      this.flush().catch(err => {
        console.error('Errore durante il flush del buffer pieno:', err);
      });
    }
    
    return logId;
  }
  
  /**
   * Invia tutti i log in coda al servizio.
   * 
   * @returns {Promise<boolean>} Promise che si risolve a true se l'invio è riuscito
   */
  async flush() {
    if (this.logBuffer.length === 0) {
      return true;
    }
    
    // Estrai tutti i log dal buffer
    const logs = [...this.logBuffer];
    this.logBuffer = [];
    
    // Invia i log al servizio
    const url = `${this.host}/api/logs/batch`;
    const headers = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey
    };
    
    // Fai più tentativi in caso di errore
    let attempt = 0;
    while (attempt < this.retryMaxAttempts) {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: headers,
          body: JSON.stringify(logs)
        });
        
        if (response.status === 201) {
          return true;
        } else {
          console.error(`Errore nell'invio dei log: ${response.status} - ${await response.text()}`);
          attempt++;
          if (attempt < this.retryMaxAttempts) {
            await new Promise(resolve => setTimeout(resolve, this.retryDelay));
          }
        }
      } catch (error) {
        console.error(`Errore durante l'invio dei log: ${error.message}`);
        attempt++;
        if (attempt < this.retryMaxAttempts) {
          await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        }
      }
    }
    
    // Se arriviamo qui, tutti i tentativi sono falliti
    // Riinserire i log nel buffer
    this.logBuffer = [...logs, ...this.logBuffer];
    
    return false;
  }
  
  /**
   * Chiude il logger e invia tutti i log rimanenti.
   * 
   * @returns {Promise<void>}
   */
  async close() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    
    await this.flush();
  }
}

/**
 * Funzione di utilità per configurare facilmente il logger
 * 
 * @param {Object} options - Opzioni di configurazione
 * @param {string} options.apiKey - API key per l'autenticazione
 * @param {string} options.project - Progetto PramaIA
 * @param {string} options.module - Nome del modulo
 * @param {string} [options.host] - Host del servizio di logging
 * @returns {PramaIALogger} Un'istanza configurata di PramaIALogger
 */
function setupLogger(options) {
  return new PramaIALogger(options);
}

// Esporta i tipi e le classi
module.exports = {
  LogLevel,
  LogProject,
  PramaIALogger,
  setupLogger
};
