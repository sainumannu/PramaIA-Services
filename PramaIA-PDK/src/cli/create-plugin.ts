/**
 * Plugin creation utility
 */

import { promises as fs } from 'fs';
import path from 'path';
import inquirer from 'inquirer';
import chalk from 'chalk';
import { PLUGIN_TIMEOUT } from '../config/index.js';
import { PluginManifest, NodeType } from '../core/interfaces.js';

interface CreatePluginOptions {
  type: NodeType;
  dir: string;
  author?: string;
  description?: string;
}

export async function createPlugin(name: string, options: CreatePluginOptions): Promise<void> {
  const pluginDir = path.join(options.dir, name);
  
  // Check if directory already exists
  try {
    await fs.access(pluginDir);
    throw new Error(`Plugin directory '${pluginDir}' already exists`);
  } catch (error: any) {
    if (error.code !== 'ENOENT') {
      throw error;
    }
  }

  // Gather additional information if not provided
  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'author',
      message: 'Plugin author:',
      default: options.author || 'Anonymous',
      when: () => !options.author
    },
    {
      type: 'input',
      name: 'description',
      message: 'Plugin description:',
      default: options.description || `A ${options.type} plugin for PramaIA workflows`,
      when: () => !options.description
    },
    {
      type: 'list',
      name: 'category',
      message: 'Plugin category:',
      choices: getCategoriesForType(options.type),
      default: 0
    },
    {
      type: 'input',
      name: 'nodeId',
      message: 'Node ID (unique identifier):',
      default: `${name.toLowerCase().replace(/[^a-z0-9]/g, '_')}_node`,
      validate: (input: string) => {
        if (!/^[a-z][a-z0-9_]*$/.test(input)) {
          return 'Node ID must start with a letter and contain only lowercase letters, numbers, and underscores';
        }
        return true;
      }
    }
  ]);

  const author = options.author || answers.author;
  const description = options.description || answers.description;

  // Create plugin manifest
  const manifest: PluginManifest = {
    name,
    version: '1.0.0',
    description,
    author,
    license: 'MIT',
    pdk_version: '^1.0.0',
    engine_compatibility: '^1.0.0',
    nodes: [
      {
        id: answers.nodeId,
        name: name,
        type: options.type,
        category: answers.category,
        description,
        inputs: getDefaultInputs(options.type),
        outputs: getDefaultOutputs(options.type),
        async: true,
        timeout: PLUGIN_TIMEOUT,
        retry_count: 0
      }
    ]
  };

  // Create directory structure
  await fs.mkdir(pluginDir, { recursive: true });
  await fs.mkdir(path.join(pluginDir, 'src'), { recursive: true });
  await fs.mkdir(path.join(pluginDir, 'tests'), { recursive: true });

  // Write files
  await Promise.all([
    // Plugin manifest
    fs.writeFile(
      path.join(pluginDir, 'plugin.json'),
      JSON.stringify(manifest, null, 2)
    ),
    
    // Package.json
    fs.writeFile(
      path.join(pluginDir, 'package.json'),
      JSON.stringify(generatePackageJson(name, description, author), null, 2)
    ),
    
    // TypeScript config
    fs.writeFile(
      path.join(pluginDir, 'tsconfig.json'),
      JSON.stringify(generateTsConfig(), null, 2)
    ),
    
    // Main processor file
    fs.writeFile(
      path.join(pluginDir, 'src', 'processor.ts'),
      generateProcessorCode(answers.nodeId, options.type, manifest.nodes[0])
    ),
    
    // Plugin entry point
    fs.writeFile(
      path.join(pluginDir, 'src', 'index.ts'),
      generateIndexCode(name, answers.nodeId)
    ),
    
    // Test file
    fs.writeFile(
      path.join(pluginDir, 'tests', 'processor.test.ts'),
      generateTestCode(answers.nodeId, options.type)
    ),
    
    // README
    fs.writeFile(
      path.join(pluginDir, 'README.md'),
      generateReadme(name, description, manifest.nodes[0])
    ),
    
    // .gitignore
    fs.writeFile(
      path.join(pluginDir, '.gitignore'),
      generateGitignore()
    )
  ]);

  console.log(chalk.green(`\n📁 Plugin created at: ${pluginDir}`));
  console.log(chalk.blue('\n📝 Next steps:'));
  console.log(chalk.white(`  1. cd ${path.relative(process.cwd(), pluginDir)}`));
  console.log(chalk.white('  2. npm install'));
  console.log(chalk.white('  3. npm run build'));
  console.log(chalk.white('  4. pramaia-pdk dev .'));
}

function getCategoriesForType(type: NodeType): string[] {
  switch (type) {
    case 'input':
      return ['File Systems', 'APIs', 'Databases', 'User Input', 'Sensors'];
    case 'processing':
      return ['AI/ML', 'Data Transform', 'Text Processing', 'Image Processing', 'Analysis'];
    case 'output':
      return ['File Systems', 'APIs', 'Databases', 'Notifications', 'Reports'];
    case 'control':
      return ['Conditionals', 'Loops', 'Branching', 'Synchronization', 'Error Handling'];
    default:
      return ['General'];
  }
}

function getDefaultInputs(type: NodeType) {
  switch (type) {
    case 'input':
      return [];
    case 'processing':
      return [
        { name: 'data', type: 'any', required: true, description: 'Input data to process' }
      ];
    case 'output':
      return [
        { name: 'data', type: 'any', required: true, description: 'Data to output' }
      ];
    case 'control':
      return [
        { name: 'condition', type: 'any', required: true, description: 'Condition to evaluate' }
      ];
    default:
      return [];
  }
}

function getDefaultOutputs(type: NodeType) {
  switch (type) {
    case 'input':
      return [
        { name: 'data', type: 'any', description: 'Generated or retrieved data' }
      ];
    case 'processing':
      return [
        { name: 'result', type: 'any', description: 'Processed data result' }
      ];
    case 'output':
      return [
        { name: 'success', type: 'boolean', description: 'Whether output was successful' }
      ];
    case 'control':
      return [
        { name: 'result', type: 'boolean', description: 'Result of condition evaluation' }
      ];
    default:
      return [];
  }
}

function generatePackageJson(name: string, description: string, author: string) {
  return {
    name: `@pramaia/plugin-${name.toLowerCase()}`,
    version: '1.0.0',
    description,
    author,
    license: 'MIT',
    type: 'module',
    main: 'dist/index.js',
    types: 'dist/index.d.ts',
    scripts: {
      build: 'tsc',
      dev: 'tsc --watch',
      test: 'vitest',
      'test:ui': 'vitest --ui'
    },
    devDependencies: {
      '@types/node': '^22.0.0',
      'typescript': '~5.8.3',
      'vitest': '^2.0.0'
    },
    dependencies: {
      '@pramaia/plugin-development-kit': '^1.0.0'
    }
  };
}

function generateTsConfig() {
  return {
    extends: '../../../tsconfig.json',
    compilerOptions: {
      outDir: './dist',
      rootDir: './src'
    },
    include: ['src/**/*'],
    exclude: ['node_modules', 'dist', 'tests']
  };
}

function generateProcessorCode(nodeId: string, type: NodeType, nodeConfig: any): string {
  const className = `${nodeId.split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')}Processor`;
  
  return `import { BaseNodeProcessor, NodeConfig, WorkflowContext } from '@pramaia/plugin-development-kit';

export class ${className} extends BaseNodeProcessor {
  async execute(nodeConfig: NodeConfig, context: WorkflowContext): Promise<any> {
    this.log(context, 'info', 'Starting ${nodeId} execution');
    
    try {
      // Get input data
      ${type === 'input' ? '// This is an input node - generate or retrieve data' : 
        'const inputData = await this.getInput(context, nodeConfig.id, \'data\');'}
      
      // TODO: Implement your ${type} logic here
      ${generateTypeSpecificLogic(type)}
      
      this.log(context, 'info', '${nodeId} execution completed successfully');
      return result;
      
    } catch (error) {
      this.log(context, 'error', \`${nodeId} execution failed: \${error}\`);
      throw error;
    }
  }

  getConfigSchema(): Record<string, any> {
    return {
      type: 'object',
      properties: {
        // TODO: Define your configuration schema here
        ${generateConfigSchema(type)}
      },
      required: []
    };
  }
}`;
}

function generateTypeSpecificLogic(type: NodeType): string {
  switch (type) {
    case 'input':
      return `      // Example: Generate or retrieve data
      const result = {
        data: 'Hello from ${type} node!',
        timestamp: new Date().toISOString()
      };`;
    case 'processing':
      return `      // Example: Process the input data
      const result = {
        processed: inputData,
        timestamp: new Date().toISOString()
      };`;
    case 'output':
      return `      // Example: Output the data (save to file, send to API, etc.)
      console.log('Outputting data:', inputData);
      const result = { success: true };`;
    case 'control':
      return `      // Example: Evaluate condition
      const condition = inputData;
      const result = Boolean(condition);`;
    default:
      return `      const result = inputData;`;
  }
}

function generateConfigSchema(type: NodeType): string {
  switch (type) {
    case 'input':
      return `        source: {
          type: 'string',
          description: 'Data source configuration'
        }`;
    case 'processing':
      return `        algorithm: {
          type: 'string',
          description: 'Processing algorithm to use'
        }`;
    case 'output':
      return `        destination: {
          type: 'string', 
          description: 'Output destination configuration'
        }`;
    case 'control':
      return `        condition_type: {
          type: 'string',
          description: 'Type of condition to evaluate'
        }`;
    default:
      return `        // Add your configuration properties here`;
  }
}

function generateIndexCode(name: string, nodeId: string): string {
  const className = `${nodeId.split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')}Processor`;
  
  return `import { BaseNodePlugin } from '@pramaia/plugin-development-kit';
import { ${className} } from './processor.js';

export class ${name}Plugin extends BaseNodePlugin {
  constructor() {
    super();
    
    // Register processor
    this.processors.set('${nodeId}', new ${className}());
  }
}

// Export for plugin loading
export default ${name}Plugin;`;
}

function generateTestCode(nodeId: string, type: NodeType): string {
  const className = `${nodeId.split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')}Processor`;
  
  return `import { describe, it, expect } from 'vitest';
import { MockWorkflowContext } from '@pramaia/plugin-development-kit/testing';
import { ${className} } from '../src/processor.js';

describe('${className}', () => {
  const processor = new ${className}();
  
  it('should execute successfully', async () => {
    const context = new MockWorkflowContext();
    const nodeConfig = {
      id: '${nodeId}',
      name: 'Test ${nodeId}',
      version: '1.0.0',
      enabled: true
    };
    
    ${type === 'input' ? '// Input node test' : 
      'await context.setInput(nodeConfig.id, \'data\', \'test input\');'}
    
    const result = await processor.execute(nodeConfig, context);
    
    expect(result).toBeDefined();
    ${generateTypeSpecificTest(type)}
  });
  
  it('should validate config schema', async () => {
    const schema = processor.getConfigSchema();
    expect(schema).toBeDefined();
    expect(schema.type).toBe('object');
  });
});`;
}

function generateTypeSpecificTest(type: NodeType): string {
  switch (type) {
    case 'input':
      return `expect(result.data).toBeDefined();`;
    case 'processing':
      return `expect(result.processed).toBeDefined();`;
    case 'output':
      return `expect(result.success).toBe(true);`;
    case 'control':
      return `expect(typeof result).toBe('boolean');`;
    default:
      return `// Add specific assertions for your node type`;
  }
}

function generateReadme(name: string, description: string, nodeConfig: any): string {
  return `# ${name} Plugin

${description}

## Installation

\`\`\`bash
npm install @pramaia/plugin-${name.toLowerCase()}
\`\`\`

## Usage

This plugin provides a **${nodeConfig.type}** node for PramaIA workflows.

### Node: ${nodeConfig.name}

- **Type**: ${nodeConfig.type}
- **Category**: ${nodeConfig.category}
- **ID**: ${nodeConfig.id}

#### Inputs

${nodeConfig.inputs.map((input: any) => `- **${input.name}** (${input.type}${input.required ? ', required' : ''}): ${input.description || 'No description'}`).join('\n')}

#### Outputs

${nodeConfig.outputs.map((output: any) => `- **${output.name}** (${output.type}): ${output.description || 'No description'}`).join('\n')}

#### Configuration

TODO: Add configuration documentation

## Development

\`\`\`bash
# Install dependencies
npm install

# Build
npm run build

# Test
npm test

# Development server
pramaia-pdk dev .
\`\`\`

## License

MIT
`;
}

function generateGitignore(): string {
  return `node_modules/
dist/
*.log
.env
.env.local
.DS_Store
Thumbs.db
`;
}
