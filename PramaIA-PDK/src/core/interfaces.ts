/**
 * Core interfaces for PramaIA Plugin Development Kit
 * 
 * These interfaces define the contract between plugins and the main workflow engine
 */

import { z } from 'zod';

// ============================================================================
// Base Types
// ============================================================================

export type NodeType = 
  | 'input'       // Data sources (file readers, API consumers)
  | 'processing'  // Data transformers (PDF processors, AI integrations)
  | 'output'      // Data destinations (file writers, notifications)
  | 'control';    // Flow control (conditions, loops)

// New: Plugin types for extended PDK
export type PluginType = 
  | 'node'         // Traditional workflow nodes
  | 'event-source'; // Event sources for triggers

// New: Event Source Lifecycle
export type EventSourceLifecycle = 
  | 'on-demand'    // Started/stopped on request
  | 'persistent'   // Always running processes
  | 'scheduled';   // Cron-like scheduled events

export type DataType = 
  | 'text' 
  | 'file' 
  | 'json' 
  | 'binary' 
  | 'image' 
  | 'pdf' 
  | 'csv' 
  | 'xml' 
  | 'any';

// ============================================================================
// Configuration Schemas
// ============================================================================

// Event Source Configuration Schema
export const EventTypeSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  
  // Tags for individual event types
  tags: z.array(z.string()).optional().default([]),
  
  outputs: z.array(z.object({
    name: z.string(),
    type: z.string(),
    description: z.string().optional()
  }))
});

export const EventSourceManifestSchema = z.object({
  name: z.string(),
  version: z.string(),
  description: z.string(),
  author: z.string(),
  license: z.string().optional(),
  homepage: z.string().url().optional(),
  repository: z.string().url().optional(),
  
  // Plugin metadata
  type: z.literal('event-source'),
  pdk_version: z.string(),
  engine_compatibility: z.string(),
  
  // Event source specific
  lifecycle: z.enum(['on-demand', 'persistent', 'scheduled']),
  
  // Tags for organization and filtering
  tags: z.array(z.string()).optional().default([]),
  
  // Event types this source can emit
  eventTypes: z.array(EventTypeSchema),
  
  // Configuration schema for the event source
  configSchema: z.record(z.any()).optional(),
  
  // Entry point for the event source
  entry: z.string(),
  
  // Dependencies
  dependencies: z.record(z.string()).optional(),
  peer_dependencies: z.record(z.string()).optional()
});

export const NodeConfigSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  version: z.string(),
  enabled: z.boolean().default(true),
  config: z.record(z.any()).optional()
});

export const PluginManifestSchema = z.object({
  name: z.string(),
  version: z.string(),
  description: z.string(),
  author: z.string(),
  license: z.string().optional(),
  homepage: z.string().url().optional(),
  repository: z.string().url().optional(),
  
  // Plugin metadata
  type: z.enum(['node', 'event-source']).default('node'),
  pdk_version: z.string(),
  engine_compatibility: z.string(),
  
  // Tags for plugin organization and filtering
  tags: z.array(z.string()).optional().default([]),
  
  // Node definitions
  nodes: z.array(z.object({
    id: z.string(),
    name: z.string(),
    type: z.enum(['input', 'processing', 'output', 'control']),
    category: z.string(),
    description: z.string(),
    icon: z.string().optional(),
    color: z.string().optional(),
    
    // Tags for organization and filtering
    tags: z.array(z.string()).optional().default([]),
    
    // I/O specifications
    inputs: z.array(z.object({
      name: z.string(),
      type: z.string(),
      required: z.boolean().default(true),
      description: z.string().optional()
    })),
    
    outputs: z.array(z.object({
      name: z.string(),
      type: z.string(),
      description: z.string().optional()
    })),
    
    // Configuration schema
    config_schema: z.record(z.any()).optional(),
    
    // Execution settings
    async: z.boolean().default(true),
    timeout: z.number().optional(),
    retry_count: z.number().default(0)
  })),
  
  // Dependencies
  dependencies: z.record(z.string()).optional(),
  peer_dependencies: z.record(z.string()).optional()
});

export type NodeConfig = z.infer<typeof NodeConfigSchema>;
export type PluginManifest = z.infer<typeof PluginManifestSchema>;

// ============================================================================
// Execution Context
// ============================================================================

export interface WorkflowContext {
  readonly executionId: string;
  readonly workflowId: string;
  readonly userId?: string;
  readonly groupId?: string;
  
  // Data flow
  getInput(nodeId: string, inputName?: string): Promise<any>;
  setOutput(nodeId: string, outputName: string, data: any): Promise<void>;
  
  // State management
  getState(key: string): Promise<any>;
  setState(key: string, value: any): Promise<void>;
  
  // Logging and monitoring
  log(level: 'info' | 'warn' | 'error' | 'debug', message: string, metadata?: any): void;
  reportProgress(percentage: number, message?: string): void;
  
  // File system (sandboxed)
  readFile(path: string): Promise<Buffer>;
  writeFile(path: string, data: Buffer | string): Promise<void>;
  
  // HTTP requests (with restrictions)
  httpRequest(config: {
    url: string;
    method?: string;
    headers?: Record<string, string>;
    data?: any;
    timeout?: number;
  }): Promise<any>;
}

// ============================================================================
// Node Processor Interface
// ============================================================================

export interface INodeProcessor {
  /**
   * Process the node with given configuration and context
   */
  execute(nodeConfig: NodeConfig, context: WorkflowContext): Promise<any>;
  
  /**
   * Validate the node configuration
   */
  validateConfig?(config: any): Promise<ValidationResult>;
  
  /**
   * Initialize the processor (called once when plugin is loaded)
   */
  initialize?(): Promise<void>;
  
  /**
   * Cleanup resources (called when plugin is unloaded)
   */
  cleanup?(): Promise<void>;
  
  /**
   * Get configuration schema for UI generation
   */
  getConfigSchema?(): Record<string, any>;
}

// ============================================================================
// Plugin Interface
// ============================================================================

export interface INodePlugin {
  readonly manifest: PluginManifest;
  readonly processors: Map<string, INodeProcessor>;
  
  /**
   * Initialize the plugin
   */
  initialize(): Promise<void>;
  
  /**
   * Get processor for a specific node type
   */
  getProcessor(nodeId: string): INodeProcessor | undefined;
  
  /**
   * Cleanup plugin resources
   */
  cleanup(): Promise<void>;
  
  /**
   * Hot reload support
   */
  reload?(): Promise<void>;
}

// ============================================================================
// Validation Results
// ============================================================================

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  code: string;
  message: string;
  path?: string;
  details?: any;
}

export interface ValidationWarning {
  code: string;
  message: string;
  path?: string;
  suggestion?: string;
}

// ============================================================================
// Plugin Registry
// ============================================================================

export interface PluginRegistryEntry {
  id: string;
  name: string;
  version: string;
  path: string;
  manifest: PluginManifest;
  loaded: boolean;
  instance?: INodePlugin;
  lastModified: Date;
}

export interface IPluginRegistry {
  /**
   * Register a plugin
   */
  register(pluginPath: string): Promise<PluginRegistryEntry>;
  
  /**
   * Unregister a plugin
   */
  unregister(pluginId: string): Promise<void>;
  
  /**
   * Get all registered plugins
   */
  getAllPlugins(): PluginRegistryEntry[];
  
  /**
   * Get plugin by ID
   */
  getPlugin(pluginId: string): PluginRegistryEntry | undefined;
  
  /**
   * Get processor for a node type
   */
  getProcessor(nodeType: string): INodeProcessor | undefined;
  
  /**
   * Reload a plugin (hot reload)
   */
  reloadPlugin(pluginId: string): Promise<void>;
  
  /**
   * Validate all plugins
   */
  validateAll(): Promise<ValidationResult[]>;
}

// ============================================================================
// Events
// ============================================================================

export interface PluginEvent {
  type: 'loaded' | 'unloaded' | 'reloaded' | 'error';
  pluginId: string;
  timestamp: Date;
  data?: any;
}

export interface IPluginEventEmitter {
  on(event: string, listener: (event: PluginEvent) => void): void;
  off(event: string, listener: (event: PluginEvent) => void): void;
  emit(event: string, data: PluginEvent): void;
}

// ============================================================================
// Event Sources Extension
// ============================================================================

export interface EventSourceOutput {
  eventType: string;
  data: Record<string, any>;
  timestamp: Date;
  sourceId: string;
}

export interface EventSourceContext {
  log: (level: 'info' | 'warn' | 'error' | 'debug', message: string, metadata?: any) => void;
  reportProgress: (percentage: number, message?: string) => void;
  emitEvent: (eventType: string, data: Record<string, any>) => Promise<void>;
  getConfig: () => Record<string, any>;
  getState: () => Record<string, any>;
  setState: (state: Record<string, any>) => Promise<void>;
}

export interface IEventSourceProcessor {
  /**
   * Initialize the event source
   */
  initialize(config: Record<string, any>, context: EventSourceContext): Promise<void>;
  
  /**
   * Start monitoring/listening for events
   */
  start(): Promise<void>;
  
  /**
   * Stop monitoring/listening for events
   */
  stop(): Promise<void>;
  
  /**
   * Get current status of the event source
   */
  getStatus(): Promise<{
    running: boolean;
    lastActivity?: Date;
    eventsEmitted: number;
    errors?: string[];
  }>;
  
  /**
   * Cleanup resources
   */
  cleanup(): Promise<void>;
  
  /**
   * Validate configuration
   */
  validateConfig(config: Record<string, any>): Promise<ValidationResult>;
}

export interface EventSourceRegistryEntry {
  id: string;
  name: string;
  version: string;
  path: string;
  manifest: EventSourceManifest;
  loaded: boolean;
  instance?: IEventSourceProcessor;
  lastModified: Date;
  status: 'stopped' | 'starting' | 'running' | 'stopping' | 'error';
}

export interface IEventSourceRegistry {
  /**
   * Register an event source
   */
  register(sourcePath: string): Promise<EventSourceRegistryEntry>;
  
  /**
   * Unregister an event source
   */
  unregister(sourceId: string): Promise<void>;
  
  /**
   * Get all registered event sources
   */
  getAllSources(): EventSourceRegistryEntry[];
  
  /**
   * Get event source by ID
   */
  getSource(sourceId: string): EventSourceRegistryEntry | undefined;
  
  /**
   * Start an event source
   */
  startSource(sourceId: string, config: Record<string, any>): Promise<void>;
  
  /**
   * Stop an event source
   */
  stopSource(sourceId: string): Promise<void>;
  
  /**
   * Get status of an event source
   */
  getSourceStatus(sourceId: string): Promise<EventSourceRegistryEntry['status']>;
  
  /**
   * Reload an event source (hot reload)
   */
  reloadSource(sourceId: string): Promise<void>;
}

// Type exports
export type EventType = z.infer<typeof EventTypeSchema>;
export type EventSourceManifest = z.infer<typeof EventSourceManifestSchema>;
