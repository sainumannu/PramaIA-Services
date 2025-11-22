/**
 * Integration utilities for PramaIA Workflow Engine
 */

import { BACKEND_BASE_URL } from '../config/index.js';

/**
 * Workflow engine client for plugin registration and communication
 */
export class WorkflowEngineClient {
  private baseUrl: string;
  private apiKey?: string;

  constructor(baseUrl: string = BACKEND_BASE_URL, apiKey?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = apiKey;
  }

  /**
   * Register a plugin with the workflow engine
   */
  async registerPlugin(pluginInfo: {
    name: string;
    version: string;
    url: string;
    nodes: Array<{
      id: string;
      name: string;
      type: string;
      category: string;
      description: string;
    }>;
  }): Promise<{ success: boolean; message?: string }> {
    try {
      const response = await this.makeRequest('/api/plugins/register', 'POST', pluginInfo);
      return { success: true, message: 'Plugin registered successfully' };
    } catch (error) {
      return { 
        success: false, 
        message: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Unregister a plugin from the workflow engine
   */
  async unregisterPlugin(pluginName: string): Promise<{ success: boolean; message?: string }> {
    try {
      await this.makeRequest(`/api/plugins/${encodeURIComponent(pluginName)}`, 'DELETE');
      return { success: true, message: 'Plugin unregistered successfully' };
    } catch (error) {
      return { 
        success: false, 
        message: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Get list of registered plugins
   */
  async getPlugins(): Promise<any[]> {
    try {
      const response = await this.makeRequest('/api/plugins', 'GET');
      return response.plugins || [];
    } catch (error) {
      console.warn('Failed to get plugins list:', error);
      return [];
    }
  }

  /**
   * Health check for the workflow engine
   */
  async healthCheck(): Promise<{ healthy: boolean; version?: string }> {
    try {
      const response = await this.makeRequest('/api/health', 'GET');
      return { healthy: true, version: response.version };
    } catch (error) {
      return { healthy: false };
    }
  }

  /**
   * Make HTTP request to workflow engine
   */
  private async makeRequest(endpoint: string, method: string, data?: any): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const config: RequestInit = {
      method,
      headers
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      config.body = JSON.stringify(data);
    }

    const response = await fetch(url, config);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }

    return await response.text();
  }
}

/**
 * External plugin processor for the Python workflow engine
 * This creates a processor that can be used in the Python engine to call PDK plugins
 */
export class ExternalPluginProcessorPython {
  /**
   * Generate Python code for an external plugin processor
   */
  static generateProcessorCode(pluginUrl: string, nodeId: string): string {
    return `
import asyncio
import aiohttp
import logging
from typing import Dict, Any
from backend.engine.node_registry import BaseNodeProcessor
from backend.engine.execution_context import ExecutionContext

logger = logging.getLogger(__name__)

class ExternalPluginProcessor_${nodeId.replace(/[^a-zA-Z0-9]/g, '_')}(BaseNodeProcessor):
    """
    External plugin processor for ${nodeId}
    Communicates with PDK plugin at ${pluginUrl}
    """
    
    def __init__(self):
        self.plugin_url = "${pluginUrl}"
        self.node_id = "${nodeId}"
        
    async def execute(self, node, context: ExecutionContext) -> Any:
        """Execute the external plugin via HTTP"""
        logger.info(f"🔌 Executing external plugin: {self.node_id}")
        
        try:
            # Prepare request data
            request_data = {
                "nodeId": self.node_id,
                "nodeConfig": {
                    "id": node.node_id,
                    "name": node.name,
                    "version": "1.0.0",
                    "enabled": True,
                    "config": node.config or {}
                },
                "context": await self._prepare_context(context, node.node_id)
            }
            
            # Make HTTP request to plugin
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.plugin_url}/execute",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Plugin execution failed: {error_text}")
                    
                    result = await response.json()
                    
                    if not result.get('success'):
                        raise Exception(f"Plugin returned error: {result.get('error')}")
                    
                    logger.info(f"✅ External plugin {self.node_id} executed successfully")
                    return result.get('result')
                    
        except Exception as error:
            logger.error(f"❌ External plugin {self.node_id} execution failed: {error}")
            raise error
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration via plugin"""
        try:
            # For now, assume valid. Could make HTTP call to plugin's validate endpoint
            return True
        except Exception:
            return False
    
    async def _prepare_context(self, context: ExecutionContext, node_id: str) -> Dict[str, Any]:
        """Prepare context data for the plugin"""
        return {
            "executionId": context.execution_id,
            "workflowId": getattr(context.workflow, 'id', 'unknown'),
            "nodeId": node_id,
            "inputData": context.get_input_for_node(node_id),
            "sharedData": context.shared_data
        }
`;
  }

  /**
   * Generate registration code for the Python workflow engine
   */
  static generateRegistrationCode(manifest: any, pluginUrl: string): string {
    const processors = manifest.nodes.map((node: any) => {
      const className = `ExternalPluginProcessor_${node.id.replace(/[^a-zA-Z0-9]/g, '_')}`;
      return `        self.register_processor("${node.id}", ${className}())`;
    }).join('\n');

    return `
# Auto-generated registration code for ${manifest.name}
# Add this to your NodeRegistry._register_default_processors method

${manifest.nodes.map((node: any) => 
  this.generateProcessorCode(pluginUrl, node.id)
).join('\n')}

# In NodeRegistry._register_default_processors method, add:
${processors}
`;
  }
}

/**
 * Plugin development server integration
 */
export class PluginDevServer {
  private client: WorkflowEngineClient;
  private pluginInfo: any;
  private registered = false;

  constructor(engineUrl: string, pluginInfo: any) {
    this.client = new WorkflowEngineClient(engineUrl);
    this.pluginInfo = pluginInfo;
  }

  /**
   * Register this plugin with the workflow engine
   */
  async register(pluginServerUrl: string): Promise<boolean> {
    if (this.registered) {
      return true;
    }

    const registrationInfo = {
      name: this.pluginInfo.name,
      version: this.pluginInfo.version,
      url: pluginServerUrl,
      nodes: this.pluginInfo.nodes.map((node: any) => ({
        id: node.id,
        name: node.name,
        type: node.type,
        category: node.category,
        description: node.description
      }))
    };

    const result = await this.client.registerPlugin(registrationInfo);
    this.registered = result.success;
    
    if (!result.success) {
      console.warn('Plugin registration failed:', result.message);
    }

    return this.registered;
  }

  /**
   * Unregister this plugin from the workflow engine
   */
  async unregister(): Promise<void> {
    if (!this.registered) {
      return;
    }

    await this.client.unregisterPlugin(this.pluginInfo.name);
    this.registered = false;
  }

  /**
   * Check if workflow engine is available
   */
  async isEngineAvailable(): Promise<boolean> {
    const health = await this.client.healthCheck();
    return health.healthy;
  }
}
