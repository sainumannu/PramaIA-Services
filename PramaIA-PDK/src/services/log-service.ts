/**
 * LogService - Servizio di logging centralizzato per il PDK
 * 
 * Questo servizio fornisce un'interfaccia unificata per il logging in tutti i componenti
 * del PDK, utilizzando il client PramaIALogger per inviare i log al servizio LogService.
 */

// Definizioni di tipi per il client PramaIALogger
const LogLevel = {
  DEBUG: 'debug',
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical'
} as const;

type LogLevelType = typeof LogLevel[keyof typeof LogLevel];

const LogProject = {
  SERVER: 'PramaIAServer',
  PDK: 'PramaIA-PDK',
  AGENTS: 'PramaIA-Agents',
  PLUGINS: 'PramaIA-Plugins',
  OTHER: 'other'
} as const;

type LogProjectType = typeof LogProject[keyof typeof LogProject];

interface PramaIALoggerOptions {
  apiKey: string;
  project: string;
  module: string;
  host?: string;
  bufferSize?: number;
  autoFlush?: boolean;
  flushInterval?: number;
  retryMaxAttempts?: number;
  retryDelay?: number;
}

// Interfaccia per PramaIALogger
interface IPramaIALogger {
  log(level: string, message: string, details?: any, context?: any): string;
  debug(message: string, details?: any, context?: any): string;
  info(message: string, details?: any, context?: any): string;
  warning(message: string, details?: any, context?: any): string;
  error(message: string, details?: any, context?: any): string;
  critical(message: string, details?: any, context?: any): string;
  flush(): Promise<boolean>;
  close(): Promise<void>;
}

// Import del client PramaIALogger
let PramaIALoggerClass: any;

try {
  // Prima tenta di importare il client locale nella directory services
  try {
    const pramaiaLog = require('./pramaialog.js');
    PramaIALoggerClass = pramaiaLog.PramaIALogger;
    console.log('Client PramaIALogger caricato dalla directory locale (services).');
  } catch (localError: any) {
    // Se fallisce, prova il percorso relativo al LogService
    PramaIALoggerClass = require('../../../PramaIA-LogService/clients/javascript/pramaialog.js').PramaIALogger;
    console.log('Client PramaIALogger caricato dal repository PramaIA-LogService.');
  }
} catch (error: any) {
  // Se l'importazione fallisce, creiamo un mock che logga su console
  console.warn(`Client PramaIALogger non trovato (${error.message}), verrà utilizzato un fallback su console`);
  
  PramaIALoggerClass = class MockPramaIALogger implements IPramaIALogger {
    private options: PramaIALoggerOptions;
    
    constructor(options: PramaIALoggerOptions) {
      this.options = options;
      console.info(`MockPramaIALogger inizializzato per ${options.project}/${options.module}`);
    }
    
    log(level: string, message: string, details?: any, context?: any): string {
      const timestamp = new Date().toISOString();
      const detailsStr = details ? ` ${JSON.stringify(details)}` : '';
      const contextStr = context ? ` Context: ${JSON.stringify(context)}` : '';
      console.log(`[${timestamp}] [${this.options.project}/${this.options.module}] [${level.toUpperCase()}] ${message}${detailsStr}${contextStr}`);
      return 'mock-log-id-' + Date.now();
    }
    
    debug(message: string, details?: any, context?: any): string {
      return this.log(LogLevel.DEBUG, message, details, context);
    }
    
    info(message: string, details?: any, context?: any): string {
      return this.log(LogLevel.INFO, message, details, context);
    }
    
    warning(message: string, details?: any, context?: any): string {
      return this.log(LogLevel.WARNING, message, details, context);
    }
    
    error(message: string, details?: any, context?: any): string {
      return this.log(LogLevel.ERROR, message, details, context);
    }
    
    critical(message: string, details?: any, context?: any): string {
      return this.log(LogLevel.CRITICAL, message, details, context);
    }
    
    async flush(): Promise<boolean> {
      console.debug(`[MockPramaIALogger] Flush chiamato per ${this.options.project}/${this.options.module}`);
      return true;
    }
    
    async close(): Promise<void> {
      console.debug(`[MockPramaIALogger] Close chiamato per ${this.options.project}/${this.options.module}`);
      // Nulla da fare
    }
  };
}

// Configurazione di default
// Resolve host preferring BACKEND_URL, then PRAMAIALOG_HOST (+ optional PRAMAIALOG_PORT), fallback to localhost:8081
function resolveBackendUrl(): string {
  if (process.env.BACKEND_URL) return process.env.BACKEND_URL;
  let host = process.env.PRAMAIALOG_HOST || '';
  const port = process.env.PRAMAIALOG_PORT;
  if (host) {
    if (port && !/:\\d+$/.test(host)) {
      return `${host.replace(/\/$/, '')}:${port}`;
    }
    return host;
  }
  return 'http://localhost:8081';
}

const DEFAULT_CONFIG = {
  host: resolveBackendUrl(),
  apiKey: process.env.PRAMAIALOG_API_KEY || 'pdk-dev-key',
  project: LogProject.PDK,
  module: 'pdk-core',
  bufferSize: 50,
  flushInterval: 5000
};

/**
 * Servizio di logging centralizzato per il PDK
 */
export class LogService {
  private static instance: LogService;
  private logger: IPramaIALogger;
  private enabled: boolean = true;
  
  /**
   * Costruttore privato per pattern Singleton
   */
  private constructor(config: any = {}) {
    const loggerConfig = { ...DEFAULT_CONFIG, ...config };
    
    try {
      this.logger = new PramaIALoggerClass(loggerConfig);
      console.log(`LogService inizializzato per ${loggerConfig.project}/${loggerConfig.module}`);
    } catch (error: any) {
      console.error(`Errore durante l'inizializzazione di LogService: ${error?.message || 'Errore sconosciuto'}`);
      // Fallback: disabilitiamo il servizio e usiamo solo console
      this.enabled = false;
      this.logger = new PramaIALoggerClass(loggerConfig);
    }
  }
  
  /**
   * Ottieni l'istanza singleton del LogService
   */
  public static getInstance(config?: any): LogService {
    if (!LogService.instance) {
      LogService.instance = new LogService(config);
    }
    return LogService.instance;
  }
  
  /**
   * Configura un logger specifico per un modulo
   */
  public getModuleLogger(moduleName: string): ModuleLogger {
    return new ModuleLogger(this, moduleName);
  }
  
  /**
   * Log di debug
   */
  public debug(message: string, details?: any, context?: any): string | null {
    return this.log(LogLevel.DEBUG, message, details, context);
  }
  
  /**
   * Log di informazione
   */
  public info(message: string, details?: any, context?: any): string | null {
    return this.log(LogLevel.INFO, message, details, context);
  }
  
  /**
   * Log di avviso
   */
  public warning(message: string, details?: any, context?: any): string | null {
    return this.log(LogLevel.WARNING, message, details, context);
  }
  
  /**
   * Log di errore
   */
  public error(message: string, details?: any, context?: any): string | null {
    return this.log(LogLevel.ERROR, message, details, context);
  }
  
  /**
   * Log critico
   */
  public critical(message: string, details?: any, context?: any): string | null {
    return this.log(LogLevel.CRITICAL, message, details, context);
  }
  
  /**
   * Metodo generico di logging
   */
  public log(level: string, message: string, details?: any, context?: any): string | null {
    if (!this.enabled) {
      // Fallback su console se il servizio è disabilitato
      this.logToConsole(level, message, details);
      return null;
    }
    
    try {
      return this.logger.log(level, message, details, context);
    } catch (error: any) {
      // Fallback su console in caso di errore
      console.error(`Errore durante il logging: ${error?.message || 'Errore sconosciuto'}`);
      this.logToConsole(level, message, details);
      return null;
    }
  }
  
  /**
   * Fallback su console
   */
  private logToConsole(level: string, message: string, details?: any): void {
    const timestamp = new Date().toISOString();
    const detailsStr = details ? ` ${JSON.stringify(details)}` : '';
    
    switch (level) {
      case LogLevel.DEBUG:
        console.debug(`[${timestamp}] [DEBUG] ${message}${detailsStr}`);
        break;
      case LogLevel.INFO:
        console.info(`[${timestamp}] [INFO] ${message}${detailsStr}`);
        break;
      case LogLevel.WARNING:
        console.warn(`[${timestamp}] [WARN] ${message}${detailsStr}`);
        break;
      case LogLevel.ERROR:
      case LogLevel.CRITICAL:
        console.error(`[${timestamp}] [${level.toUpperCase()}] ${message}${detailsStr}`);
        break;
      default:
        console.log(`[${timestamp}] [${level.toUpperCase()}] ${message}${detailsStr}`);
    }
  }
  
  /**
   * Flush dei log pendenti
   */
  public async flush(): Promise<boolean> {
    if (!this.enabled) return true;
    
    try {
      return await this.logger.flush();
    } catch (error: any) {
      console.error(`Errore durante il flush dei log: ${error?.message || 'Errore sconosciuto'}`);
      return false;
    }
  }
  
  /**
   * Chiusura del logger
   */
  public async close(): Promise<void> {
    if (!this.enabled) return;
    
    try {
      await this.logger.close();
    } catch (error: any) {
      console.error(`Errore durante la chiusura del logger: ${error?.message || 'Errore sconosciuto'}`);
    }
  }
}

/**
 * Logger specifico per un modulo
 */
export class ModuleLogger {
  private service: LogService;
  private moduleName: string;
  
  constructor(service: LogService, moduleName: string) {
    this.service = service;
    this.moduleName = moduleName;
  }
  
  public debug(message: string, details?: any, context?: any): string | null {
    return this.log(LogLevel.DEBUG, message, details, context);
  }
  
  public info(message: string, details?: any, context?: any): string | null {
    return this.log(LogLevel.INFO, message, details, context);
  }
  
  public warning(message: string, details?: any, context?: any): string | null {
    return this.log(LogLevel.WARNING, message, details, context);
  }
  
  public error(message: string, details?: any, context?: any): string | null {
    return this.log(LogLevel.ERROR, message, details, context);
  }
  
  public critical(message: string, details?: any, context?: any): string | null {
    return this.log(LogLevel.CRITICAL, message, details, context);
  }
  
  public log(level: string, message: string, details?: any, context?: any): string | null {
    // Aggiungi il nome del modulo al contesto
    const enrichedContext = {
      ...(context || {}),
      module: this.moduleName
    };
    
    return this.service.log(level, message, details, enrichedContext);
  }
}

// Esporta anche le enumerazioni dal client
export { LogLevel, LogProject };
