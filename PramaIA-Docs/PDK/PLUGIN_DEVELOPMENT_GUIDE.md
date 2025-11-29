# Plugin Development Guide

**Complete Guide to Creating PDK Plugins**

This is the authoritative reference for developing plugins for the PramaIA Plugin Development Kit (PDK).

---

## 📚 **Table of Contents**

1. [Introduction](#introduction)
2. [Plugin Structure](#plugin-structure)
3. [Plugin Configuration (plugin.json)](#plugin-configuration-pluginjson)
4. [Node Processor Implementation](#node-processor-implementation)
5. [Event Sources](#event-sources)
6. [Icons and UI](#icons-and-ui)
7. [Installation and Deployment](#installation-and-deployment)
8. [Testing and Debugging](#testing-and-debugging)
9. [Best Practices](#best-practices)
10. [FAQ and Troubleshooting](#faq-and-troubleshooting)

---

## 📖 **Introduction**

PramaIA-PDK (Plugin Development Kit) is a framework for creating modular plugins that extend PDK system functionality. Each plugin can contain one or more nodes that perform specific operations within workflows.

This guide provides comprehensive information for creating, implementing, and testing functional PDK plugins.

### **Plugin Types**
- **Node Plugins** - Custom processing nodes for workflows
- **Event Source Plugins** - Custom triggers and event generators
- **UI Extension Plugins** - Workflow designer enhancements
- **Utility Plugins** - Shared functionality and helpers

---

## 🏗️ **Plugin Structure**

A PDK plugin requires a specific directory and file structure:

```
my-plugin/                    # Main plugin directory
├── plugin.json               # Main plugin configuration
├── README.md                 # Plugin documentation (recommended)
├── requirements.txt          # Python dependencies (if applicable)
├── package.json              # Node.js dependencies (if applicable)
└── src/                      # Implementation files directory
    ├── plugin.js             # Optional entry point
    ├── nodes/                # Node implementations
    │   ├── node1.js          # First node implementation
    │   ├── node2.js          # Second node implementation
    │   └── utils.js          # Shared utilities
    ├── event-sources/        # Event source implementations
    │   └── my-source.js      # Custom event source
    └── ui/                   # UI components (optional)
        ├── icons/            # Custom icons
        └── components/       # UI components
```

### **Plugin Location**

Plugins must be placed in the PDK's `plugins` directory:

```
PramaIA-PDK/
├── plugins/                  # ALL PLUGINS GO HERE
│   ├── core-rag-plugin/
│   ├── workflow-scheduler/
│   └── my-new-plugin/        # Your new plugin here
├── server/
├── docs/
└── ...
```

---

## ⚙️ **Plugin Configuration (plugin.json)**

The `plugin.json` file defines the plugin's metadata, nodes, and capabilities:

### **Basic Plugin Manifest**
```json
{
  "name": "my-custom-plugin",
  "version": "1.0.0",
  "description": "Custom functionality plugin for specific use cases",
  "author": "Developer Name <email@example.com>",
  "homepage": "https://github.com/user/my-plugin",
  "license": "MIT",
  "keywords": ["pdk", "workflow", "automation"],
  
  "main": "src/plugin.js",
  "engines": {
    "pdk": ">=2.0.0"
  },
  
  "nodes": [
    {
      "id": "my-custom-processor",
      "name": "My Custom Processor",
      "description": "Performs custom data processing",
      "category": "processing",
      "implementation": "src/nodes/custom-processor.js",
      
      "inputs": [
        {
          "name": "data",
          "type": "object",
          "description": "Input data to process",
          "required": true
        }
      ],
      
      "outputs": [
        {
          "name": "result",
          "type": "object", 
          "description": "Processed data result"
        }
      ],
      
      "config": {
        "processing_mode": {
          "type": "string",
          "enum": ["fast", "thorough", "custom"],
          "default": "fast",
          "description": "Processing mode for the operation"
        },
        "batch_size": {
          "type": "integer",
          "minimum": 1,
          "maximum": 1000,
          "default": 100,
          "description": "Number of items to process in each batch"
        }
      },
      
      "ui": {
        "icon": "ui/icons/custom-processor.svg",
        "color": "#4CAF50",
        "category": "Custom Operations"
      }
    }
  ],
  
  "eventSources": [
    {
      "id": "my-event-source",
      "name": "My Event Source",
      "description": "Custom event source for specific triggers",
      "implementation": "src/event-sources/my-source.js",
      "config": {
        "polling_interval": {
          "type": "integer",
          "default": 5000,
          "description": "Polling interval in milliseconds"
        }
      }
    }
  ],
  
  "dependencies": {
    "axios": "^1.4.0",
    "lodash": "^4.17.21"
  },
  
  "peerDependencies": {
    "node": ">=16.0.0"
  }
}
```

### **Configuration Schema**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Unique plugin identifier |
| `version` | string | ✅ | Semantic version (x.y.z) |
| `description` | string | ✅ | Brief plugin description |
| `author` | string | ✅ | Plugin author information |
| `nodes` | array | ✅ | Array of node definitions |
| `eventSources` | array | ⚪ | Array of event source definitions |
| `dependencies` | object | ⚪ | Runtime dependencies |
| `ui` | object | ⚪ | UI customization options |

---

## 🔧 **Node Processor Implementation**

Node processors handle the core logic for data transformation and operations.

### **Basic Node Implementation**
```javascript
// src/nodes/custom-processor.js

class CustomProcessor {
    constructor(config) {
        this.config = config;
        this.processing_mode = config.processing_mode || 'fast';
        this.batch_size = config.batch_size || 100;
    }
    
    async process(inputs) {
        try {
            const { data } = inputs;
            
            // Validate input
            if (!data) {
                throw new Error('Missing required input: data');
            }
            
            // Process based on configuration
            const result = await this.processData(data);
            
            return {
                result: result,
                metadata: {
                    processed_items: Array.isArray(data) ? data.length : 1,
                    processing_mode: this.processing_mode,
                    timestamp: new Date().toISOString()
                }
            };
            
        } catch (error) {
            throw new Error(`Custom processing failed: ${error.message}`);
        }
    }
    
    async processData(data) {
        switch (this.processing_mode) {
            case 'fast':
                return this.fastProcess(data);
            case 'thorough':
                return this.thoroughProcess(data);
            case 'custom':
                return this.customProcess(data);
            default:
                throw new Error(`Unknown processing mode: ${this.processing_mode}`);
        }
    }
    
    async fastProcess(data) {
        // Implement fast processing logic
        return data.map(item => ({ 
            ...item, 
            processed: true,
            method: 'fast' 
        }));
    }
    
    async thoroughProcess(data) {
        // Implement thorough processing logic
        const results = [];
        
        for (let i = 0; i < data.length; i += this.batch_size) {
            const batch = data.slice(i, i + this.batch_size);
            const processed = await this.processBatch(batch);
            results.push(...processed);
        }
        
        return results;
    }
    
    async processBatch(batch) {
        // Process batch with detailed analysis
        return Promise.all(batch.map(async item => {
            // Simulate complex processing
            await this.delay(10); // Simulate processing time
            return { 
                ...item, 
                processed: true,
                method: 'thorough',
                analysis: this.analyzeItem(item)
            };
        }));
    }
    
    async customProcess(data) {
        // Implement custom processing logic
        throw new Error('Custom processing mode not implemented');
    }
    
    analyzeItem(item) {
        // Implement item analysis
        return {
            complexity: Math.random(),
            confidence: Math.random() * 100,
            tags: ['processed', 'analyzed']
        };
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

module.exports = CustomProcessor;
```

### **Advanced Node Features**

#### **Error Handling**
```javascript
class RobustProcessor {
    async process(inputs) {
        try {
            // Main processing logic
            return await this.doProcess(inputs);
        } catch (error) {
            // Log error for debugging
            console.error('Processing error:', error);
            
            // Return error with context
            throw new Error(`${this.constructor.name} failed: ${error.message}`);
        }
    }
    
    async doProcess(inputs) {
        // Validate inputs
        this.validateInputs(inputs);
        
        // Process with retries
        return await this.processWithRetry(inputs, 3);
    }
    
    validateInputs(inputs) {
        const required = ['data'];
        for (const field of required) {
            if (!(field in inputs)) {
                throw new Error(`Missing required input: ${field}`);
            }
        }
    }
    
    async processWithRetry(inputs, maxRetries) {
        let attempt = 0;
        
        while (attempt < maxRetries) {
            try {
                return await this.actualProcess(inputs);
            } catch (error) {
                attempt++;
                if (attempt >= maxRetries) {
                    throw error;
                }
                
                // Wait before retry
                await this.delay(1000 * attempt);
            }
        }
    }
}
```

#### **Performance Optimization**
```javascript
class OptimizedProcessor {
    constructor(config) {
        super(config);
        
        // Initialize caches
        this.cache = new Map();
        this.batchCache = new Map();
        
        // Setup performance monitoring
        this.metrics = {
            processedItems: 0,
            totalTime: 0,
            averageTime: 0
        };
    }
    
    async process(inputs) {
        const startTime = Date.now();
        
        try {
            const result = await this.cachedProcess(inputs);
            
            // Update metrics
            const duration = Date.now() - startTime;
            this.updateMetrics(duration);
            
            return result;
        } catch (error) {
            throw error;
        }
    }
    
    async cachedProcess(inputs) {
        const cacheKey = this.generateCacheKey(inputs);
        
        // Check cache
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }
        
        // Process and cache result
        const result = await this.actualProcess(inputs);
        this.cache.set(cacheKey, result);
        
        return result;
    }
    
    generateCacheKey(inputs) {
        return JSON.stringify(inputs);
    }
    
    updateMetrics(duration) {
        this.metrics.processedItems++;
        this.metrics.totalTime += duration;
        this.metrics.averageTime = this.metrics.totalTime / this.metrics.processedItems;
    }
}
```

---

## ⚡ **Event Sources**

Event sources generate triggers that initiate workflows.

### **Basic Event Source Implementation**
```javascript
// src/event-sources/my-source.js

class MyEventSource {
    constructor(config) {
        this.config = config;
        this.polling_interval = config.polling_interval || 5000;
        this.isRunning = false;
        this.timer = null;
    }
    
    async start(emitEvent) {
        if (this.isRunning) {
            return;
        }
        
        this.isRunning = true;
        this.emitEvent = emitEvent;
        
        console.log('Starting custom event source...');
        
        // Start polling
        this.timer = setInterval(() => {
            this.checkForEvents();
        }, this.polling_interval);
    }
    
    async stop() {
        if (!this.isRunning) {
            return;
        }
        
        this.isRunning = false;
        
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        
        console.log('Custom event source stopped');
    }
    
    async checkForEvents() {
        try {
            // Check for events (implement your logic here)
            const events = await this.detectEvents();
            
            // Emit each event
            for (const event of events) {
                await this.emitEvent(event);
            }
            
        } catch (error) {
            console.error('Event detection error:', error);
        }
    }
    
    async detectEvents() {
        // Implement your event detection logic
        // This example generates random events
        
        const shouldEmit = Math.random() < 0.1; // 10% chance
        
        if (shouldEmit) {
            return [{
                type: 'custom_event',
                source: 'my-event-source',
                timestamp: new Date().toISOString(),
                data: {
                    id: this.generateId(),
                    message: 'Custom event occurred',
                    value: Math.floor(Math.random() * 100)
                }
            }];
        }
        
        return [];
    }
    
    generateId() {
        return 'evt_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

module.exports = MyEventSource;
```

---

## 🎨 **Icons and UI**

Customize the visual appearance of your plugin nodes in the workflow designer.

### **Custom Icons**
```
ui/
├── icons/
│   ├── processor-icon.svg      # Node icon
│   ├── source-icon.svg         # Event source icon
│   └── plugin-logo.png         # Plugin logo
└── themes/
    └── custom-theme.css        # Custom styling
```

### **SVG Icon Example**
```svg
<!-- ui/icons/custom-processor.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#2E7D32;stop-opacity:1" />
    </linearGradient>
  </defs>
  <circle cx="12" cy="12" r="10" fill="url(#grad1)"/>
  <path d="M8 12l2 2 4-4" stroke="white" stroke-width="2" fill="none"/>
</svg>
```

### **UI Configuration in plugin.json**
```json
{
  "nodes": [
    {
      "id": "my-processor",
      "ui": {
        "icon": "ui/icons/custom-processor.svg",
        "color": "#4CAF50",
        "category": "Custom Operations",
        "description": "Advanced data processing with custom algorithms",
        "tags": ["processing", "data", "custom"],
        "displayOptions": {
          "showConfig": true,
          "collapsible": false,
          "resizable": true
        }
      }
    }
  ]
}
```

---

## 🚀 **Installation and Deployment**

### **Local Development Installation**
```bash
# Navigate to PDK plugins directory
cd PramaIA-PDK/plugins

# Create plugin directory
mkdir my-custom-plugin
cd my-custom-plugin

# Initialize plugin
npm init -y  # For Node.js dependencies

# Install dependencies
npm install axios lodash

# Create plugin structure
mkdir -p src/nodes src/event-sources ui/icons
```

### **Plugin Registration**
The PDK automatically discovers and registers plugins at startup:

1. **Automatic Discovery** - PDK scans `plugins/` directory
2. **Plugin Validation** - Validates `plugin.json` format
3. **Node Registration** - Registers nodes with workflow engine
4. **Event Source Setup** - Initializes event sources

### **Hot Reloading (Development)**
```bash
# Restart PDK server to reload plugins
cd PramaIA-PDK
npm run dev

# Or use plugin hot-reload (if available)
curl -X POST http://localhost:3001/api/plugins/reload
```

---

## 🧪 **Testing and Debugging**

### **Unit Testing**
```javascript
// tests/custom-processor.test.js

const CustomProcessor = require('../src/nodes/custom-processor');

describe('CustomProcessor', () => {
    let processor;
    
    beforeEach(() => {
        processor = new CustomProcessor({
            processing_mode: 'fast',
            batch_size: 10
        });
    });
    
    test('should process data correctly', async () => {
        const inputs = {
            data: [
                { id: 1, name: 'Item 1' },
                { id: 2, name: 'Item 2' }
            ]
        };
        
        const result = await processor.process(inputs);
        
        expect(result.result).toHaveLength(2);
        expect(result.result[0]).toHaveProperty('processed', true);
        expect(result.metadata).toHaveProperty('processed_items', 2);
    });
    
    test('should handle missing input gracefully', async () => {
        const inputs = {};
        
        await expect(processor.process(inputs))
            .rejects.toThrow('Missing required input: data');
    });
});
```

### **Integration Testing**
```bash
# Test plugin installation
curl -X GET http://localhost:3001/api/nodes | jq '.[] | select(.id == "my-custom-processor")'

# Test node execution
curl -X POST http://localhost:3001/api/nodes/my-custom-processor/execute \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "data": [{"test": "data"}]
    },
    "config": {
      "processing_mode": "fast"
    }
  }'
```

### **Debugging Tips**
```javascript
// Add debug logging
class DebuggableProcessor {
    constructor(config) {
        super(config);
        this.debug = config.debug || false;
    }
    
    log(message, data) {
        if (this.debug) {
            console.log(`[${this.constructor.name}] ${message}`, data);
        }
    }
    
    async process(inputs) {
        this.log('Processing started', { inputs });
        
        try {
            const result = await super.process(inputs);
            this.log('Processing completed', { result });
            return result;
        } catch (error) {
            this.log('Processing failed', { error: error.message });
            throw error;
        }
    }
}
```

---

## ✨ **Best Practices**

### **1. Configuration Design**
- Use clear, descriptive configuration parameter names
- Provide sensible defaults for all optional parameters
- Validate configuration during node construction
- Document all configuration options thoroughly

### **2. Error Handling**
- Always validate inputs before processing
- Provide meaningful error messages with context
- Use try-catch blocks around external API calls
- Implement retry logic for transient failures

### **3. Performance**
- Cache results when appropriate
- Use batch processing for large datasets
- Monitor memory usage in long-running processes
- Implement timeouts for external operations

### **4. Documentation**
- Write comprehensive README files
- Document all node inputs, outputs, and configuration
- Include usage examples and common patterns
- Keep documentation updated with code changes

### **5. Security**
- Validate and sanitize all inputs
- Use secure methods for handling credentials
- Avoid logging sensitive information
- Follow principle of least privilege

---

## 🆘 **FAQ and Troubleshooting**

### **Common Issues**

#### **Plugin Not Loading**
```bash
# Check plugin directory structure
ls -la PramaIA-PDK/plugins/my-plugin/

# Validate plugin.json syntax
cat PramaIA-PDK/plugins/my-plugin/plugin.json | jq .

# Check PDK logs
tail -f PramaIA-PDK/logs/pdk.log
```

#### **Node Not Available in Workflow Designer**
- Verify plugin.json syntax is correct
- Check that node ID is unique
- Ensure all required fields are present
- Restart PDK server after changes

#### **Runtime Errors**
```javascript
// Add error boundary to node
try {
    return await this.process(inputs);
} catch (error) {
    console.error(`Node ${this.id} error:`, error);
    throw new Error(`Processing failed: ${error.message}`);
}
```

### **Debug Checklist**
- [ ] Plugin directory is in correct location
- [ ] plugin.json syntax is valid
- [ ] All dependencies are installed
- [ ] Node implementation files exist
- [ ] PDK server has been restarted
- [ ] Check console/log output for errors

---

## 🔗 **Related Documentation**

- [PDK API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [Event Sources Guide](EVENT_SOURCES_GUIDE.md) - Event source development
- [Workflow Creation Guide](WORKFLOW_CREATION_GUIDE.md) - Workflow design
- [Node Reference](NODES_REFERENCE.md) - Available node types

---

## 🛠️ **Development Support**

For additional support:
- Check [PDK API Documentation](API_DOCUMENTATION.md) for technical details
- Review [existing plugins](../../plugins/) for implementation examples  
- See [Testing Guide](../TESTING/README.md) for testing strategies

**Plugin Development Resources:**
- API Endpoint: `http://localhost:3001/api/plugins`
- Node Registry: `http://localhost:3001/api/nodes`
- Plugin Manager: `http://localhost:3001/api/plugins/manage`