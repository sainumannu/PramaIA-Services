/**
 * Base classes for PramaIA Plugin Development
 */

import { 
  INodePlugin, 
  INodeProcessor, 
  PluginManifest, 
  NodeConfig, 
  WorkflowContext, 
  ValidationResult 
} from './interfaces.js';

import { LogService, LogLevel } from '../services/log-service.js';

// Logger centralizzato per i nodi
const logger = LogService.getInstance();

// ============================================================================
// Base Node Processor
// ============================================================================

export abstract class BaseNodeProcessor implements INodeProcessor {
  // Logger per questa istanza di processor
  private moduleLogger = logger.getModuleLogger(this.constructor.name);
  
  /**
   * The main execution method that must be implemented by subclasses
   */
  abstract execute(nodeConfig: NodeConfig, context: WorkflowContext): Promise<any>;

  /**
   * Validate node configuration (override if needed)
   */
  async validateConfig(config: any): Promise<ValidationResult> {
    const schema = this.getConfigSchema();
    if (!schema) {
      return { valid: true, errors: [], warnings: [] };
    }

    // Basic validation - can be enhanced with proper schema validation
    const errors: any[] = [];
    const warnings: any[] = [];
    
    // TODO: Implement proper schema validation with ajv or zod
    
    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Initialize the processor (optional)
   */
  async initialize(): Promise<void> {
    // Default implementation - override if needed
    this.moduleLogger.debug('Inizializzazione del processore');
  }

  /**
   * Cleanup resources (optional)
   */
  async cleanup(): Promise<void> {
    // Default implementation - override if needed
    this.moduleLogger.debug('Pulizia delle risorse del processore');
  }

  /**
   * Get configuration schema for UI generation (optional)
   */
  getConfigSchema(): Record<string, any> {
    return {};
  }

  /**
   * Helper method for logging
   * 
   * INTEGRAZIONE CON LOGSERVICE: Ora il metodo log() integra sia il logging di contesto
   * che il logging centralizzato tramite LogService
   */
  protected log(context: WorkflowContext, level: 'info' | 'warn' | 'error' | 'debug', message: string, metadata?: any): void {
    // Log nel contesto di workflow (preserva la funzionalità originale)
    context.log(level, `[${this.constructor.name}] ${message}`, metadata);
    
    // Log anche nel LogService centralizzato
    const logDetails = {
      ...(metadata || {}),
      nodeType: this.constructor.name
    };
    
    const logContext = {
      workflowId: context.workflowId,
      executionId: context.executionId
    };
    
    // Mappa i livelli di log
    switch (level) {
      case 'debug':
        this.moduleLogger.debug(message, logDetails, logContext);
        break;
      case 'info':
        this.moduleLogger.info(message, logDetails, logContext);
        break;
      case 'warn':
        this.moduleLogger.warning(message, logDetails, logContext);
        break;
      case 'error':
        this.moduleLogger.error(message, logDetails, logContext);
        break;
      default:
        this.moduleLogger.info(message, logDetails, logContext);
    }
  }

  /**
   * Helper method for progress reporting
   */
  protected reportProgress(context: WorkflowContext, percentage: number, message?: string): void {
    context.reportProgress(percentage, message ? `[${this.constructor.name}] ${message}` : undefined);
    
    // Log anche il progresso
    if (message) {
      this.moduleLogger.debug(`Progresso: ${percentage}% - ${message}`, {
        percentage,
        nodeType: this.constructor.name
      }, {
        workflowId: context.workflowId,
        executionId: context.executionId
      });
    }
  }

  /**
   * Helper method for safe input retrieval
   */
  protected async getInput(context: WorkflowContext, nodeId: string, inputName?: string, required: boolean = true): Promise<any> {
    try {
      const input = await context.getInput(nodeId, inputName);
      
      if (required && (input === undefined || input === null)) {
        const error = `Required input '${inputName || 'default'}' not provided for node '${nodeId}'`;
        this.moduleLogger.error(error, { nodeId, inputName }, {
          workflowId: context.workflowId,
          executionId: context.executionId
        });
        throw new Error(error);
      }
      
      return input;
    } catch (error: any) {
      this.log(context, 'error', `Failed to get input '${inputName || 'default'}' for node '${nodeId}': ${error.message}`);
      throw error;
    }
  }

  /**
   * Helper method for safe output setting
   */
  protected async setOutput(context: WorkflowContext, nodeId: string, outputName: string, data: any): Promise<void> {
    try {
      await context.setOutput(nodeId, outputName, data);
      this.log(context, 'debug', `Output '${outputName}' set for node '${nodeId}'`);
    } catch (error: any) {
      this.log(context, 'error', `Failed to set output '${outputName}' for node '${nodeId}': ${error.message}`);
      throw error;
    }
  }
}

// ============================================================================
// Base Plugin Class
// ============================================================================

export abstract class BaseNodePlugin implements INodePlugin {
  abstract readonly manifest: PluginManifest;
  readonly processors: Map<string, INodeProcessor> = new Map();
  
  // Logger per questa istanza di plugin
  private moduleLogger = logger.getModuleLogger(`Plugin:${this.constructor.name}`);
  private _initialized = false;

  /**
   * Initialize the plugin
   */
  async initialize(): Promise<void> {
    if (this._initialized) {
      return;
    }

    try {
      this.moduleLogger.info(`Inizializzazione plugin: ${this.manifest?.name || this.constructor.name}`, {
        pluginName: this.manifest?.name,
        version: this.manifest?.version
      });
      
      // Register processors defined in manifest
      await this.registerProcessors();
      
      // Initialize all processors
      for (const processor of this.processors.values()) {
        if (processor.initialize) {
          await processor.initialize();
        }
      }

      this._initialized = true;
      this.moduleLogger.info(`Plugin inizializzato: ${this.manifest?.name || this.constructor.name}`, {
        pluginName: this.manifest?.name,
        processors: Array.from(this.processors.keys())
      });
    } catch (error: any) {
      const errorMsg = `Failed to initialize plugin '${this.manifest?.name || this.constructor.name}': ${error?.message}`;
      this.moduleLogger.error(errorMsg, { error: error?.stack || error?.message });
      throw new Error(errorMsg);
    }
  }

  /**
   * Get processor for a specific node type
   */
  getProcessor(nodeId: string): INodeProcessor | undefined {
    return this.processors.get(nodeId);
  }

  /**
   * Cleanup plugin resources
   */
  async cleanup(): Promise<void> {
    if (!this._initialized) {
      return;
    }

    try {
      this.moduleLogger.info(`Pulizia risorse plugin: ${this.manifest?.name || this.constructor.name}`);
      
      // Cleanup all processors
      for (const processor of this.processors.values()) {
        if (processor.cleanup) {
          await processor.cleanup();
        }
      }

      this.processors.clear();
      this._initialized = false;
      this.moduleLogger.info(`Plugin terminato: ${this.manifest?.name || this.constructor.name}`);
    } catch (error: any) {
      const errorMsg = `Failed to cleanup plugin '${this.manifest?.name || this.constructor.name}': ${error?.message}`;
      this.moduleLogger.error(errorMsg, { error: error?.stack || error?.message });
      throw new Error(errorMsg);
    }
  }

  /**
   * Hot reload support (optional)
   */
  async reload(): Promise<void> {
    this.moduleLogger.info(`Ricaricamento plugin: ${this.manifest?.name || this.constructor.name}`);
    await this.cleanup();
    await this.initialize();
  }

  /**
   * Register processors - must be implemented by subclasses
   */
  protected abstract registerProcessors(): Promise<void>;

  /**
   * Helper method to register a processor
   */
  protected registerProcessor(nodeId: string, processor: INodeProcessor): void {
    if (this.processors.has(nodeId)) {
      const errorMsg = `Processor for node '${nodeId}' already registered`;
      this.moduleLogger.error(errorMsg, { nodeId });
      throw new Error(errorMsg);
    }
    
    this.processors.set(nodeId, processor);
    this.moduleLogger.debug(`Registrato processore: ${nodeId}`, { 
      processorType: processor.constructor.name
    });
  }

  /**
   * Validate plugin manifest against defined nodes
   */
  protected validateManifest(): ValidationResult {
    const errors: any[] = [];
    const warnings: any[] = [];

    this.moduleLogger.debug(`Validazione manifest per ${this.manifest?.name || this.constructor.name}`);

    // Check if all nodes in manifest have corresponding processors
    for (const node of this.manifest.nodes) {
      if (!this.processors.has(node.id)) {
        const error = {
          code: 'MISSING_PROCESSOR',
          message: `No processor found for node '${node.id}'`,
          path: `nodes.${node.id}`
        };
        errors.push(error);
        this.moduleLogger.warning(`Validazione manifest: ${error.message}`, error);
      }
    }

    // Check if all processors have corresponding manifest entries
    for (const nodeId of this.processors.keys()) {
      const found = this.manifest.nodes.find(node => node.id === nodeId);
      if (!found) {
        const warning = {
          code: 'UNREGISTERED_PROCESSOR',
          message: `Processor '${nodeId}' not declared in manifest`,
          path: `processors.${nodeId}`,
          suggestion: `Add node definition for '${nodeId}' to manifest`
        };
        warnings.push(warning);
        this.moduleLogger.warning(`Validazione manifest: ${warning.message}`, warning);
      }
    }

    const isValid = errors.length === 0;
    this.moduleLogger.info(`Validazione manifest completata: ${isValid ? 'valido' : 'non valido'}`, {
      errors: errors.length,
      warnings: warnings.length
    });

    return {
      valid: isValid,
      errors,
      warnings
    };
  }
}

// ============================================================================
// Plugin Factory Function
// ============================================================================

export type PluginFactory = () => Promise<INodePlugin>;

/**
 * Helper function to create a plugin factory
 */
export function createPluginFactory(PluginClass: new () => INodePlugin): PluginFactory {
  return async () => {
    const plugin = new PluginClass();
    await plugin.initialize();
    return plugin;
  };
}
