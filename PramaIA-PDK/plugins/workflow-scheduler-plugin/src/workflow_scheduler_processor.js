// workflow_scheduler_processor.js
import { BaseNodeProcessor, LogService, LogLevel } from '@pramaia/plugin-development-kit';

// Ottieni un logger specifico per questo processore
const logger = LogService.getInstance().getModuleLogger('WorkflowSchedulerProcessor');

/**
 * WorkflowSchedulerProcessor 
 * Implementa un nodo che permette di schedulare l'esecuzione di workflow
 * con diverse configurazioni temporali
 */
export class WorkflowSchedulerProcessor extends BaseNodeProcessor {
  // Map per memorizzare i timer attivi
  #activeSchedulers = new Map();
  
  // Map per memorizzare lo storico delle esecuzioni
  #executionHistory = new Map();
  
  // Map per memorizzare i contatori di esecuzione
  #executionCounters = new Map();

  /**
   * Inizializzazione del processore
   */
  async initialize() {
    await super.initialize();
    logger.info('Inizializzazione WorkflowSchedulerProcessor');
  }

  /**
   * Cleanup delle risorse
   */
  async cleanup() {
    logger.info('Pulizia risorse WorkflowSchedulerProcessor');
    
    // Rimuovi tutti gli scheduler attivi
    for (const [nodeId, scheduler] of this.#activeSchedulers.entries()) {
      this.#clearScheduler(nodeId);
    }
    
    // Pulisci le altre risorse
    this.#activeSchedulers.clear();
    this.#executionHistory.clear();
    this.#executionCounters.clear();
    
    await super.cleanup();
  }

  /**
   * Metodo principale di esecuzione
   */
  async execute(nodeConfig, context) {
    const { id } = nodeConfig;
    const config = nodeConfig.config || {};
    
    this.log(context, 'info', `Esecuzione del nodo Workflow Scheduler ${id}`);
    logger.info(`Esecuzione del nodo Workflow Scheduler ${id}`, { 
      nodeId: id, 
      scheduler_type: config.schedule_type,
      workflow_id: context.workflowId,
      execution_id: context.executionId
    });
    
    try {
      // Recupera il trigger se presente (facoltativo)
      const triggerInput = await this.getInput(context, id, 'trigger', false);
      
      // Se è un evento di attivazione diretta, esegui subito
      if (triggerInput && config.schedule_type === 'event' && 
          triggerInput.event === config.event_name) {
        return this.#handleScheduledExecution(nodeConfig, context, { 
          triggered_by: 'event',
          event: config.event_name 
        });
      }
      
      // Verifica se è già attivo uno scheduler per questo nodo
      const existingScheduler = this.#activeSchedulers.get(id);
      if (existingScheduler) {
        // Cancella lo scheduler esistente se c'è una nuova configurazione
        this.log(context, 'info', `Cancellazione scheduler esistente per ${id}`);
        logger.info(`Cancellazione scheduler esistente per ${id}`, {
          nodeId: id,
          scheduler_type: existingScheduler.type
        });
        this.#clearScheduler(id);
      }
      
      // Imposta il nuovo scheduler in base al tipo
      await this.#setupScheduler(nodeConfig, context);
      
      // Inizializza il contatore delle esecuzioni se non esiste
      if (!this.#executionCounters.has(id)) {
        this.#executionCounters.set(id, 0);
      }
      
      // Inizializza lo storico delle esecuzioni se non esiste
      if (!this.#executionHistory.has(id)) {
        this.#executionHistory.set(id, []);
      }
      
      // Se non dobbiamo saltare la prima esecuzione, esegui subito
      if (!config.skip_immediate) {
        await this.#handleScheduledExecution(nodeConfig, context, { 
          triggered_by: 'immediate',
          initial_execution: true
        });
      }
      
      // Restituisci lo stato dello scheduler
      const status = {
        node_id: id,
        scheduler_type: config.schedule_type,
        is_active: true,
        next_execution: this.#calculateNextExecution(config),
        max_executions: config.max_executions || 'unlimited',
        current_execution_count: this.#executionCounters.get(id),
        timezone: config.timezone || 'Europe/Rome'
      };
      
      // Imposta l'output metadata
      await this.setOutput(context, id, 'metadata', status);
      
      logger.info(`Scheduler configurato con successo per ${id}`, {
        nodeId: id,
        status
      });
      
      return status;
    } catch (error) {
      this.log(context, 'error', `Errore durante l'esecuzione dello scheduler: ${error.message}`);
      logger.error(`Errore durante l'esecuzione dello scheduler per ${id}`, {
        nodeId: id,
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }
  
  /**
   * Configurazione dello scheduler in base al tipo
   */
  async #setupScheduler(nodeConfig, context) {
    const { id } = nodeConfig;
    const config = nodeConfig.config || {};
    
    // Controlla se sono state raggiunte le esecuzioni massime
    if (this.#hasReachedMaxExecutions(id, config)) {
      this.log(context, 'info', `Raggiunto il numero massimo di esecuzioni per ${id}`);
      logger.info(`Raggiunto il numero massimo di esecuzioni per ${id}`, {
        nodeId: id,
        max_executions: config.max_executions,
        current_count: this.#executionCounters.get(id)
      });
      return;
    }
    
    // Controlla se la data corrente è oltre la data di fine
    if (this.#isAfterEndDate(config)) {
      this.log(context, 'info', `Data corrente oltre la data di fine per ${id}`);
      logger.info(`Data corrente oltre la data di fine per ${id}`, {
        nodeId: id,
        end_date: config.end_date
      });
      return;
    }
    
    // Controlla se la data corrente è prima della data di inizio
    if (this.#isBeforeStartDate(config)) {
      // Imposta un timer per attivare lo scheduler alla data di inizio
      const msUntilStart = this.#getMsUntilStartDate(config);
      if (msUntilStart > 0) {
        this.log(context, 'info', `Schedulazione per data di inizio tra ${msUntilStart}ms per ${id}`);
        logger.info(`Schedulazione per data di inizio tra ${msUntilStart}ms per ${id}`, {
          nodeId: id,
          start_date: config.start_date,
          ms_until_start: msUntilStart
        });
        const startTimer = setTimeout(() => {
          this.#setupScheduler(nodeConfig, context);
        }, msUntilStart);
        
        this.#activeSchedulers.set(id, { timer: startTimer, type: 'start_date' });
        return;
      }
    }
    
    // Configurazione in base al tipo di schedulazione
    switch (config.schedule_type) {
      case 'interval':
        await this.#setupIntervalScheduler(nodeConfig, context);
        break;
        
      case 'cron':
        await this.#setupCronScheduler(nodeConfig, context);
        break;
        
      case 'date':
        await this.#setupDateScheduler(nodeConfig, context);
        break;
        
      case 'event':
        // Per gli eventi non creiamo timer, ma ci affidiamo ai trigger
        this.log(context, 'info', `Configurato scheduler a eventi per ${id}, in attesa di ${config.event_name}`);
        logger.info(`Configurato scheduler a eventi per ${id}`, {
          nodeId: id,
          event_name: config.event_name
        });
        this.#activeSchedulers.set(id, { type: 'event', eventName: config.event_name });
        break;
        
      default:
        const errorMsg = `Tipo di schedulazione non supportato: ${config.schedule_type}`;
        logger.error(errorMsg, {
          nodeId: id,
          schedule_type: config.schedule_type
        });
        throw new Error(errorMsg);
    }
  }
  
  /**
   * Configurazione scheduler a intervalli
   */
  async #setupIntervalScheduler(nodeConfig, context) {
    const { id } = nodeConfig;
    const config = nodeConfig.config || {};
    const { interval = {} } = config;
    
    // Calcola l'intervallo in millisecondi
    const intervalMs = this.#calculateIntervalMs(interval);
    
    this.log(context, 'info', `Configurato scheduler a intervalli ogni ${intervalMs}ms per ${id}`);
    logger.info(`Configurato scheduler a intervalli per ${id}`, {
      nodeId: id,
      interval_ms: intervalMs,
      interval_value: interval.value,
      interval_unit: interval.unit
    });
    
    // Crea l'intervallo
    const timer = setInterval(async () => {
      // Controlla se sono state raggiunte le esecuzioni massime
      if (this.#hasReachedMaxExecutions(id, config)) {
        logger.info(`Raggiunto il numero massimo di esecuzioni per ${id}`, {
          nodeId: id,
          max_executions: config.max_executions
        });
        this.#clearScheduler(id);
        return;
      }
      
      // Controlla se la data corrente è oltre la data di fine
      if (this.#isAfterEndDate(config)) {
        logger.info(`Data corrente oltre la data di fine per ${id}`, {
          nodeId: id,
          end_date: config.end_date
        });
        this.#clearScheduler(id);
        return;
      }
      
      await this.#handleScheduledExecution(nodeConfig, context, { 
        triggered_by: 'interval',
        interval_ms: intervalMs
      });
    }, intervalMs);
    
    this.#activeSchedulers.set(id, { timer, type: 'interval', intervalMs });
  }
  
  /**
   * Configurazione scheduler cron
   * Nota: questa è una implementazione semplificata, in un ambiente reale
   * si utilizzerebbe una libreria come 'node-cron' o 'cron-parser'
   */
  async #setupCronScheduler(nodeConfig, context) {
    const { id } = nodeConfig;
    const config = nodeConfig.config || {};
    
    this.log(context, 'info', `Configurato scheduler cron con espressione ${config.cron_expression} per ${id}`);
    logger.info(`Configurato scheduler cron per ${id}`, {
      nodeId: id,
      cron_expression: config.cron_expression,
      timezone: config.timezone
    });
    
    // Calcola quando dovrebbe avvenire la prossima esecuzione
    const nextExecutionMs = this.#calculateNextCronExecutionMs(config.cron_expression, config.timezone);
    
    // Imposta un timeout per la prossima esecuzione
    const timer = setTimeout(async () => {
      // Esegui l'azione schedulata
      await this.#handleScheduledExecution(nodeConfig, context, { 
        triggered_by: 'cron',
        cron_expression: config.cron_expression
      });
      
      // Riconfigura per la prossima esecuzione
      this.#setupCronScheduler(nodeConfig, context);
    }, nextExecutionMs);
    
    this.#activeSchedulers.set(id, { timer, type: 'cron', nextExecutionMs });
  }
  
  /**
   * Configurazione scheduler con data specifica
   */
  async #setupDateScheduler(nodeConfig, context) {
    const { id } = nodeConfig;
    const config = nodeConfig.config || {};
    
    // Calcola i millisecondi fino alla data specifica
    const msUntilDate = this.#getMsUntilSpecificDate(config.specific_date, config.timezone);
    
    if (msUntilDate <= 0) {
      this.log(context, 'warn', `La data specificata è già passata per ${id}`);
      logger.warning(`La data specificata è già passata per ${id}`, {
        nodeId: id,
        specific_date: config.specific_date
      });
      return;
    }
    
    this.log(context, 'info', `Configurato scheduler per data specifica tra ${msUntilDate}ms per ${id}`);
    logger.info(`Configurato scheduler per data specifica per ${id}`, {
      nodeId: id,
      specific_date: config.specific_date,
      ms_until_date: msUntilDate
    });
    
    // Imposta un timeout per l'esecuzione alla data specifica
    const timer = setTimeout(async () => {
      await this.#handleScheduledExecution(nodeConfig, context, { 
        triggered_by: 'date',
        scheduled_date: config.specific_date
      });
      
      // Rimuovi lo scheduler dopo l'esecuzione
      this.#clearScheduler(id);
    }, msUntilDate);
    
    this.#activeSchedulers.set(id, { timer, type: 'date', scheduledDate: config.specific_date });
  }
  
  /**
   * Gestione dell'esecuzione schedulata
   */
  async #handleScheduledExecution(nodeConfig, context, metadata = {}) {
    const { id } = nodeConfig;
    const config = nodeConfig.config || {};
    
    try {
      // Incrementa il contatore delle esecuzioni
      const currentCount = (this.#executionCounters.get(id) || 0) + 1;
      this.#executionCounters.set(id, currentCount);
      
      // Prepara i metadati dell'esecuzione
      const executionMetadata = {
        ...metadata,
        execution_number: currentCount,
        timestamp: new Date().toISOString(),
        node_id: id,
        scheduler_type: config.schedule_type
      };
      
      this.log(context, 'info', `Esecuzione #${currentCount} per ${id}`, executionMetadata);
      logger.info(`Esecuzione #${currentCount} per ${id}`, {
        nodeId: id,
        execution: executionMetadata
      });
      
      // Aggiorna lo storico delle esecuzioni se richiesto
      if (config.execution_tracking?.store_history) {
        const history = this.#executionHistory.get(id) || [];
        history.unshift(executionMetadata);
        
        // Limita la dimensione dello storico
        const maxItems = config.execution_tracking?.max_history_items || 100;
        if (history.length > maxItems) {
          history.length = maxItems;
        }
        
        this.#executionHistory.set(id, history);
        logger.debug(`Aggiornato storico esecuzioni per ${id}`, {
          nodeId: id,
          history_size: history.length,
          max_items: maxItems
        });
      }
      
      // Invia notifica se richiesto
      if (config.execution_tracking?.notify_on_execution) {
        // Implementazione della notifica
        this.#sendNotification(nodeConfig, context, {
          type: 'execution',
          message: `Esecuzione #${currentCount} avvenuta per ${id}`,
          metadata: executionMetadata
        });
      }
      
      // Imposta l'output
      await this.setOutput(context, id, 'output', {
        trigger_time: new Date().toISOString(),
        execution_number: currentCount,
        ...metadata
      });
      
      // Imposta i metadati aggiornati
      await this.setOutput(context, id, 'metadata', {
        node_id: id,
        scheduler_type: config.schedule_type,
        is_active: true,
        last_execution: new Date().toISOString(),
        next_execution: this.#calculateNextExecution(config),
        max_executions: config.max_executions || 'unlimited',
        current_execution_count: currentCount,
        timezone: config.timezone || 'Europe/Rome',
        execution_history: this.#executionHistory.get(id) || []
      });
      
      return executionMetadata;
    } catch (error) {
      this.log(context, 'error', `Errore durante l'esecuzione schedulata: ${error.message}`);
      logger.error(`Errore durante l'esecuzione schedulata per ${id}`, {
        nodeId: id,
        error: error.message,
        stack: error.stack,
        execution_number: this.#executionCounters.get(id)
      });
      
      // Invia notifica di errore se richiesto
      if (config.execution_tracking?.notify_on_error) {
        this.#sendNotification(nodeConfig, context, {
          type: 'error',
          message: `Errore durante l'esecuzione #${this.#executionCounters.get(id)} per ${id}: ${error.message}`,
          error: error.message
        });
      }
      
      throw error;
    }
  }
  
  /**
   * Rimuovi lo scheduler e pulisci le risorse
   */
  #clearScheduler(nodeId) {
    const scheduler = this.#activeSchedulers.get(nodeId);
    if (!scheduler) return;
    
    if (scheduler.timer) {
      if (scheduler.type === 'interval') {
        clearInterval(scheduler.timer);
        logger.debug(`Cancellato interval timer per ${nodeId}`);
      } else {
        clearTimeout(scheduler.timer);
        logger.debug(`Cancellato timeout timer per ${nodeId}`);
      }
    }
    
    logger.info(`Rimosso scheduler per ${nodeId}`, {
      nodeId: nodeId,
      scheduler_type: scheduler.type
    });
    
    this.#activeSchedulers.delete(nodeId);
  }
  
  /**
   * Verifica se sono state raggiunte le esecuzioni massime
   */
  #hasReachedMaxExecutions(nodeId, config) {
    if (!config.max_executions || config.max_executions <= 0) {
      return false;
    }
    
    const currentCount = this.#executionCounters.get(nodeId) || 0;
    return currentCount >= config.max_executions;
  }
  
  /**
   * Verifica se la data corrente è oltre la data di fine
   */
  #isAfterEndDate(config) {
    if (!config.end_date) {
      return false;
    }
    
    const endDate = new Date(config.end_date);
    return new Date() > endDate;
  }
  
  /**
   * Verifica se la data corrente è prima della data di inizio
   */
  #isBeforeStartDate(config) {
    if (!config.start_date) {
      return false;
    }
    
    const startDate = new Date(config.start_date);
    return new Date() < startDate;
  }
  
  /**
   * Calcola i millisecondi mancanti alla data di inizio
   */
  #getMsUntilStartDate(config) {
    if (!config.start_date) {
      return 0;
    }
    
    const startDate = new Date(config.start_date);
    const now = new Date();
    return Math.max(0, startDate.getTime() - now.getTime());
  }
  
  /**
   * Calcola i millisecondi mancanti alla data specifica
   */
  #getMsUntilSpecificDate(dateStr, timezone) {
    if (!dateStr) {
      return -1;
    }
    
    const targetDate = new Date(dateStr);
    const now = new Date();
    return Math.max(0, targetDate.getTime() - now.getTime());
  }
  
  /**
   * Calcola l'intervallo in millisecondi
   */
  #calculateIntervalMs(interval) {
    const value = interval.value || 5;
    const unit = interval.unit || 'minutes';
    
    switch (unit) {
      case 'seconds':
        return value * 1000;
      case 'minutes':
        return value * 60 * 1000;
      case 'hours':
        return value * 60 * 60 * 1000;
      case 'days':
        return value * 24 * 60 * 60 * 1000;
      default:
        return value * 60 * 1000; // default: minuti
    }
  }
  
  /**
   * Calcola quando dovrebbe avvenire la prossima esecuzione CRON
   * Nota: Questa è una implementazione molto semplificata, in un ambiente reale
   * utilizzeremmo una libreria come 'node-cron' o 'cron-parser'
   */
  #calculateNextCronExecutionMs(cronExpression, timezone) {
    // Implementazione semplificata: esegue ogni minuto
    return 60 * 1000;
  }
  
  /**
   * Calcola la prossima esecuzione prevista
   */
  #calculateNextExecution(config) {
    const now = new Date();
    
    switch (config.schedule_type) {
      case 'interval': {
        const intervalMs = this.#calculateIntervalMs(config.interval || {});
        const nextDate = new Date(now.getTime() + intervalMs);
        return nextDate.toISOString();
      }
      
      case 'cron':
        // Implementazione semplificata
        return new Date(now.getTime() + 60 * 1000).toISOString();
        
      case 'date':
        return config.specific_date;
        
      case 'event':
        return 'on event trigger';
        
      default:
        return 'unknown';
    }
  }
  
  /**
   * Invia una notifica
   */
  #sendNotification(nodeConfig, context, notification) {
    // Implementazione della notifica - in un ambiente reale potrebbe
    // utilizzare un sistema di messaggistica, webhook, o altro
    this.log(context, 'info', `Notifica: ${notification.message}`, notification);
    logger.info(`Invio notifica per ${nodeConfig.id}`, {
      nodeId: nodeConfig.id,
      notification_type: notification.type,
      notification_message: notification.message
    });
  }
  
  /**
   * Restituisce lo schema di configurazione
   */
  getConfigSchema() {
    return {
      title: "Configurazione Scheduler",
      type: "object",
      properties: {
        schedule_type: {
          type: "string",
          title: "Tipo di schedulazione",
          enum: ["interval", "cron", "date", "event"],
          enumNames: ["Intervallo", "Espressione Cron", "Data specifica", "Evento"],
          default: "interval"
        },
        interval: {
          type: "object",
          title: "Configurazione intervallo",
          properties: {
            value: {
              type: "integer",
              title: "Valore",
              default: 5
            },
            unit: {
              type: "string",
              title: "Unità",
              enum: ["seconds", "minutes", "hours", "days"],
              enumNames: ["Secondi", "Minuti", "Ore", "Giorni"],
              default: "minutes"
            }
          },
          dependencies: {
            schedule_type: {
              oneOf: [
                {
                  properties: {
                    schedule_type: {
                      enum: ["interval"]
                    }
                  }
                }
              ]
            }
          }
        },
        cron_expression: {
          type: "string",
          title: "Espressione Cron",
          default: "0 * * * *",
          description: "Formato: minuto ora giorno-del-mese mese giorno-della-settimana",
          dependencies: {
            schedule_type: {
              oneOf: [
                {
                  properties: {
                    schedule_type: {
                      enum: ["cron"]
                    }
                  }
                }
              ]
            }
          }
        },
        specific_date: {
          type: "string",
          title: "Data e ora specifiche",
          format: "date-time",
          dependencies: {
            schedule_type: {
              oneOf: [
                {
                  properties: {
                    schedule_type: {
                      enum: ["date"]
                    }
                  }
                }
              ]
            }
          }
        },
        event_name: {
          type: "string",
          title: "Nome evento",
          default: "workflow_trigger",
          dependencies: {
            schedule_type: {
              oneOf: [
                {
                  properties: {
                    schedule_type: {
                      enum: ["event"]
                    }
                  }
                }
              ]
            }
          }
        },
        start_date: {
          type: "string",
          title: "Data di inizio",
          format: "date-time",
          description: "Quando iniziare la schedulazione (opzionale)"
        },
        end_date: {
          type: "string",
          title: "Data di fine",
          format: "date-time",
          description: "Quando terminare la schedulazione (opzionale)"
        },
        max_executions: {
          type: "integer",
          title: "Numero massimo di esecuzioni",
          description: "Limitare il numero di esecuzioni (0 = illimitato)",
          default: 0,
          minimum: 0
        },
        timezone: {
          type: "string",
          title: "Fuso orario",
          default: "Europe/Rome",
          description: "Fuso orario per la schedulazione (es. Europe/Rome, UTC)"
        },
        skip_immediate: {
          type: "boolean",
          title: "Salta prima esecuzione",
          default: false,
          description: "Se attivo, la prima esecuzione viene saltata"
        },
        execution_tracking: {
          type: "object",
          title: "Monitoraggio esecuzioni",
          properties: {
            store_history: {
              type: "boolean",
              title: "Mantieni storico esecuzioni",
              default: true
            },
            max_history_items: {
              type: "integer",
              title: "Numero massimo di elementi nello storico",
              default: 100,
              minimum: 1
            },
            notify_on_execution: {
              type: "boolean",
              title: "Notifica ad ogni esecuzione",
              default: false
            },
            notify_on_error: {
              type: "boolean",
              title: "Notifica in caso di errore",
              default: true
            }
          }
        }
      },
      required: ["schedule_type"]
    };
  }
}
