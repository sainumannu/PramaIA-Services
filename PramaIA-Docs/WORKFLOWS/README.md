# Workflows Documentation

**PramaIA Workflow System - Automated Process Design**

Visual workflow designer and execution engine for creating automated AI workflows using PDK nodes and plugins.

---

## 🎯 **Workflow System Overview**

The PramaIA workflow system enables:
- **Visual Design** - Drag-and-drop workflow creation
- **Event-Driven Execution** - Automatic workflow triggers
- **Node Composition** - Universal processors for any task
- **Template Library** - Reusable workflow patterns

---

## 📖 **Documentation Index**

### **Getting Started**
- **[Templates Guide](TEMPLATES_GUIDE.md)** - Pre-built workflow templates
- **[Workflow Creation Guide](../PDK/WORKFLOW_CREATION_GUIDE.md)** - Step-by-step workflow design
- **[Workflow Tutorial](../PDK/WORKFLOW_TUTORIAL.md)** - Hands-on examples

### **Advanced Topics**
- **[Best Practices](BEST_PRACTICES.md)** - Workflow design patterns
- **[Examples](EXAMPLES/)** - Real-world workflow implementations

---

## 🏗️ **Workflow Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Event Sources  │───►│ Workflow Engine │───►│ Node Processors │
│  (Triggers)     │    │  (Execution)    │    │ (Actions)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ File Monitor    │    │  Workflow UI    │    │ Generic Nodes   │
│ API Webhooks    │    │  Visual Design  │    │ Custom Plugins  │
│ Schedule Tasks  │    │  JSON Config    │    │ Service APIs    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🚀 **Quick Start**

### **1. Create Your First Workflow**
```bash
# Start PDK with workflow UI
.\start-pdk.ps1

# Open workflow designer
http://localhost:3001/workflows
```

### **2. Use Template Library**
1. Browse [Templates Guide](TEMPLATES_GUIDE.md)
2. Copy template configuration
3. Customize for your needs
4. Test and deploy

### **3. Set Up Event Triggers**
- [Event Sources Guide](../PDK/EVENT_SOURCES_GUIDE.md) - Configure triggers
- [File Monitor Setup](../EVENT_SOURCES_TRIGGERS_WORKFLOWS.md) - File-based triggers

---

## 🔧 **Available Workflow Types**

### **Document Processing Workflows**
- Document ingestion and chunking
- Metadata extraction and enrichment  
- Vector embedding generation
- Search index updates

### **RAG (Retrieval-Augmented Generation)**
- Query processing and routing
- Context retrieval from vector stores
- LLM response generation
- Response enhancement and filtering

### **System Maintenance**
- Automated backup procedures
- Log cleanup and archival
- Performance monitoring
- Error detection and reporting

### **Data Pipeline Workflows**  
- ETL (Extract, Transform, Load) processes
- Data validation and cleansing
- Cross-service synchronization
- Batch processing automation

---

## 📋 **Workflow Templates**

| Template | Description | Use Case |
|----------|-------------|-----------|
| **Document Ingestion** | PDF/DOCX → Chunks → Vectors | Document knowledge base |
| **RAG Query Processing** | Query → Context → LLM → Response | Question answering |
| **File Monitor Pipeline** | File Change → Process → Store | Real-time document processing |
| **Batch Vector Update** | Documents → Embeddings → Bulk Insert | Large document imports |
| **System Health Check** | Monitor → Log → Alert | Service monitoring |

See [Templates Guide](TEMPLATES_GUIDE.md) for complete templates.

---

## 🎛️ **Node Types for Workflows**

### **Universal Processors** (PDK Generic Nodes)
- **[Text Processor](../PDK/NODES_REFERENCE.md#text-processor)** - Text chunking, embedding, filtering
- **[Document Processor](../PDK/NODES_REFERENCE.md#document-processor)** - PDF/DOCX/HTML extraction
- **[Vector Store Processor](../PDK/NODES_REFERENCE.md#vectorstore-processor)** - Vector operations
- **[LLM Processor](../PDK/NODES_REFERENCE.md#llm-processor)** - AI model interactions
- **[System Processor](../PDK/NODES_REFERENCE.md#system-processor)** - File and system operations

### **Plugin Nodes**
- **[Core RAG Plugin](../PLUGINS/CORE_RAG_PLUGIN.md)** - Specialized RAG operations
- **[Workflow Scheduler](../PLUGINS/WORKFLOW_SCHEDULER_PLUGIN.md)** - Advanced scheduling

---

## 🧪 **Testing Workflows**

### **Development Testing**
```bash
# Test individual workflow components
.\test_generic_vector_store_processor.py

# Test complete workflow pipelines
.\test_upload_retrieve.ps1
```

### **Integration Testing**
- [Workflow Testing Guide](../TESTING/TEST_SUITE_GUIDE.md)
- [Integration Test Examples](../TESTING/INTEGRATION_TESTS.md)

---

## 🔗 **Related Documentation**

- [PDK Documentation](../PDK/README.md) - Plugin and node system
- [Services Documentation](../SERVICES/README.md) - Backend services
- [Plugins Documentation](../PLUGINS/README.md) - Available plugins
- [Event Sources Guide](../EVENT_SOURCES_TRIGGERS_WORKFLOWS.md) - Trigger setup

---

## 🆘 **Getting Help**

- **Workflow Designer Issues:** Check [PDK API Documentation](../PDK/API_DOCUMENTATION.md)
- **Node Configuration:** See [Nodes Reference](../PDK/NODES_REFERENCE.md)
- **Template Problems:** Review [Best Practices](BEST_PRACTICES.md)
- **Performance Issues:** Check [System Health Workflows](EXAMPLES/)

**Workflow Designer:** `http://localhost:3001/workflows`  
**API Endpoint:** `http://localhost:3001/api/workflows`