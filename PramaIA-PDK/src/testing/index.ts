/**
 * Testing utilities for plugin development
 */

import { WorkflowContext, NodeConfig } from '../core/interfaces.js';

/**
 * Mock workflow context for testing plugins in isolation
 */
export class MockWorkflowContext implements WorkflowContext {
  readonly executionId: string;
  readonly workflowId: string;
  readonly userId?: string;
  readonly groupId?: string;

  private inputs: Map<string, Map<string, any>> = new Map();
  private outputs: Map<string, Map<string, any>> = new Map();
  private state: Map<string, any> = new Map();
  private logs: Array<{ level: string; message: string; metadata?: any; timestamp: Date }> = [];
  private progressReports: Array<{ percentage: number; message?: string; timestamp: Date }> = [];
  private files: Map<string, Buffer | string> = new Map();

  constructor(options: {
    executionId?: string;
    workflowId?: string;
    userId?: string;
    groupId?: string;
  } = {}) {
    this.executionId = options.executionId || 'test-execution-' + Date.now();
    this.workflowId = options.workflowId || 'test-workflow';
    this.userId = options.userId;
    this.groupId = options.groupId;
  }

  // Input/Output management
  async getInput(nodeId: string, inputName?: string): Promise<any> {
    const nodeInputs = this.inputs.get(nodeId);
    if (!nodeInputs) {
      return undefined;
    }
    
    if (inputName) {
      return nodeInputs.get(inputName);
    }
    
    // If no specific input name, return all inputs for the node
    return Object.fromEntries(nodeInputs.entries());
  }

  async setOutput(nodeId: string, outputName: string, data: any): Promise<void> {
    if (!this.outputs.has(nodeId)) {
      this.outputs.set(nodeId, new Map());
    }
    this.outputs.get(nodeId)!.set(outputName, data);
  }

  // State management
  async getState(key: string): Promise<any> {
    return this.state.get(key);
  }

  async setState(key: string, value: any): Promise<void> {
    this.state.set(key, value);
  }

  // Logging and monitoring
  log(level: 'info' | 'warn' | 'error' | 'debug', message: string, metadata?: any): void {
    this.logs.push({
      level,
      message,
      metadata,
      timestamp: new Date()
    });
  }

  reportProgress(percentage: number, message?: string): void {
    this.progressReports.push({
      percentage,
      message,
      timestamp: new Date()
    });
  }

  // File system (sandboxed)
  async readFile(path: string): Promise<Buffer> {
    const file = this.files.get(path);
    if (!file) {
      throw new Error(`File not found: ${path}`);
    }
    return Buffer.isBuffer(file) ? file : Buffer.from(file, 'utf-8');
  }

  async writeFile(path: string, data: Buffer | string): Promise<void> {
    this.files.set(path, data);
  }

  // HTTP requests (mock implementation)
  async httpRequest(config: {
    url: string;
    method?: string;
    headers?: Record<string, string>;
    data?: any;
    timeout?: number;
  }): Promise<any> {
    // Mock HTTP response
    return {
      status: 200,
      headers: {},
      data: { message: 'Mock HTTP response', url: config.url }
    };
  }

  // Test helpers
  
  /**
   * Set input data for a specific node
   */
  async setInput(nodeId: string, inputName: string, data: any): Promise<void> {
    if (!this.inputs.has(nodeId)) {
      this.inputs.set(nodeId, new Map());
    }
    this.inputs.get(nodeId)!.set(inputName, data);
  }

  /**
   * Get output data from a specific node
   */
  async getOutput(nodeId: string, outputName?: string): Promise<any> {
    const nodeOutputs = this.outputs.get(nodeId);
    if (!nodeOutputs) {
      return undefined;
    }
    
    if (outputName) {
      return nodeOutputs.get(outputName);
    }
    
    return Object.fromEntries(nodeOutputs.entries());
  }

  /**
   * Get all logs
   */
  getLogs(): Array<{ level: string; message: string; metadata?: any; timestamp: Date }> {
    return [...this.logs];
  }

  /**
   * Get logs by level
   */
  getLogsByLevel(level: string): Array<{ level: string; message: string; metadata?: any; timestamp: Date }> {
    return this.logs.filter(log => log.level === level);
  }

  /**
   * Get all progress reports
   */
  getProgressReports(): Array<{ percentage: number; message?: string; timestamp: Date }> {
    return [...this.progressReports];
  }

  /**
   * Check if a file exists in the mock file system
   */
  hasFile(path: string): boolean {
    return this.files.has(path);
  }

  /**
   * List all files in the mock file system
   */
  listFiles(): string[] {
    return Array.from(this.files.keys());
  }

  /**
   * Clear all data (useful for test cleanup)
   */
  clear(): void {
    this.inputs.clear();
    this.outputs.clear();
    this.state.clear();
    this.logs.length = 0;
    this.progressReports.length = 0;
    this.files.clear();
  }

  /**
   * Create a snapshot of the current context state
   */
  snapshot(): any {
    return {
      executionId: this.executionId,
      workflowId: this.workflowId,
      inputs: Object.fromEntries(
        Array.from(this.inputs.entries()).map(([nodeId, nodeInputs]) => [
          nodeId,
          Object.fromEntries(nodeInputs.entries())
        ])
      ),
      outputs: Object.fromEntries(
        Array.from(this.outputs.entries()).map(([nodeId, nodeOutputs]) => [
          nodeId,
          Object.fromEntries(nodeOutputs.entries())
        ])
      ),
      state: Object.fromEntries(this.state.entries()),
      logs: this.getLogs(),
      progressReports: this.getProgressReports(),
      files: Object.fromEntries(
        Array.from(this.files.entries()).map(([path, data]) => [
          path,
          Buffer.isBuffer(data) ? data.toString('base64') : data
        ])
      )
    };
  }
}

/**
 * Test utilities for plugin testing
 */
export class PluginTestUtils {
  /**
   * Create a basic node config for testing - NON registra un nodo PDK reale
   */
  static createNodeConfig(overrides: Partial<NodeConfig> = {}): NodeConfig {
    return {
      id: overrides.id || 'test-plugin-node',  // Rimosso prefisso pdk_ per evitare registrazione
      name: overrides.name || 'Test Node',     // Nome generico senza prefisso PDK
      version: '1.0.0',
      enabled: true,
      // Nessun campo type, non è nel tipo NodeConfig
      ...overrides
    };
  }

  /**
   * Create a workflow context with pre-populated data
   */
  static createContextWithData(data: {
    inputs?: Record<string, Record<string, any>>;
    state?: Record<string, any>;
    files?: Record<string, string | Buffer>;
  } = {}): MockWorkflowContext {
    const context = new MockWorkflowContext();

    // Set inputs
    if (data.inputs) {
      Object.entries(data.inputs).forEach(([nodeId, nodeInputs]) => {
        Object.entries(nodeInputs).forEach(([inputName, inputData]) => {
          context.setInput(nodeId, inputName, inputData);
        });
      });
    }

    // Set state
    if (data.state) {
      Object.entries(data.state).forEach(([key, value]) => {
        context.setState(key, value);
      });
    }

    // Set files
    if (data.files) {
      Object.entries(data.files).forEach(([path, content]) => {
        context.writeFile(path, content);
      });
    }

    return context;
  }

  /**
   * Assert that a processor produces expected output
   */
  static async assertProcessorOutput(
    processor: any,
    nodeConfig: NodeConfig,
    context: MockWorkflowContext,
    expectedOutput: any
  ): Promise<void> {
    const result = await processor.execute(nodeConfig, context);
    
    if (JSON.stringify(result) !== JSON.stringify(expectedOutput)) {
      throw new Error(`Expected output ${JSON.stringify(expectedOutput)}, but got ${JSON.stringify(result)}`);
    }
  }

  /**
   * Assert that a processor logs a specific message
   */
  static assertLogMessage(
    context: MockWorkflowContext,
    level: string,
    messagePattern: string | RegExp
  ): void {
    const logs = context.getLogsByLevel(level);
    const found = logs.some(log => {
      if (typeof messagePattern === 'string') {
        return log.message.includes(messagePattern);
      }
      return messagePattern.test(log.message);
    });

    if (!found) {
      throw new Error(`Expected log message matching "${messagePattern}" not found in ${level} logs`);
    }
  }

  /**
   * Assert that progress was reported
   */
  static assertProgress(
    context: MockWorkflowContext,
    expectedPercentage?: number
  ): void {
    const reports = context.getProgressReports();
    
    if (reports.length === 0) {
      throw new Error('No progress reports found');
    }

    if (expectedPercentage !== undefined) {
      const found = reports.some(report => report.percentage === expectedPercentage);
      if (!found) {
        throw new Error(`Expected progress report with ${expectedPercentage}% not found`);
      }
    }
  }
}

/**
 * Plugin test runner for integration testing
 */
export class PluginTestRunner {
  private plugin: any;
  private context: MockWorkflowContext;

  constructor(plugin: any) {
    this.plugin = plugin;
    this.context = new MockWorkflowContext();
  }

  /**
   * Test all nodes in the plugin
   */
  async runAllTests(): Promise<Array<{ nodeId: string; success: boolean; error?: string }>> {
    const results: Array<{ nodeId: string; success: boolean; error?: string }> = [];

    for (const [nodeId, processor] of this.plugin.processors.entries()) {
      try {
        const nodeConfig = PluginTestUtils.createNodeConfig({ id: nodeId });
        await processor.execute(nodeConfig, this.context);
        
        results.push({ nodeId, success: true });
      } catch (error) {
        results.push({ 
          nodeId, 
          success: false, 
          error: error instanceof Error ? error.message : String(error)
        });
      }
    }

    return results;
  }

  /**
   * Test a specific node
   */
  async testNode(nodeId: string, nodeConfig?: Partial<NodeConfig>): Promise<any> {
    const processor = this.plugin.getProcessor(nodeId);
    if (!processor) {
      throw new Error(`Processor not found for node: ${nodeId}`);
    }

    const config = PluginTestUtils.createNodeConfig({ id: nodeId, ...nodeConfig });
    return await processor.execute(config, this.context);
  }

  /**
   * Get the test context
   */
  getContext(): MockWorkflowContext {
    return this.context;
  }

  /**
   * Reset the test context
   */
  resetContext(): void {
    this.context.clear();
  }
}
