/**
 * Utility classes for plugin development
 */

import { ValidationResult, ValidationError, ValidationWarning, PluginManifest, INodeProcessor } from '../core/interfaces.js';

/**
 * Plugin validator utility
 */
export class PluginValidator {
  /**
   * Validate a plugin manifest
   */
  static validateManifest(manifest: any): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    try {
      // Basic structure validation
      if (!manifest.name) {
        errors.push({
          code: 'MISSING_NAME',
          message: 'Plugin name is required'
        });
      }

      if (!manifest.version) {
        errors.push({
          code: 'MISSING_VERSION',
          message: 'Plugin version is required'
        });
      }

      if (!manifest.nodes || !Array.isArray(manifest.nodes)) {
        errors.push({
          code: 'MISSING_NODES',
          message: 'Plugin must define at least one node'
        });
      } else {
        // Validate nodes
        manifest.nodes.forEach((node: any, index: number) => {
          this.validateNode(node, `nodes[${index}]`, errors, warnings);
        });
      }

      // Validate version format
      if (manifest.version && !this.isValidVersion(manifest.version)) {
        warnings.push({
          code: 'INVALID_VERSION_FORMAT',
          message: 'Version should follow semantic versioning (e.g., 1.0.0)',
          suggestion: 'Use semantic versioning format'
        });
      }

      // Check for recommended fields
      if (!manifest.description) {
        warnings.push({
          code: 'MISSING_DESCRIPTION',
          message: 'Consider adding a description',
          suggestion: 'Add description field for better discoverability'
        });
      }

      if (!manifest.author) {
        warnings.push({
          code: 'MISSING_AUTHOR',
          message: 'Consider adding author information',
          suggestion: 'Add author field'
        });
      }

    } catch (error) {
      errors.push({
        code: 'VALIDATION_ERROR',
        message: `Manifest validation failed: ${error}`,
        details: error
      });
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Validate a plugin instance
   */
  static validatePlugin(plugin: any): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    try {
      // Check if plugin has required methods
      if (!plugin.manifest) {
        errors.push({
          code: 'MISSING_MANIFEST',
          message: 'Plugin must have a manifest property'
        });
      }

      if (!plugin.processors || !(plugin.processors instanceof Map)) {
        errors.push({
          code: 'MISSING_PROCESSORS',
          message: 'Plugin must have a processors Map'
        });
      }

      if (typeof plugin.getProcessor !== 'function') {
        errors.push({
          code: 'MISSING_GET_PROCESSOR',
          message: 'Plugin must implement getProcessor method'
        });
      }

      // Validate processors
      if (plugin.processors instanceof Map) {
        for (const [nodeId, processor] of plugin.processors.entries()) {
          this.validateProcessor(processor, nodeId, errors, warnings);
        }
      }

      // Check if all manifest nodes have corresponding processors
      if (plugin.manifest && plugin.manifest.nodes) {
        plugin.manifest.nodes.forEach((node: any) => {
          if (!plugin.processors.has(node.id)) {
            errors.push({
              code: 'MISSING_PROCESSOR',
              message: `No processor found for node: ${node.id}`,
              path: node.id
            });
          }
        });
      }

    } catch (error) {
      errors.push({
        code: 'PLUGIN_VALIDATION_ERROR',
        message: `Plugin validation failed: ${error}`,
        details: error
      });
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Validate a processor implementation
   */
  static validateProcessor(processor: any, nodeId: string, errors: ValidationError[], warnings: ValidationWarning[]): void {
    if (!processor) {
      errors.push({
        code: 'NULL_PROCESSOR',
        message: `Processor for node ${nodeId} is null or undefined`
      });
      return;
    }

    // Check required methods
    if (typeof processor.execute !== 'function') {
      errors.push({
        code: 'MISSING_EXECUTE_METHOD',
        message: `Processor for node ${nodeId} must implement execute method`
      });
    }

    // Check optional methods
    if (processor.validateConfig && typeof processor.validateConfig !== 'function') {
      warnings.push({
        code: 'INVALID_VALIDATE_CONFIG',
        message: `validateConfig for node ${nodeId} should be a function`,
        suggestion: 'Implement validateConfig as a function or remove it'
      });
    }

    if (processor.getConfigSchema && typeof processor.getConfigSchema !== 'function') {
      warnings.push({
        code: 'INVALID_GET_CONFIG_SCHEMA',
        message: `getConfigSchema for node ${nodeId} should be a function`,
        suggestion: 'Implement getConfigSchema as a function or remove it'
      });
    }
  }

  /**
   * Validate a node definition
   */
  private static validateNode(node: any, path: string, errors: ValidationError[], warnings: ValidationWarning[]): void {
    if (!node.id) {
      errors.push({
        code: 'MISSING_NODE_ID',
        message: 'Node must have an id',
        path
      });
    }

    if (!node.name) {
      errors.push({
        code: 'MISSING_NODE_NAME',
        message: 'Node must have a name',
        path
      });
    }

    if (!node.type) {
      errors.push({
        code: 'MISSING_NODE_TYPE',
        message: 'Node must have a type',
        path
      });
    } else if (!['input', 'processing', 'output', 'control'].includes(node.type)) {
      errors.push({
        code: 'INVALID_NODE_TYPE',
        message: `Invalid node type: ${node.type}`,
        path
      });
    }

    // Validate inputs and outputs
    if (node.inputs && !Array.isArray(node.inputs)) {
      errors.push({
        code: 'INVALID_INPUTS',
        message: 'Node inputs must be an array',
        path: `${path}.inputs`
      });
    }

    if (node.outputs && !Array.isArray(node.outputs)) {
      errors.push({
        code: 'INVALID_OUTPUTS',
        message: 'Node outputs must be an array',
        path: `${path}.outputs`
      });
    }

    // Check for recommended fields
    if (!node.description) {
      warnings.push({
        code: 'MISSING_NODE_DESCRIPTION',
        message: `Node ${node.id} should have a description`,
        suggestion: 'Add description for better UX'
      });
    }

    if (!node.category) {
      warnings.push({
        code: 'MISSING_NODE_CATEGORY',
        message: `Node ${node.id} should have a category`,
        suggestion: 'Add category for better organization'
      });
    }
  }

  /**
   * Check if version follows semantic versioning
   */
  private static isValidVersion(version: string): boolean {
    const semverRegex = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;
    return semverRegex.test(version);
  }
}

/**
 * Plugin builder utility
 */
export class PluginBuilder {
  /**
   * Build a plugin package for distribution
   */
  static async buildPackage(pluginPath: string, options: {
    outputPath?: string;
    includeDev?: boolean;
    minify?: boolean;
  } = {}): Promise<{ success: boolean; packagePath?: string; errors: string[] }> {
    const errors: string[] = [];

    try {
      // Validate plugin first
      // Implementation would go here
      
      return {
        success: true,
        packagePath: options.outputPath || `${pluginPath}.pramaia-plugin`,
        errors
      };
    } catch (error) {
      errors.push(error instanceof Error ? error.message : String(error));
      return { success: false, errors };
    }
  }

  /**
   * Generate TypeScript declarations for a plugin
   */
  static generateDeclarations(manifest: PluginManifest): string {
    let declarations = `// Generated type declarations for ${manifest.name}\n\n`;

    manifest.nodes.forEach(node => {
      const inputTypes = node.inputs.map(input => 
        `${input.name}${input.required ? '' : '?'}: ${this.mapDataType(input.type)};`
      ).join('\n  ');

      const outputTypes = node.outputs.map(output =>
        `${output.name}: ${this.mapDataType(output.type)};`
      ).join('\n  ');

      declarations += `export interface ${this.pascalCase(node.id)}Input {\n  ${inputTypes}\n}\n\n`;
      declarations += `export interface ${this.pascalCase(node.id)}Output {\n  ${outputTypes}\n}\n\n`;
    });

    return declarations;
  }

  private static mapDataType(dataType: string): string {
    switch (dataType) {
      case 'text': return 'string';
      case 'file': return 'Buffer | string';
      case 'json': return 'any';
      case 'binary': return 'Buffer';
      case 'image': return 'Buffer';
      case 'pdf': return 'Buffer';
      case 'csv': return 'string';
      case 'xml': return 'string';
      default: return 'any';
    }
  }

  private static pascalCase(str: string): string {
    return str.split('_').map(part => 
      part.charAt(0).toUpperCase() + part.slice(1)
    ).join('');
  }
}

/**
 * Hot reload utility for development
 */
export class HotReloader {
  private watchers: Map<string, any> = new Map();
  private callbacks: Map<string, Function[]> = new Map();

  /**
   * Watch a plugin directory for changes
   */
  watchPlugin(pluginPath: string, callback: (event: string, filePath: string) => void): void {
    if (this.watchers.has(pluginPath)) {
      return; // Already watching
    }

    // Implementation would use chokidar or similar
    // For now, this is a placeholder
    
    if (!this.callbacks.has(pluginPath)) {
      this.callbacks.set(pluginPath, []);
    }
    this.callbacks.get(pluginPath)!.push(callback);
  }

  /**
   * Stop watching a plugin directory
   */
  stopWatching(pluginPath: string): void {
    const watcher = this.watchers.get(pluginPath);
    if (watcher) {
      // watcher.close();
      this.watchers.delete(pluginPath);
      this.callbacks.delete(pluginPath);
    }
  }

  /**
   * Stop all watchers
   */
  stopAll(): void {
    for (const [path] of this.watchers) {
      this.stopWatching(path);
    }
  }
}

/**
 * Configuration schema validator
 */
export class ConfigurationValidator {
  /**
   * Validate configuration against a JSON schema
   */
  static validateConfig(config: any, schema: any): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    try {
      // Basic validation implementation
      // In a full implementation, this would use ajv or similar
      
      if (schema.type === 'object' && schema.properties) {
        Object.entries(schema.properties).forEach(([key, propSchema]: [string, any]) => {
          if (schema.required && schema.required.includes(key) && !(key in config)) {
            errors.push({
              code: 'MISSING_REQUIRED_PROPERTY',
              message: `Missing required property: ${key}`,
              path: key
            });
          }
        });
      }

    } catch (error) {
      errors.push({
        code: 'SCHEMA_VALIDATION_ERROR',
        message: `Schema validation failed: ${error}`,
        details: error
      });
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }
}
