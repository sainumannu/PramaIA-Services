# Plugins Documentation

**PramaIA Plugin Ecosystem - Extensible Components**

Official and community plugins that extend PDK functionality with specialized capabilities.

---

## 🎯 **Plugin System Overview**

The PramaIA plugin system provides:
- **Modular Extensions** - Add functionality without core changes
- **Hot-Loading** - Deploy plugins without restarts
- **Universal Interface** - Consistent plugin development patterns
- **Dynamic Discovery** - Automatic plugin registration

---

## 📖 **Available Plugins**

### **Core Plugins** (Official)
- **[Core RAG Plugin](CORE_RAG_PLUGIN.md)** - Advanced RAG operations and optimizations
- **[Workflow Scheduler Plugin](WORKFLOW_SCHEDULER_PLUGIN.md)** - Advanced workflow scheduling and management

### **Development Tools**
- **[Plugin Development Guide](DEVELOPMENT_GUIDE.md)** - Creating custom plugins
- **[PDK Plugin Creation Guide](../PDK/PLUGIN_DEVELOPMENT_GUIDE.md)** - Complete development workflow

---

## 🏗️ **Plugin Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDK Server    │◄──►│  Plugin Loader  │◄──►│   Plugin API    │
│   (Core)        │    │  (Discovery)    │    │  (Interface)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Generic Nodes   │    │ Plugin Registry │    │   Custom Nodes  │
│ (Built-in)      │    │ (plugin.json)   │    │  (Plugin Code)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🚀 **Quick Start**

### **1. Install Plugin**
```bash
# Copy plugin to PDK plugins directory
# Restart PDK server to load plugin
.\start-pdk.ps1
```

### **2. Verify Plugin Registration**
```bash
# Check available plugins
curl http://localhost:3001/api/plugins

# Check plugin nodes  
curl http://localhost:3001/api/nodes
```

### **3. Use Plugin in Workflows**
- Plugin nodes appear in workflow designer
- Configure plugin-specific parameters
- Chain with generic nodes for complete workflows

---

## 🔧 **Core Plugin Details**

### **Core RAG Plugin**
**Purpose:** Advanced RAG operations beyond generic processors
- **Specialized Chunking** - Smart document segmentation
- **Context Optimization** - Intelligent context selection  
- **Response Enhancement** - Advanced response processing
- **Performance Optimizations** - Caching and batching

**Configuration:**
```json
{
  "nodeId": "core-rag-advanced-chunker",
  "config": {
    "chunkSize": 1000,
    "overlap": 200,
    "strategy": "semantic"
  }
}
```

### **Workflow Scheduler Plugin**  
**Purpose:** Advanced workflow scheduling and automation
- **Cron Scheduling** - Complex time-based triggers
- **Dependency Management** - Workflow coordination
- **Resource Management** - Load balancing and queuing
- **Monitoring & Alerts** - Workflow health tracking

**Configuration:**
```json
{
  "nodeId": "workflow-scheduler-cron",
  "config": {
    "schedule": "0 */6 * * *",
    "timezone": "UTC",
    "maxConcurrent": 3
  }
}
```

---

## 🛠️ **Plugin Development**

### **1. Plugin Structure**
```
my-plugin/
├── plugin.json          # Plugin manifest
├── src/
│   ├── nodes/           # Node implementations  
│   ├── utils/           # Helper functions
│   └── index.js         # Main plugin entry
├── tests/               # Plugin tests
├── docs/                # Plugin documentation
└── README.md           # Plugin overview
```

### **2. Plugin Manifest (plugin.json)**
```json
{
  "name": "my-custom-plugin",
  "version": "1.0.0",
  "description": "Custom functionality plugin",
  "author": "Developer Name",
  "nodes": [
    {
      "id": "my-custom-node",
      "name": "My Custom Node", 
      "category": "custom",
      "inputs": [...],
      "outputs": [...],
      "config": {...}
    }
  ],
  "dependencies": {
    "axios": "^1.0.0"
  }
}
```

### **3. Node Implementation**
```javascript
class MyCustomNode {
  constructor(config) {
    this.config = config;
  }
  
  async process(inputs) {
    // Node processing logic
    return outputs;
  }
}

module.exports = MyCustomNode;
```

---

## 📋 **Plugin Registry**

| Plugin Name | Version | Category | Description |
|-------------|---------|----------|-------------|
| Core RAG Plugin | 1.2.0 | RAG | Advanced RAG operations |
| Workflow Scheduler | 1.1.0 | Automation | Advanced scheduling |
| *[Plugin Slots Available]* | - | - | Submit your plugins! |

---

## 🧪 **Plugin Testing**

### **Development Testing**
```bash
# Test plugin loading
node test-plugin-loader.js

# Test individual nodes
npm test -- --plugin=my-plugin

# Integration testing  
.\test_generic_vector_store_processor.py
```

### **Quality Standards**
- **Unit Tests** - All nodes must have tests
- **Documentation** - Complete README and API docs
- **Error Handling** - Graceful failure and recovery
- **Performance** - Reasonable resource usage

---

## 🔗 **Integration Points**

### **With Generic Nodes**
Plugins can:
- **Extend Generic Nodes** - Add specialized behavior
- **Chain with Generic Nodes** - Combine in workflows  
- **Override Generic Behavior** - Replace with optimized versions

### **With Services**
Plugins can:
- **Access VectorStore Service** - Direct database operations
- **Use Log Service** - Centralized logging
- **Call External APIs** - Third-party integrations

---

## 📚 **Development Resources**

- **[Plugin Development Guide](DEVELOPMENT_GUIDE.md)** - Complete development workflow
- **[PDK Plugin Creation Guide](../PDK/PLUGIN_DEVELOPMENT_GUIDE.md)** - PDK-specific development
- **[Node Reference](../PDK/NODES_REFERENCE.md)** - Available node interfaces
- **[API Documentation](../PDK/API_DOCUMENTATION.md)** - PDK API for plugins

---

## 🆘 **Plugin Support**

### **Common Issues**
- **Plugin Not Loading** - Check plugin.json syntax and dependencies
- **Node Not Available** - Verify plugin registration and restart PDK
- **Configuration Errors** - Review node parameter requirements
- **Performance Issues** - Check resource usage and optimize

### **Getting Help**
- Review [Plugin Development Guide](DEVELOPMENT_GUIDE.md)
- Check [PDK API Documentation](../PDK/API_DOCUMENTATION.md)
- See [Testing Guide](../TESTING/README.md) for debugging strategies

**Plugin Registry:** `http://localhost:3001/api/plugins`  
**Development Support:** [Development Guide](../DEVELOPMENT_GUIDE.md)