/**
 * Base classes for PramaIA Event Sources
 */

import { 
  IEventSourceProcessor,
  EventSourceContext,
  ValidationResult,
  ValidationError,
  ValidationWarning,
  EventSourceManifest
} from './interfaces.js';

// ============================================================================
// Base Event Source Processor
// ============================================================================

export abstract class BaseEventSourceProcessor implements IEventSourceProcessor {
  protected config: Record<string, any> = {};
  protected context: EventSourceContext | null = null;
  protected running: boolean = false;
  protected eventsEmitted: number = 0;
  protected errors: string[] = [];
  protected lastActivity?: Date;

  /**
   * Initialize the event source with configuration and context
   */
  async initialize(config: Record<string, any>, context: EventSourceContext): Promise<void> {
    this.config = config;
    this.context = context;
    
    // Validate configuration
    const validation = await this.validateConfig(config);
    if (!validation.valid) {
      throw new Error(`Configuration validation failed: ${validation.errors.join(', ')}`);
    }
    
    // Call subclass initialization
    await this.onInitialize();
    
    this.log('info', 'Event source initialized successfully');
  }

  /**
   * Start the event source
   */
  async start(): Promise<void> {
    if (this.running) {
      this.log('warn', 'Event source is already running');
      return;
    }

    try {
      this.log('info', 'Starting event source...');
      this.running = true;
      this.errors = []; // Clear previous errors
      
      await this.onStart();
      
      this.log('info', 'Event source started successfully');
    } catch (error: any) {
      this.running = false;
      const errorMsg = `Failed to start event source: ${error.message}`;
      this.errors.push(errorMsg);
      this.log('error', errorMsg, { error: error.stack });
      throw error;
    }
  }

  /**
   * Stop the event source
   */
  async stop(): Promise<void> {
    if (!this.running) {
      this.log('warn', 'Event source is not running');
      return;
    }

    try {
      this.log('info', 'Stopping event source...');
      
      await this.onStop();
      
      this.running = false;
      this.log('info', 'Event source stopped successfully');
    } catch (error: any) {
      const errorMsg = `Error while stopping event source: ${error.message}`;
      this.errors.push(errorMsg);
      this.log('error', errorMsg, { error: error.stack });
      throw error;
    }
  }

  /**
   * Get current status
   */
  async getStatus(): Promise<{
    running: boolean;
    lastActivity?: Date;
    eventsEmitted: number;
    errors?: string[];
  }> {
    return {
      running: this.running,
      lastActivity: this.lastActivity,
      eventsEmitted: this.eventsEmitted,
      errors: this.errors.length > 0 ? this.errors : undefined
    };
  }

  /**
   * Cleanup resources
   */
  async cleanup(): Promise<void> {
    if (this.running) {
      await this.stop();
    }
    
    await this.onCleanup();
    this.log('info', 'Event source cleaned up');
  }

  /**
   * Validate configuration (override if needed)
   */
  async validateConfig(config: Record<string, any>): Promise<ValidationResult> {
    const schema = this.getConfigSchema();
    if (!schema || Object.keys(schema).length === 0) {
      return { valid: true, errors: [], warnings: [] };
    }

    // Basic validation - can be enhanced with proper schema validation
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    
    // TODO: Implement proper schema validation with ajv or zod
    
    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  // ============================================================================
  // Abstract Methods (must be implemented by subclasses)
  // ============================================================================

  /**
   * Called during initialization - override for custom setup
   */
  protected async onInitialize(): Promise<void> {
    // Default implementation - override if needed
  }

  /**
   * Called when starting the event source - must be implemented
   */
  protected abstract onStart(): Promise<void>;

  /**
   * Called when stopping the event source - must be implemented
   */
  protected abstract onStop(): Promise<void>;

  /**
   * Called during cleanup - override for custom cleanup
   */
  protected async onCleanup(): Promise<void> {
    // Default implementation - override if needed
  }

  /**
   * Get configuration schema for UI generation (optional)
   */
  protected getConfigSchema(): Record<string, any> {
    return {};
  }

  // ============================================================================
  // Helper Methods
  // ============================================================================

  /**
   * Helper method for logging
   */
  protected log(level: 'info' | 'warn' | 'error' | 'debug', message: string, metadata?: any): void {
    if (this.context) {
      this.context.log(level, `[${this.constructor.name}] ${message}`, metadata);
    }
  }

  /**
   * Helper method for progress reporting
   */
  protected reportProgress(percentage: number, message?: string): void {
    if (this.context) {
      this.context.reportProgress(percentage, message ? `[${this.constructor.name}] ${message}` : undefined);
    }
  }

  /**
   * Helper method for emitting events
   */
  protected async emitEvent(eventType: string, data: Record<string, any>): Promise<void> {
    if (!this.context) {
      throw new Error('Event source context not initialized');
    }

    try {
      await this.context.emitEvent(eventType, data);
      this.eventsEmitted++;
      this.lastActivity = new Date();
      this.log('debug', `Event emitted: ${eventType}`, { data });
    } catch (error: any) {
      const errorMsg = `Failed to emit event ${eventType}: ${error.message}`;
      this.errors.push(errorMsg);
      this.log('error', errorMsg, { error: error.stack });
      throw error;
    }
  }

  /**
   * Helper method for safe configuration retrieval
   */
  protected getConfigValue<T>(key: string, defaultValue?: T, required: boolean = false): T {
    const value = this.config[key];
    
    if (required && (value === undefined || value === null)) {
      throw new Error(`Required configuration '${key}' not provided`);
    }
    
    return value !== undefined ? value : (defaultValue as T);
  }

  /**
   * Helper method for getting current state
   */
  protected async getState(): Promise<Record<string, any>> {
    if (!this.context) {
      return {};
    }
    return this.context.getState();
  }

  /**
   * Helper method for setting state
   */
  protected async setState(state: Record<string, any>): Promise<void> {
    if (!this.context) {
      throw new Error('Event source context not initialized');
    }
    await this.context.setState(state);
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Create an event source manifest validator
 */
export function createEventSourceManifestValidator() {
  return (manifest: any): manifest is EventSourceManifest => {
    // Basic validation
    return (
      manifest &&
      typeof manifest === 'object' &&
      typeof manifest.name === 'string' &&
      typeof manifest.version === 'string' &&
      manifest.type === 'event-source' &&
      Array.isArray(manifest.eventTypes) &&
      typeof manifest.entry === 'string'
    );
  };
}

/**
 * Helper to load event source manifest from plugin directory
 */
export async function loadEventSourceManifest(pluginPath: string): Promise<EventSourceManifest> {
  const fs = await import('fs/promises');
  const path = await import('path');
  
  const manifestPath = path.join(pluginPath, 'plugin.json');
  
  try {
    const manifestContent = await fs.readFile(manifestPath, 'utf-8');
    const manifest = JSON.parse(manifestContent);
    
    const validator = createEventSourceManifestValidator();
    if (!validator(manifest)) {
      throw new Error('Invalid event source manifest format');
    }
    
    return manifest;
  } catch (error: any) {
    throw new Error(`Failed to load event source manifest from ${manifestPath}: ${error.message}`);
  }
}
