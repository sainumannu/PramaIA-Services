import { BaseNodeProcessor, NodeConfig, WorkflowContext } from '@pramaia/plugin-development-kit';

export class {{processorClass}} extends BaseNodeProcessor {
  async execute(nodeConfig: NodeConfig, context: WorkflowContext): Promise<any> {
    this.log(context, 'info', 'Starting data processing');
    
    try {
      // Get input data
      const inputData = await this.getInput(context, nodeConfig.id, 'data');
      
      // Report progress
      this.reportProgress(context, 25, 'Processing input data');
      
      // TODO: Implement your processing logic here
      const result = await this.processData(inputData, nodeConfig.config);
      
      this.reportProgress(context, 100, 'Processing completed');
      this.log(context, 'info', 'Data processing completed successfully');
      
      return result;
      
    } catch (error) {
      this.log(context, 'error', `Processing failed: ${error}`);
      throw error;
    }
  }

  private async processData(data: any, config: any): Promise<any> {
    // Example processing logic
    // Replace this with your actual processing implementation
    
    if (typeof data === 'string') {
      // String processing example
      return {
        original: data,
        processed: data.toUpperCase(),
        length: data.length,
        timestamp: new Date().toISOString()
      };
    } else if (Array.isArray(data)) {
      // Array processing example
      return {
        original: data,
        processed: data.map(item => String(item).toUpperCase()),
        count: data.length,
        timestamp: new Date().toISOString()
      };
    } else if (typeof data === 'object' && data !== null) {
      // Object processing example
      return {
        original: data,
        processed: Object.fromEntries(
          Object.entries(data).map(([key, value]) => [
            key.toUpperCase(), 
            String(value).toUpperCase()
          ])
        ),
        keys: Object.keys(data),
        timestamp: new Date().toISOString()
      };
    } else {
      // Default processing
      return {
        original: data,
        processed: String(data).toUpperCase(),
        type: typeof data,
        timestamp: new Date().toISOString()
      };
    }
  }

  getConfigSchema(): Record<string, any> {
    return {
      type: 'object',
      properties: {
        format: {
          type: 'string',
          enum: ['uppercase', 'lowercase', 'capitalize'],
          default: 'uppercase',
          description: 'Text formatting option'
        },
        include_metadata: {
          type: 'boolean',
          default: true,
          description: 'Include processing metadata in result'
        },
        custom_prefix: {
          type: 'string',
          description: 'Optional prefix to add to processed text'
        }
      },
      required: []
    };
  }
}
