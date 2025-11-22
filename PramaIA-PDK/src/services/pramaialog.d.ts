/**
 * Definizioni di tipi per il client PramaIALogger
 */

/**
 * Livelli di log supportati
 */
export const LogLevel: {
  readonly DEBUG: 'debug';
  readonly INFO: 'info';
  readonly WARNING: 'warning';
  readonly ERROR: 'error';
  readonly CRITICAL: 'critical';
};

export type LogLevelType = typeof LogLevel[keyof typeof LogLevel];

/**
 * Progetti PramaIA supportati
 */
export const LogProject: {
  readonly SERVER: 'PramaIAServer';
  readonly PDK: 'PramaIA-PDK';
  readonly AGENTS: 'PramaIA-Agents';
  readonly PLUGINS: 'PramaIA-Plugins';
  readonly OTHER: 'other';
};

export type LogProjectType = typeof LogProject[keyof typeof LogProject];

/**
 * Opzioni per il client PramaIALogger
 */
export interface PramaIALoggerOptions {
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

/**
 * Client per il servizio di logging PramaIA
 */
export class PramaIALogger {
  constructor(options: PramaIALoggerOptions);
  
  log(level: string, message: string, details?: any, context?: any): string;
  debug(message: string, details?: any, context?: any): string;
  info(message: string, details?: any, context?: any): string;
  warning(message: string, details?: any, context?: any): string;
  error(message: string, details?: any, context?: any): string;
  critical(message: string, details?: any, context?: any): string;
  flush(): Promise<boolean>;
  close(): Promise<void>;
}

/**
 * Funzione di utilità per configurare facilmente il logger
 */
export function setupLogger(options: PramaIALoggerOptions): PramaIALogger;
