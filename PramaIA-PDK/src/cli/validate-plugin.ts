/**
 * Plugin validation utility
 */

import { promises as fs } from 'fs';
import path from 'path';
import { ValidationResult, ValidationError, ValidationWarning, PluginManifestSchema } from '../core/interfaces.js';

interface ValidateOptions {
  strict?: boolean;
}

export async function validatePlugin(pluginPath: string, options: ValidateOptions = {}): Promise<ValidationResult> {
  const errors: ValidationError[] = [];
  const warnings: ValidationWarning[] = [];

  try {
    // Check if directory exists
    const stats = await fs.stat(pluginPath);
    if (!stats.isDirectory()) {
      errors.push({
        code: 'INVALID_PATH',
        message: 'Plugin path must be a directory'
      });
      return { valid: false, errors, warnings };
    }

    // Validate plugin manifest
    await validateManifest(pluginPath, errors, warnings, options);
    
    // Validate package.json
    await validatePackageJson(pluginPath, errors, warnings, options);
    
    // Validate source files
    await validateSourceFiles(pluginPath, errors, warnings, options);
    
    // Validate dependencies
    await validateDependencies(pluginPath, errors, warnings, options);

  } catch (error: any) {
    errors.push({
      code: 'VALIDATION_ERROR',
      message: `Validation failed: ${error.message}`,
      details: error
    });
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}

async function validateManifest(
  pluginPath: string, 
  errors: ValidationError[], 
  warnings: ValidationWarning[],
  options: ValidateOptions
): Promise<void> {
  const manifestPath = path.join(pluginPath, 'plugin.json');
  
  try {
    const manifestContent = await fs.readFile(manifestPath, 'utf-8');
    const manifest = JSON.parse(manifestContent);
    
    // Validate against schema
    const result = PluginManifestSchema.safeParse(manifest);
    
    if (!result.success) {
      result.error.errors.forEach((error: any) => {
        errors.push({
          code: 'MANIFEST_VALIDATION_ERROR',
          message: `Manifest validation error: ${error.message}`,
          path: error.path?.join('.'),
          details: error
        });
      });
    } else {
      // Additional validation checks
      const validatedManifest = result.data;
      
      // Check for duplicate node IDs
      const nodeIds = new Set();
      validatedManifest.nodes.forEach((node: any) => {
        if (nodeIds.has(node.id)) {
          errors.push({
            code: 'DUPLICATE_NODE_ID',
            message: `Duplicate node ID: ${node.id}`,
            path: `nodes.${node.id}`
          });
        }
        nodeIds.add(node.id);
      });
      
      // Check for valid node types
      validatedManifest.nodes.forEach((node: any) => {
        if (!['input', 'processing', 'output', 'control'].includes(node.type)) {
          errors.push({
            code: 'INVALID_NODE_TYPE',
            message: `Invalid node type: ${node.type}`,
            path: `nodes.${node.id}.type`
          });
        }
      });
      
      // Warnings for best practices
      if (!validatedManifest.homepage && options.strict) {
        warnings.push({
          code: 'MISSING_HOMEPAGE',
          message: 'Consider adding a homepage URL',
          suggestion: 'Add homepage field to manifest'
        });
      }
      
      if (!validatedManifest.repository && options.strict) {
        warnings.push({
          code: 'MISSING_REPOSITORY',
          message: 'Consider adding a repository URL',
          suggestion: 'Add repository field to manifest'
        });
      }
    }
    
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      errors.push({
        code: 'MISSING_MANIFEST',
        message: 'plugin.json file not found'
      });
    } else if (error instanceof SyntaxError) {
      errors.push({
        code: 'INVALID_JSON',
        message: 'plugin.json contains invalid JSON',
        details: error.message
      });
    } else {
      errors.push({
        code: 'MANIFEST_READ_ERROR',
        message: `Failed to read plugin.json: ${error.message}`
      });
    }
  }
}

async function validatePackageJson(
  pluginPath: string, 
  errors: ValidationError[], 
  warnings: ValidationWarning[],
  options: ValidateOptions
): Promise<void> {
  const packagePath = path.join(pluginPath, 'package.json');
  
  try {
    const packageContent = await fs.readFile(packagePath, 'utf-8');
    const packageJson = JSON.parse(packageContent);
    
    // Check required fields
    const requiredFields = ['name', 'version', 'description'];
    requiredFields.forEach(field => {
      if (!packageJson[field]) {
        errors.push({
          code: 'MISSING_PACKAGE_FIELD',
          message: `Missing required field in package.json: ${field}`,
          path: field
        });
      }
    });
    
    // Check for PDK dependency
    if (!packageJson.dependencies?.['@pramaia/plugin-development-kit'] && 
        !packageJson.peerDependencies?.['@pramaia/plugin-development-kit']) {
      errors.push({
        code: 'MISSING_PDK_DEPENDENCY',
        message: 'Missing @pramaia/plugin-development-kit dependency'
      });
    }
    
    // Check scripts
    const recommendedScripts = ['build', 'test'];
    recommendedScripts.forEach(script => {
      if (!packageJson.scripts?.[script]) {
        warnings.push({
          code: 'MISSING_SCRIPT',
          message: `Consider adding ${script} script to package.json`,
          suggestion: `Add "${script}" script for better development experience`
        });
      }
    });
    
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      errors.push({
        code: 'MISSING_PACKAGE_JSON',
        message: 'package.json file not found'
      });
    } else if (error instanceof SyntaxError) {
      errors.push({
        code: 'INVALID_PACKAGE_JSON',
        message: 'package.json contains invalid JSON',
        details: error.message
      });
    }
  }
}

async function validateSourceFiles(
  pluginPath: string, 
  errors: ValidationError[], 
  warnings: ValidationWarning[],
  options: ValidateOptions
): Promise<void> {
  const srcPath = path.join(pluginPath, 'src');
  
  try {
    const stats = await fs.stat(srcPath);
    if (!stats.isDirectory()) {
      errors.push({
        code: 'MISSING_SRC_DIRECTORY',
        message: 'src directory not found'
      });
      return;
    }
    
    // Check for main entry point
    const possibleEntryPoints = ['index.ts', 'index.js', 'main.ts', 'main.js'];
    let hasEntryPoint = false;
    
    for (const entry of possibleEntryPoints) {
      try {
        await fs.access(path.join(srcPath, entry));
        hasEntryPoint = true;
        break;
      } catch {
        // File doesn't exist, continue
      }
    }
    
    if (!hasEntryPoint) {
      errors.push({
        code: 'MISSING_ENTRY_POINT',
        message: 'No entry point found in src directory'
      });
    }
    
    // Check for processor files
    const files = await fs.readdir(srcPath);
    const hasProcessor = files.some(file => 
      file.includes('processor') && (file.endsWith('.ts') || file.endsWith('.js'))
    );
    
    if (!hasProcessor) {
      warnings.push({
        code: 'NO_PROCESSOR_FILES',
        message: 'No processor files found',
        suggestion: 'Consider organizing your code with processor.ts files'
      });
    }
    
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      errors.push({
        code: 'MISSING_SRC_DIRECTORY',
        message: 'src directory not found'
      });
    }
  }
}

async function validateDependencies(
  pluginPath: string, 
  errors: ValidationError[], 
  warnings: ValidationWarning[],
  options: ValidateOptions
): Promise<void> {
  const nodeModulesPath = path.join(pluginPath, 'node_modules');
  
  try {
    await fs.access(nodeModulesPath);
  } catch {
    warnings.push({
      code: 'NO_NODE_MODULES',
      message: 'node_modules directory not found',
      suggestion: 'Run npm install to install dependencies'
    });
    return;
  }
  
  // Check if PDK is actually installed
  const pdkPath = path.join(nodeModulesPath, '@pramaia', 'plugin-development-kit');
  try {
    await fs.access(pdkPath);
  } catch {
    warnings.push({
      code: 'PDK_NOT_INSTALLED',
      message: '@pramaia/plugin-development-kit not found in node_modules',
      suggestion: 'Run npm install to install the PDK'
    });
  }
}
