// index.js
import { BaseNodePlugin, createPluginFactory } from '@pramaia/plugin-development-kit';
import { WorkflowSchedulerProcessor } from './workflow_scheduler_processor.js';
import manifest from '../plugin.json';

/**
 * Classe principale del plugin Workflow Scheduler
 */
class WorkflowSchedulerPlugin extends BaseNodePlugin {
  manifest = manifest;
  
  /**
   * Registra i processori dei nodi
   */
  async registerProcessors() {
    this.registerProcessor('workflow_scheduler', new WorkflowSchedulerProcessor());
  }
}

/**
 * Factory per la creazione del plugin
 */
export default createPluginFactory(WorkflowSchedulerPlugin);
