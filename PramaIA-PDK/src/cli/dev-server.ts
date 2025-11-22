/**
 * Development server for plugin testing
 */

import { promises as fs } from 'fs';
import path from 'path';
import http from 'http';
import { URL } from 'url';
import chalk from 'chalk';
import chokidar from 'chokidar';

interface DevServerOptions {
  port: string | number;
  engineUrl: string;
  watch: boolean;
}

interface PluginServer {
  manifest: any;
  plugin: any;
  server: http.Server;
}

export async function devServer(pluginPath: string, options: DevServerOptions): Promise<void> {
  const port = parseInt(options.port.toString());
  
  console.log(chalk.blue(`🔧 Starting development server for plugin at: ${pluginPath}`));
  
  // Load plugin
  let pluginServer = await loadPlugin(pluginPath, port);
  
  // Setup hot reload if watching
  if (options.watch) {
    console.log(chalk.blue('👀 Watching for changes...'));
    
    const watcher = chokidar.watch([
      path.join(pluginPath, 'src/**/*'),
      path.join(pluginPath, 'plugin.json'),
      path.join(pluginPath, 'package.json')
    ], {
      ignored: /node_modules/,
      persistent: true
    });
    
    watcher.on('change', async (filePath) => {
      console.log(chalk.yellow(`📝 File changed: ${path.relative(pluginPath, filePath)}`));
      
      try {
        // Rebuild if source files changed
        if (filePath.includes('src')) {
          console.log(chalk.blue('🔨 Rebuilding plugin...'));
          await rebuildPlugin(pluginPath);
        }
        
        // Reload plugin
        console.log(chalk.blue('🔄 Reloading plugin...'));
        pluginServer.server.close();
        pluginServer = await loadPlugin(pluginPath, port);
        
        console.log(chalk.green('✅ Plugin reloaded successfully!'));
      } catch (error) {
        console.error(chalk.red('❌ Failed to reload plugin:'), error);
      }
    });
    
    // Graceful shutdown
    process.on('SIGINT', () => {
      console.log(chalk.blue('\n🛑 Shutting down development server...'));
      watcher.close();
      pluginServer.server.close();
      process.exit(0);
    });
  }
  
  // Try to register with workflow engine
  try {
    await registerWithEngine(pluginServer.manifest, `http://localhost:${port}`, options.engineUrl);
    console.log(chalk.green(`✅ Plugin registered with workflow engine at ${options.engineUrl}`));
  } catch (error) {
    console.warn(chalk.yellow(`⚠️  Could not register with workflow engine: ${error}`));
    console.log(chalk.gray('   The plugin server is still running and can be used standalone.'));
  }
  
  console.log(chalk.green(`🚀 Plugin server running at http://localhost:${port}`));
  console.log(chalk.gray('   Press Ctrl+C to stop'));
}

async function loadPlugin(pluginPath: string, port: number): Promise<PluginServer> {
  // Read plugin manifest
  const manifestPath = path.join(pluginPath, 'plugin.json');
  const manifestContent = await fs.readFile(manifestPath, 'utf-8');
  const manifest = JSON.parse(manifestContent);
  
  // Load built plugin
  const distPath = path.join(pluginPath, 'dist');
  let plugin;
  
  try {
    // Try to import the built plugin
    const indexPath = path.join(distPath, 'index.js');
    await fs.access(indexPath);
    
    // Dynamic import with timestamp to avoid caching
    const timestamp = Date.now();
    const moduleUrl = `file://${indexPath}?t=${timestamp}`;
    const module = await import(moduleUrl);
    
    plugin = module.default ? new module.default() : new module();
  } catch (error) {
    throw new Error(`Failed to load plugin. Make sure to build it first with: npm run build\nError: ${error}`);
  }
  
  // Create HTTP server
  const server = http.createServer(async (req, res) => {
    await handleRequest(req, res, plugin, manifest);
  });
  
  // Start server
  await new Promise<void>((resolve, reject) => {
    server.listen(port, (error?: Error) => {
      if (error) reject(error);
      else resolve();
    });
  });
  
  return { manifest, plugin, server };
}

async function handleRequest(
  req: http.IncomingMessage, 
  res: http.ServerResponse, 
  plugin: any, 
  manifest: any
): Promise<void> {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  const url = new URL(req.url || '/', `http://${req.headers.host}`);
  
  try {
    switch (url.pathname) {
      case '/':
        await handleHealthCheck(res, manifest);
        break;
        
      case '/manifest':
        await handleManifest(res, manifest);
        break;
        
      case '/execute':
        await handleExecution(req, res, plugin);
        break;
        
      case '/validate':
        await handleValidation(req, res, plugin);
        break;
        
      default:
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Not found' }));
    }
  } catch (error) {
    console.error('Request handling error:', error);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
      error: 'Internal server error', 
      details: error instanceof Error ? error.message : String(error)
    }));
  }
}

async function handleHealthCheck(res: http.ServerResponse, manifest: any): Promise<void> {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({
    status: 'healthy',
    plugin: manifest.name,
    version: manifest.version,
    nodes: manifest.nodes.map((node: any) => node.id)
  }));
}

async function handleManifest(res: http.ServerResponse, manifest: any): Promise<void> {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(manifest));
}

async function handleExecution(
  req: http.IncomingMessage, 
  res: http.ServerResponse, 
  plugin: any
): Promise<void> {
  if (req.method !== 'POST') {
    res.writeHead(405, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Method not allowed' }));
    return;
  }
  
  // Read request body
  const body = await readRequestBody(req);
  const requestData = JSON.parse(body);
  
  const { nodeId, nodeConfig, context } = requestData;
  
  if (!nodeId || !nodeConfig || !context) {
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
      error: 'Missing required fields: nodeId, nodeConfig, context' 
    }));
    return;
  }
  
  // Get processor for node
  const processor = plugin.getProcessor(nodeId);
  if (!processor) {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: `Processor not found for node: ${nodeId}` }));
    return;
  }
  
  try {
    // Execute the processor
    const result = await processor.execute(nodeConfig, context);
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ success: true, result }));
  } catch (error) {
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
      success: false, 
      error: error instanceof Error ? error.message : String(error)
    }));
  }
}

async function handleValidation(
  req: http.IncomingMessage, 
  res: http.ServerResponse, 
  plugin: any
): Promise<void> {
  if (req.method !== 'POST') {
    res.writeHead(405, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Method not allowed' }));
    return;
  }
  
  const body = await readRequestBody(req);
  const requestData = JSON.parse(body);
  
  const { nodeId, config } = requestData;
  
  if (!nodeId || !config) {
    res.writeHead(400, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Missing required fields: nodeId, config' }));
    return;
  }
  
  const processor = plugin.getProcessor(nodeId);
  if (!processor) {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: `Processor not found for node: ${nodeId}` }));
    return;
  }
  
  try {
    const result = await processor.validateConfig(config);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(result));
  } catch (error) {
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
      valid: false, 
      error: error instanceof Error ? error.message : String(error)
    }));
  }
}

async function readRequestBody(req: http.IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      resolve(body);
    });
    req.on('error', reject);
  });
}

async function rebuildPlugin(pluginPath: string): Promise<void> {
  const { exec } = await import('child_process');
  const { promisify } = await import('util');
  const execAsync = promisify(exec);
  
  try {
    await execAsync('npm run build', { cwd: pluginPath });
  } catch (error) {
    throw new Error(`Build failed: ${error}`);
  }
}

async function registerWithEngine(manifest: any, pluginUrl: string, engineUrl: string): Promise<void> {
  try {
    const registrationData = {
      name: manifest.name,
      version: manifest.version,
      url: pluginUrl,
      nodes: manifest.nodes.map((node: any) => ({
        id: node.id,
        name: node.name,
        type: node.type,
        category: node.category,
        description: node.description
      }))
    };

    const response = await fetch(`${engineUrl}/api/plugins/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(registrationData)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Registration failed: ${response.status} ${errorText}`);
    }

    const result = await response.json();
    console.log(`✅ Plugin registered: ${result.nodes_registered} nodes registered`);
  } catch (error: any) {
    // If it's a fetch error, it might be that node-fetch is not available
    // Let's use a more compatible approach
    throw new Error(`Registration failed: ${error.message}`);
  }
}
