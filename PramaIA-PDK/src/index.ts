/**
 * PramaIA Plugin Development Kit (PDK)
 * 
 * Main entry point for the plugin development kit
 */

// Core interfaces and types
export * from './core/interfaces.js';
export * from './core/base.js';

// Services
export * from './services/log-service.js';

// Testing utilities
export * from './testing/index.js';

// Development utilities
export * from './utils/index.js';

// Re-export commonly used types for convenience
export type {
  NodeType,
  DataType,
  NodeConfig,
  PluginManifest,
  WorkflowContext,
  INodeProcessor,
  INodePlugin,
  ValidationResult,
  ValidationError,
  ValidationWarning
} from './core/interfaces.js';

export {
  BaseNodeProcessor,
  BaseNodePlugin,
  createPluginFactory
} from './core/base.js';

export {
  LogService,
  LogLevel,
  LogProject,
  ModuleLogger
} from './services/log-service.js';

export {
  MockWorkflowContext,
  PluginTestUtils,
  PluginTestRunner
} from './testing/index.js';

export {
  PluginValidator,
  PluginBuilder,
  HotReloader,
  ConfigurationValidator
} from './utils/index.js';

// Version information
export const VERSION = '1.0.0';
export const PDK_VERSION = VERSION;

// Plugin integration utilities
export * from './integration/workflow-engine.js';
